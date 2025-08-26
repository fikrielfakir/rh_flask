from app import db
from datetime import datetime, date
from sqlalchemy import func

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(191), nullable=False)
    email = db.Column(db.String(191), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    type = db.Column(db.String(50), nullable=False, default='employee')
    lang = db.Column(db.String(10), default='fr')
    created_by = db.Column(db.Integer, default=1)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Branch(db.Model):
    __tablename__ = 'branches'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(191), nullable=False)
    created_by = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Department(db.Model):
    __tablename__ = 'departments'
    
    id = db.Column(db.Integer, primary_key=True)
    branch_id = db.Column(db.Integer, db.ForeignKey('branches.id'), nullable=False)
    name = db.Column(db.String(191), nullable=False)
    created_by = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    branch = db.relationship('Branch', backref='departments')

class Designation(db.Model):
    __tablename__ = 'designations'
    
    id = db.Column(db.Integer, primary_key=True)
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=False)
    name = db.Column(db.String(191), nullable=False)
    created_by = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    department = db.relationship('Department', backref='designations')

class Employee(db.Model):
    __tablename__ = 'employees'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(191), nullable=False)
    cin = db.Column(db.String(20), unique=True)
    phone = db.Column(db.String(20))
    address = db.Column(db.Text)
    email = db.Column(db.String(191), unique=True)
    password = db.Column(db.String(255))
    employee_id = db.Column(db.String(50), unique=True)
    branch_id = db.Column(db.Integer, db.ForeignKey('branches.id'))
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'))
    designation_id = db.Column(db.Integer, db.ForeignKey('designations.id'))
    company_doj = db.Column(db.Date)
    documents = db.Column(db.String(255))
    account_holder_name = db.Column(db.String(191))
    account_number = db.Column(db.String(50))
    bank_name = db.Column(db.String(191))
    bank_identifier_code = db.Column(db.String(50))
    branch_location = db.Column(db.String(191))
    tax_payer_id = db.Column(db.String(50))
    salary_type = db.Column(db.String(50))
    salary = db.Column(db.Numeric(15, 2))
    is_active = db.Column(db.Integer, default=1)
    
    # Enhanced Personal Information
    date_of_birth = db.Column(db.Date)
    gender = db.Column(db.String(20))
    marital_status = db.Column(db.String(20))
    nationality = db.Column(db.String(50))
    religion = db.Column(db.String(50))
    blood_group = db.Column(db.String(10))
    
    # Professional Information
    contract_type = db.Column(db.String(50), default='permanent')  # permanent, temporary, contract
    employment_status = db.Column(db.String(50), default='active')  # active, inactive, terminated, suspended
    manager_id = db.Column(db.Integer, db.ForeignKey('employees.id'))
    work_location = db.Column(db.String(191))
    work_phone = db.Column(db.String(20))
    
    # Contract & Benefits
    probation_period_months = db.Column(db.Integer, default=3)
    notice_period_days = db.Column(db.Integer, default=30)
    weekly_working_hours = db.Column(db.Numeric(5, 2), default=40)
    overtime_eligible = db.Column(db.Boolean, default=True)
    health_insurance = db.Column(db.Boolean, default=False)
    life_insurance = db.Column(db.Boolean, default=False)
    
    # Performance & Skills
    performance_rating = db.Column(db.Numeric(3, 2))  # 0.00 to 5.00
    skills = db.Column(db.Text)  # JSON string of skills
    certifications = db.Column(db.Text)  # JSON string of certifications
    languages = db.Column(db.Text)  # JSON string of languages
    
    # Leave Management
    annual_leave_days = db.Column(db.Integer, default=22)
    sick_leave_days = db.Column(db.Integer, default=10)
    personal_leave_days = db.Column(db.Integer, default=5)
    
    created_by = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = db.relationship('User', backref='employee_profile')
    branch = db.relationship('Branch', backref='employees')
    department = db.relationship('Department', backref='employees')
    designation = db.relationship('Designation', backref='employees')
    manager = db.relationship('Employee', remote_side=[id], backref='subordinates')

class AttendanceEmployee(db.Model):
    __tablename__ = 'attendance_employees'
    
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(191), nullable=False)
    hs = db.Column(db.String(191), nullable=False)
    clock_in = db.Column(db.Time, nullable=False)
    clock_out = db.Column(db.Time, nullable=False)
    late = db.Column(db.Time, nullable=False)
    early_leaving = db.Column(db.Time, nullable=False)
    overtime = db.Column(db.Time, nullable=False)
    total_rest = db.Column(db.Time, nullable=False)
    created_by = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    employee = db.relationship('Employee', backref='attendance_records')

class AllowanceOption(db.Model):
    __tablename__ = 'allowance_options'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(191), nullable=False)
    amount = db.Column(db.Numeric(15, 2), nullable=False, default=0)
    is_taxable = db.Column(db.Boolean, default=True)
    is_active = db.Column(db.Boolean, default=True)
    created_by = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class DeductionOption(db.Model):
    __tablename__ = 'deduction_options'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(191), nullable=False)
    amount = db.Column(db.Numeric(15, 2), nullable=False, default=0)
    is_percentage = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    created_by = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# New models for advanced employee features
class EmergencyContact(db.Model):
    __tablename__ = 'emergency_contacts'
    
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    name = db.Column(db.String(191), nullable=False)
    relationship = db.Column(db.String(50), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(191))
    address = db.Column(db.Text)
    is_primary = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    employee = db.relationship('Employee', backref='emergency_contacts')

class EmployeeDocument(db.Model):
    __tablename__ = 'employee_documents'
    
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    document_type = db.Column(db.String(50), nullable=False)  # CV, contract, certificate, etc.
    document_name = db.Column(db.String(191), nullable=False)
    file_path = db.Column(db.String(255))
    file_size = db.Column(db.Integer)
    mime_type = db.Column(db.String(100))
    uploaded_by = db.Column(db.Integer, nullable=False)
    expiry_date = db.Column(db.Date)  # For documents like passports, licenses
    is_verified = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    employee = db.relationship('Employee', backref='documents_uploaded')

class PerformanceReview(db.Model):
    __tablename__ = 'performance_reviews'
    
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    reviewer_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    review_period_start = db.Column(db.Date, nullable=False)
    review_period_end = db.Column(db.Date, nullable=False)
    overall_rating = db.Column(db.Numeric(3, 2))  # 0.00 to 5.00
    goals_achievement = db.Column(db.Numeric(3, 2))
    communication_skills = db.Column(db.Numeric(3, 2))
    technical_skills = db.Column(db.Numeric(3, 2))
    teamwork = db.Column(db.Numeric(3, 2))
    punctuality = db.Column(db.Numeric(3, 2))
    strengths = db.Column(db.Text)
    areas_for_improvement = db.Column(db.Text)
    goals_next_period = db.Column(db.Text)
    reviewer_comments = db.Column(db.Text)
    employee_comments = db.Column(db.Text)
    status = db.Column(db.String(50), default='draft')  # draft, submitted, approved
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    employee = db.relationship('Employee', foreign_keys=[employee_id], backref='performance_reviews')
    reviewer = db.relationship('Employee', foreign_keys=[reviewer_id], backref='reviews_conducted')

class LeaveRequest(db.Model):
    __tablename__ = 'leave_requests'
    
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    leave_type = db.Column(db.String(50), nullable=False)  # annual, sick, personal, maternity, etc.
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    days_requested = db.Column(db.Integer, nullable=False)
    reason = db.Column(db.Text)
    status = db.Column(db.String(50), default='pending')  # pending, approved, rejected, cancelled
    approved_by = db.Column(db.Integer, db.ForeignKey('employees.id'))
    approved_at = db.Column(db.DateTime)
    rejection_reason = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    employee = db.relationship('Employee', foreign_keys=[employee_id], backref='leave_requests')
    approver = db.relationship('Employee', foreign_keys=[approved_by], backref='leave_approvals')

class EmployeeTraining(db.Model):
    __tablename__ = 'employee_trainings'
    
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    training_title = db.Column(db.String(191), nullable=False)
    training_provider = db.Column(db.String(191))
    training_type = db.Column(db.String(50))  # internal, external, online, workshop
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    duration_hours = db.Column(db.Integer)
    cost = db.Column(db.Numeric(10, 2))
    status = db.Column(db.String(50), default='planned')  # planned, ongoing, completed, cancelled
    certification_received = db.Column(db.Boolean, default=False)
    certificate_file = db.Column(db.String(255))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    employee = db.relationship('Employee', backref='trainings')

class PaySlip(db.Model):
    __tablename__ = 'pay_slips'
    
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    net_payble = db.Column(db.Numeric(15, 2), nullable=False)  # Keep original field name
    salary_month = db.Column(db.String(191), nullable=False)
    status = db.Column(db.Integer, default=0)  # Keep original field type
    basic_salary = db.Column(db.Numeric(15, 2), nullable=False)
    allowance = db.Column(db.Numeric(15, 2), default=0)
    commission = db.Column(db.Numeric(15, 2), default=0)
    loan = db.Column(db.Numeric(15, 2), default=0)
    saturation_deduction = db.Column(db.Numeric(15, 2), default=0)
    other_payment = db.Column(db.Numeric(15, 2), default=0)
    overtime = db.Column(db.Numeric(15, 2), default=0)
    created_by = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    employee = db.relationship('Employee', backref='pay_slips')



class PayrollConfiguration(db.Model):
    __tablename__ = 'payroll_configurations'
    
    id = db.Column(db.Integer, primary_key=True)
    config_key = db.Column(db.String(100), unique=True, nullable=False)
    config_value = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class RetirementEvent(db.Model):
    __tablename__ = 'retirement_events'
    
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    retirement_date = db.Column(db.Date, nullable=False)
    notification_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(50), default='scheduled')  # scheduled, notified, processed
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    employee = db.relationship('Employee', backref='retirement_events')

class Advance(db.Model):
    __tablename__ = 'advances'
    
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    date = db.Column(db.Date, nullable=False)
    reason = db.Column(db.String(191))
    status = db.Column(db.String(50), default='active')  # active, deducted
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    employee = db.relationship('Employee', backref='advances')
