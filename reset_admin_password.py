# reset_admin_password.py
from application import app, db
from application.flicket.models.flicket_user import FlicketUser
from application.flicket.scripts.hash_password import hash_password

NEW_PASSWORD = "Password123!"  # pick any password you want

with app.app_context():
    user = FlicketUser.query.filter_by(username="admin").first()
    if not user:
        print("Admin user not found.")
    else:
        user.password = hash_password(NEW_PASSWORD)
        db.session.commit()
        print(f"Password successfully reset to: {NEW_PASSWORD}")