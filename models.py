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
    created_by = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = db.relationship('User', backref='employee_profile')
    branch = db.relationship('Branch', backref='employees')
    department = db.relationship('Department', backref='employees')
    designation = db.relationship('Designation', backref='employees')

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
    created_by = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class DeductionOption(db.Model):
    __tablename__ = 'deduction_options'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(191), nullable=False)
    created_by = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class PaySlip(db.Model):
    __tablename__ = 'pay_slips'
    
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    net_payble = db.Column(db.Numeric(15, 2), nullable=False)
    salary_month = db.Column(db.String(191), nullable=False)
    status = db.Column(db.Integer, default=0)
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

class Advance(db.Model):
    __tablename__ = 'advances'
    
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    date = db.Column(db.Date, nullable=False)
    reason = db.Column(db.String(191))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    employee = db.relationship('Employee', backref='advances')
