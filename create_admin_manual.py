# create_admin_manual.py
import datetime

from application import app, db
from application.flicket.models.flicket_user import FlicketUser
from application.flicket.scripts.hash_password import hash_password

def ensure_admin(username="admin", email="admin@localhost", password="password123"):
    with app.app_context():
        existing = FlicketUser.query.filter_by(username=username).first()
        if existing:
            print(f'Admin "{username}" already exists (email={existing.email}).')
            return

        hashed = hash_password(password)
        user = FlicketUser(
            username=username,
            name=username,
            email=email,
            password=hashed,
            date_added=datetime.datetime.now()
        )

        db.session.add(user)
        db.session.commit()
        print(f'✅ Admin "{username}" created with email "{email}".')

if __name__ == "__main__":
    ensure_admin()