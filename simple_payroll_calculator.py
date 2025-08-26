"""
Simplified Moroccan Payroll Calculator
Works with existing database structure while implementing key Moroccan labor law calculations
"""

from datetime import datetime, date
from decimal import Decimal, ROUND_HALF_UP
from app import db
from models import Employee, PaySlip, Advance

class SimpleMoroccanPayrollCalculator:
    """
    Simplified payroll calculator that works with existing database structure
    but implements key Moroccan labor law calculations
    """
    
    # Constants
    CNSS_RATE = Decimal('0.0448')  # 4.48%
    AMO_RATE = Decimal('0.0226')   # 2.26%
    CIMR_RATE = Decimal('0.07')    # 7%
    CNSS_CEILING = Decimal('6000')
    
    # Seniority bonus rates
    SENIORITY_RATES = {
        (2, 4): Decimal('0.05'),    # 5% for 2-4 years
        (5, 11): Decimal('0.10'),   # 10% for 5-11 years
        (12, 19): Decimal('0.15'),  # 15% for 12-19 years
        (20, 24): Decimal('0.20'),  # 20% for 20-24 years
        (25, 99): Decimal('0.25'),  # 25% for 25+ years
    }
    
    # Tax brackets
    TAX_BRACKETS = [
        {'min': 0, 'max': 2500, 'rate': 0, 'deduction': 0},
        {'min': 2501, 'max': 4166, 'rate': 0.10, 'deduction': 250},
        {'min': 4167, 'max': 5000, 'rate': 0.20, 'deduction': 666.67},
        {'min': 5001, 'max': 6666, 'rate': 0.30, 'deduction': 1166.67},
        {'min': 6667, 'max': 15000, 'rate': 0.34, 'deduction': 1433.33},
        {'min': 15001, 'max': 999999, 'rate': 0.38, 'deduction': 2033.33},
    ]
    
    def __init__(self, employee_id, salary_month):
        self.employee_id = employee_id
        self.salary_month = salary_month
        self.employee = Employee.query.get(employee_id)
        if not self.employee:
            raise ValueError(f"Employee {employee_id} not found")
    
    def calculate_seniority_bonus(self, basic_salary):
        """Calculate seniority bonus based on years of service"""
        if not self.employee.company_doj:
            return Decimal('0')
        
        today = date.today()
        years_of_service = today.year - self.employee.company_doj.year
        if today.month < self.employee.company_doj.month or \
           (today.month == self.employee.company_doj.month and today.day < self.employee.company_doj.day):
            years_of_service -= 1
        
        # Find applicable rate
        for (min_years, max_years), rate in self.SENIORITY_RATES.items():
            if min_years <= years_of_service <= max_years:
                return basic_salary * rate
        
        return Decimal('0')
    
    def calculate_social_contributions(self, gross_salary):
        """Calculate CNSS, AMO, CIMR contributions"""
        # CNSS with ceiling
        cnss_base = min(gross_salary, self.CNSS_CEILING)
        cnss = cnss_base * self.CNSS_RATE
        
        # AMO and CIMR (no ceiling)
        amo = gross_salary * self.AMO_RATE
        cimr = gross_salary * self.CIMR_RATE
        
        return cnss, amo, cimr
    
    def calculate_professional_expenses(self, gross_salary):
        """Calculate professional expenses deduction"""
        if gross_salary <= 6500:
            return gross_salary * Decimal('0.35')  # 35%
        else:
            return gross_salary * Decimal('0.25')  # 25%
    
    def calculate_income_tax(self, net_taxable_salary, is_married=False, children=0):
        """Calculate income tax with family allowances"""
        gross_ir = Decimal('0')
        
        # Find applicable tax bracket
        for bracket in self.TAX_BRACKETS:
            if bracket['min'] <= net_taxable_salary <= bracket['max']:
                gross_ir = (net_taxable_salary * Decimal(str(bracket['rate']))) - Decimal(str(bracket['deduction']))
                break
        
        # Family allowances
        family_allowance = Decimal('0')
        if is_married:
            family_allowance += Decimal('30')
        family_allowance += Decimal(str(children)) * Decimal('30')
        
        # Net IR cannot be negative
        net_ir = max(gross_ir - family_allowance, Decimal('0'))
        
        return net_ir, family_allowance
    
    def calculate_enhanced_payslip(self, overtime_hours=0, leave_allowance=0):
        """
        Calculate payslip with enhanced Moroccan labor law calculations
        while working with existing database structure
        """
        basic_salary = Decimal(str(self.employee.salary or 0))
        
        # Calculate seniority bonus
        seniority_bonus = self.calculate_seniority_bonus(basic_salary)
        
        # Calculate overtime (simple 25% rate for now)
        overtime_amount = Decimal(str(overtime_hours)) * (basic_salary / Decimal('191')) * Decimal('1.25')
        
        # Calculate gross salary
        gross_salary = basic_salary + seniority_bonus + overtime_amount + Decimal(str(leave_allowance))
        
        # Calculate social contributions
        cnss, amo, cimr = self.calculate_social_contributions(gross_salary)
        
        # Calculate professional expenses
        professional_expenses = self.calculate_professional_expenses(gross_salary)
        
        # Calculate net taxable salary
        net_taxable_salary = gross_salary - cnss - amo - cimr - professional_expenses
        
        # Calculate income tax (simplified family data)
        is_married = getattr(self.employee, 'marital_status', '') == 'Marié'
        net_ir, family_allowance = self.calculate_income_tax(net_taxable_salary, is_married, 0)
        
        # Get advances and loans
        advances = self.get_employee_advances()
        
        # Calculate final net payable
        total_deductions = cnss + amo + cimr + net_ir
        net_salary = gross_salary - total_deductions
        net_payable = net_salary - advances
        
        # Prepare payslip data for existing database structure
        payslip_data = {
            'basic_salary': basic_salary,
            'allowance': seniority_bonus + Decimal(str(leave_allowance)),  # Combine allowances
            'commission': Decimal('0'),  # Can be used for other bonuses
            'overtime': overtime_amount,
            'other_payment': family_allowance,  # Store family allowance here for reference
            'loan': advances,  # Store advances as loans
            'saturation_deduction': total_deductions - advances,  # Store other deductions
            'net_payble': net_payable  # Note: keeping original typo in field name
        }
        
        return payslip_data
    
    def get_employee_advances(self):
        """Get employee advance payments"""
        advances = Advance.query.filter_by(employee_id=self.employee_id, status='active').all()
        return sum(Decimal(str(advance.amount)) for advance in advances)
    
    def save_payslip(self, overtime_hours=0, leave_allowance=0):
        """Calculate and save payslip"""
        payslip_data = self.calculate_enhanced_payslip(overtime_hours, leave_allowance)
        
        # Check if payslip exists
        existing_payslip = PaySlip.query.filter_by(
            employee_id=self.employee_id,
            salary_month=self.salary_month
        ).first()
        
        if existing_payslip:
            payslip = existing_payslip
        else:
            payslip = PaySlip(
                employee_id=self.employee_id,
                salary_month=self.salary_month,
                created_by=1
            )
        
        # Update payslip with calculated data
        for key, value in payslip_data.items():
            setattr(payslip, key, value)
        
        payslip.status = 1  # Mark as calculated
        payslip.updated_at = datetime.utcnow()
        
        if not existing_payslip:
            db.session.add(payslip)
        
        db.session.commit()
        return payslip

def calculate_simple_payslip(employee_id, salary_month, overtime_hours=0, leave_allowance=0):
    """
    Convenience function to calculate payslip with Moroccan labor law compliance
    """
    try:
        calculator = SimpleMoroccanPayrollCalculator(employee_id, salary_month)
        payslip = calculator.save_payslip(overtime_hours, leave_allowance)
        return payslip, []
    except Exception as e:
        return None, [str(e)]