from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from app.services.auth_service import verify_login
from app.models.audit import AuditModel

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        admin = verify_login(username, password)
        if admin:
            session['admin_id'] = str(admin['_id'])
            session['username'] = admin['username']
            AuditModel.log(str(admin['_id']), "Login", "Admin", str(admin['_id']))
            return redirect(url_for('dashboard.index'))
        else:
            flash("Invalid username or password", "error")
            
    return render_template('login.html')

@auth_bp.route('/logout')
def logout():
    admin_id = session.get('admin_id')
    if admin_id:
        AuditModel.log(admin_id, "Logout", "Admin", admin_id)
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for('auth.login'))
