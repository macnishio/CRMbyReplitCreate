from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, FloatField, DateField, SelectField, TextAreaField, DateTimeField, BooleanField, IntegerField, HiddenField
from wtforms.validators import DataRequired, Email, EqualTo, Length, Optional, NumberRange, ValidationError
from models import Lead, SubscriptionPlan
from datetime import date
from wtforms.fields import DateTimeLocalField

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
    plan_id = SelectField('プラン', 
        coerce=int,
        validators=[DataRequired(message='プランを選択してください')],
        render_kw={"class": "form-control"}
    )
    stripe_payment_method = HiddenField('支払い方法')
    submit = SubmitField('登録')

    def __init__(self, *args, **kwargs):
        super(RegistrationForm, self).__init__(*args, **kwargs)
        # プランの選択肢を動的に設定
        self.plan_id.choices = [
            (plan.id, f"{plan.name} - ¥{plan.price:,.0f}/月") 
            for plan in SubscriptionPlan.query.all()
        ]

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
    name = StringField('名前', validators=[DataRequired()])
    amount = FloatField('金額', validators=[Optional()])
    stage = SelectField('ステージ', 
                       choices=[
                           ('Initial Contact', '初期接触'),
                           ('Qualification', '適格性確認'),
                           ('Proposal', '提案'),
                           ('Negotiation', '交渉'),
                           ('Closed Won', '成約'),
                           ('Closed Lost', '失注')
                       ],
                       validators=[DataRequired()])
    close_date = DateField('完了予定日', validators=[Optional()])
    account = SelectField('取引先', coerce=int, validators=[Optional()])
    lead = SelectField('リード', coerce=lambda x: int(x) if x else None, validators=[DataRequired()])
    submit = SubmitField('保存')

    def validate_close_date(self, close_date):
        if close_date.data <= date.today():
            raise ValidationError('Close date must be in the future.')

class AccountForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    industry = StringField('Industry')
    website = StringField('Website')
    submit = SubmitField('Submit')

class ScheduleForm(FlaskForm):
    title = StringField('タイトル', validators=[DataRequired()], render_kw={"class": "form-control"})
    description = TextAreaField('説明', render_kw={"class": "form-control", "rows": 3})
    start_time = DateTimeLocalField('開始時間', format='%Y-%m-%dT%H:%M', validators=[DataRequired()], render_kw={"class": "form-control"})
    end_time = DateTimeLocalField('終了時間', format='%Y-%m-%dT%H:%M', validators=[DataRequired()], render_kw={"class": "form-control"})
    # lead_idはフォームでは直接HTMLで描画するので、ここではバリデーションのみ定義
    lead_id = IntegerField('リード', validators=[Optional()])
    submit = SubmitField('保存', render_kw={"class": "btn btn-primary"})

class TaskForm(FlaskForm):
    title = StringField('タイトル', validators=[DataRequired()], render_kw={"class": "form-control"})
    description = TextAreaField('説明', render_kw={"class": "form-control", "rows": 3})
    due_date = DateField('期限', validators=[DataRequired()], render_kw={"class": "form-control"})
    status = SelectField('ステータス', 
                        choices=[
                            ('New', '新規'),
                            ('In Progress', '進行中'),
                            ('Completed', '完了')
                        ],
                        validators=[DataRequired()],
                        render_kw={"class": "form-control"})
    completed = BooleanField('完了済み', render_kw={"class": "form-check-input"})
    lead_id = IntegerField('リード', validators=[Optional()])
    submit = SubmitField('保存', render_kw={"class": "btn btn-primary"})