from flask import Flask, jsonify, request
from flask_cors import CORS
import sqlite3
import os
import hashlib

app = Flask(__name__)
CORS(app)

DB_PATH = "db.sqlite3"

# 🔐 해시 생성 함수 (익명화용)
def hash_identifier(student_id, name):
    raw = f"{student_id}_{name}"
    return hashlib.sha256(raw.encode()).hexdigest()

# ✅ DB 초기화 함수
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # 팀 테이블
    c.execute('''
        CREATE TABLE IF NOT EXISTS teams (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            votes INTEGER DEFAULT 0
        )
    ''')

    # 참여자 테이블 (익명 해시 + 실명)
    c.execute('''
        CREATE TABLE IF NOT EXISTS voters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT,
            name TEXT,
            identifier_hash TEXT UNIQUE
        )
    ''')

    # 팀 데이터 초기화
    c.execute("SELECT COUNT(*) FROM teams")
    if c.fetchone()[0] == 0:
        for i in range(1, 11):
            c.execute("INSERT INTO teams (name, votes) VALUES (?, ?)", (f"Team {i}", 0))

    conn.commit()
    conn.close()

# ✅ 팀 목록 조회
@app.route("/teams", methods=["GET"])
def get_teams():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, name, votes FROM teams")
    teams = [{"id": row[0], "name": row[1], "votes": row[2]} for row in c.fetchall()]
    conn.close()
    return jsonify(teams)

# ✅ 투표 가능 여부 확인
@app.route("/can_vote", methods=["POST"])
def can_vote():
    data = request.json
    student_id = data.get("student_id")
    name = data.get("name")
    identifier_hash = hash_identifier(student_id, name)

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT 1 FROM voters WHERE identifier_hash = ?", (identifier_hash,))
    already_voted = c.fetchone() is not None
    conn.close()

    return jsonify({"can_vote": not already_voted})

# ✅ 투표 처리
@app.route("/vote/<int:team_id>", methods=["POST"])
def vote_team(team_id):
    data = request.json
    student_id = data.get("student_id")
    name = data.get("name")
    identifier_hash = hash_identifier(student_id, name)

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # 중복 확인
    c.execute("SELECT 1 FROM voters WHERE identifier_hash = ?", (identifier_hash,))
    if c.fetchone():
        conn.close()
        return jsonify({"success": False, "message": "이미 투표하셨습니다."}), 403

    # 투표 반영 + 참여자 기록 저장
    c.execute("UPDATE teams SET votes = votes + 1 WHERE id = ?", (team_id,))
    c.execute("INSERT INTO voters (student_id, name, identifier_hash) VALUES (?, ?, ?)",
              (student_id, name, identifier_hash))
    conn.commit()
    conn.close()

    return jsonify({"success": True, "message": f"{team_id}번 팀에 투표 완료"})

# ✅ 간단 결과 조회 (팀별)
@app.route("/results", methods=["GET"])
def get_results():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT name, votes FROM teams ORDER BY votes DESC")
    results = [{"name": row[0], "votes": row[1]} for row in c.fetchall()]
    conn.close()
    return jsonify(results)

# ✅ 전체 결과 조회 (팀 + 참여자)
@app.route("/results_full", methods=["GET"])
def results_full():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("SELECT name, votes FROM teams ORDER BY votes DESC")
    teams = [{"name": row[0], "votes": row[1]} for row in c.fetchall()]

    c.execute("SELECT student_id, name FROM voters")
    voters = [{"student_id": row[0], "name": row[1]} for row in c.fetchall()]

    conn.close()
    return jsonify({"teams": teams, "voters": voters})

# ✅ 투표 및 기록 초기화
@app.route("/reset", methods=["POST"])
def reset_votes():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE teams SET votes = 0")
    c.execute("DELETE FROM voters")
    conn.commit()
    conn.close()
    return jsonify({"success": True, "message": "모든 투표 및 참여 기록이 초기화되었습니다."})

# ✅ 서버 실행
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
