from app.models.payroll import PayrollModel
from app.models.worker import WorkerModel
from app.models.settings import SettingsModel
from app.models.salary_history import SalaryHistoryModel
from app.services.time_service import parse_date
from app.services.attendance_service import AttendanceService
from decimal import Decimal, ROUND_HALF_UP

class PayrollService:
    @staticmethod
    def calculate_draft(worker_id, period_start_str, period_end_str, period_type="Custom"):
        """
        Calculates draft payroll for a worker in the given period.
        Uses exact Decimal arithmetic for financial safety.
        """
        start_date = parse_date(period_start_str)
        end_date = parse_date(period_end_str)
        
        if not start_date or not end_date or end_date < start_date:
            raise ValueError("Invalid period dates")

        worker = WorkerModel.get_by_id(worker_id)
        if not worker:
            raise ValueError("Worker not found")
            
        settings = SettingsModel.get_settings()
        
        # Determine applicable salary rate based on period_end and history
        # (For simplicity in this calculation, we look at the rate active at the end of the period)
        # Ideally, we would pro-rate if salary changed mid-period, but the spec says:
        # "Payroll must use the salary rate effective during the payroll period."
        history = SalaryHistoryModel.get_history(worker_id)
        
        applicable_weekly = worker.get("weekly_salary", settings["default_weekly_salary"])
        applicable_monthly = worker.get("monthly_salary", settings["default_monthly_salary"])
        
        for record in history:
            effective_dt = parse_date(record["effective_date"]) if isinstance(record["effective_date"], str) else record["effective_date"]
            if effective_dt and effective_dt <= end_date:
                applicable_weekly = record["weekly_salary"]
                applicable_monthly = record["monthly_salary"]
                break
                
        gross_amount = Decimal(applicable_weekly) if period_type == "Weekly" else Decimal(applicable_monthly)
        
        # Attendance Summary
        summary = AttendanceService.get_period_summary(worker, start_date, end_date)
        eligible_days = summary["eligible_days"]
        absent_count = Decimal(summary["absent_days"])
        
        # Calculate deduction
        deduction_method = settings.get("absence_deduction_method", "fixed")
        deduction_value = Decimal(str(settings.get("absence_deduction_value", 25)))
        
        deduction_amount = Decimal("0.00")
        if absent_count > 0:
            if deduction_method == "fixed":
                deduction_amount = absent_count * deduction_value
            elif deduction_method == "percentage":
                deduction_amount = (deduction_value / Decimal("100")) * gross_amount * absent_count
            elif deduction_method == "pro_rated":
                if eligible_days > 0:
                    daily_rate = gross_amount / Decimal(eligible_days)
                    deduction_amount = daily_rate * absent_count

        gross_amount = gross_amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        deduction_amount = deduction_amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        net_amount = max(Decimal("0.00"), gross_amount - deduction_amount)
        
        data = {
            "worker_id": worker_id,
            "period_type": period_type,
            "period_start": period_start_str,
            "period_end": period_end_str,
            "salary_rate_used": str(gross_amount),
            "gross_amount": str(gross_amount),
            
            # Attendance stats
            "eligible_days": eligible_days,
            "marked_days": summary["marked_days"],
            "present_days": summary["present_days"],
            "absent_days": summary["absent_days"],
            "not_marked_days": summary["not_marked_days"],
            "attendance_rate": summary["attendance_rate"],
            
            "absence_count": summary["absent_days"],
            "deduction_amount": str(deduction_amount),
            "net_amount": str(net_amount)
        }
        
        # Ensure we don't overlap with finalized payroll
        if PayrollModel.check_overlap(worker_id, period_start_str, period_end_str):
            raise ValueError("Overlapping finalized payroll exists for this period")
            
        payroll_id = PayrollModel.save_draft(data)
        data["_id"] = payroll_id
        return data

def format_date_for_query(d):
    return d.strftime('%Y-%m-%d')
