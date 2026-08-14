from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app.auth.decorators import login_required
from app.models.worker import WorkerModel
from app.models.payroll import PayrollModel
from app.services.payroll_service import PayrollService
from app.models.audit import AuditModel

payroll_bp = Blueprint('payroll', __name__, url_prefix='/payroll')

@payroll_bp.route('/', methods=['GET', 'POST'])
@login_required
def index():
    if request.method == 'POST':
        period_type = request.form.get('period_type')
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')
        worker_id = request.form.get('worker_id')
        
        try:
            payroll_data = PayrollService.calculate_draft(worker_id, start_date, end_date, period_type)
            flash("Draft payroll generated successfully", "success")
            return redirect(url_for('payroll.view', payroll_id=payroll_data['_id']))
        except ValueError as e:
            flash(str(e), "error")
            
    workers = WorkerModel.get_all(active_only=False)
    return render_template('payroll/index.html', workers=workers)

@payroll_bp.route('/<payroll_id>')
@login_required
def view(payroll_id):
    payroll = PayrollModel.get_by_id(payroll_id)
    if not payroll:
        flash("Payroll record not found", "error")
        return redirect(url_for('payroll.index'))
        
    worker = WorkerModel.get_by_id(payroll['worker_id'])
    return render_template('payroll/view.html', payroll=payroll, worker=worker)

@payroll_bp.route('/<payroll_id>/finalize', methods=['POST'])
@login_required
def finalize(payroll_id):
    payroll = PayrollModel.get_by_id(payroll_id)
    if not payroll:
        flash("Payroll record not found", "error")
        return redirect(url_for('payroll.index'))
        
    # Check for overlaps right before finalizing again
    if PayrollModel.check_overlap(payroll['worker_id'], payroll['period_start'], payroll['period_end']):
        flash("Overlapping finalized payroll exists for this period", "error")
        return redirect(url_for('payroll.view', payroll_id=payroll_id))
        
    PayrollModel.finalize(payroll_id)
    AuditModel.log(session.get('admin_id'), "Finalize Payroll", "Payroll", payroll_id)
    flash("Payroll finalized successfully", "success")
    return redirect(url_for('payroll.view', payroll_id=payroll_id))
