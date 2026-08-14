from app.services.time_service import parse_date, format_date, get_current_date
from app.models.attendance import AttendanceModel
import calendar
from datetime import date, timedelta

class AttendanceService:
    @staticmethod
    def get_days_in_month(year, month):
        return calendar.monthrange(year, month)[1]

    @staticmethod
    def is_date_eligible(check_date, employment_periods):
        if not employment_periods:
            return False
        for period in employment_periods:
            start = parse_date(period["start_date"])
            end = parse_date(period["end_date"]) if period["end_date"] else None
            
            if start and check_date >= start:
                if end is None or check_date <= end:
                    return True
        return False

    @staticmethod
    def get_period_summary(worker, start_date, end_date):
        days_in_period = (end_date - start_date).days + 1
        current_date = get_current_date()

        all_dates = [start_date + timedelta(days=i) for i in range(days_in_period)]
        eligible_dates = [d for d in all_dates if AttendanceService.is_date_eligible(d, worker.get("employment_periods", []))]
        
        records = AttendanceModel.get_worker_history(str(worker["_id"]), format_date(start_date), format_date(end_date))
        records_by_date = {r["attendance_date"]: r["status"] for r in records}
        
        present_count = 0
        absent_count = 0
        not_marked_count = 0
        
        for d in eligible_dates:
            d_str = format_date(d)
            if d_str in records_by_date:
                status = records_by_date[d_str]
                if status == "present":
                    present_count += 1
                elif status == "absent":
                    absent_count += 1

        eligible_count = len(eligible_dates)
        marked_count = present_count + absent_count
        not_marked_count = eligible_count - marked_count
        
        # Mathematical Invariant Validation
        if eligible_count != present_count + absent_count + not_marked_count:
            raise ValueError(f"Attendance Invariant Violation: Eligible ({eligible_count}) != Present ({present_count}) + Absent ({absent_count}) + Not Marked ({not_marked_count})")
        if marked_count != present_count + absent_count:
            raise ValueError(f"Attendance Invariant Violation: Marked ({marked_count}) != Present ({present_count}) + Absent ({absent_count})")
            
        attendance_rate = 0.0
        if eligible_count > 0:
            attendance_rate = (present_count / eligible_count) * 100

        return {
            "eligible_days": eligible_count,
            "marked_days": marked_count,
            "present_days": present_count,
            "absent_days": absent_count,
            "not_marked_days": not_marked_count,
            "attendance_rate": round(attendance_rate, 2),
            "days_in_period": days_in_period,
            "records_by_date": records_by_date
        }

    @staticmethod
    def get_monthly_summary(worker, year, month):
        days_in_month = AttendanceService.get_days_in_month(year, month)
        start_date = date(year, month, 1)
        end_date = date(year, month, days_in_month)
        summary = AttendanceService.get_period_summary(worker, start_date, end_date)
        summary["days_in_month"] = days_in_month
        return summary


    @staticmethod
    def generate_calendar_grid(worker, year, month):
        summary = AttendanceService.get_monthly_summary(worker, year, month)
        records_by_date = summary["records_by_date"]
        current_date = get_current_date()
        
        cal = calendar.Calendar(firstweekday=0)
        weeks = cal.monthdatescalendar(year, month)
        
        grid = []
        for week in weeks:
            week_data = []
            for d in week:
                if d.month != month:
                    week_data.append({"date": d, "day": "", "status": "outside_month"})
                else:
                    is_eligible = AttendanceService.is_date_eligible(d, worker.get("employment_periods", []))
                    if not is_eligible:
                        week_data.append({"date": d, "day": d.day, "status": "not_eligible"})
                    else:
                        d_str = format_date(d)
                        if d_str in records_by_date:
                            week_data.append({"date": d, "day": d.day, "status": records_by_date[d_str]})
                        else:
                            if d > current_date:
                                week_data.append({"date": d, "day": d.day, "status": "future"})
                            else:
                                week_data.append({"date": d, "day": d.day, "status": "not_marked"})
            grid.append(week_data)
            
        return grid, summary
