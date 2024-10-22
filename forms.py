from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, FloatField, DateField, SelectField, TextAreaField, DateTimeField, BooleanField, IntegerField
from wtforms.validators import DataRequired, Email, EqualTo, Length, Optional, NumberRange, ValidationError
from models import Lead
from datetime import date

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Sign In')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')

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
    title = StringField('タイトル', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('説明')
    due_date = DateTimeField('期限', format='%Y-%m-%d %H:%M')
    priority = SelectField('優先度', choices=[('low', '低'), ('medium', '中'), ('high', '高')], default='medium')
    status = SelectField('ステータス', choices=[('New', '新規'), ('In Progress', '進行中'), ('Completed', '完了')])
    user_id = SelectField('担当者', coerce=int)
    lead_id = SelectField('リード', coerce=int)
    opportunity_id = SelectField('商談', coerce=int)
    account_id = SelectField('取引先', coerce=int)