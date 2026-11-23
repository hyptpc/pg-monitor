#!/usr/bin/env python3
"""Export / restore Grafana configuration without secrets.

  ./grafana-backup.py export              # Grafana -> dashboards/, alerting/, config/
  ./grafana-backup.py restore             # dry run: show what would change
  ./grafana-backup.py restore --apply     # write to Grafana
  ./grafana-backup.py snapshot            # full copy of grafana.db + grafana.ini

Secrets are never written to the repo. They are replaced by ${NAME}
placeholders and filled in on restore from the environment or from
secret.env next to this script (gitignored). See secret.env.example.

snapshot (also run at the end of export) copies the whole Grafana state,
secrets included, to private/ (gitignored, mode 700). It needs read access
to grafana.db and grafana.ini (member of the grafana group). To restore it,
as root: systemctl stop grafana-server; cp the .db to /var/lib/grafana/grafana.db
(owner grafana:grafana, mode 640); put back grafana.ini if needed (its
secret_key must match the db); systemctl start grafana-server.

Environment:
  GRAFANA_URL         default http://localhost:3000
  GRAFANA_TOKEN_FILE  default ./api-token (service account with Admin role)
  GRAFANA_DB          default /var/lib/grafana/grafana.db
  GRAFANA_INI         default /etc/grafana/grafana.ini
  SNAPSHOT_KEEP       number of snapshots kept in private/ (default 10)
"""
import argparse, datetime, json, os, re, shutil, sqlite3, sys
import urllib.error, urllib.parse, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
URL = os.environ.get('GRAFANA_URL', 'http://localhost:3000').rstrip('/')
DASH_DIR = os.path.join(HERE, 'dashboards')
CONF_DIR = os.path.join(HERE, 'config')      # folders, datasources
ALERT_DIR = os.path.join(HERE, 'alerting')   # rules, contact points, policies
PRIV_DIR = os.path.join(HERE, 'private')
GRAFANA_DB = os.environ.get('GRAFANA_DB', '/var/lib/grafana/grafana.db')
GRAFANA_INI = os.environ.get('GRAFANA_INI', '/etc/grafana/grafana.ini')

# Contact point settings that are not secret for Grafana but should not be
# published (personal data). They are stored as placeholders as well.
PRIVATE_KEYS = {'addresses'}
# Datasource fields Grafana manages itself; dropped from the export.
DS_DROP = {'id', 'orgId', 'typeLogoUrl', 'typeName', 'version', 'readOnly',
           'password', 'basicAuthPassword', 'secureJsonFields', 'apiVersion'}
RULE_DROP = {'id', 'updated', 'provenance'}
PLACEHOLDER = re.compile(r'^\$\{([A-Z0-9_]+)\}$')


def token():
  path = os.environ.get('GRAFANA_TOKEN_FILE', os.path.join(HERE, 'api-token'))
  return open(os.path.expanduser(path)).read().strip()


def api(method, path, body=None, ok404=False):
  req = urllib.request.Request(
    URL + '/api/' + path, method=method,
    data=None if body is None else json.dumps(body).encode(),
    headers={'Authorization': f'Bearer {TOKEN}',
             'Content-Type': 'application/json',
             'X-Disable-Provenance': 'true'})
  try:
    with urllib.request.urlopen(req, timeout=30) as r:
      data = r.read()
      return json.loads(data) if data else None
  except urllib.error.HTTPError as e:
    if ok404 and e.code == 404:
      return None
    msg = e.read().decode(errors='replace')[:300]
    raise SystemExit(f'{method} {path}: HTTP {e.code} {msg}')


def q(s):
  return urllib.parse.quote(s, safe='')


def env_name(*parts):
  return re.sub(r'[^A-Z0-9]+', '_', '_'.join(parts).upper()).strip('_')


def dump(path, obj):
  os.makedirs(os.path.dirname(path), exist_ok=True)
  with open(path, 'w') as f:
    json.dump(obj, f, indent=2, ensure_ascii=False, sort_keys=True)
    f.write('\n')


def load(path, default=None):
  if not os.path.exists(path):
    return default
  with open(path) as f:
    return json.load(f)


def safe_title(title):
  return re.sub(r'[^A-Za-z0-9_.-]+', '_', title).strip('_.') or 'untitled'


def json_files(top):
  for root, _, files in os.walk(top):
    for f in files:
      if f.endswith('.json'):
        yield os.path.relpath(os.path.join(root, f), top)


# ---------------------------------------------------------------- export
def export():
  secrets = {}

  folders = [{'uid': f['uid'], 'title': f['title'], 'parentUid': f.get('parentUid')}
             for f in api('GET', 'folders') if f['uid'] != 'sharedwithme']
  dump(f'{CONF_DIR}/folders.json', folders)

  datasources = []
  for d in api('GET', 'datasources'):
    full = api('GET', f"datasources/uid/{q(d['uid'])}")
    out = {k: v for k, v in full.items() if k not in DS_DROP}
    sec = sorted(k for k, v in (full.get('secureJsonFields') or {}).items() if v)
    if sec:
      out['secureJsonData'] = {}
      for k in sec:
        name = env_name('DS', d['name'], k)
        out['secureJsonData'][k] = '${' + name + '}'
        secrets[name] = f"datasource '{d['name']}' {k}"
    datasources.append(out)
  dump(f'{CONF_DIR}/datasources.json', datasources)

  cps = []
  for c in api('GET', 'v1/provisioning/contact-points'):
    c = {k: v for k, v in c.items() if k != 'provenance'}
    for k, v in list(c.get('settings', {}).items()):
      if v == '[REDACTED]' or k in PRIVATE_KEYS:
        name = env_name('CP', c['name'], k)
        c['settings'][k] = '${' + name + '}'
        secrets[name] = f"contact point '{c['name']}' {k}"
    cps.append(c)
  dump(f'{ALERT_DIR}/contact-points.json', cps)

  dump(f'{ALERT_DIR}/notification-policies.json', api('GET', 'v1/provisioning/policies'))
  dump(f'{ALERT_DIR}/mute-timings.json',
       [{k: v for k, v in m.items() if k not in ('provenance', 'version')}
        for m in api('GET', 'v1/provisioning/mute-timings') or []])
  dump(f'{ALERT_DIR}/templates.json',
       [{'name': t['name'], 'template': t['template']}
        for t in api('GET', 'v1/provisioning/templates') or []])

  groups = sorted({(r['folderUID'], r['ruleGroup'])
                   for r in api('GET', 'v1/provisioning/alert-rules')})
  rule_groups = []
  for fuid, gname in groups:
    g = api('GET', f'v1/provisioning/folder/{q(fuid)}/rule-groups/{q(gname)}')
    g['rules'] = [{k: v for k, v in r.items() if k not in RULE_DROP}
                  for r in sorted(g['rules'], key=lambda r: r['uid'])]
    rule_groups.append(g)
  dump(f'{ALERT_DIR}/rule-groups.json', rule_groups)

  # Dashboards: dashboards/<folder>/<title>.json, one directory per Grafana
  # folder (nested folders become nested directories, root is General/).
  # The directory is only for people; restore uses folderUid in the file.
  # Rewrite the whole tree so deleted or moved dashboards disappear too.
  fpath = {}
  def folder_path(uid):
    if not uid:
      return 'General'
    if uid not in fpath:
      f = api('GET', f'folders/{q(uid)}')
      parent = f.get('parentUid')
      fpath[uid] = (folder_path(parent) + '/' if parent else '') + safe_title(f['title'])
    return fpath[uid]
  os.makedirs(DASH_DIR, exist_ok=True)
  old = set(json_files(DASH_DIR))
  new = set()
  for s in api('GET', 'search?type=dash-db&limit=5000'):
    r = api('GET', f"dashboards/uid/{q(s['uid'])}")
    dash = r['dashboard']
    dash.pop('id', None)
    dash.pop('version', None)
    fuid = r['meta'].get('folderUid', '')
    fname = f"{folder_path(fuid)}/{safe_title(dash['title'])}"
    if fname + '.json' in new:  # same title twice in one folder
      fname += '-' + dash['uid']
    fname += '.json'
    dump(f'{DASH_DIR}/{fname}', {'folderUid': fuid, 'dashboard': dash})
    new.add(fname)
  for f in sorted(old - new):
    os.remove(f'{DASH_DIR}/{f}')
    print(f'removed dashboards/{f} (no longer in Grafana or moved)')
  for root, dirs, files in os.walk(DASH_DIR, topdown=False):
    if root != DASH_DIR and not os.listdir(root):
      os.rmdir(root)

  with open(os.path.join(HERE, 'secret.env.example'), 'w') as f:
    f.write('# Copy to secret.env (gitignored, chmod 600) and fill in before restore.\n')
    for name, what in sorted(secrets.items()):
      f.write(f'# {what}\n{name}=\n')

  print(f'exported {len(folders)} folders, {len(datasources)} datasources, '
        f'{len(cps)} contact points, {len(rule_groups)} alert rule groups '
        f'({sum(len(g["rules"]) for g in rule_groups)} rules), {len(new)} dashboards')
  print(f'placeholders: {", ".join(sorted(secrets)) or "none"}')
  snapshot()


# ---------------------------------------------------------------- snapshot
def snapshot():
  """Consistent copy of grafana.db (sqlite online backup) and grafana.ini."""
  for f in (GRAFANA_DB, GRAFANA_INI):
    if not os.access(f, os.R_OK):
      print(f'snapshot skipped: cannot read {f} (add this user to the grafana group '
            'and log in again)')
      return False
  old_umask = os.umask(0o077)
  try:
    os.makedirs(PRIV_DIR, exist_ok=True)
    os.chmod(PRIV_DIR, 0o700)
    stamp = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
    dst = os.path.join(PRIV_DIR, f'grafana-{stamp}')
    src = sqlite3.connect(f'file:{GRAFANA_DB}?mode=ro', uri=True)
    out = sqlite3.connect(dst + '.db')
    with out:
      src.backup(out)
    ok = out.execute('PRAGMA integrity_check').fetchone()[0]
    out.close()
    src.close()
    shutil.copyfile(GRAFANA_INI, dst + '.ini')
  finally:
    os.umask(old_umask)
  if ok != 'ok':
    raise SystemExit(f'snapshot {dst}.db failed integrity check: {ok}')
  print(f'snapshot private/{os.path.basename(dst)}.db/.ini '
        f'({os.path.getsize(dst + ".db") // 1024} KiB)')
  keep = int(os.environ.get('SNAPSHOT_KEEP', '10'))
  stamps = sorted({f[:-3] for f in os.listdir(PRIV_DIR)
                   if f.startswith('grafana-') and f.endswith('.db')})
  for old in stamps[:-keep] if keep > 0 else []:
    for ext in ('.db', '.ini'):
      p = os.path.join(PRIV_DIR, old + ext)
      if os.path.exists(p):
        os.remove(p)
    print(f'removed old snapshot private/{old}')
  return True


# ---------------------------------------------------------------- restore
def read_secrets():
  vals = {}
  path = os.path.join(HERE, 'secret.env')
  if os.path.exists(path):
    for line in open(path):
      line = line.strip()
      if line and not line.startswith('#') and '=' in line:
        k, v = line.split('=', 1)
        vals[k.strip()] = v.strip().strip('"\'')
  vals.update(os.environ)  # environment wins over secret.env
  return vals


def fill(obj, secrets, missing):
  """Replace ${NAME} placeholders; record names that have no value."""
  if isinstance(obj, dict):
    return {k: fill(v, secrets, missing) for k, v in obj.items()}
  if isinstance(obj, list):
    return [fill(v, secrets, missing) for v in obj]
  if isinstance(obj, str):
    m = PLACEHOLDER.match(obj)
    if m:
      if secrets.get(m.group(1)):
        return secrets[m.group(1)]
      missing.add(m.group(1))
  return obj


class Restorer:
  def __init__(self, apply):
    self.apply = apply
    self.secrets = read_secrets()
    self.warnings = []

  def do(self, what, method, path, body=None):
    print(('  ' if self.apply else '  [dry-run] ') + what)
    if self.apply:
      api(method, path, body)

  def warn(self, msg):
    self.warnings.append(msg)
    print('  WARNING: ' + msg)

  def folders(self):
    print('folders')
    for f in load(f'{CONF_DIR}/folders.json', []):
      cur = api('GET', f"folders/{q(f['uid'])}", ok404=True)
      if cur is None:
        self.do(f"create folder {f['title']}", 'POST', 'folders',
                {k: v for k, v in f.items() if v is not None})
      elif cur['title'] != f['title']:
        self.do(f"rename folder {cur['title']} -> {f['title']}", 'PUT',
                f"folders/{q(f['uid'])}", {'title': f['title'], 'overwrite': True})

  def datasources(self):
    print('datasources')
    for d in load(f'{CONF_DIR}/datasources.json', []):
      missing = set()
      body = fill(d, self.secrets, missing)
      cur = api('GET', f"datasources/uid/{q(d['uid'])}", ok404=True)
      if missing:
        body.pop('secureJsonData', None)  # keep whatever Grafana already has
        if cur is None:
          self.warn(f"datasource {d['name']}: no value for {', '.join(sorted(missing))}; "
                    'created without it, set it in the UI or secret.env')
      if cur is None:
        self.do(f"create datasource {d['name']}", 'POST', 'datasources', body)
      else:
        body['version'] = cur.get('version')
        self.do(f"update datasource {d['name']}", 'PUT', f"datasources/uid/{q(d['uid'])}", body)

  def contact_points(self):
    print('contact points')
    cur = api('GET', 'v1/provisioning/contact-points')
    by_uid = {c['uid']: c for c in cur if c.get('uid')}
    by_name = {}
    for c in cur:
      by_name.setdefault((c['name'], c['type']), c)
    for c in load(f'{ALERT_DIR}/contact-points.json', []):
      missing = set()
      body = fill(c, self.secrets, missing)
      exist = by_uid.get(c.get('uid')) or by_name.get((c['name'], c['type']))
      if missing:
        if exist:
          print(f"  keep contact point {c['name']} as is (no value for {', '.join(sorted(missing))})")
        else:
          self.warn(f"contact point {c['name']} not created: no value for {', '.join(sorted(missing))}")
        continue
      if exist and exist.get('uid'):
        self.do(f"update contact point {c['name']}", 'PUT',
                f"v1/provisioning/contact-points/{q(exist['uid'])}", {**body, 'uid': exist['uid']})
      elif exist:
        print(f"  keep contact point {c['name']} (built-in, no uid)")
      else:
        if not body.get('uid'):
          body.pop('uid', None)
        self.do(f"create contact point {c['name']}", 'POST', 'v1/provisioning/contact-points', body)

  def templates_and_mute_timings(self):
    print('templates / mute timings')
    for t in load(f'{ALERT_DIR}/templates.json', []):
      self.do(f"put template {t['name']}", 'PUT', f"v1/provisioning/templates/{q(t['name'])}",
              {'template': t['template']})
    cur = {m['name'] for m in api('GET', 'v1/provisioning/mute-timings') or []}
    for m in load(f'{ALERT_DIR}/mute-timings.json', []):
      if m['name'] in cur:
        self.do(f"update mute timing {m['name']}", 'PUT',
                f"v1/provisioning/mute-timings/{q(m['name'])}", m)
      else:
        self.do(f"create mute timing {m['name']}", 'POST', 'v1/provisioning/mute-timings', m)

  def policies(self):
    print('notification policies')
    p = load(f'{ALERT_DIR}/notification-policies.json')
    if p:
      self.do('replace notification policy tree', 'PUT', 'v1/provisioning/policies', p)

  def dashboards(self):
    print('dashboards')
    for f in sorted(json_files(DASH_DIR)):
      d = load(f'{DASH_DIR}/{f}')
      dash = dict(d['dashboard'], id=None)
      self.do(f"save dashboard {dash['title']}", 'POST', 'dashboards/db',
              {'dashboard': dash, 'folderUid': d.get('folderUid', ''),
               'overwrite': True, 'message': 'restored by grafana-backup.py'})

  def alert_rules(self):
    print('alert rules')
    for g in load(f'{ALERT_DIR}/rule-groups.json', []):
      self.do(f"put rule group {g['title']} ({len(g['rules'])} rules)", 'PUT',
              f"v1/provisioning/folder/{q(g['folderUid'])}/rule-groups/{q(g['title'])}", g)

  def run(self, only):
    steps = ['folders', 'datasources', 'contact_points', 'templates_and_mute_timings',
             'policies', 'dashboards', 'alert_rules']
    for s in steps:
      if not only or s in only:
        getattr(self, s)()
    if not self.apply:
      print('\ndry run only; add --apply to write to', URL)
    for w in self.warnings:
      print('WARNING:', w, file=sys.stderr)


if __name__ == '__main__':
  ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
  sub = ap.add_subparsers(dest='cmd', required=True)
  sub.add_parser('export', help='export config (and take a snapshot if possible)')
  sub.add_parser('snapshot', help='only copy grafana.db + grafana.ini to private/')
  r = sub.add_parser('restore')
  r.add_argument('--apply', action='store_true', help='actually write (default: dry run)')
  r.add_argument('--only', nargs='+', choices=['folders', 'datasources', 'contact_points',
                 'templates_and_mute_timings', 'policies', 'dashboards', 'alert_rules'])
  a = ap.parse_args()
  if a.cmd == 'snapshot':
    sys.exit(0 if snapshot() else 1)
  TOKEN = token()
  if a.cmd == 'export':
    export()
  else:
    Restorer(a.apply).run(a.only)
