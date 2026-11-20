import os
import tempfile
import unittest
from werkzeug.security import generate_password_hash
from app import create_app
from database import get_db

class CourseRegistrationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        db_path = os.path.join(self.temp.name, "test.db")
        self.app = create_app({"TESTING": True, "DATABASE": db_path, "SECRET_KEY": "test-secret"})
        self.client = self.app.test_client()
        with self.app.app_context():
            db = get_db()
            db.execute("INSERT INTO admins (username,password_hash) VALUES (?,?)",
                       ("admin", generate_password_hash("adminpass123")))
            db.execute("INSERT INTO students (name,email,phone,branch,password_hash) VALUES (?,?,?,?,?)",
                       ("Test Student", "student@example.com", "1234567890", "EEE",
                        generate_password_hash("studentpass123")))
            db.execute("""INSERT INTO courses
                (course_code,course_name,description,instructor,credits,total_seats,available_seats)
                VALUES ('CS101','Intro to CS','','Dr A',3,2,2)""")
            db.execute("""INSERT INTO courses
                (course_code,course_name,description,instructor,credits,total_seats,available_seats)
                VALUES ('EE201','Power Systems','','Dr B',22,1,1)""")
            db.execute("""INSERT INTO courses
                (course_code,course_name,description,instructor,credits,total_seats,available_seats)
                VALUES ('ME301','Full Course','','Dr C',2,0,0)""")
            db.commit()

    def tearDown(self):
        self.temp.cleanup()

    def login_student(self):
        return self.client.post("/login", data={"email":"student@example.com","password":"studentpass123"},
                                follow_redirects=True)

    def login_admin(self):
        return self.client.post("/admin/login", data={"username":"admin","password":"adminpass123"},
                                follow_redirects=True)

    def test_student_registration(self):
        response = self.client.post("/register", data={"name":"New Student","email":"new@example.com",
            "phone":"9999999999","branch":"CSE","password":"newpass123"}, follow_redirects=True)
        self.assertIn(b"Account created", response.data)

    def test_duplicate_email_rejected(self):
        response = self.client.post("/register", data={"name":"Duplicate","email":"student@example.com",
            "phone":"9999999999","branch":"CSE","password":"newpass123"}, follow_redirects=True)
        self.assertIn(b"already registered", response.data)

    def test_student_login(self):
        response = self.login_student()
        self.assertIn(b"Welcome", response.data)

    def test_invalid_login(self):
        response = self.client.post("/login", data={"email":"student@example.com","password":"wrong"},
                                    follow_redirects=True)
        self.assertIn(b"Invalid email or password", response.data)

    def test_course_list_requires_login(self):
        response = self.client.get("/courses")
        self.assertEqual(response.status_code, 302)

    def test_course_listing(self):
        self.login_student()
        response = self.client.get("/courses")
        self.assertIn(b"Intro to CS", response.data)

    def test_course_search(self):
        self.login_student()
        response = self.client.get("/courses?q=CS101")
        self.assertIn(b"Intro to CS", response.data)
        self.assertNotIn(b"Power Systems", response.data)

    def test_successful_registration_and_seat_decrement(self):
        self.login_student()
        response = self.client.post("/register-course/1", follow_redirects=True)
        self.assertIn(b"registered successfully", response.data)
        with self.app.app_context():
            self.assertEqual(get_db().execute("SELECT available_seats FROM courses WHERE course_id=1").fetchone()[0], 1)

    def test_duplicate_registration_prevented(self):
        self.login_student()
        self.client.post("/register-course/1")
        response = self.client.post("/register-course/1", follow_redirects=True)
        self.assertIn(b"already registered", response.data)

    def test_full_course_rejected(self):
        self.login_student()
        response = self.client.post("/register-course/3", follow_redirects=True)
        self.assertIn(b"No seats are available", response.data)

    def test_credit_limit_enforced(self):
        self.login_student()
        self.client.post("/register-course/2")
        response = self.client.post("/register-course/1", follow_redirects=True)
        self.assertIn(b"24-credit limit", response.data)

    def test_drop_course_increases_seat(self):
        self.login_student()
        self.client.post("/register-course/1")
        response = self.client.post("/drop-course/1", follow_redirects=True)
        self.assertIn(b"dropped successfully", response.data)
        with self.app.app_context():
            self.assertEqual(get_db().execute("SELECT available_seats FROM courses WHERE course_id=1").fetchone()[0], 2)

    def test_my_courses(self):
        self.login_student()
        self.client.post("/register-course/1")
        response = self.client.get("/my-courses")
        self.assertIn(b"Intro to CS", response.data)

    def test_admin_login(self):
        response = self.login_admin()
        self.assertIn(b"Dashboard", response.data)

    def test_admin_pages_require_admin(self):
        response = self.client.get("/admin/courses")
        self.assertEqual(response.status_code, 302)

    def test_admin_add_course(self):
        self.login_admin()
        response = self.client.post("/admin/courses/add", data={
            "course_code":"MA101","course_name":"Mathematics","instructor":"Dr M",
            "credits":"4","total_seats":"30","description":"Math course"
        }, follow_redirects=True)
        self.assertIn(b"Mathematics", response.data)

    def test_admin_edit_course(self):
        self.login_admin()
        response = self.client.post("/admin/courses/edit/1", data={
            "course_code":"CS101","course_name":"Computer Science","instructor":"Dr A",
            "credits":"3","total_seats":"2","description":"Updated"
        }, follow_redirects=True)
        self.assertIn(b"Computer Science", response.data)

    def test_admin_delete_course(self):
        self.login_admin()
        response = self.client.post("/admin/courses/delete/1", follow_redirects=True)
        self.assertIn(b"Course deleted", response.data)

    def test_admin_cannot_delete_active_course(self):
        self.login_student()
        self.client.post("/register-course/1")
        self.client.get("/logout")
        self.login_admin()
        response = self.client.post("/admin/courses/delete/1", follow_redirects=True)
        self.assertIn(b"Cannot delete", response.data)

    def test_admin_students_page(self):
        self.login_admin()
        response = self.client.get("/admin/students")
        self.assertIn(b"student@example.com", response.data)

    def test_course_registration_view(self):
        self.login_admin()
        response = self.client.get("/admin/courses/1/students")
        self.assertEqual(response.status_code, 200)

    def test_logout_clears_session(self):
        self.login_student()
        self.client.get("/logout")
        response = self.client.get("/student")
        self.assertEqual(response.status_code, 302)

if __name__ == "__main__":
    unittest.main()
