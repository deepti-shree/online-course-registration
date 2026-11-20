import re
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from database import get_db

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        phone = request.form.get("phone", "").strip()
        branch = request.form.get("branch", "").strip()
        password = request.form.get("password", "")
        if not all([name, email, phone, branch, password]):
            flash("All fields are required.", "error")
        elif not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
            flash("Enter a valid email address.", "error")
        elif len(password) < 8:
            flash("Password must contain at least 8 characters.", "error")
        else:
            db = get_db()
            try:
                db.execute(
                    "INSERT INTO students (name,email,phone,branch,password_hash) VALUES (?,?,?,?,?)",
                    (name, email, phone, branch, generate_password_hash(password))
                )
                db.commit()
                flash("Account created. Please log in.", "success")
                return redirect(url_for("auth.login"))
            except Exception as exc:
                db.rollback()
                if "UNIQUE constraint failed" in str(exc):
                    flash("This email is already registered.", "error")
                else:
                    flash("Could not create account. Check your details.", "error")
    return render_template("register.html")

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = get_db().execute("SELECT * FROM students WHERE email = ?", (email,)).fetchone()
        if user and check_password_hash(user["password_hash"], password):
            session.clear()
            session["user_id"] = user["student_id"]
            session["user_name"] = user["name"]
            session["role"] = "student"
            return redirect(url_for("student.dashboard"))
        flash("Invalid email or password.", "error")
    return render_template("login.html", admin_login=False)

@auth_bp.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        admin = get_db().execute("SELECT * FROM admins WHERE username = ?", (username,)).fetchone()
        if admin and check_password_hash(admin["password_hash"], password):
            session.clear()
            session["admin_id"] = admin["admin_id"]
            session["user_name"] = admin["username"]
            session["role"] = "admin"
            return redirect(url_for("admin.dashboard"))
        flash("Invalid administrator credentials.", "error")
    return render_template("login.html", admin_login=True)

@auth_bp.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("home"))
