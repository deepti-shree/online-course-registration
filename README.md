# Online Course Registration System

A beginner-friendly Flask + SQLite academic project with student and administrator modules.

## Features
- Student signup, login and logout with hashed passwords.
- Course catalogue and search.
- Course registration and dropping.
- 24-credit limit and seat tracking.
- Administrator course and student management.
- SQLite transactions and role-based access.
- Automated tests using `unittest`.

## Windows PowerShell setup
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python create_admin.py
python app.py
```
Open http://127.0.0.1:5000

If PowerShell blocks activation:
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.venv\Scripts\Activate.ps1
```

## Administrator
Run `python create_admin.py` and enter your own username and password. Credentials are not hardcoded.

## Database
The database is created automatically on first run as `registration.db`. The schema is in `schema.sql`.
To add sample courses, log in as admin and use Manage Courses.

## Tests
```powershell
python -m unittest discover -s tests -v
```
Tests use a temporary database and do not modify your real database.

## Main routes
- `/` Home
- `/register` Student signup
- `/login` Student login
- `/admin/login` Admin login
- `/student` Student dashboard
- `/courses` Course catalogue
- `/my-courses` Registered courses
- `/admin/` Admin dashboard
- `/admin/courses` Course management
- `/admin/students` Student list

For a classroom deployment, set a strong `SECRET_KEY` environment variable and disable Flask debug mode.
