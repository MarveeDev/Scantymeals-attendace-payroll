from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app.auth.decorators import login_required
from app.models.worker import WorkerModel
from app.models.payroll import PayrollModel
from app.models.payment import PaymentModel
from app.models.audit import AuditModel
from app.services.time_service import get_current_date, format_date

payments_bp = Blueprint('payments', __name__, url_prefix='/payments')

@payments_bp.route('/record/<payroll_id>', methods=['GET', 'POST'])
@login_required
def record(payroll_id):
    payroll = PayrollModel.get_by_id(payroll_id)
    if not payroll:
        flash("Payroll not found", "error")
        return redirect(url_for('payroll.index'))
        
    worker = WorkerModel.get_by_id(payroll['worker_id'])
    
    if request.method == 'POST':
        data = {
            "worker_id": payroll['worker_id'],
            "payroll_id": payroll_id,
            "amount": request.form.get("amount"),
            "payment_date": request.form.get("payment_date"),
            "payment_method": request.form.get("payment_method"),
            "reference": request.form.get("reference"),
            "notes": request.form.get("notes"),
            "recorded_by": session.get('admin_id')
        }
        
        payment_id = PaymentModel.record_payment(data)
        
        # Update payroll payment status based on math
        payments = PaymentModel.get_by_worker(payroll['worker_id'])
        payroll_payments = sum(p['amount'] for p in payments if str(p.get('payroll_id')) == str(payroll_id))
        
        if payroll_payments >= payroll['net_amount']:
            new_status = "Paid"
        elif payroll_payments > 0:
            new_status = "Partially Paid"
        else:
            new_status = "Unpaid"
            
        PayrollModel.collection().update_one(
            {"_id": payroll['_id']}, 
            {"$set": {"payment_status": new_status}}
        )
            
        AuditModel.log(session.get('admin_id'), "Record Payment", "Payment", payment_id)
        flash("Payment recorded successfully", "success")
        return redirect(url_for('payroll.view', payroll_id=payroll_id))
        
    return render_template('payroll/payment.html', payroll=payroll, worker=worker, default_date=format_date(get_current_date()))
