import os
from pathlib import Path
from flask import Flask
from models import db
from config import Config

def test_db():
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)
    
    print(f"Current Working Directory: {os.getcwd()}")
    print(f"Configured SQLAlchemy URI: {app.config['SQLALCHEMY_DATABASE_URI']}")
    
    with app.app_context():
        try:
            db.create_all()
            print("Successfully initialized database!")
            db_path = Path("submissions/database.db")
            if db_path.exists():
                print(f"Database file found at: {db_path.absolute()}")
            else:
                print("Database file NOT found in submissions folder.")
        except Exception as e:
            print(f"FAILED to initialize database: {e}")

if __name__ == "__main__":
    test_db()
