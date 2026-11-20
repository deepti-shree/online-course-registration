import os
import sqlite3
from flask import current_app, g

def get_db():
    if "db" not in g:
        db_path = current_app.config["DATABASE"]
        os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
        g.db = sqlite3.connect(db_path, timeout=10)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
        g.db.execute("PRAGMA busy_timeout = 10000")
    return g.db

def close_db(exception=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()

def init_db():
    from flask import current_app
    db_path = current_app.config["DATABASE"]
    os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
    db = sqlite3.connect(db_path)
    db.execute("PRAGMA foreign_keys = ON")
    schema_path = os.path.join(current_app.root_path, "schema.sql")
    with open(schema_path, "r", encoding="utf-8") as schema_file:
        db.executescript(schema_file.read())
    db.commit()
    db.close()

def init_app(app):
    app.teardown_appcontext(close_db)
