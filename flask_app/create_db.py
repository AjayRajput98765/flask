from app import app, db  # Import your app and db from app.py

with app.app_context():
    db.create_all()  # Create all tables
