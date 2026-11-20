import os
from flask import Flask, render_template
from database import init_db, init_app as init_database_app
from auth import auth_bp
from student import student_bp
from admin import admin_bp

def create_app(test_config=None):
    app = Flask(__name__)
    app.config.update(
        SECRET_KEY=os.environ.get("SECRET_KEY", "change-this-development-secret"),
        DATABASE=os.environ.get("DATABASE_PATH", os.path.join(app.root_path, "registration.db")),
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
    )
    if test_config:
        app.config.update(test_config)
    init_database_app(app)

    with app.app_context():
        init_db()

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
