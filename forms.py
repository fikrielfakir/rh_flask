from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, DecimalField, DateField, TimeField, IntegerField, EmailField
from wtforms.validators import DataRequired, Email, Length, Optional, NumberRange
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
    name = StringField('Nom Complet', validators=[DataRequired(), Length(min=2, max=191)])
    cin = StringField('CIN', validators=[Optional(), Length(max=20)])
    phone = StringField('Téléphone', validators=[Optional(), Length(max=20)])
    address = TextAreaField('Adresse', validators=[Optional()])
    email = EmailField('Email', validators=[DataRequired(), Email()])
    employee_id = StringField('ID Employé', validators=[DataRequired(), Length(max=50)])
    branch_id = SelectField('Branche', coerce=int, validators=[DataRequired()])
    department_id = SelectField('Département', coerce=int, validators=[DataRequired()])
    designation_id = SelectField('Poste', coerce=int, validators=[DataRequired()])
    company_doj = DateField('Date d\'Embauche', validators=[Optional()])
    account_holder_name = StringField('Nom du Titulaire du Compte', validators=[Optional(), Length(max=191)])
    account_number = StringField('Numéro de Compte', validators=[Optional(), Length(max=50)])
    bank_name = StringField('Nom de la Banque', validators=[Optional(), Length(max=191)])
    bank_identifier_code = StringField('Code BIC', validators=[Optional(), Length(max=50)])
    branch_location = StringField('Agence', validators=[Optional(), Length(max=191)])
    tax_payer_id = StringField('Numéro Fiscal', validators=[Optional(), Length(max=50)])
    salary_type = SelectField('Type de Salaire', choices=[('monthly', 'Mensuel'), ('hourly', 'Horaire')], validators=[DataRequired()])
    salary = DecimalField('Salaire', validators=[DataRequired(), NumberRange(min=0)])
    
    def __init__(self, *args, **kwargs):
        super(EmployeeForm, self).__init__(*args, **kwargs)
        self.branch_id.choices = [(b.id, b.name) for b in Branch.query.all()]
        self.department_id.choices = [(d.id, f"{d.name} ({d.branch.name})") for d in Department.query.join(Branch).all()]
        self.designation_id.choices = [(d.id, f"{d.name} ({d.department.name})") for d in Designation.query.join(Department).all()]

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
