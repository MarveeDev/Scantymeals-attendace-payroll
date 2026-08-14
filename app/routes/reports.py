from flask import Blueprint, render_template, request, Response, session
from app.auth.decorators import login_required
from app.models.worker import WorkerModel
from app.models.attendance import AttendanceModel
from app.models.payroll import PayrollModel
from app.models.payment import PaymentModel
import csv
import io

reports_bp = Blueprint('reports', __name__, url_prefix='/reports')

@reports_bp.route('/')
@login_required
def index():
    return render_template('reports/index.html')

@reports_bp.route('/attendance')
@login_required
def attendance():
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    worker_id = request.args.get('worker_id')
    
    workers = WorkerModel.get_all(active_only=False)
    
    records = []
    if start_date and end_date:
        from app.services.attendance_service import AttendanceService
        from app.services.time_service import parse_date
        s_date = parse_date(start_date)
        e_date = parse_date(end_date)
        
        for w in workers:
            if worker_id and str(w['_id']) != worker_id:
                continue
            
            summary = AttendanceService.get_period_summary(w, s_date, e_date)
            if summary["eligible_days"] > 0:
                summary["worker"] = w
                records.append(summary)
            
    return render_template('reports/attendance.html', workers=workers, records=records, start_date=start_date, end_date=end_date, worker_id=worker_id)

@reports_bp.route('/attendance/export/summary')
@login_required
def export_attendance_summary():
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    worker_id = request.args.get('worker_id')
    
    workers = WorkerModel.get_all(active_only=False)
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Staff ID', 'Worker', 'Eligible Days', 'Marked Days', 'Present Days', 'Absent Days', 'Not Marked Days', 'Attendance Rate'])
    
    if start_date and end_date:
        from app.services.attendance_service import AttendanceService
        from app.services.time_service import parse_date
        s_date = parse_date(start_date)
        e_date = parse_date(end_date)
        
        for w in workers:
            if worker_id and str(w['_id']) != worker_id:
                continue
            summary = AttendanceService.get_period_summary(w, s_date, e_date)
            if summary["eligible_days"] > 0:
                writer.writerow([
                    w['staff_id'], 
                    w['full_name'], 
                    summary['eligible_days'],
                    summary['marked_days'],
                    summary['present_days'],
                    summary['absent_days'],
                    summary['not_marked_days'],
                    f"{summary['attendance_rate']}%"
                ])
        
    return Response(output.getvalue(), mimetype="text/csv", headers={"Content-Disposition": "attachment;filename=attendance_summary_report.csv"})

@reports_bp.route('/attendance/export/detailed')
@login_required
def export_attendance_detailed():
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    worker_id = request.args.get('worker_id')
    
    workers = WorkerModel.get_all(active_only=False)
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Staff ID', 'Worker', 'Date', 'Status', 'Eligibility'])
    
    if start_date and end_date:
        from app.services.attendance_service import AttendanceService
        from app.services.time_service import parse_date, format_date
        from datetime import timedelta
        s_date = parse_date(start_date)
        e_date = parse_date(end_date)
        days_in_period = (e_date - s_date).days + 1
        
        for w in workers:
            if worker_id and str(w['_id']) != worker_id:
                continue
            
            summary = AttendanceService.get_period_summary(w, s_date, e_date)
            if summary["eligible_days"] > 0:
                records_dict = summary["records_by_date"]
                for i in range(days_in_period):
                    d = s_date + timedelta(days=i)
                    d_str = format_date(d)
                    
                    is_eligible = AttendanceService.is_date_eligible(d, w.get("employment_periods", []))
                    if is_eligible:
                        status = "Not Marked"
                        if d_str in records_dict:
                            status = records_dict[d_str].capitalize()
                        writer.writerow([w['staff_id'], w['full_name'], d_str, status, 'Eligible'])
        
    return Response(output.getvalue(), mimetype="text/csv", headers={"Content-Disposition": "attachment;filename=attendance_detailed_report.csv"})
