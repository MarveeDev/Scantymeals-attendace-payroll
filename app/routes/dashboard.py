from flask import Blueprint, render_template
from app.auth.decorators import login_required
from app.models.worker import WorkerModel
from app.models.attendance import AttendanceModel
from app.services.time_service import get_current_date, format_date

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
@login_required
def index():
    active_workers = WorkerModel.get_all(active_only=True)
    total_active = len(active_workers)
    
    from app.services.attendance_service import AttendanceService
    
    today = get_current_date()
    today_str = format_date(today)
    
    present_today = 0
    absent_today = 0
    not_marked = 0
    
    for w in active_workers:
        summary = AttendanceService.get_period_summary(w, today, today)
        if summary["eligible_days"] > 0:
            present_today += summary["present_days"]
            absent_today += summary["absent_days"]
            not_marked += summary["not_marked_days"]
    
    # Simple calculation of payroll stats would go here
    # For now we'll pass placeholders
    
    return render_template(
        'dashboard.html',
        total_active=total_active,
        present_today=present_today,
        absent_today=absent_today,
        not_marked=not_marked
    )
