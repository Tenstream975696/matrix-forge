import os
import sqlite3
import psycopg2
from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "matrix_forge_super_secret_key"

DATABASE_URL = os.environ.get("DATABASE_URL")

def get_db_connection():
    if DATABASE_URL:
        return psycopg2.connect(DATABASE_URL)
    return sqlite3.connect("users.db")

def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    if DATABASE_URL:
        c.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                has_paid INTEGER DEFAULT 0
            )
        """)
    else:
        c.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                has_paid INTEGER DEFAULT 0
            )
        """)
    conn.commit()
    conn.close()

init_db()

@app.route("/")
def home():
    return render_template("index.html", username=session.get("username"))

@app.route("/index.html")
def index_redirect():
    return redirect(url_for("home"))

@app.route("/signup.html", methods=["GET"])
def signup_page():
    return render_template("signup.html")

@app.route("/login.html", methods=["GET"])
def login_page():
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))

@app.route("/register", methods=["POST"])
def register():
    username = request.form["username"]
    email = request.form["email"]
    hashed_pw = generate_password_hash(request.form["password"])

    try:
        conn = get_db_connection()
        c = conn.cursor()
        if DATABASE_URL:
            c.execute("INSERT INTO users (username, email, password) VALUES (%s, %s, %s)", (username, email, hashed_pw))
        else:
            c.execute("INSERT INTO users (username, email, password) VALUES (?, ?, ?)", (username, email, hashed_pw))
        conn.commit()
        conn.close()
        
        session["username"] = username
        session["email"] = email
        return redirect(url_for("home"))
    except Exception:
        return "That email is already registered! Go back and Log In."

@app.route("/login", methods=["POST"])
def login():
    email = request.form["email"]
    password = request.form["password"]

    conn = get_db_connection()
    c = conn.cursor()
    if DATABASE_URL:
        c.execute("SELECT username, password FROM users WHERE email = %s", (email,))
    else:
        c.execute("SELECT username, password FROM users WHERE email = ?", (email,))
    user = c.fetchone()
    conn.close()

    if user and check_password_hash(user[1], password):
        session["username"] = user[0]
        session["email"] = email
        return redirect(url_for("home"))
    return "Invalid email or password! Go back and try again."

@app.route("/checkout")
def checkout():
    if "username" not in session:
        return redirect(url_for("signup_page"))
    return render_template("checkout.html", username=session["username"])

if __name__ == "__main__":
    app.run(debug=False)
