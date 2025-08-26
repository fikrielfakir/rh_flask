from flask import render_template, request, redirect, url_for, flash, jsonify
from app import app, db
from models import (
    User, Branch, Department, Designation, Employee, AttendanceEmployee, 
    AllowanceOption, DeductionOption, PaySlip, EmergencyContact, 
    EmployeeDocument, PerformanceReview, LeaveRequest, EmployeeTraining
)
from forms import (
    BranchForm, DepartmentForm, DesignationForm, EmployeeForm, 
    AttendanceForm, PayrollForm, EmergencyContactForm, DocumentUploadForm, 
    PerformanceReviewForm, LeaveRequestForm, TrainingForm
)
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

@app.route('/employees/<int:id>')
def employees_view(id):
    employee = Employee.query.get_or_404(id)
    return render_template('employees/view.html', employee=employee)

@app.route('/employees/<int:id>/edit', methods=['GET', 'POST'])
def employees_edit(id):
    employee = Employee.query.get_or_404(id)
    form = EmployeeForm(obj=employee)
    
    if form.validate_on_submit():
        # Update employee data
        form.populate_obj(employee)
        employee.updated_at = datetime.utcnow()
        db.session.commit()
        flash('Employé mis à jour avec succès!', 'success')
        return redirect(url_for('employees_view', id=employee.id))
    
    return render_template('employees/edit.html', form=form, employee=employee)

@app.route('/employees/<int:id>/profile')
def employees_profile(id):
    employee = Employee.query.get_or_404(id)
    emergency_contacts = EmergencyContact.query.filter_by(employee_id=id).all()
    documents = EmployeeDocument.query.filter_by(employee_id=id).all()
    performance_reviews = PerformanceReview.query.filter_by(employee_id=id).order_by(PerformanceReview.created_at.desc()).all()
    leave_requests = LeaveRequest.query.filter_by(employee_id=id).order_by(LeaveRequest.created_at.desc()).limit(10).all()
    trainings = EmployeeTraining.query.filter_by(employee_id=id).order_by(EmployeeTraining.created_at.desc()).limit(10).all()
    
    return render_template('employees/profile.html', 
                         employee=employee,
                         emergency_contacts=emergency_contacts,
                         documents=documents,
                         performance_reviews=performance_reviews,
                         leave_requests=leave_requests,
                         trainings=trainings)

# Emergency Contacts
@app.route('/employees/<int:employee_id>/emergency-contacts/add', methods=['GET', 'POST'])
def emergency_contacts_add(employee_id):
    employee = Employee.query.get_or_404(employee_id)
    form = EmergencyContactForm()
    
    if form.validate_on_submit():
        # If this is marked as primary, remove primary status from others
        if form.is_primary.data:
            EmergencyContact.query.filter_by(employee_id=employee_id, is_primary=True).update({'is_primary': False})
        
        contact = EmergencyContact(
            employee_id=employee_id,
            name=form.name.data,
            relationship=form.relationship.data,
            phone=form.phone.data,
            email=form.email.data,
            address=form.address.data,
            is_primary=form.is_primary.data
        )
        db.session.add(contact)
        db.session.commit()
        flash('Contact d\'urgence ajouté avec succès!', 'success')
        return redirect(url_for('employees_profile', id=employee_id))
    
    return render_template('employees/emergency_contact_form.html', form=form, employee=employee)

# Document Management
@app.route('/employees/<int:employee_id>/documents/upload', methods=['GET', 'POST'])
def documents_upload(employee_id):
    employee = Employee.query.get_or_404(employee_id)
    form = DocumentUploadForm()
    
    if form.validate_on_submit():
        # Here you would normally handle file upload to a storage service
        # For now, we'll just store the metadata
        document = EmployeeDocument(
            employee_id=employee_id,
            document_type=form.document_type.data,
            document_name=form.document_name.data,
            file_path=f"uploads/{employee_id}/{form.file.data.filename}",  # Placeholder
            uploaded_by=1,  # Current user ID
            expiry_date=form.expiry_date.data
        )
        db.session.add(document)
        db.session.commit()
        flash('Document téléchargé avec succès!', 'success')
        return redirect(url_for('employees_profile', id=employee_id))
    
    return render_template('employees/document_upload.html', form=form, employee=employee)

# Performance Reviews
@app.route('/employees/performance-reviews')
def performance_reviews_list():
    reviews = PerformanceReview.query.join(Employee).order_by(PerformanceReview.created_at.desc()).all()
    return render_template('employees/performance_reviews.html', reviews=reviews)

@app.route('/employees/performance-reviews/create', methods=['GET', 'POST'])
def performance_reviews_create():
    form = PerformanceReviewForm()
    
    if form.validate_on_submit():
        review = PerformanceReview(
            employee_id=form.employee_id.data,
            reviewer_id=1,  # Current user ID
            review_period_start=form.review_period_start.data,
            review_period_end=form.review_period_end.data,
            overall_rating=form.overall_rating.data,
            goals_achievement=form.goals_achievement.data,
            communication_skills=form.communication_skills.data,
            technical_skills=form.technical_skills.data,
            teamwork=form.teamwork.data,
            punctuality=form.punctuality.data,
            strengths=form.strengths.data,
            areas_for_improvement=form.areas_for_improvement.data,
            goals_next_period=form.goals_next_period.data,
            reviewer_comments=form.reviewer_comments.data
        )
        db.session.add(review)
        db.session.commit()
        flash('Évaluation de performance créée avec succès!', 'success')
        return redirect(url_for('performance_reviews_list'))
    
    return render_template('employees/performance_review_form.html', form=form)

# Leave Management
@app.route('/employees/leave-requests')
def leave_requests_list():
    requests = LeaveRequest.query.join(Employee).order_by(LeaveRequest.created_at.desc()).all()
    return render_template('employees/leave_requests.html', requests=requests)

@app.route('/employees/leave-requests/create', methods=['GET', 'POST'])
def leave_requests_create():
    form = LeaveRequestForm()
    
    if form.validate_on_submit():
        # Calculate days requested
        start_date = form.start_date.data
        end_date = form.end_date.data
        days_requested = (end_date - start_date).days + 1
        
        leave_request = LeaveRequest(
            employee_id=form.employee_id.data,
            leave_type=form.leave_type.data,
            start_date=start_date,
            end_date=end_date,
            days_requested=days_requested,
            reason=form.reason.data
        )
        db.session.add(leave_request)
        db.session.commit()
        flash('Demande de congé soumise avec succès!', 'success')
        return redirect(url_for('leave_requests_list'))
    
    return render_template('employees/leave_request_form.html', form=form)

@app.route('/employees/leave-requests/<int:id>/approve')
def leave_requests_approve(id):
    leave_request = LeaveRequest.query.get_or_404(id)
    leave_request.status = 'approved'
    leave_request.approved_by = 1  # Current user ID
    leave_request.approved_at = datetime.utcnow()
    db.session.commit()
    flash('Demande de congé approuvée!', 'success')
    return redirect(url_for('leave_requests_list'))

@app.route('/employees/leave-requests/<int:id>/reject')
def leave_requests_reject(id):
    leave_request = LeaveRequest.query.get_or_404(id)
    leave_request.status = 'rejected'
    leave_request.approved_by = 1  # Current user ID
    leave_request.approved_at = datetime.utcnow()
    db.session.commit()
    flash('Demande de congé rejetée!', 'warning')
    return redirect(url_for('leave_requests_list'))

# Training Management
@app.route('/employees/trainings')
def trainings_list():
    trainings = EmployeeTraining.query.join(Employee).order_by(EmployeeTraining.created_at.desc()).all()
    return render_template('employees/trainings.html', trainings=trainings)

@app.route('/employees/trainings/create', methods=['GET', 'POST'])
def trainings_create():
    form = TrainingForm()
    
    if form.validate_on_submit():
        training = EmployeeTraining(
            employee_id=form.employee_id.data,
            training_title=form.training_title.data,
            training_provider=form.training_provider.data,
            training_type=form.training_type.data,
            start_date=form.start_date.data,
            end_date=form.end_date.data,
            duration_hours=form.duration_hours.data,
            cost=form.cost.data,
            notes=form.notes.data
        )
        db.session.add(training)
        db.session.commit()
        flash('Formation enregistrée avec succès!', 'success')
        return redirect(url_for('trainings_list'))
    
    return render_template('employees/training_form.html', form=form)

# Employee Dashboard/Analytics
@app.route('/employees/dashboard')
def employees_dashboard():
    # Employee statistics
    total_employees = Employee.query.filter_by(is_active=1).count()
    new_employees_this_month = Employee.query.filter(
        extract('month', Employee.created_at) == datetime.now().month,
        extract('year', Employee.created_at) == datetime.now().year
    ).count()
    
    # Performance statistics
    avg_performance = db.session.query(func.avg(PerformanceReview.overall_rating)).scalar() or 0
    
    # Leave statistics
    pending_leaves = LeaveRequest.query.filter_by(status='pending').count()
    approved_leaves_this_month = LeaveRequest.query.filter(
        LeaveRequest.status == 'approved',
        extract('month', LeaveRequest.start_date) == datetime.now().month
    ).count()
    
    # Training statistics
    ongoing_trainings = EmployeeTraining.query.filter_by(status='ongoing').count()
    completed_trainings = EmployeeTraining.query.filter_by(status='completed').count()
    
    # Recent activities
    recent_employees = Employee.query.filter_by(is_active=1).order_by(Employee.created_at.desc()).limit(5).all()
    recent_reviews = PerformanceReview.query.join(Employee).order_by(PerformanceReview.created_at.desc()).limit(5).all()
    recent_leaves = LeaveRequest.query.join(Employee).order_by(LeaveRequest.created_at.desc()).limit(5).all()
    
    return render_template('employees/dashboard.html',
                         total_employees=total_employees,
                         new_employees_this_month=new_employees_this_month,
                         avg_performance=round(avg_performance, 2),
                         pending_leaves=pending_leaves,
                         approved_leaves_this_month=approved_leaves_this_month,
                         ongoing_trainings=ongoing_trainings,
                         completed_trainings=completed_trainings,
                         recent_employees=recent_employees,
                         recent_reviews=recent_reviews,
                         recent_leaves=recent_leaves)

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
            created_by=1,
            # Enhanced fields
            date_of_birth=form.date_of_birth.data,
            gender=form.gender.data,
            marital_status=form.marital_status.data,
            nationality=form.nationality.data,
            blood_group=form.blood_group.data,
            contract_type=form.contract_type.data,
            employment_status=form.employment_status.data,
            manager_id=form.manager_id.data if form.manager_id.data else None,
            work_location=form.work_location.data,
            work_phone=form.work_phone.data,
            probation_period_months=form.probation_period_months.data,
            notice_period_days=form.notice_period_days.data,
            weekly_working_hours=form.weekly_working_hours.data,
            overtime_eligible=form.overtime_eligible.data,
            health_insurance=form.health_insurance.data,
            life_insurance=form.life_insurance.data,
            annual_leave_days=form.annual_leave_days.data,
            sick_leave_days=form.sick_leave_days.data,
            personal_leave_days=form.personal_leave_days.data,
            skills=form.skills.data,
            languages=form.languages.data,
            certifications=form.certifications.data
        )
        db.session.add(employee)
        db.session.commit()
        flash('Employé créé avec succès!', 'success')
        return redirect(url_for('employees_view', id=employee.id))
    return render_template('employees/create.html', form=form)

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
