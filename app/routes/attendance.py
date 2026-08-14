from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app.auth.decorators import login_required
from app.models.worker import WorkerModel
from app.models.attendance import AttendanceModel
from app.models.audit import AuditModel
from app.services.time_service import get_current_date, format_date

attendance_bp = Blueprint('attendance', __name__, url_prefix='/attendance')

@attendance_bp.route('/', methods=['GET', 'POST'])
@login_required
def index():
    selected_date_str = request.args.get('date', format_date(get_current_date()))
    
    from app.services.attendance_service import AttendanceService
    from app.services.time_service import parse_date
    
    selected_date = parse_date(selected_date_str)
    all_workers = WorkerModel.get_all(active_only=False)
    
    # Filter workers based on employment period intersection
    valid_workers = []
    for w in all_workers:
        if AttendanceService.is_date_eligible(selected_date, w.get('employment_periods', [])):
            valid_workers.append(w)
            
    # Get current attendance for selected date
    attendance_records = AttendanceModel.get_by_date(selected_date_str)
    att_map = {str(r['worker_id']): r for r in attendance_records}
    
    return render_template('attendance/index.html', 
                           date=selected_date_str, 
                           workers=valid_workers, 
                           att_map=att_map)

@attendance_bp.route('/mark', methods=['POST'])
@login_required
def mark():
    date_str = request.form.get('date')
    worker_id = request.form.get('worker_id')
    status = request.form.get('status')
    
    from app.services.attendance_service import AttendanceService
    from app.services.time_service import parse_date
    
    worker = WorkerModel.get_by_id(worker_id)
    selected_date = parse_date(date_str)
    
    if not worker or not AttendanceService.is_date_eligible(selected_date, worker.get('employment_periods', [])):
        flash("Invalid worker or date is outside employment periods", "error")
        return redirect(url_for('attendance.index', date=date_str))
        
    _, action, old_status = AttendanceModel.upsert_attendance(worker_id, date_str, status, session.get('admin_id'))
    
    if action == "updated":
        AuditModel.log(session.get('admin_id'), "Edit Attendance", "Attendance", worker_id, 
                       previous_value=f"{date_str}: {old_status}", 
                       new_value=f"{date_str}: {status}")
    
    return redirect(url_for('attendance.index', date=date_str))

@attendance_bp.route('/mark_all', methods=['POST'])
@login_required
def mark_all():
    date_str = request.form.get('date')
    from app.services.attendance_service import AttendanceService
    from app.services.time_service import parse_date
    
    all_workers = WorkerModel.get_all(active_only=False)
    admin_id = session.get('admin_id')
    selected_date = parse_date(date_str)
    
    for w in all_workers:
        if AttendanceService.is_date_eligible(selected_date, w.get('employment_periods', [])):
            # Check if not already marked
            existing = AttendanceModel.get_by_worker_and_date(w['_id'], date_str)
            if not existing:
                AttendanceModel.upsert_attendance(w['_id'], date_str, 'present', admin_id)
                
    flash(f"Unmarked active workers were marked Present for {date_str}", "success")
    return redirect(url_for('attendance.index', date=date_str))
