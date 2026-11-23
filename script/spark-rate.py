#!/usr/bin/env python

import psycopg
from datetime import datetime, timezone
import numpy as np
import ROOT

t_from = datetime(2025, 10, 2, 0, 0, 0, tzinfo=timezone.utc)
t_to   = datetime(2025, 10, 2, 23, 59, 59, tzinfo=timezone.utc)

from myenv import db_config

sql = """
SELECT t AS time, n AS count,
       GREATEST(n - sqrt(n), 0.0) AS lower,
       n + sqrt(n) AS upper
FROM (
  SELECT
    time_bucket('10 min', "timestamp" - interval '5 min') + interval '5 min' AS t,
    COALESCE(count(*), 0)::double precision AS n
  FROM spark
  WHERE "timestamp" >= %(t_from)s AND "timestamp" <= %(t_to)s
  GROUP BY 1
) s
ORDER BY 1;
"""

with psycopg.connect(**db_config) as conn:
  with conn.cursor() as cur:
    cur.execute(sql, {"t_from": t_from, "t_to": t_to})
    rows = cur.fetchall()

# rows: [(datetime, count, lower, upper), ...]
times  = np.array([r[0].timestamp() for r in rows], dtype="float64")  # Unix time [s]
counts = np.array([r[1] for r in rows], dtype="float64")
lower  = np.array([r[2] for r in rows], dtype="float64")
upper  = np.array([r[3] for r in rows], dtype="float64")

# 非対称誤差（y方向）
yerr_low  = counts - lower
yerr_high = upper  - counts

# x方向の誤差は 5min
xerr = np.full_like(times, 300.0)

# ====== PyROOT: TGraphAsymmErrors を作る ======
g = ROOT.TGraphAsymmErrors(
  len(times),
  times, counts,      # x, y
  xerr, xerr,       # exlow, exhigh
  yerr_low, yerr_high # eylow, eyhigh
)

# 軸の時間表示を有効化
g.GetXaxis().SetTimeDisplay(1)
# g.GetXaxis().SetTimeOffset(0, "gmt")
g.GetXaxis().SetTimeFormat("%m/%d %H:%M")  # 好みで
g.SetTitle("Spark rate (10-min bins);time;count")
ROOT.gStyle.SetEndErrorSize(0)

def style_for_slides(g: ROOT.TGraphAsymmErrors, title="spark events (10-min bins)"):
  # ===== Canvas 大きめ（16:9） =====
  c = ROOT.TCanvas("c", "slides", 1600, 900)

  # ===== 余白（文字が切れないよう広め） =====
  ROOT.gStyle.SetPadLeftMargin(0.16)
  ROOT.gStyle.SetPadRightMargin(0.05)
  ROOT.gStyle.SetPadBottomMargin(0.16)
  ROOT.gStyle.SetPadTopMargin(0.10)

  # ===== フォント・サイズ（見やすい標準フォント 42） =====
  for ax in (g.GetXaxis(), g.GetYaxis()):
      ax.SetLabelFont(42)
      ax.SetTitleFont(42)
      ax.SetLabelSize(0.055)   # 目盛り数字
      ax.SetTitleSize(0.070)   # 軸タイトル
  g.GetXaxis().SetTitleOffset(1.2)
  g.GetYaxis().SetTitleOffset(1.25)

  # ===== タイトル（TLatexで大きめ） =====
  latex = ROOT.TLatex()
  latex.SetNDC(True)
  latex.SetTextFont(42)
  latex.SetTextSize(0.060)
  # 上余白内に描く
  def draw_title():
      latex.DrawLatex(0.16, 0.94, title)

  # ===== 線・マーカー・エラーバー =====
  g.SetLineWidth(4)       # 線を太く
  g.SetMarkerStyle(20)    # 丸
  g.SetMarkerSize(1.8)    # 大きめ
  # g.SetEndErrorSize(0)    # 先端キャップ消す（ユーザー要望）
  ROOT.gStyle.SetLineWidth(2)

  # ===== グリッド＆目盛り =====
  c.SetGridx(True)
  c.SetGridy(True)
  g.GetXaxis().SetNdivisions(508, True)   # 目盛り数を適度に
  g.GetYaxis().SetNdivisions(510, True)

  # ===== 時間軸表示 =====
  g.GetXaxis().SetTimeDisplay(1)
  g.GetXaxis().SetTimeFormat("%m/%d\n %H:%M")
  # UTC表示にしたい場合は次を有効化：
  # g.GetXaxis().SetTimeOffset(0, "gmt")

  # ===== 軸タイトル（適宜変更）=====
  g.SetTitle("")
  g.GetXaxis().SetTitle("time")
  g.GetYaxis().SetTitle("count")

  # ===== 描画 =====
  g.Draw("AP")    # 点＋誤差棒
  draw_title()
  c.Update()

  # ===== 保存（大きめPNG & PDF） =====
  # c.SaveAs("spark_10min_tgraph_slides.png")
  # c.SaveAs("spark_10min_tgraph_slides.pdf")
  return c

# ====== Draw ======
c = style_for_slides(g)
g.Draw("AP")
c.Update()
c.SaveAs("/tmp/spark_10min_tgraph.pdf")
c.SaveAs("/tmp/spark_10min_tgraph.png")

