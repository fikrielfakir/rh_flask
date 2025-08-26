from flask import render_template, request, redirect, url_for, flash, jsonify
from app import app, db
from models import *
from forms import *
from datetime import datetime, timedelta
from sqlalchemy import func, extract

@app.route('/')
def index():
    # Dashboard statistics
    total_employees = Employee.query.filter_by(is_active=1).count()
    total_branches = Branch.query.count()
    total_departments = Department.query.count()
    
    # Recent attendance
    today = datetime.now().date()
    present_today = AttendanceEmployee.query.filter_by(date=today, status='present').count()
    
    # Recent pay slips
    current_month = datetime.now().strftime('%m/%Y')
    payroll_this_month = PaySlip.query.filter_by(salary_month=current_month).count()
    
    # Current date for display
    current_date = datetime.now().strftime('%d/%m/%Y')
    
    return render_template('index.html',
                         total_employees=total_employees,
                         total_branches=total_branches,
                         total_departments=total_departments,
                         present_today=present_today,
                         payroll_this_month=payroll_this_month,
                         current_date=current_date)

# Branch routes
@app.route('/branches')
def branches_list():
    branches = Branch.query.all()
    return render_template('branches/list.html', branches=branches)

@app.route('/branches/create', methods=['GET', 'POST'])
def branches_create():
    form = BranchForm()
    if form.validate_on_submit():
        branch = Branch(name=form.name.data, created_by=1)
        db.session.add(branch)
        db.session.commit()
        flash('Branche créée avec succès!', 'success')
        return redirect(url_for('branches_list'))
    return render_template('branches/create.html', form=form)

# Department routes
@app.route('/departments')
def departments_list():
    departments = Department.query.join(Branch).all()
    return render_template('departments/list.html', departments=departments)

@app.route('/departments/create', methods=['GET', 'POST'])
def departments_create():
    form = DepartmentForm()
    if form.validate_on_submit():
        department = Department(
            branch_id=form.branch_id.data,
            name=form.name.data,
            created_by=1
        )
        db.session.add(department)
        db.session.commit()
        flash('Département créé avec succès!', 'success')
        return redirect(url_for('departments_list'))
    return render_template('departments/create.html', form=form)

# Employee routes
@app.route('/employees')
def employees_list():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '', type=str)
    
    query = Employee.query.filter_by(is_active=1)
    
    if search:
        query = query.filter(
            (Employee.name.contains(search)) |
            (Employee.employee_id.contains(search)) |
            (Employee.email.contains(search))
        )
    
    employees = query.join(Branch, isouter=True).join(Department, isouter=True).paginate(
        page=page, per_page=10, error_out=False
    )
    
    return render_template('employees/list.html', employees=employees, search=search)

@app.route('/employees/create', methods=['GET', 'POST'])
def employees_create():
    form = EmployeeForm()
    if form.validate_on_submit():
        # Create user first
        user = User(
            name=form.name.data,
            email=form.email.data,
            password='default123',  # Should be hashed in production
            type='employee'
        )
        db.session.add(user)
        db.session.flush()  # Get the user ID
        
        # Create employee
        employee = Employee(
            user_id=user.id,
            name=form.name.data,
            cin=form.cin.data,
            phone=form.phone.data,
            address=form.address.data,
            email=form.email.data,
            employee_id=form.employee_id.data,
            branch_id=form.branch_id.data,
            department_id=form.department_id.data,
            designation_id=form.designation_id.data,
            company_doj=form.company_doj.data,
            account_holder_name=form.account_holder_name.data,
            account_number=form.account_number.data,
            bank_name=form.bank_name.data,
            bank_identifier_code=form.bank_identifier_code.data,
            branch_location=form.branch_location.data,
            tax_payer_id=form.tax_payer_id.data,
            salary_type=form.salary_type.data,
            salary=form.salary.data,
            created_by=1
        )
        db.session.add(employee)
        db.session.commit()
        flash('Employé créé avec succès!', 'success')
        return redirect(url_for('employees_list'))
    return render_template('employees/create.html', form=form)

@app.route('/employees/<int:id>')
def employees_view(id):
    employee = Employee.query.get_or_404(id)
    return render_template('employees/view.html', employee=employee)

@app.route('/employees/<int:id>/edit', methods=['GET', 'POST'])
def employees_edit(id):
    employee = Employee.query.get_or_404(id)
    form = EmployeeForm(obj=employee)
    
    if form.validate_on_submit():
        form.populate_obj(employee)
        employee.updated_at = datetime.utcnow()
        db.session.commit()
        flash('Employé modifié avec succès!', 'success')
        return redirect(url_for('employees_view', id=id))
    return render_template('employees/edit.html', form=form, employee=employee)

# Attendance routes
@app.route('/attendance')
def attendance_list():
    page = request.args.get('page', 1, type=int)
    date_filter = request.args.get('date', datetime.now().date().strftime('%Y-%m-%d'))
    
    attendance = AttendanceEmployee.query.join(Employee).filter(
        AttendanceEmployee.date == datetime.strptime(date_filter, '%Y-%m-%d').date()
    ).paginate(page=page, per_page=20, error_out=False)
    
    return render_template('attendance/list.html', attendance=attendance, date_filter=date_filter)

@app.route('/attendance/create', methods=['GET', 'POST'])
def attendance_create():
    form = AttendanceForm()
    if form.validate_on_submit():
        # Calculate time differences  
        if form.date.data and form.clock_in.data and form.clock_out.data:
            clock_in = datetime.combine(form.date.data, form.clock_in.data)
            clock_out = datetime.combine(form.date.data, form.clock_out.data)
        else:
            clock_in = None
            clock_out = None
        
        # Simple calculations (can be enhanced)
        late = datetime.strptime('00:00:00', '%H:%M:%S').time()
        early_leaving = datetime.strptime('00:00:00', '%H:%M:%S').time()
        overtime = datetime.strptime('00:00:00', '%H:%M:%S').time()
        total_rest = datetime.strptime('00:00:00', '%H:%M:%S').time()
        
        attendance = AttendanceEmployee(
            employee_id=form.employee_id.data,
            date=form.date.data,
            status=form.status.data,
            hs='8',  # Default 8 hours
            clock_in=form.clock_in.data,
            clock_out=form.clock_out.data,
            late=late,
            early_leaving=early_leaving,
            overtime=overtime,
            total_rest=total_rest,
            created_by=1
        )
        db.session.add(attendance)
        db.session.commit()
        flash('Présence enregistrée avec succès!', 'success')
        return redirect(url_for('attendance_list'))
    return render_template('attendance/create.html', form=form)

# Payroll routes
@app.route('/payroll')
def payroll_list():
    page = request.args.get('page', 1, type=int)
    payrolls = PaySlip.query.join(Employee).paginate(page=page, per_page=10, error_out=False)
    return render_template('payroll/list.html', payrolls=payrolls)

@app.route('/payroll/create', methods=['GET', 'POST'])
def payroll_create():
    form = PayrollForm()
    if form.validate_on_submit():
        # Calculate net payable
        basic_salary = form.basic_salary.data or 0
        allowance = form.allowance.data or 0
        commission = form.commission.data or 0
        other_payment = form.other_payment.data or 0
        overtime = form.overtime.data or 0
        loan = form.loan.data or 0
        saturation_deduction = form.saturation_deduction.data or 0
        
        net_payable = (basic_salary + allowance + commission + other_payment + overtime - loan - saturation_deduction)
        
        payroll = PaySlip(
            employee_id=form.employee_id.data,
            salary_month=form.salary_month.data,
            basic_salary=basic_salary,
            allowance=allowance,
            commission=commission,
            loan=loan,
            saturation_deduction=saturation_deduction,
            other_payment=other_payment,
            overtime=overtime,
            net_payble=net_payable,
            created_by=1
        )
        db.session.add(payroll)
        db.session.commit()
        flash('Bulletin de paie créé avec succès!', 'success')
        return redirect(url_for('payroll_list'))
    return render_template('payroll/create.html', form=form)

# Reports and Dashboard
@app.route('/reports/dashboard')
def reports_dashboard():
    # Employee statistics
    total_employees = Employee.query.filter_by(is_active=1).count()
    employees_by_branch = db.session.query(
        Branch.name, func.count(Employee.id)
    ).join(Employee).group_by(Branch.id, Branch.name).all()
    
    # Attendance statistics
    today = datetime.now().date()
    present_today = AttendanceEmployee.query.filter_by(date=today, status='present').count()
    absent_today = AttendanceEmployee.query.filter_by(date=today, status='absent').count()
    
    # Monthly payroll
    current_month = datetime.now().strftime('%m/%Y')
    monthly_payroll = db.session.query(
        func.sum(PaySlip.net_payble)
    ).filter_by(salary_month=current_month).scalar() or 0
    
    return render_template('reports/dashboard.html',
                         total_employees=total_employees,
                         employees_by_branch=employees_by_branch,
                         present_today=present_today,
                         absent_today=absent_today,
                         monthly_payroll=monthly_payroll)

@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500
