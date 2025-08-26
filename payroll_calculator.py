"""
Moroccan Payroll Calculation System
Implements comprehensive payroll calculations according to Moroccan labor law
"""

from datetime import datetime, date, timedelta
from decimal import Decimal, ROUND_HALF_UP
from app import db
from models import Employee, PaySlip, AttendanceEmployee, Advance, PayrollConfiguration, RetirementEvent
import calendar

class MoroccanPayrollCalculator:
    """
    Comprehensive payroll calculator for Moroccan labor law compliance
    """
    
    # Constants
    STANDARD_MONTHLY_HOURS = Decimal('191')
    MAX_WORKING_DAYS = 26
    CNSS_CEILING = Decimal('6000')
    RETIREMENT_AGE = 60
    
    # Default Rates (configurable)
    DEFAULT_CNSS_RATE = Decimal('0.0448')  # 4.48%
    DEFAULT_AMO_RATE = Decimal('0.0226')   # 2.26%
    DEFAULT_CIMR_RATE = Decimal('0.07')    # 7%
    DEFAULT_FAMILY_ALLOWANCE = Decimal('30')  # 30 MAD
    
    # Overtime Rates
    OVERTIME_REGULAR = Decimal('0.25')    # 25%
    OVERTIME_WEEKEND = Decimal('0.50')    # 50%
    OVERTIME_HOLIDAY = Decimal('1.00')    # 100%
    
    # Professional Expenses Rates
    PROFESSIONAL_EXPENSES_HIGH = Decimal('0.35')  # 35% if salary ≤ 6,500
    PROFESSIONAL_EXPENSES_LOW = Decimal('0.25')   # 25% if salary > 6,500
    PROFESSIONAL_EXPENSES_THRESHOLD = Decimal('6500')
    
    # Income Tax Brackets
    TAX_BRACKETS = [
        {'min': Decimal('0'), 'max': Decimal('2500'), 'rate': Decimal('0'), 'deduction': Decimal('0')},
        {'min': Decimal('2501'), 'max': Decimal('4166'), 'rate': Decimal('0.10'), 'deduction': Decimal('250')},
        {'min': Decimal('4167'), 'max': Decimal('5000'), 'rate': Decimal('0.20'), 'deduction': Decimal('666.67')},
        {'min': Decimal('5001'), 'max': Decimal('6666'), 'rate': Decimal('0.30'), 'deduction': Decimal('1166.67')},
        {'min': Decimal('6667'), 'max': Decimal('15000'), 'rate': Decimal('0.34'), 'deduction': Decimal('1433.33')},
        {'min': Decimal('15001'), 'max': Decimal('999999'), 'rate': Decimal('0.38'), 'deduction': Decimal('2033.33')},
    ]
    
    # Seniority Bonus Rates
    SENIORITY_BRACKETS = [
        {'min_years': 2, 'max_years': 4, 'rate': Decimal('0.05')},   # 5%
        {'min_years': 5, 'max_years': 11, 'rate': Decimal('0.10')},  # 10%
        {'min_years': 12, 'max_years': 19, 'rate': Decimal('0.15')}, # 15%
        {'min_years': 20, 'max_years': 24, 'rate': Decimal('0.20')}, # 20%
        {'min_years': 25, 'max_years': 99, 'rate': Decimal('0.25')}, # 25%
    ]
    
    def __init__(self, employee_id, salary_month):
        self.employee_id = employee_id
        self.salary_month = salary_month
        self.employee = Employee.query.get(employee_id)
        if not self.employee:
            raise ValueError(f"Employee {employee_id} not found")
        
        # Initialize calculation results
        self.payslip_data = {}
        self.errors = []
        
    def calculate_payslip(self, attendance_data=None, overtime_data=None, leave_data=None):
        """
        Main calculation method that orchestrates the entire payroll calculation
        """
        try:
            # Step 1: Basic Salary Calculations
            self._calculate_basic_salary(attendance_data)
            
            # Step 2: Leave and Holiday Calculations
            self._calculate_leave_and_holidays(leave_data)
            
            # Step 3: Overtime Calculations
            self._calculate_overtime(overtime_data)
            
            # Step 4: Taxable Basic Salary
            self._calculate_taxable_basic_salary()
            
            # Step 5: Seniority Bonus
            self._calculate_seniority_bonus()
            
            # Step 6: Gross Salary
            self._calculate_gross_salary()
            
            # Step 7: Social Security Contributions
            self._calculate_social_contributions()
            
            # Step 8: Net Taxable Salary
            self._calculate_net_taxable_salary()
            
            # Step 9: Income Tax
            self._calculate_income_tax()
            
            # Step 10: Final Net Salary
            self._calculate_final_net_salary()
            
            # Step 11: Check for retirement events
            self._check_retirement_eligibility()
            
            return self.payslip_data
            
        except Exception as e:
            self.errors.append(f"Calculation error: {str(e)}")
            return None
    
    def _calculate_basic_salary(self, attendance_data):
        """Calculate basic salary based on attendance"""
        base_salary = Decimal(str(self.employee.salary or 0))
        
        # Get attendance data for the month
        if attendance_data:
            days_worked = attendance_data.get('days_worked', self.MAX_WORKING_DAYS)
            holiday_days = attendance_data.get('holiday_days', 0)
        else:
            days_worked = self.MAX_WORKING_DAYS
            holiday_days = 0
        
        # Calculate actual working hours
        actual_working_hours = (days_worked - holiday_days) * Decimal('7.3461538462')
        hourly_rate = base_salary / self.STANDARD_MONTHLY_HOURS
        monthly_salary = hourly_rate * actual_working_hours
        
        self.payslip_data.update({
            'base_salary': base_salary,
            'days_worked': days_worked,
            'actual_working_hours': actual_working_hours,
            'monthly_salary': monthly_salary.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        })
    
    def _calculate_leave_and_holidays(self, leave_data):
        """Calculate paid leave and holiday payments"""
        base_salary = self.payslip_data['base_salary']
        
        if leave_data:
            leave_days = leave_data.get('approved_leave_days', 0)
            holiday_days = leave_data.get('holiday_days', 0)
            worked_on_holidays = leave_data.get('worked_on_holidays', False)
        else:
            leave_days = 0
            holiday_days = 0
            worked_on_holidays = False
        
        # Paid Leave Calculation
        paid_leave_amount = Decimal('0')
        if leave_days > 0:
            paid_leave_amount = (Decimal(str(leave_days)) * base_salary) / Decimal(str(self.MAX_WORKING_DAYS))
        
        # Paid Holiday Calculation (only if didn't work on holidays)
        paid_holiday_amount = Decimal('0')
        if holiday_days > 0 and not worked_on_holidays:
            paid_holiday_amount = (Decimal(str(holiday_days)) * base_salary) / Decimal(str(self.MAX_WORKING_DAYS))
        
        self.payslip_data.update({
            'leave_days': leave_days,
            'holiday_days': holiday_days,
            'paid_leave_amount': paid_leave_amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
            'paid_holiday_amount': paid_holiday_amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        })
    
    def _calculate_overtime(self, overtime_data):
        """Calculate overtime payments with different rates"""
        base_salary = self.payslip_data['base_salary']
        hourly_rate = base_salary / self.STANDARD_MONTHLY_HOURS
        
        if overtime_data:
            regular_hours = Decimal(str(overtime_data.get('regular_overtime_hours', 0)))
            weekend_hours = Decimal(str(overtime_data.get('weekend_overtime_hours', 0)))
            holiday_hours = Decimal(str(overtime_data.get('holiday_overtime_hours', 0)))
        else:
            regular_hours = Decimal('0')
            weekend_hours = Decimal('0')
            holiday_hours = Decimal('0')
        
        # Calculate overtime amounts
        overtime_regular_amount = regular_hours * hourly_rate * (Decimal('1') + self.OVERTIME_REGULAR)
        overtime_weekend_amount = weekend_hours * hourly_rate * (Decimal('1') + self.OVERTIME_WEEKEND)
        overtime_holiday_amount = holiday_hours * hourly_rate * (Decimal('1') + self.OVERTIME_HOLIDAY)
        
        total_overtime_amount = overtime_regular_amount + overtime_weekend_amount + overtime_holiday_amount
        
        self.payslip_data.update({
            'overtime_regular_hours': regular_hours,
            'overtime_weekend_hours': weekend_hours,
            'overtime_holiday_hours': holiday_hours,
            'overtime_regular_amount': overtime_regular_amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
            'overtime_weekend_amount': overtime_weekend_amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
            'overtime_holiday_amount': overtime_holiday_amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
            'total_overtime_amount': total_overtime_amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        })
    
    def _calculate_taxable_basic_salary(self):
        """Calculate taxable basic salary"""
        monthly_salary = self.payslip_data['monthly_salary']
        paid_leave_amount = self.payslip_data['paid_leave_amount']
        paid_holiday_amount = self.payslip_data['paid_holiday_amount']
        total_overtime_amount = self.payslip_data['total_overtime_amount']
        
        taxable_basic_salary = monthly_salary + paid_leave_amount + paid_holiday_amount + total_overtime_amount
        
        self.payslip_data['taxable_basic_salary'] = taxable_basic_salary.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    
    def _calculate_seniority_bonus(self):
        """Calculate seniority bonus based on years of service"""
        if not self.employee.company_doj:
            self.payslip_data.update({
                'years_of_service': 0,
                'seniority_bonus_rate': Decimal('0'),
                'seniority_bonus_amount': Decimal('0')
            })
            return
        
        # Calculate years of service
        today = date.today()
        years_of_service = today.year - self.employee.company_doj.year
        if today.month < self.employee.company_doj.month or \
           (today.month == self.employee.company_doj.month and today.day < self.employee.company_doj.day):
            years_of_service -= 1
        
        # Find applicable seniority rate
        seniority_rate = Decimal('0')
        for bracket in self.SENIORITY_BRACKETS:
            if bracket['min_years'] <= years_of_service <= bracket['max_years']:
                seniority_rate = bracket['rate']
                break
        
        # Calculate seniority bonus
        taxable_basic_salary = self.payslip_data['taxable_basic_salary']
        seniority_bonus_amount = taxable_basic_salary * seniority_rate
        
        self.payslip_data.update({
            'years_of_service': years_of_service,
            'seniority_bonus_rate': seniority_rate,
            'seniority_bonus_amount': seniority_bonus_amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        })
    
    def _calculate_gross_salary(self):
        """Calculate gross salary components"""
        taxable_basic_salary = self.payslip_data['taxable_basic_salary']
        seniority_bonus_amount = self.payslip_data['seniority_bonus_amount']
        
        # For now, we'll use simple allowances (can be extended)
        taxable_allowances = Decimal('0')  # This could come from employee allowances
        non_taxable_allowances = Decimal('0')  # This could come from employee allowances
        
        gross_salary = taxable_basic_salary + seniority_bonus_amount + taxable_allowances
        gross_taxable_salary = gross_salary - non_taxable_allowances
        
        self.payslip_data.update({
            'taxable_allowances': taxable_allowances,
            'non_taxable_allowances': non_taxable_allowances,
            'gross_salary': gross_salary.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
            'gross_taxable_salary': gross_taxable_salary.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        })
    
    def _calculate_social_contributions(self):
        """Calculate social security contributions"""
        gross_taxable_salary = self.payslip_data['gross_taxable_salary']
        
        # CNSS (with ceiling)
        cnss_base = min(gross_taxable_salary, self.CNSS_CEILING)
        cnss_amount = cnss_base * self.DEFAULT_CNSS_RATE
        
        # AMO (no ceiling)
        amo_amount = gross_taxable_salary * self.DEFAULT_AMO_RATE
        
        # CIMR (no ceiling)
        cimr_amount = gross_taxable_salary * self.DEFAULT_CIMR_RATE
        
        # Professional Expenses
        taxable_basic_salary = self.payslip_data['taxable_basic_salary']
        if taxable_basic_salary <= self.PROFESSIONAL_EXPENSES_THRESHOLD:
            professional_expenses_rate = self.PROFESSIONAL_EXPENSES_HIGH
        else:
            professional_expenses_rate = self.PROFESSIONAL_EXPENSES_LOW
        
        professional_expenses_amount = gross_taxable_salary * professional_expenses_rate
        
        self.payslip_data.update({
            'cnss_rate': self.DEFAULT_CNSS_RATE,
            'cnss_amount': cnss_amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
            'amo_rate': self.DEFAULT_AMO_RATE,
            'amo_amount': amo_amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
            'cimr_rate': self.DEFAULT_CIMR_RATE,
            'cimr_amount': cimr_amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
            'professional_expenses_rate': professional_expenses_rate,
            'professional_expenses_amount': professional_expenses_amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        })
    
    def _calculate_net_taxable_salary(self):
        """Calculate net taxable salary after deductions"""
        gross_taxable_salary = self.payslip_data['gross_taxable_salary']
        cnss_amount = self.payslip_data['cnss_amount']
        amo_amount = self.payslip_data['amo_amount']
        cimr_amount = self.payslip_data['cimr_amount']
        professional_expenses_amount = self.payslip_data['professional_expenses_amount']
        
        net_taxable_salary = gross_taxable_salary - cnss_amount - amo_amount - cimr_amount - professional_expenses_amount
        
        self.payslip_data['net_taxable_salary'] = net_taxable_salary.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    
    def _calculate_income_tax(self):
        """Calculate income tax using progressive brackets"""
        net_taxable_salary = self.payslip_data['net_taxable_salary']
        
        # Find applicable tax bracket
        gross_ir = Decimal('0')
        for bracket in self.TAX_BRACKETS:
            if bracket['min'] <= net_taxable_salary <= bracket['max']:
                gross_ir = (net_taxable_salary * bracket['rate']) - bracket['deduction']
                break
        
        # Family Allowance Calculation
        # For now, we'll use simple logic (can be enhanced with employee family data)
        is_married = getattr(self.employee, 'marital_status', '') == 'Marié'
        number_of_children = 0  # This could come from employee family data
        
        family_allowance = Decimal('0')
        if is_married:
            family_allowance += self.DEFAULT_FAMILY_ALLOWANCE  # Base allowance for marriage
        family_allowance += Decimal(str(number_of_children)) * self.DEFAULT_FAMILY_ALLOWANCE
        
        # Final IR calculation
        net_ir = max(gross_ir - family_allowance, Decimal('0'))
        
        self.payslip_data.update({
            'gross_ir': gross_ir.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
            'is_married': is_married,
            'number_of_children': number_of_children,
            'family_allowance': family_allowance.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
            'net_ir': net_ir.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        })
    
    def _calculate_final_net_salary(self):
        """Calculate final net salary after all deductions"""
        gross_taxable_salary = self.payslip_data['gross_taxable_salary']
        amo_amount = self.payslip_data['amo_amount']
        cnss_amount = self.payslip_data['cnss_amount']
        cimr_amount = self.payslip_data['cimr_amount']
        net_ir = self.payslip_data['net_ir']
        
        # Calculate advance payments and loans
        advance_payments = self._get_advance_payments()
        loans = self._get_loan_deductions()
        
        total_deductions = amo_amount + cnss_amount + cimr_amount + net_ir
        net_salary = gross_taxable_salary - total_deductions
        net_payable = net_salary - advance_payments - loans
        
        self.payslip_data.update({
            'advance_payments': advance_payments,
            'loans': loans,
            'total_deductions': total_deductions.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
            'net_salary': net_salary.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
            'net_payable': net_payable.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        })
    
    def _get_advance_payments(self):
        """Get advance payments for the month"""
        # This could be enhanced to get actual advance payments
        advances = Advance.query.filter_by(employee_id=self.employee_id, status='active').all()
        total_advances = sum(Decimal(str(advance.amount)) for advance in advances)
        return total_advances.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    
    def _get_loan_deductions(self):
        """Get loan deductions for the month"""
        # This could be enhanced to get actual loan deductions
        return Decimal('0').quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    
    def _check_retirement_eligibility(self):
        """Check if employee is approaching retirement and create events"""
        if not self.employee.date_of_birth:
            return
        
        # Calculate retirement date (age 60)
        retirement_date = date(
            self.employee.date_of_birth.year + self.RETIREMENT_AGE,
            self.employee.date_of_birth.month,
            self.employee.date_of_birth.day
        )
        
        # Check if within 60 days of retirement
        today = date.today()
        days_to_retirement = (retirement_date - today).days
        
        if 0 <= days_to_retirement <= 60:
            # Check if retirement event already exists
            existing_event = RetirementEvent.query.filter_by(
                employee_id=self.employee_id,
                retirement_date=retirement_date
            ).first()
            
            if not existing_event:
                # Create retirement event
                retirement_event = RetirementEvent(
                    employee_id=self.employee_id,
                    retirement_date=retirement_date,
                    notification_date=today,
                    notes=f"Employee approaching retirement in {days_to_retirement} days"
                )
                db.session.add(retirement_event)
                db.session.commit()
    
    def save_payslip(self):
        """Save the calculated payslip to database"""
        if not self.payslip_data:
            raise ValueError("No payslip data calculated")
        
        # Check if payslip already exists
        existing_payslip = PaySlip.query.filter_by(
            employee_id=self.employee_id,
            salary_month=self.salary_month
        ).first()
        
        if existing_payslip:
            # Update existing payslip
            payslip = existing_payslip
        else:
            # Create new payslip
            payslip = PaySlip(
                employee_id=self.employee_id,
                salary_month=self.salary_month,
                created_by=1  # This should come from current user
            )
        
        # Update payslip fields
        for key, value in self.payslip_data.items():
            if hasattr(payslip, key):
                setattr(payslip, key, value)
        
        payslip.updated_at = datetime.utcnow()
        
        if not existing_payslip:
            db.session.add(payslip)
        
        db.session.commit()
        return payslip

def calculate_employee_payslip(employee_id, salary_month, attendance_data=None, overtime_data=None, leave_data=None):
    """
    Convenience function to calculate and save payslip
    """
    calculator = MoroccanPayrollCalculator(employee_id, salary_month)
    payslip_data = calculator.calculate_payslip(attendance_data, overtime_data, leave_data)
    
    if payslip_data:
        payslip = calculator.save_payslip()
        return payslip, calculator.errors
    else:
        return None, calculator.errors