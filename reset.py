# reset_votes.py
import sqlite3

conn = sqlite3.connect("db.sqlite3")
c = conn.cursor()
c.execute("UPDATE teams SET votes = 0")
conn.commit()
conn.close()

print("✅ 모든 투표 수가 0으로 초기화되었습니다.")
