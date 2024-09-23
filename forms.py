from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, FloatField, DateField, SelectField, TextAreaField, DateTimeField
from wtforms.validators import DataRequired, Email, EqualTo, Length, Optional, NumberRange

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

class OpportunityForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    amount = FloatField('Amount', validators=[DataRequired()])
    stage = SelectField('Stage', choices=[('Prospecting', 'Prospecting'), ('Qualification', 'Qualification'), ('Proposal', 'Proposal'), ('Negotiation', 'Negotiation'), ('Closed Won', 'Closed Won'), ('Closed Lost', 'Closed Lost')])
    close_date = DateField('Close Date', validators=[DataRequired()])
    account = SelectField('Account', coerce=int)
    lead = SelectField('Lead', coerce=int, validators=[Optional()])
    submit = SubmitField('Submit')

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
