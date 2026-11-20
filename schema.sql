CREATE TABLE IF NOT EXISTS students (
    student_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE COLLATE NOCASE,
    phone TEXT NOT NULL,
    branch TEXT NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS admins (
    admin_id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE COLLATE NOCASE,
    password_hash TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS courses (
    course_id INTEGER PRIMARY KEY AUTOINCREMENT,
    course_code TEXT NOT NULL UNIQUE COLLATE NOCASE,
    course_name TEXT NOT NULL,
    description TEXT DEFAULT '',
    instructor TEXT NOT NULL,
    credits INTEGER NOT NULL CHECK (credits > 0 AND credits <= 24),
    total_seats INTEGER NOT NULL CHECK (total_seats >= 0),
    available_seats INTEGER NOT NULL CHECK (available_seats >= 0 AND available_seats <= total_seats)
);

CREATE TABLE IF NOT EXISTS registrations (
    registration_id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL REFERENCES students(student_id) ON DELETE RESTRICT,
    course_id INTEGER NOT NULL REFERENCES courses(course_id) ON DELETE RESTRICT,
    registration_date TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'dropped')),
    UNIQUE(student_id, course_id)
);

CREATE INDEX IF NOT EXISTS idx_registrations_student ON registrations(student_id);
CREATE INDEX IF NOT EXISTS idx_registrations_course ON registrations(course_id);
