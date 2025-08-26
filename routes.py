from flask import render_template, request, redirect, url_for, flash, jsonify, make_response, send_file
import csv
import io
from werkzeug.utils import secure_filename
import os
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

@app.route('/employees/export')
def employees_export():
    """Export employees to CSV"""
    employees = Employee.query.filter_by(is_active=1).join(Branch, isouter=True).join(Department, isouter=True).all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow([
        'ID Employé', 'Nom', 'CIN', 'Téléphone', 'Adresse', 'Email',
        'Branche', 'Département', 'Date d\'embauche', 'Salaire',
        'Date de naissance', 'Genre', 'Statut matrimonial', 'Nationalité',
        'Groupe sanguin', 'Type de contrat', 'Statut d\'emploi'
    ])
    
    # Write employee data
    for employee in employees:
        writer.writerow([
            employee.employee_id,
            employee.name,
            employee.cin,
            employee.phone,
            employee.address,
            employee.email,
            employee.branch.name if employee.branch else '',
            employee.department.name if employee.department else '',
            employee.company_doj.strftime('%d/%m/%Y') if employee.company_doj else '',
            employee.salary if employee.salary else '',
            employee.date_of_birth.strftime('%d/%m/%Y') if employee.date_of_birth else '',
            employee.gender if employee.gender else '',
            employee.marital_status if employee.marital_status else '',
            employee.nationality if employee.nationality else '',
            employee.blood_group if employee.blood_group else '',
            employee.contract_type if employee.contract_type else '',
            employee.employment_status if employee.employment_status else ''
        ])
    
    output.seek(0)
    
    # Create response
    response = make_response(output.getvalue())
    response.headers["Content-Disposition"] = "attachment; filename=employes_export.csv"
    response.headers["Content-type"] = "text/csv; charset=utf-8"
    
    return response

@app.route('/employees/import', methods=['GET', 'POST'])
def employees_import():
    """Import employees from CSV"""
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('Aucun fichier sélectionné', 'error')
            return redirect(request.url)
        
        file = request.files['file']
        if file.filename == '':
            flash('Aucun fichier sélectionné', 'error')
            return redirect(request.url)
        
        if file and file.filename.lower().endswith('.csv'):
            try:
                # Read the raw bytes first
                raw_data = file.stream.read()
                
                # Try to detect encoding using chardet
                import chardet
                detected = chardet.detect(raw_data)
                encoding = detected['encoding'] if detected['confidence'] > 0.7 else 'utf-8'
                
                # Try different encodings in order of preference
                encodings_to_try = [encoding, 'utf-8', 'latin-1', 'windows-1252', 'iso-8859-1']
                
                decoded_data = None
                for enc in encodings_to_try:
                    try:
                        decoded_data = raw_data.decode(enc)
                        break
                    except UnicodeDecodeError:
                        continue
                
                if decoded_data is None:
                    flash('Erreur: Le fichier ne peut pas être lu avec les encodages supportés (UTF-8, Latin-1, Windows-1252). Veuillez vérifier le format du fichier.', 'error')
                    return redirect(request.url)
                
                stream = io.StringIO(decoded_data, newline=None)
                csv_input = csv.DictReader(stream)
                
                imported_count = 0
                errors = []
                
                for row_num, row in enumerate(csv_input, start=2):
                    try:
                        # Check if employee already exists
                        existing_employee = Employee.query.filter_by(employee_id=row.get('ID Employé', '').strip()).first()
                        if existing_employee:
                            errors.append(f"Ligne {row_num}: Employé avec ID '{row.get('ID Employé', '').strip()}' existe déjà")
                            continue
                        
                        # Check email uniqueness
                        if row.get('Email', '').strip():
                            existing_email = Employee.query.filter_by(email=row.get('Email', '').strip()).first()
                            if existing_email:
                                errors.append(f"Ligne {row_num}: Email '{row.get('Email', '').strip()}' déjà utilisé")
                                continue
                        
                        # Find branch and department
                        branch = None
                        department = None
                        
                        if row.get('Branche', '').strip():
                            branch = Branch.query.filter_by(name=row.get('Branche', '').strip()).first()
                            if not branch:
                                errors.append(f"Ligne {row_num}: Branche '{row.get('Branche', '').strip()}' introuvable")
                                continue
                        
                        if row.get('Département', '').strip():
                            department = Department.query.filter_by(name=row.get('Département', '').strip()).first()
                            if not department:
                                errors.append(f"Ligne {row_num}: Département '{row.get('Département', '').strip()}' introuvable")
                                continue
                        
                        # Create user first
                        user = User(
                            name=row.get('Nom', '').strip(),
                            email=row.get('Email', '').strip(),
                            password='default123',  # Should be hashed in production
                            type='employee'
                        )
                        db.session.add(user)
                        db.session.flush()
                        
                        # Parse dates
                        company_doj = None
                        date_of_birth = None
                        
                        if row.get('Date d\'embauche', '').strip():
                            try:
                                company_doj = datetime.strptime(row.get('Date d\'embauche', '').strip(), '%d/%m/%Y')
                            except ValueError:
                                errors.append(f"Ligne {row_num}: Format de date d'embauche invalide (utilisez JJ/MM/AAAA)")
                                continue
                        
                        if row.get('Date de naissance', '').strip():
                            try:
                                date_of_birth = datetime.strptime(row.get('Date de naissance', '').strip(), '%d/%m/%Y')
                            except ValueError:
                                errors.append(f"Ligne {row_num}: Format de date de naissance invalide (utilisez JJ/MM/AAAA)")
                                continue
                        
                        # Parse salary
                        salary = None
                        if row.get('Salaire', '').strip():
                            try:
                                salary = float(row.get('Salaire', '').strip())
                            except ValueError:
                                errors.append(f"Ligne {row_num}: Format de salaire invalide")
                                continue
                        
                        # Create employee
                        employee = Employee(
                            user_id=user.id,
                            name=row.get('Nom', '').strip(),
                            cin=row.get('CIN', '').strip(),
                            phone=row.get('Téléphone', '').strip(),
                            address=row.get('Adresse', '').strip(),
                            email=row.get('Email', '').strip(),
                            employee_id=row.get('ID Employé', '').strip(),
                            branch_id=branch.id if branch else None,
                            department_id=department.id if department else None,
                            company_doj=company_doj,
                            salary=salary,
                            date_of_birth=date_of_birth,
                            gender=row.get('Genre', '').strip(),
                            marital_status=row.get('Statut matrimonial', '').strip(),
                            nationality=row.get('Nationalité', '').strip(),
                            blood_group=row.get('Groupe sanguin', '').strip(),
                            contract_type=row.get('Type de contrat', '').strip(),
                            employment_status=row.get('Statut d\'emploi', '').strip(),
                            created_by=1,
                            is_active=1
                        )
                        db.session.add(employee)
                        imported_count += 1
                        
                    except Exception as e:
                        errors.append(f"Ligne {row_num}: Erreur - {str(e)}")
                        continue
                
                if imported_count > 0:
                    db.session.commit()
                    flash(f'{imported_count} employé(s) importé(s) avec succès!', 'success')
                else:
                    db.session.rollback()
                
                if errors:
                    flash('Erreurs d\'importation:', 'warning')
                    for error in errors[:10]:  # Show only first 10 errors
                        flash(f'• {error}', 'warning')
                    if len(errors) > 10:
                        flash(f'... et {len(errors) - 10} autres erreurs', 'warning')
                
                return redirect(url_for('employees_list'))
                
            except Exception as e:
                flash(f'Erreur lors de la lecture du fichier: {str(e)}', 'error')
                return redirect(request.url)
        else:
            flash('Veuillez sélectionner un fichier CSV', 'error')
            return redirect(request.url)
    
    return render_template('employees/import.html')

@app.route('/employees/import-template')
def employees_import_template():
    """Download CSV template for employee import"""
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header with example data
    writer.writerow([
        'ID Employé', 'Nom', 'CIN', 'Téléphone', 'Adresse', 'Email',
        'Branche', 'Département', 'Date d\'embauche', 'Salaire',
        'Date de naissance', 'Genre', 'Statut matrimonial', 'Nationalité',
        'Groupe sanguin', 'Type de contrat', 'Statut d\'emploi'
    ])
    
    # Add example row
    writer.writerow([
        'EMP001', 'Ahmed Alami', 'AB123456', '+212612345678', 
        '123 Rue Hassan II, Casablanca', 'ahmed.alami@ceramica.ma',
        'Casablanca', 'Ressources Humaines', '01/01/2024', '8000',
        '15/05/1990', 'Masculin', 'Marié', 'Marocaine',
        'O+', 'CDI', 'Actif'
    ])
    
    output.seek(0)
    
    response = make_response(output.getvalue())
    response.headers["Content-Disposition"] = "attachment; filename=modele_import_employes.csv"
    response.headers["Content-type"] = "text/csv; charset=utf-8"
    
    return response

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
        try:
            # Import the simplified payroll calculator
            from simple_payroll_calculator import calculate_simple_payslip
            
            # Get form data
            employee_id = form.employee_id.data
            salary_month = form.salary_month.data
            
            # Convert overtime amount to hours (approximate)
            overtime_amount = float(form.overtime.data or 0)
            employee = Employee.query.get(employee_id)
            if employee and employee.salary:
                hourly_rate = float(employee.salary) / 191  # Standard monthly hours
                overtime_hours = overtime_amount / (hourly_rate * 1.25) if hourly_rate > 0 else 0
            else:
                overtime_hours = 0
            
            leave_allowance = float(form.allowance.data or 0)
            
            # Calculate payslip using simplified Moroccan labor law calculator
            payslip, errors = calculate_simple_payslip(
                employee_id, 
                salary_month, 
                overtime_hours, 
                leave_allowance
            )
            
            if payslip:
                flash('Fiche de paie calculée avec succès selon la loi marocaine!', 'success')
                flash('Incluant: bonus ancienneté, contributions sociales (CNSS/AMO/CIMR), et impôt progressif', 'info')
                if errors:
                    for error in errors:
                        flash(f'Avertissement: {error}', 'warning')
                return redirect(url_for('payroll_view', id=payslip.id))
            else:
                for error in errors:
                    flash(f'Erreur de calcul: {error}', 'error')
                return redirect(request.url)
                
        except Exception as e:
            flash(f'Erreur lors du calcul de la paie: {str(e)}', 'error')
            return redirect(request.url)
    
    return render_template('payroll/create.html', form=form)

@app.route('/payroll/<int:id>')
def payroll_view(id):
    """View detailed payslip"""
    payslip = PaySlip.query.get_or_404(id)
    return render_template('payroll/view.html', payslip=payslip)

@app.route('/payroll/calculate-batch', methods=['POST'])
def payroll_calculate_batch():
    """Calculate payroll for all employees for a given month"""
    salary_month = request.form.get('salary_month')
    if not salary_month:
        flash('Mois de salaire requis', 'error')
        return redirect(url_for('payroll_list'))
    
    try:
        from simple_payroll_calculator import calculate_simple_payslip
        
        # Get all active employees
        employees = Employee.query.filter_by(is_active=1).all()
        successful_calculations = 0
        total_errors = []
        
        for employee in employees:
            try:
                # Basic calculation with no overtime or special allowances for batch
                payslip, errors = calculate_simple_payslip(
                    employee.id, 
                    salary_month, 
                    overtime_hours=0, 
                    leave_allowance=0
                )
                
                if payslip:
                    successful_calculations += 1
                if errors:
                    total_errors.extend([f"{employee.name}: {error}" for error in errors])
                    
            except Exception as e:
                total_errors.append(f"{employee.name}: {str(e)}")
        
        flash(f'{successful_calculations} fiches de paie calculées avec succès selon la loi marocaine!', 'success')
        flash('Calculs incluant: bonus ancienneté, CNSS/AMO/CIMR, et impôt progressif', 'info')
        if total_errors:
            flash(f'{len(total_errors)} erreurs rencontrées lors du calcul', 'warning')
            
    except Exception as e:
        flash(f'Erreur lors du calcul en lot: {str(e)}', 'error')
    
    return redirect(url_for('payroll_list'))