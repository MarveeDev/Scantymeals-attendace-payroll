from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app.auth.decorators import login_required
from app.models.settings import SettingsModel
from app.models.audit import AuditModel

settings_bp = Blueprint('settings', __name__, url_prefix='/settings')

@settings_bp.route('/', methods=['GET', 'POST'])
@login_required
def index():
    settings = SettingsModel.get_settings()
    
    if request.method == 'POST':
        data = {
            "default_weekly_salary": request.form.get("default_weekly_salary"),
            "default_monthly_salary": request.form.get("default_monthly_salary"),
            "absence_deduction_method": request.form.get("absence_deduction_method"),
            "absence_deduction_value": request.form.get("absence_deduction_value")
        }
        
        SettingsModel.update_settings(data, session.get('admin_id'))
        AuditModel.log(session.get('admin_id'), "Update Settings", "Settings", "global_config")
        
        flash("Settings updated successfully", "success")
        return redirect(url_for('settings.index'))
        
    return render_template('settings/index.html', settings=settings)
