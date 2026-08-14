import os
from werkzeug.security import generate_password_hash, check_password_hash
from app.models.admin import AdminModel

def bootstrap_admin():
    """Bootstraps the initial admin user from environment variables if no admin exists."""
    username = os.getenv("ADMIN_USERNAME")
    password = os.getenv("ADMIN_PASSWORD")

    if not username or not password:
        print("Warning: ADMIN_USERNAME or ADMIN_PASSWORD not set in environment.")
        return

    # Check if this admin already exists
    existing = AdminModel.get_by_username(username)
    if not existing:
        print(f"Bootstrapping initial admin account: {username}")
        password_hash = generate_password_hash(password)
        AdminModel.create(username, password_hash)
        print("Initial admin account created successfully.")
    else:
        print(f"Admin account {username} already exists. Skipping bootstrap.")

def verify_login(username, password):
    """Verifies admin login credentials."""
    admin = AdminModel.get_by_username(username)
    if admin and check_password_hash(admin["password_hash"], password):
        return admin
    return None
