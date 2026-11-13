import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "matrix_forge_super_secret_key"

def init_db():
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
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

@app.route("/")
def home():
    # Pass the logged-in username (if any) to the landing page
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
        conn = sqlite3.connect("users.db")
        c = conn.cursor()
        c.execute("INSERT INTO users (username, email, password) VALUES (?, ?, ?)", (username, email, hashed_pw))
        conn.commit()
        conn.close()
        
        session["username"] = username
        session["email"] = email
        # Send them back to the landing page after signing up
        return redirect(url_for("home"))
    except sqlite3.IntegrityError:
        return "That email is already registered! Go back and Log In."

@app.route("/login", methods=["POST"])
def login():
    email = request.form["email"]
    password = request.form["password"]

    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("SELECT username, password FROM users WHERE email = ?", (email,))
    user = c.fetchone()
    conn.close()

    if user and check_password_hash(user[1], password):
        session["username"] = user[0]
        session["email"] = email
        # Send them back to the landing page after logging in
        return redirect(url_for("home"))
    return "Invalid email or password! Go back and try again."

@app.route("/checkout")
def checkout():
    # Require an account before buying so we know who owns the game
    if "username" not in session:
        return redirect(url_for("signup_page"))
    return render_template("checkout.html", username=session["username"])

if __name__ == "__main__":
    init_db()
    app.run(debug=False)
