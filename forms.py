from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, FloatField, DateField, SelectField, TextAreaField, DateTimeField, BooleanField
from wtforms.validators import DataRequired, Email, EqualTo, Length, Optional, NumberRange, ValidationError
from models import Lead
from datetime import date

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Sign In')

class RegistrationForm(FlaskForm):
    email = StringField('メールアドレス', validators=[
        DataRequired(message='メールアドレスを入力してください'),
        Email(message='有効なメールアドレスを入力してください'),
        Length(max=120, message='メールアドレスは120文字以内で入力してください')
    ])
    password = PasswordField('パスワード', validators=[
        DataRequired(message='パスワードを入力してください'),
        Length(min=8, message='パスワードは8文字以上で入力してください')
    ])
    confirm_password = PasswordField('パスワード（確認）', validators=[
        DataRequired(message='パスワードを再入力してください'),
        EqualTo('password', message='パスワードが一致しません')
    ])
    submit = SubmitField('登録')

class LeadForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    phone = StringField('Phone')
    status = SelectField('Status', choices=[('New', 'New'), ('Contacted', 'Contacted'), ('Qualified', 'Qualified'), ('Lost', 'Lost')], validators=[DataRequired()])
    score = FloatField('Score', validators=[Optional(), NumberRange(min=0, max=100)])
    submit = SubmitField('Submit')

    def validate_email(self, email):
        lead = Lead.query.filter_by(email=email.data).first()
        if lead:
            raise ValidationError('That email is already in use. Please choose a different one.')

class OpportunityForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    amount = FloatField('Amount', validators=[DataRequired(), NumberRange(min=0.01, message="Amount must be a positive number.")])
    stage = SelectField('Stage', choices=[('Prospecting', 'Prospecting'), ('Qualification', 'Qualification'), ('Proposal', 'Proposal'), ('Negotiation', 'Negotiation'), ('Closed Won', 'Closed Won'), ('Closed Lost', 'Closed Lost')])
    close_date = DateField('Close Date', validators=[DataRequired()])
    account = SelectField('Account', coerce=int)
    lead = SelectField('Lead', coerce=lambda x: int(x) if x else None, validators=[Optional()])
    submit = SubmitField('Submit')

    def validate_close_date(self, close_date):
        if close_date.data <= date.today():
            raise ValidationError('Close date must be in the future.')

class AccountForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    industry = StringField('Industry')
    website = StringField('Website')
    submit = SubmitField('Submit')

class ScheduleForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    description = TextAreaField('Description')
    start_time = DateTimeField('Start Time', format='%Y-%m-%dT%H:%M', validators=[DataRequired()])
    end_time = DateTimeField('End Time', format='%Y-%m-%dT%H:%M', validators=[DataRequired()])
    user_id = SelectField('User', coerce=int, validators=[DataRequired()])
    account_id = SelectField('Account', coerce=int, validators=[Optional()])
    lead_id = SelectField('Lead', coerce=int, validators=[Optional()])
    opportunity_id = SelectField('Opportunity', coerce=int, validators=[Optional()])
    submit = SubmitField('Submit')

class TaskForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    description = TextAreaField('Description')
    due_date = DateTimeField('Due Date', format='%Y-%m-%dT%H:%M', validators=[DataRequired()])
    completed = BooleanField('Completed')
    user_id = SelectField('User', coerce=int, validators=[DataRequired()])
    lead_id = SelectField('Lead', coerce=int, validators=[Optional()])
    opportunity_id = SelectField('Opportunity', coerce=int, validators=[Optional()])
    account_id = SelectField('Account', coerce=int, validators=[Optional()])
    submit = SubmitField('Submit')
