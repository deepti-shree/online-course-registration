from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from functools import wraps
from database import get_db

student_bp = Blueprint("student", __name__)

def student_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if session.get("role") != "student":
            flash("Please log in as a student.", "error")
            return redirect(url_for("auth.login"))
        return view(*args, **kwargs)
    return wrapped

@student_bp.route("/student")
@student_required
def dashboard():
    db = get_db()
    student_id = session["user_id"]
    courses = db.execute("""
        SELECT c.*, r.registration_date FROM registrations r
        JOIN courses c ON c.course_id = r.course_id
        WHERE r.student_id = ? AND r.status = 'active'
        ORDER BY c.course_name
    """, (student_id,)).fetchall()
    credits = sum(course["credits"] for course in courses)
    return render_template("student_dashboard.html", courses=courses, credits=credits)

@student_bp.route("/courses")
@student_required
def courses():
    search = request.args.get("q", "").strip()
    db = get_db()
    rows = db.execute("""
        SELECT * FROM courses
        WHERE course_name LIKE ? OR course_code LIKE ?
        ORDER BY course_code
    """, (f"%{search}%", f"%{search}%")).fetchall()
    return render_template("courses.html", courses=rows, search=search)

@student_bp.route("/register-course/<int:course_id>", methods=["POST"])
@student_required
def register_course(course_id):
    db = get_db()
    student_id = session["user_id"]
    try:
        # BEGIN IMMEDIATE serializes writers so seats cannot be overbooked.
        db.execute("BEGIN IMMEDIATE")
        course = db.execute("SELECT * FROM courses WHERE course_id = ?", (course_id,)).fetchone()
        if course is None:
            raise ValueError("Course not found.")
        existing = db.execute(
            "SELECT registration_id FROM registrations WHERE student_id=? AND course_id=? AND status='active'",
            (student_id, course_id)
        ).fetchone()
        if existing:
            raise ValueError("You are already registered for this course.")
        total = db.execute("""
            SELECT COALESCE(SUM(c.credits),0) AS credits
            FROM registrations r JOIN courses c ON c.course_id=r.course_id
            WHERE r.student_id=? AND r.status='active'
        """, (student_id,)).fetchone()["credits"]
        if total + course["credits"] > 24:
            raise ValueError("Registration would exceed the 24-credit limit.")
        if course["available_seats"] <= 0:
            raise ValueError("No seats are available in this course.")
        db.execute("UPDATE courses SET available_seats=available_seats-1 WHERE course_id=?", (course_id,))
        # Reactivate a previously dropped registration rather than violating UNIQUE.
        old = db.execute(
            "SELECT registration_id FROM registrations WHERE student_id=? AND course_id=?",
            (student_id, course_id)
        ).fetchone()
        if old:
            db.execute("UPDATE registrations SET status='active', registration_date=CURRENT_TIMESTAMP WHERE registration_id=?",
                       (old["registration_id"],))
        else:
            db.execute("INSERT INTO registrations (student_id,course_id,status) VALUES (?,?, 'active')",
                       (student_id, course_id))
        db.commit()
        flash("Course registered successfully.", "success")
    except ValueError as exc:
        db.rollback()
        flash(str(exc), "error")
    except Exception:
        db.rollback()
        flash("Registration failed. Please try again.", "error")
    return redirect(url_for("student.courses"))

@student_bp.route("/drop-course/<int:course_id>", methods=["POST"])
@student_required
def drop_course(course_id):
    db = get_db()
    student_id = session["user_id"]
    try:
        db.execute("BEGIN IMMEDIATE")
        registration = db.execute("""
            SELECT registration_id FROM registrations
            WHERE student_id=? AND course_id=? AND status='active'
        """, (student_id, course_id)).fetchone()
        if not registration:
            raise ValueError("Active registration not found.")
        db.execute("UPDATE registrations SET status='dropped' WHERE registration_id=?",
                   (registration["registration_id"],))
        db.execute("UPDATE courses SET available_seats=MIN(total_seats, available_seats+1) WHERE course_id=?",
                   (course_id,))
        db.commit()
        flash("Course dropped successfully.", "success")
    except ValueError as exc:
        db.rollback()
        flash(str(exc), "error")
    except Exception:
        db.rollback()
        flash("Could not drop the course.", "error")
    return redirect(url_for("student.dashboard"))

@student_bp.route("/my-courses")
@student_required
def my_courses():
    rows = get_db().execute("""
        SELECT c.*, r.registration_date FROM registrations r
        JOIN courses c ON c.course_id=r.course_id
        WHERE r.student_id=? AND r.status='active'
        ORDER BY r.registration_date DESC
    """, (session["user_id"],)).fetchall()
    credits = sum(row["credits"] for row in rows)
    return render_template("my_courses.html", courses=rows, credits=credits)
