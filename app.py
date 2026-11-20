
import os
from flask import Flask, render_template
from werkzeug.security import generate_password_hash
from database import init_db, init_app as init_database_app
from auth import auth_bp
from student import student_bp
from admin import admin_bp


def create_app(test_config=None):
    app = Flask(__name__)

    app.config.update(
        SECRET_KEY=os.environ.get("SECRET_KEY", "change-this-development-secret"),
        DATABASE=os.environ.get(
            "DATABASE_PATH",
            os.path.join(app.root_path, "registration.db")
        ),
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
    )

    if test_config:
        app.config.update(test_config)

    init_database_app(app)

    with app.app_context():
        init_db()

        admin_username = os.environ.get("ADMIN_USERNAME")
        admin_password = os.environ.get("ADMIN_PASSWORD")

        if admin_username and admin_password:
            from database import get_db
            db = get_db()

            existing = db.execute(
                "SELECT admin_id FROM admins WHERE username = ?",
                (admin_username,)
            ).fetchone()

            if not existing:
                db.execute(
                    "INSERT INTO admins (username, password_hash) VALUES (?, ?)",
                    (admin_username, generate_password_hash(admin_password))
                )
                db.commit()

    app.register_blueprint(auth_bp)
    app.register_blueprint(student_bp)
    app.register_blueprint(admin_bp)

    @app.route("/")
    def home():
        return render_template("index.html")

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
