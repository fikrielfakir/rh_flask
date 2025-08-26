from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, DecimalField, DateField, TimeField, IntegerField, EmailField, BooleanField, FileField, PasswordField
from wtforms.validators import DataRequired, Email, Length, Optional, NumberRange, EqualTo
from flask_wtf.file import FileAllowed
from models import Branch, Department, Designation, Employee

class BranchForm(FlaskForm):
    name = StringField('Nom de la Branche', validators=[DataRequired(), Length(min=2, max=191)])

class DepartmentForm(FlaskForm):
    branch_id = SelectField('Branche', coerce=int, validators=[DataRequired()])
    name = StringField('Nom du Département', validators=[DataRequired(), Length(min=2, max=191)])
    
    def __init__(self, *args, **kwargs):
        super(DepartmentForm, self).__init__(*args, **kwargs)
        self.branch_id.choices = [(b.id, b.name) for b in Branch.query.all()]

class DesignationForm(FlaskForm):
    department_id = SelectField('Département', coerce=int, validators=[DataRequired()])
    name = StringField('Nom du Poste', validators=[DataRequired(), Length(min=2, max=191)])
    
    def __init__(self, *args, **kwargs):
        super(DesignationForm, self).__init__(*args, **kwargs)
        self.department_id.choices = [(d.id, f"{d.name} ({d.branch.name})") for d in Department.query.join(Branch).all()]

class EmployeeForm(FlaskForm):
    # Basic Information
    name = StringField('Nom Complet', validators=[DataRequired(), Length(min=2, max=191)])
    cin = StringField('CIN', validators=[Optional(), Length(max=20)])
    phone = StringField('Téléphone', validators=[Optional(), Length(max=20)])
    address = TextAreaField('Adresse', validators=[Optional()])
    email = EmailField('Email', validators=[DataRequired(), Email()])
    employee_id = StringField('ID Employé', validators=[DataRequired(), Length(max=50)])
    
    # Enhanced Personal Information
    date_of_birth = DateField('Date de Naissance', validators=[Optional()])
    gender = SelectField('Genre', choices=[
        ('', 'Sélectionner...'),
        ('male', 'Homme'),
        ('female', 'Femme')
    ], validators=[Optional()])
    marital_status = SelectField('État Civil', choices=[
        ('', 'Sélectionner...'),
        ('single', 'Célibataire'),
        ('married', 'Marié(e)'),
        ('divorced', 'Divorcé(e)'),
        ('widowed', 'Veuf/Veuve')
    ], validators=[Optional()])
    nationality = StringField('Nationalité', validators=[Optional(), Length(max=50)])
    blood_group = SelectField('Groupe Sanguin', choices=[
        ('', 'Sélectionner...'),
        ('A+', 'A+'), ('A-', 'A-'),
        ('B+', 'B+'), ('B-', 'B-'),
        ('AB+', 'AB+'), ('AB-', 'AB-'),
        ('O+', 'O+'), ('O-', 'O-')
    ], validators=[Optional()])
    
    # Professional Information
    branch_id = SelectField('Branche', coerce=int, validators=[DataRequired()])
    department_id = SelectField('Département', coerce=int, validators=[DataRequired()])
    designation_id = SelectField('Poste', coerce=int, validators=[DataRequired()])
    manager_id = SelectField('Manager', coerce=int, validators=[Optional()])
    company_doj = DateField('Date d\'Embauche', validators=[Optional()])
    work_location = StringField('Lieu de Travail', validators=[Optional(), Length(max=191)])
    work_phone = StringField('Téléphone Professionnel', validators=[Optional(), Length(max=20)])
    
    # Contract Information
    contract_type = SelectField('Type de Contrat', choices=[
        ('permanent', 'Permanent'),
        ('temporary', 'Temporaire'),
        ('contract', 'Contrat')
    ], validators=[DataRequired()])
    employment_status = SelectField('Statut d\'Emploi', choices=[
        ('active', 'Actif'),
        ('inactive', 'Inactif'),
        ('suspended', 'Suspendu')
    ], validators=[DataRequired()])
    probation_period_months = IntegerField('Période d\'Essai (mois)', validators=[Optional(), NumberRange(min=0, max=24)])
    notice_period_days = IntegerField('Préavis (jours)', validators=[Optional(), NumberRange(min=0, max=365)])
    weekly_working_hours = DecimalField('Heures Travail/Semaine', validators=[Optional(), NumberRange(min=0, max=80)])
    
    # Benefits
    overtime_eligible = BooleanField('Éligible aux Heures Supplémentaires')
    health_insurance = BooleanField('Assurance Santé')
    life_insurance = BooleanField('Assurance Vie')
    annual_leave_days = IntegerField('Jours Congé Annuels', validators=[Optional(), NumberRange(min=0, max=50)])
    sick_leave_days = IntegerField('Jours Congé Maladie', validators=[Optional(), NumberRange(min=0, max=30)])
    personal_leave_days = IntegerField('Jours Congé Personnel', validators=[Optional(), NumberRange(min=0, max=20)])
    
    # Banking Information
    account_holder_name = StringField('Nom du Titulaire du Compte', validators=[Optional(), Length(max=191)])
    account_number = StringField('Numéro de Compte', validators=[Optional(), Length(max=50)])
    bank_name = StringField('Nom de la Banque', validators=[Optional(), Length(max=191)])
    bank_identifier_code = StringField('Code BIC', validators=[Optional(), Length(max=50)])
    branch_location = StringField('Agence', validators=[Optional(), Length(max=191)])
    tax_payer_id = StringField('Numéro Fiscal', validators=[Optional(), Length(max=50)])
    
    # Salary Information
    salary_type = SelectField('Type de Salaire', choices=[('monthly', 'Mensuel'), ('hourly', 'Horaire')], validators=[DataRequired()])
    salary = DecimalField('Salaire', validators=[DataRequired(), NumberRange(min=0)])
    
    # Skills and Additional Info
    skills = TextAreaField('Compétences (séparées par des virgules)', validators=[Optional()])
    languages = TextAreaField('Langues Parlées (séparées par des virgules)', validators=[Optional()])
    certifications = TextAreaField('Certifications', validators=[Optional()])
    
    def __init__(self, *args, **kwargs):
        super(EmployeeForm, self).__init__(*args, **kwargs)
        self.branch_id.choices = [(b.id, b.name) for b in Branch.query.all()]
        self.department_id.choices = [(d.id, f"{d.name} ({d.branch.name})") for d in Department.query.join(Branch).all()]
        self.designation_id.choices = [(d.id, f"{d.name} ({d.department.name})") for d in Designation.query.join(Department).all()]
        # Managers are employees who can manage others
        self.manager_id.choices = [('', 'Aucun Manager')] + [(e.id, f"{e.name} ({e.employee_id})") for e in Employee.query.filter_by(is_active=1).all()]

class EmergencyContactForm(FlaskForm):
    name = StringField('Nom Complet', validators=[DataRequired(), Length(min=2, max=191)])
    relationship = SelectField('Relation', choices=[
        ('parent', 'Parent'),
        ('spouse', 'Époux/Épouse'),
        ('sibling', 'Frère/Sœur'),
        ('child', 'Enfant'),
        ('friend', 'Ami(e)'),
        ('other', 'Autre')
    ], validators=[DataRequired()])
    phone = StringField('Téléphone', validators=[DataRequired(), Length(max=20)])
    email = EmailField('Email', validators=[Optional(), Email()])
    address = TextAreaField('Adresse', validators=[Optional()])
    is_primary = BooleanField('Contact Principal')

class DocumentUploadForm(FlaskForm):
    document_type = SelectField('Type de Document', choices=[
        ('cv', 'CV'),
        ('contract', 'Contrat'),
        ('certificate', 'Certificat'),
        ('passport', 'Passeport'),
        ('license', 'Permis'),
        ('diploma', 'Diplôme'),
        ('photo', 'Photo'),
        ('other', 'Autre')
    ], validators=[DataRequired()])
    document_name = StringField('Nom du Document', validators=[DataRequired(), Length(max=191)])
    file = FileField('Fichier', validators=[DataRequired(), FileAllowed(['pdf', 'jpg', 'jpeg', 'png', 'doc', 'docx'], 'Fichiers PDF, images et documents Word uniquement!')])
    expiry_date = DateField('Date d\'Expiration', validators=[Optional()])

class PerformanceReviewForm(FlaskForm):
    employee_id = SelectField('Employé', coerce=int, validators=[DataRequired()])
    review_period_start = DateField('Début de Période', validators=[DataRequired()])
    review_period_end = DateField('Fin de Période', validators=[DataRequired()])
    overall_rating = DecimalField('Note Globale (0-5)', validators=[DataRequired(), NumberRange(min=0, max=5)])
    goals_achievement = DecimalField('Atteinte des Objectifs (0-5)', validators=[Optional(), NumberRange(min=0, max=5)])
    communication_skills = DecimalField('Communication (0-5)', validators=[Optional(), NumberRange(min=0, max=5)])
    technical_skills = DecimalField('Compétences Techniques (0-5)', validators=[Optional(), NumberRange(min=0, max=5)])
    teamwork = DecimalField('Travail d\'Équipe (0-5)', validators=[Optional(), NumberRange(min=0, max=5)])
    punctuality = DecimalField('Ponctualité (0-5)', validators=[Optional(), NumberRange(min=0, max=5)])
    strengths = TextAreaField('Points Forts', validators=[Optional()])
    areas_for_improvement = TextAreaField('Axes d\'Amélioration', validators=[Optional()])
    goals_next_period = TextAreaField('Objectifs Prochaine Période', validators=[Optional()])
    reviewer_comments = TextAreaField('Commentaires du Superviseur', validators=[Optional()])
    
    def __init__(self, *args, **kwargs):
        super(PerformanceReviewForm, self).__init__(*args, **kwargs)
        self.employee_id.choices = [(e.id, f"{e.name} ({e.employee_id})") for e in Employee.query.filter_by(is_active=1).all()]

class LeaveRequestForm(FlaskForm):
    employee_id = SelectField('Employé', coerce=int, validators=[DataRequired()])
    leave_type = SelectField('Type de Congé', choices=[
        ('annual', 'Congé Annuel'),
        ('sick', 'Congé Maladie'),
        ('personal', 'Congé Personnel'),
        ('maternity', 'Congé Maternité'),
        ('paternity', 'Congé Paternité'),
        ('emergency', 'Congé Urgence')
    ], validators=[DataRequired()])
    start_date = DateField('Date de Début', validators=[DataRequired()])
    end_date = DateField('Date de Fin', validators=[DataRequired()])
    reason = TextAreaField('Raison', validators=[Optional()])
    
    def __init__(self, *args, **kwargs):
        super(LeaveRequestForm, self).__init__(*args, **kwargs)
        self.employee_id.choices = [(e.id, f"{e.name} ({e.employee_id})") for e in Employee.query.filter_by(is_active=1).all()]

class TrainingForm(FlaskForm):
    employee_id = SelectField('Employé', coerce=int, validators=[DataRequired()])
    training_title = StringField('Titre de la Formation', validators=[DataRequired(), Length(max=191)])
    training_provider = StringField('Organisme de Formation', validators=[Optional(), Length(max=191)])
    training_type = SelectField('Type de Formation', choices=[
        ('internal', 'Interne'),
        ('external', 'Externe'),
        ('online', 'En Ligne'),
        ('workshop', 'Atelier'),
        ('conference', 'Conférence')
    ], validators=[DataRequired()])
    start_date = DateField('Date de Début', validators=[Optional()])
    end_date = DateField('Date de Fin', validators=[Optional()])
    duration_hours = IntegerField('Durée (heures)', validators=[Optional(), NumberRange(min=0)])
    cost = DecimalField('Coût', validators=[Optional(), NumberRange(min=0)])
    notes = TextAreaField('Notes', validators=[Optional()])
    
    def __init__(self, *args, **kwargs):
        super(TrainingForm, self).__init__(*args, **kwargs)
        self.employee_id.choices = [(e.id, f"{e.name} ({e.employee_id})") for e in Employee.query.filter_by(is_active=1).all()]

class AttendanceForm(FlaskForm):
    employee_id = SelectField('Employé', coerce=int, validators=[DataRequired()])
    date = DateField('Date', validators=[DataRequired()])
    status = SelectField('Statut', choices=[
        ('present', 'Présent'),
        ('absent', 'Absent'),
        ('late', 'En retard'),
        ('half_day', 'Demi-journée')
    ], validators=[DataRequired()])
    clock_in = TimeField('Heure d\'Arrivée', validators=[DataRequired()])
    clock_out = TimeField('Heure de Sortie', validators=[DataRequired()])
    
    def __init__(self, *args, **kwargs):
        super(AttendanceForm, self).__init__(*args, **kwargs)
        self.employee_id.choices = [(e.id, f"{e.name} ({e.employee_id})") for e in Employee.query.filter_by(is_active=1).all()]

class PayrollForm(FlaskForm):
    employee_id = SelectField('Employé', coerce=int, validators=[DataRequired()])
    salary_month = StringField('Mois/Année', validators=[DataRequired()])
    basic_salary = DecimalField('Salaire de Base', validators=[DataRequired(), NumberRange(min=0)])
    allowance = DecimalField('Indemnités', validators=[Optional(), NumberRange(min=0)])
    commission = DecimalField('Commission', validators=[Optional(), NumberRange(min=0)])
    loan = DecimalField('Prêt', validators=[Optional(), NumberRange(min=0)])
    saturation_deduction = DecimalField('Déduction Saturation', validators=[Optional(), NumberRange(min=0)])
    other_payment = DecimalField('Autres Paiements', validators=[Optional(), NumberRange(min=0)])
    overtime = DecimalField('Heures Supplémentaires', validators=[Optional(), NumberRange(min=0)])
    
    def __init__(self, *args, **kwargs):
        super(PayrollForm, self).__init__(*args, **kwargs)
        self.employee_id.choices = [(e.id, f"{e.name} ({e.employee_id})") for e in Employee.query.filter_by(is_active=1).all()]

class AdvanceForm(FlaskForm):
    employee_id = SelectField('Employé', coerce=int, validators=[DataRequired()])
    amount = DecimalField('Montant', validators=[DataRequired(), NumberRange(min=0)])
    date = DateField('Date', validators=[DataRequired()])
    reason = StringField('Raison', validators=[Optional(), Length(max=191)])
    
    def __init__(self, *args, **kwargs):
        super(AdvanceForm, self).__init__(*args, **kwargs)
        self.employee_id.choices = [(e.id, f"{e.name} ({e.employee_id})") for e in Employee.query.filter_by(is_active=1).all()]
