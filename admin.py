from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from functools import wraps
from database import get_db

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if session.get("role") != "admin":
            flash("Administrator access required.", "error")
            return redirect(url_for("auth.admin_login"))
        return view(*args, **kwargs)
    return wrapped

@admin_bp.route("/")
@admin_required
def dashboard():
    db = get_db()
    stats = {
        "students": db.execute("SELECT COUNT(*) FROM students").fetchone()[0],
        "courses": db.execute("SELECT COUNT(*) FROM courses").fetchone()[0],
        "registrations": db.execute("SELECT COUNT(*) FROM registrations WHERE status='active'").fetchone()[0],
    }
    return render_template("admin_dashboard.html", stats=stats)

@admin_bp.route("/courses")
@admin_required
def courses():
    rows = get_db().execute("SELECT * FROM courses ORDER BY course_code").fetchall()
    return render_template("manage_courses.html", courses=rows)

@admin_bp.route("/courses/add", methods=["GET", "POST"])
@admin_required
def add_course():
    if request.method == "POST":
        data = course_form_data()
        error = validate_course(data)
        if error:
            flash(error, "error")
        else:
            db = get_db()
            try:
                db.execute("""INSERT INTO courses
                    (course_code,course_name,description,instructor,credits,total_seats,available_seats)
                    VALUES (?,?,?,?,?,?,?)""",
                    (data["code"], data["name"], data["description"], data["instructor"],
                     data["credits"], data["seats"], data["seats"]))
                db.commit()
                flash("Course added successfully.", "success")
                return redirect(url_for("admin.courses"))
            except Exception:
                db.rollback()
                flash("Course code already exists or course could not be added.", "error")
    return render_template("add_course.html", course=None)

@admin_bp.route("/courses/edit/<int:course_id>", methods=["GET", "POST"])
@admin_required
def edit_course(course_id):
    db = get_db()
    course = db.execute("SELECT * FROM courses WHERE course_id=?", (course_id,)).fetchone()
    if not course:
        flash("Course not found.", "error")
        return redirect(url_for("admin.courses"))
    if request.method == "POST":
        data = course_form_data()
        error = validate_course(data)
        if error:
            flash(error, "error")
        else:
            registered = db.execute("""
                SELECT COUNT(*) FROM registrations WHERE course_id=? AND status='active'
            """, (course_id,)).fetchone()[0]
            if data["seats"] < registered:
                flash("Total seats cannot be lower than current active registrations.", "error")
            else:
                available = data["seats"] - registered
                try:
                    db.execute("""UPDATE courses SET course_code=?,course_name=?,description=?,
                        instructor=?,credits=?,total_seats=?,available_seats=? WHERE course_id=?""",
                        (data["code"], data["name"], data["description"], data["instructor"],
                         data["credits"], data["seats"], available, course_id))
                    db.commit()
                    flash("Course updated successfully.", "success")
                    return redirect(url_for("admin.courses"))
                except Exception:
                    db.rollback()
                    flash("Course could not be updated. Check for duplicate course code.", "error")
    return render_template("edit_course.html", course=course)

@admin_bp.route("/courses/delete/<int:course_id>", methods=["POST"])
@admin_required
def delete_course(course_id):
    db = get_db()
    active = db.execute("SELECT COUNT(*) FROM registrations WHERE course_id=? AND status='active'",
                        (course_id,)).fetchone()[0]
    if active:
        flash("Cannot delete a course with active registrations.", "error")
    else:
        db.execute("DELETE FROM courses WHERE course_id=?", (course_id,))
        db.commit()
        flash("Course deleted.", "success")
    return redirect(url_for("admin.courses"))

@admin_bp.route("/students")
@admin_required
def students():
    rows = get_db().execute("SELECT student_id,name,email,phone,branch,created_at FROM students ORDER BY name").fetchall()
    return render_template("students.html", students=rows)

@admin_bp.route("/courses/<int:course_id>/students")
@admin_required
def course_students(course_id):
    course = get_db().execute("SELECT * FROM courses WHERE course_id=?", (course_id,)).fetchone()
    if not course:
        flash("Course not found.", "error")
        return redirect(url_for("admin.courses"))
    rows = get_db().execute("""
        SELECT s.name,s.email,r.registration_date FROM registrations r
        JOIN students s ON s.student_id=r.student_id
        WHERE r.course_id=? AND r.status='active' ORDER BY s.name
    """, (course_id,)).fetchall()
    return render_template("course_students.html", course=course, students=rows)

def course_form_data():
    form = request.form
    try:
        credits = int(form.get("credits", "0"))
        seats = int(form.get("total_seats", "0"))
    except ValueError:
        credits, seats = 0, -1
    return {
        "code": form.get("course_code", "").strip().upper(),
        "name": form.get("course_name", "").strip(),
        "description": form.get("description", "").strip(),
        "instructor": form.get("instructor", "").strip(),
        "credits": credits,
        "seats": seats,
    }

def validate_course(data):
    if not all([data["code"], data["name"], data["instructor"]]):
        return "Course code, name and instructor are required."
    if not 1 <= data["credits"] <= 24:
        return "Credits must be between 1 and 24."
    if data["seats"] < 0:
        return "Total seats must be zero or greater."
    return None
