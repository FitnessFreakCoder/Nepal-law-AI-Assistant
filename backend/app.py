import datetime
import re
import jwt
import bcrypt
import mysql.connector
from functools import wraps
from flask import Flask, request, jsonify
from flask_cors import CORS
from config import Config
from rag_engine import get_answer, gemini_client

app = Flask(__name__)
app.config.from_object(Config)
CORS(app, supports_credentials=True)

# ──────────────────────────────────────
# Database helpers
# ──────────────────────────────────────

def get_db():
    return mysql.connector.connect(
        host=Config.MYSQL_HOST,
        user=Config.MYSQL_USER,
        password=Config.MYSQL_PASSWORD,
        database=Config.MYSQL_DB
    )


def init_db():
    """Create tables if they don't exist."""
    try:
        conn = mysql.connector.connect(
            host=Config.MYSQL_HOST,
            user=Config.MYSQL_USER,
            password=Config.MYSQL_PASSWORD
        )
        cur = conn.cursor()
        cur.execute("CREATE DATABASE IF NOT EXISTS nepal_law_ai")
        cur.close()
        conn.close()

        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                email VARCHAR(255) NOT NULL UNIQUE,
                password VARCHAR(255) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS chat_sessions (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                title VARCHAR(120) DEFAULT 'New Chat',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INT AUTO_INCREMENT PRIMARY KEY,
                session_id INT NOT NULL,
                role ENUM('user','assistant') NOT NULL,
                content TEXT,
                summary TEXT,
                legal_references TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES chat_sessions(id) ON DELETE CASCADE
            )
        """)
        conn.commit()
        cur.close()
        conn.close()
        print("✅ MySQL database connected successfully!")
        print(f"   Database: {Config.MYSQL_DB} @ {Config.MYSQL_HOST}")
    except mysql.connector.Error as e:
        print(f"❌ MySQL connection failed: {e}")
        raise


# ──────────────────────────────────────
# JWT auth decorator
# ──────────────────────────────────────

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
        if not token:
            return jsonify({"error": "Token is missing"}), 401
        try:
            data = jwt.decode(token, Config.SECRET_KEY, algorithms=["HS256"])
            current_user_id = data["user_id"]
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid token"}), 401
        return f(current_user_id, *args, **kwargs)
    return decorated


# ──────────────────────────────────────
# Input validation helpers
# ──────────────────────────────────────

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def validate_signup(data):
    errors = []
    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip()
    password = data.get("password") or ""
    if not name or len(name) > 100:
        errors.append("Name is required (max 100 chars).")
    if not email or not EMAIL_RE.match(email):
        errors.append("Valid email is required.")
    if len(password) < 6:
        errors.append("Password must be at least 6 characters.")
    return errors


# ──────────────────────────────────────
# Routes
# ──────────────────────────────────────

@app.route("/api/signup", methods=["POST"])
def signup():
    data = request.get_json() or {}
    errors = validate_signup(data)
    if errors:
        return jsonify({"error": "; ".join(errors)}), 400

    name = data["name"].strip()
    email = data["email"].strip().lower()
    password = data["password"]

    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO users (name, email, password) VALUES (%s, %s, %s)",
            (name, email, hashed)
        )
        conn.commit()
    except mysql.connector.IntegrityError:
        return jsonify({"error": "Email already registered."}), 409
    finally:
        cur.close()
        conn.close()

    return jsonify({"message": "Account created successfully."}), 201


@app.route("/api/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not email or not password:
        return jsonify({"error": "Email and password are required."}), 400

    conn = get_db()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM users WHERE email = %s", (email,))
    user = cur.fetchone()
    cur.close()
    conn.close()

    if not user or not bcrypt.checkpw(password.encode("utf-8"), user["password"].encode("utf-8")):
        return jsonify({"error": "Invalid credentials."}), 401

    token = jwt.encode(
        {
            "user_id": user["id"],
            "exp": datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=24)
        },
        Config.SECRET_KEY,
        algorithm="HS256"
    )

    return jsonify({
        "token": token,
        "user": {"id": user["id"], "name": user["name"], "email": user["email"]}
    })


@app.route("/api/ask", methods=["POST"])
@token_required
def ask(current_user_id):
    data = request.get_json() or {}
    question = (data.get("question") or "").strip()
    session_id = data.get("session_id")  # None for first message in new chat

    if not question:
        return jsonify({"error": "Question is required."}), 400
    if len(question) > 2000:
        return jsonify({"error": "Question too long (max 2000 chars)."}), 400

    # Single Gemini call: answer + title + legal check
    result = get_answer(question)
    summary = result.get("summary", "")
    legal_references = result.get("legal_references", "")
    title = result.get("title", question[:60])

    conn = get_db()
    cur = conn.cursor()

    # Create new session if needed
    if not session_id:
        cur.execute(
            "INSERT INTO chat_sessions (user_id, title) VALUES (%s, %s)",
            (current_user_id, title)
        )
        conn.commit()
        session_id = cur.lastrowid
    else:
        # Verify session belongs to user
        cur.execute(
            "SELECT id FROM chat_sessions WHERE id = %s AND user_id = %s",
            (session_id, current_user_id)
        )
        if not cur.fetchone():
            cur.close()
            conn.close()
            return jsonify({"error": "Session not found"}), 404

    # Save user message
    cur.execute(
        "INSERT INTO messages (session_id, role, content) VALUES (%s, 'user', %s)",
        (session_id, question)
    )
    # Save assistant message
    cur.execute(
        "INSERT INTO messages (session_id, role, summary, legal_references) VALUES (%s, 'assistant', %s, %s)",
        (session_id, summary, legal_references)
    )
    conn.commit()
    msg_id = cur.lastrowid
    cur.close()
    conn.close()

    return jsonify({
        "id": msg_id,
        "session_id": session_id,
        "summary": summary,
        "legal_references": legal_references
    })


@app.route("/api/sessions", methods=["GET"])
@token_required
def get_sessions(current_user_id):
    """Get all chat sessions for the user (sidebar history)."""
    conn = get_db()
    cur = conn.cursor(dictionary=True)
    cur.execute(
        "SELECT id, title, created_at, updated_at FROM chat_sessions WHERE user_id = %s ORDER BY updated_at DESC",
        (current_user_id,)
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()
    for row in rows:
        if row.get("created_at"):
            row["created_at"] = row["created_at"].isoformat()
        if row.get("updated_at"):
            row["updated_at"] = row["updated_at"].isoformat()
    return jsonify(rows)


@app.route("/api/sessions/<int:session_id>/messages", methods=["GET"])
@token_required
def get_session_messages(current_user_id, session_id):
    """Get all messages in a chat session."""
    conn = get_db()
    cur = conn.cursor(dictionary=True)
    # Verify ownership
    cur.execute(
        "SELECT id FROM chat_sessions WHERE id = %s AND user_id = %s",
        (session_id, current_user_id)
    )
    if not cur.fetchone():
        cur.close()
        conn.close()
        return jsonify({"error": "Session not found"}), 404

    cur.execute(
        "SELECT id, role, content, summary, legal_references, created_at FROM messages WHERE session_id = %s ORDER BY created_at ASC",
        (session_id,)
    )
    msgs = cur.fetchall()
    cur.close()
    conn.close()
    for m in msgs:
        if m.get("created_at"):
            m["created_at"] = m["created_at"].isoformat()
    return jsonify(msgs)


@app.route("/api/sessions/<int:session_id>", methods=["DELETE"])
@token_required
def delete_session(current_user_id, session_id):
    """Delete a chat session and all its messages."""
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "DELETE FROM chat_sessions WHERE id = %s AND user_id = %s",
        (session_id, current_user_id)
    )
    conn.commit()
    deleted = cur.rowcount
    cur.close()
    conn.close()
    if deleted == 0:
        return jsonify({"error": "Session not found"}), 404
    return jsonify({"message": "Deleted"})


@app.route("/api/sessions", methods=["DELETE"])
@token_required
def clear_sessions(current_user_id):
    """Delete all chat sessions for the user."""
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM chat_sessions WHERE user_id = %s", (current_user_id,))
    conn.commit()
    deleted = cur.rowcount
    cur.close()
    conn.close()
    return jsonify({"message": f"Deleted {deleted} sessions"})


@app.route("/api/me", methods=["GET"])
@token_required
def me(current_user_id):
    conn = get_db()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT id, name, email FROM users WHERE id = %s", (current_user_id,))
    user = cur.fetchone()
    cur.close()
    conn.close()
    if not user:
        return jsonify({"error": "User not found"}), 404
    return jsonify(user)


@app.route("/api/translate", methods=["POST"])
@token_required
def translate_text(current_user_id):
    data = request.get_json()
    text = data.get("text", "").strip()
    if not text:
        return jsonify({"error": "No text provided"}), 400
    try:
        response = gemini_client.models.generate_content(
            model="gemini-2.5-flash",
            contents=f"Translate the following English text to Nepali. Return ONLY the Nepali translation, nothing else:\n\n{text}"
        )
        return jsonify({"translated": response.text.strip()})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ──────────────────────────────────────
# Start
# ──────────────────────────────────────

if __name__ == "__main__":
    print("=" * 50)
    print("  Nepal Law AI Backend")
    print("=" * 50)
    init_db()
    print("✅ RAG engine loaded (ChromaDB)")
    print("✅ All systems ready!")
    print("=" * 50)
    print("🚀 Server running on http://localhost:5000")
    print("=" * 50)
    app.run(debug=True, port=5000)
