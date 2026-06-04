from application.models import User
from application.database import get_db

from werkzeug.security import generate_password_hash

def create_admin():
    db = next(get_db())

    # Check if admin exists
    admin = db.query(User).filter_by(username="admin").first()

    if not admin:
        hashed_pw = generate_password_hash("password123")

        new_admin = User(
            username="admin",
            password=hashed_pw,
            is_admin=True
        )

        db.add(new_admin)
        db.commit()

        print("Admin user created successfully!")
    else:
        print("Admin user already exists.")

if __name__ == "__main__":
    create_admin()