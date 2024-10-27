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
    username = StringField('ユーザー名', validators=[
        DataRequired(message='ユーザー名を入力してください'),
        Length(min=3, max=80, message='ユーザー名は3文字以上80文字以内で入力してください')
    ])
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
    name = StringField('名前', validators=[DataRequired(message='名前を入力してください')])
    email = StringField('メールアドレス', validators=[DataRequired(message='メールアドレスを入力してください'), Email(message='有効なメールアドレスを入力してください')])
    phone = StringField('電話番号')
    status = SelectField('ステータス', 
                        choices=[('New', '新規'), 
                                ('Contacted', '連絡済み'), 
                                ('Qualified', '適格'), 
                                ('Lost', '失注')],
                        validators=[DataRequired(message='ステータスを選択してください')])
    score = FloatField('スコア', validators=[Optional(), NumberRange(min=0, max=100, message='スコアは0から100の間で入力してください')])
    submit = SubmitField('保存')

    def validate_email(self, email):
        lead = Lead.query.filter_by(email=email.data).first()
        if lead and (not hasattr(self, '_obj') or lead.id != self._obj.id):
            raise ValidationError('このメールアドレスは既に登録されています。')

class AccountForm(FlaskForm):
    name = StringField('会社名', validators=[DataRequired(message='会社名を入力してください')])
    industry = StringField('業種')
    website = StringField('Webサイト')
    submit = SubmitField('保存')

class OpportunityForm(FlaskForm):
    name = StringField('商談名', validators=[DataRequired(message='商談名を入力してください')])
    amount = FloatField('金額', validators=[DataRequired(message='金額を入力してください'), NumberRange(min=0.01, message="金額は0より大きい値を入力してください")])
    stage = SelectField('ステージ', choices=[
        ('Initial Contact', '初回接触'),
        ('Qualification', '案件化'),
        ('Proposal', '提案'),
        ('Negotiation', '交渉'),
        ('Closed Won', '成約'),
        ('Closed Lost', '失注')
    ])
    close_date = DateField('完了予定日', validators=[DataRequired(message='完了予定日を入力してください')])
    account = SelectField('取引先', coerce=str)
    lead = SelectField('リード', coerce=str)
    submit = SubmitField('保存')

    def validate_close_date(self, close_date):
        if close_date.data <= date.today():
            raise ValidationError('完了予定日は未来の日付を選択してください')

class ScheduleForm(FlaskForm):
    title = StringField('タイトル', validators=[DataRequired(message='タイトルを入力してください')])
    description = TextAreaField('説明')
    start_time = DateTimeField('開始時間', format='%Y-%m-%dT%H:%M', validators=[DataRequired(message='開始時間を入力してください')])
    end_time = DateTimeField('終了時間', format='%Y-%m-%dT%H:%M', validators=[DataRequired(message='終了時間を入力してください')])
    lead_id = SelectField('リード', coerce=str, validators=[Optional()])
    opportunity_id = SelectField('商談', coerce=str, validators=[Optional()])
    account_id = SelectField('取引先', coerce=str, validators=[Optional()])
    submit = SubmitField('保存')

class TaskForm(FlaskForm):
    title = StringField('タイトル', validators=[DataRequired(message='タイトルを入力してください')])
    description = TextAreaField('説明')
    due_date = DateTimeField('期限', format='%Y-%m-%dT%H:%M', validators=[DataRequired(message='期限を入力してください')])
    completed = BooleanField('完了')
    lead_id = SelectField('リード', coerce=str, validators=[Optional()])
    opportunity_id = SelectField('商談', coerce=str, validators=[Optional()])
    account_id = SelectField('取引先', coerce=str, validators=[Optional()])
    submit = SubmitField('保存')
