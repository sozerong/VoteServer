from flask import Flask, jsonify, request
from flask_cors import CORS
import sqlite3
import os

app = Flask(__name__)
CORS(app)  # React와 연동 위해 CORS 허용

DB_PATH = "db.sqlite3"

# DB 초기화 함수
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS teams (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            votes INTEGER DEFAULT 0
        )
    ''')
    # 팀이 10개 없으면 초기화
    c.execute("SELECT COUNT(*) FROM teams")
    if c.fetchone()[0] == 0:
        for i in range(1, 11):
            c.execute("INSERT INTO teams (name, votes) VALUES (?, ?)", (f"Team {i}", 0))
    conn.commit()
    conn.close()

# 모든 팀 목록 조회
@app.route("/teams", methods=["GET"])
def get_teams():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, name, votes FROM teams")
    teams = [{"id": row[0], "name": row[1], "votes": row[2]} for row in c.fetchall()]
    conn.close()
    return jsonify(teams)

# 특정 팀에 투표
@app.route("/vote/<int:team_id>", methods=["POST"])
def vote_team(team_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE teams SET votes = votes + 1 WHERE id = ?", (team_id,))
    conn.commit()
    conn.close()
    return jsonify({"success": True, "message": f"Voted for team {team_id}."})

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000)
