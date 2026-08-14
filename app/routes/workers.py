from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app.auth.decorators import login_required
from app.models.worker import WorkerModel
from app.models.audit import AuditModel
from app.models.salary_history import SalaryHistoryModel
from app.services.time_service import format_date, get_current_date

workers_bp = Blueprint('workers', __name__, url_prefix='/workers')

@workers_bp.route('/')
@login_required
def index():
    active_only = request.args.get('status', 'active') == 'active'
    workers = WorkerModel.get_all(active_only=active_only)
    return render_template('workers/list.html', workers=workers, active_only=active_only)

@workers_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    if request.method == 'POST':
        from app.models.counter import CounterModel
        import re
        
        # Ensure counter is initialized
        existing_counter = CounterModel.collection().find_one({"_id": "staff_id"})
        if not existing_counter:
            workers = WorkerModel.collection().find({}, {"staff_id": 1})
            max_val = 0
            for w in workers:
                match = re.search(r'\d+', w.get("staff_id", ""))
                if match:
                    val = int(match.group())
                    if val > max_val:
                        max_val = val
            CounterModel.init_sequence("staff_id", max_val)
            
        seq = CounterModel.get_next_sequence("staff_id")
        new_staff_id = f"SM{seq:03d}"
        
        data = {
            "staff_id": new_staff_id,
            "full_name": request.form.get("full_name"),
            "phone": request.form.get("phone"),
            "role": request.form.get("role"),
            "date_joined": request.form.get("date_joined"),
            "weekly_salary": request.form.get("weekly_salary", 200),
            "monthly_salary": request.form.get("monthly_salary", 800),
            "notes": request.form.get("notes")
        }
        
        worker_id = WorkerModel.create(data)
        
        # Record initial salary history
        SalaryHistoryModel.record_change(
            worker_id, data["weekly_salary"], data["monthly_salary"], data["date_joined"], session.get('admin_id')
        )
        AuditModel.log(session.get('admin_id'), "Create Worker", "Worker", worker_id, new_value=data["full_name"])
        flash("Worker added successfully", "success")
        return redirect(url_for('workers.index'))
        
    return render_template('workers/add.html', default_date=format_date(get_current_date()))

@workers_bp.route('/<worker_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(worker_id):
    worker = WorkerModel.get_by_id(worker_id)
    if not worker:
        flash("Worker not found", "error")
        return redirect(url_for('workers.index'))
        
    if request.method == 'POST':
        old_weekly = worker.get("weekly_salary")
        old_monthly = worker.get("monthly_salary")
        
        new_weekly = int(request.form.get("weekly_salary", old_weekly))
        new_monthly = int(request.form.get("monthly_salary", old_monthly))
        
        data = {
            "full_name": request.form.get("full_name"),
            "phone": request.form.get("phone"),
            "role": request.form.get("role"),
            "weekly_salary": new_weekly,
            "monthly_salary": new_monthly,
            "notes": request.form.get("notes")
        }
        
        WorkerModel.update(worker_id, data)
        AuditModel.log(session.get('admin_id'), "Edit Worker", "Worker", worker_id)
        
        if old_weekly != new_weekly or old_monthly != new_monthly:
            SalaryHistoryModel.record_change(
                worker_id, new_weekly, new_monthly, format_date(get_current_date()), session.get('admin_id')
            )
            AuditModel.log(session.get('admin_id'), "Salary Changed", "Worker", worker_id, 
                           previous_value=f"W:{old_weekly} M:{old_monthly}", 
                           new_value=f"W:{new_weekly} M:{new_monthly}")
                           
        flash("Worker updated successfully", "success")
        return redirect(url_for('workers.profile', worker_id=worker_id))
        
    return render_template('workers/edit.html', worker=worker)

@workers_bp.route('/<worker_id>/profile')
@login_required
def profile(worker_id):
    worker = WorkerModel.get_by_id(worker_id)
    if not worker:
        flash("Worker not found", "error")
        return redirect(url_for('workers.index'))
        
    # Get histories
    salary_history = SalaryHistoryModel.get_history(worker_id)
    
    from app.services.attendance_service import AttendanceService
    from datetime import datetime
    
    now = datetime.now()
    year = int(request.args.get("year", now.year))
    month = int(request.args.get("month", now.month))
    
    calendar_grid, attendance_summary = AttendanceService.generate_calendar_grid(worker, year, month)
    
    return render_template('workers/profile.html', 
                           worker=worker, 
                           salary_history=salary_history,
                           calendar_grid=calendar_grid,
                           attendance_summary=attendance_summary,
                           current_year=year,
                           current_month=month)

@workers_bp.route('/<worker_id>/deactivate', methods=['POST'])
@login_required
def deactivate(worker_id):
    WorkerModel.deactivate(worker_id, format_date(get_current_date()))
    AuditModel.log(session.get('admin_id'), "Deactivate Worker", "Worker", worker_id)
    flash("Worker deactivated", "success")
    return redirect(url_for('workers.profile', worker_id=worker_id))

@workers_bp.route('/<worker_id>/reactivate', methods=['POST'])
@login_required
def reactivate(worker_id):
    WorkerModel.reactivate(worker_id, format_date(get_current_date()))
    AuditModel.log(session.get('admin_id'), "Reactivate Worker", "Worker", worker_id)
    flash("Worker reactivated", "success")
    return redirect(url_for('workers.profile', worker_id=worker_id))
