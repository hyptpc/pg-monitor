import psycopg2
import ROOT
import array
from datetime import date, timedelta

# DB接続設定
conn = psycopg2.connect(
    host="localhost", dbname="your_db", user="your_user", password="your_pass"
)
cur = conn.cursor()

# 対象とするテーブル名一覧（明示または自動収集でも可）
table_names = ["magnet", "hyptpc", "detectors"]  # 例

# 日付範囲設定
start_date = date(2025, 5, 1)
end_date = date(2025, 5, 5)
delta = timedelta(days=1)

while start_date <= end_date:
    day_str = start_date.isoformat()
    print(f"== {day_str} ==")

    # ROOTファイルを1日単位で作成
    f = ROOT.TFile(f"{day_str}.root", "RECREATE")

    for table in table_names:
        # カラム一覧を取得（timestamp除外）
        cur.execute(f"""
            SELECT column_name FROM information_schema.columns
            WHERE table_name = %s AND column_name != 'timestamp'
            ORDER BY ordinal_position
        """, (table,))
        column_names = [row[0] for row in cur.fetchall()]

        # データ取得
        cur.execute(
            f"SELECT timestamp, {', '.join(column_names)} FROM {table} "
            f"WHERE timestamp::date = %s ORDER BY timestamp",
            (day_str,)
        )
        rows = cur.fetchall()
        if not rows:
            print(f"  - {table}: データなし")
            continue

        print(f"  - {table}: {len(rows)}行")

        # TTree作成（テーブル名をTTree名に）
        tree = ROOT.TTree(table, f"Data from {table} on {day_str}")

        # ブランチの用意
        arrays = {
            "timestamp": array.array("d", [0.0])
        }
        tree.Branch("timestamp", arrays["timestamp"], "timestamp/D")

        for name in column_names:
            arrays[name] = array.array("f", [0.0])
            tree.Branch(name, arrays[name], f"{name}/F")

        for row in rows:
            arrays["timestamp"][0] = row[0].timestamp()
            for i, name in enumerate(column_names):
                arrays[name][0] = row[i + 1]
            tree.Fill()

        tree.Write()

    f.Close()
    start_date += delta

cur.close()
conn.close()
