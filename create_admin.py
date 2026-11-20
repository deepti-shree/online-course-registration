import getpass
from werkzeug.security import generate_password_hash
from app import app
from database import get_db

def main():
    with app.app_context():
        username = input("Admin username: ").strip()
        password = getpass.getpass("Admin password (minimum 8 characters): ")
        if not username or len(password) < 8:
            print("Username is required and password must have at least 8 characters.")
            return
        db = get_db()
        try:
            db.execute("INSERT INTO admins (username,password_hash) VALUES (?,?)",
                       (username, generate_password_hash(password)))
            db.commit()
            print("Administrator account created.")
        except Exception:
            db.rollback()
            print("Could not create administrator. Username may already exist.")

if __name__ == "__main__":
    main()
