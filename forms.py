from flask_wtf import FlaskForm
from wtforms import (
    StringField, PasswordField, SubmitField, FloatField, DateField, 
    SelectField, TextAreaField, DateTimeField, BooleanField
)
from wtforms.validators import (
    DataRequired, Email, EqualTo, Length, Optional, 
    NumberRange, ValidationError, URL, Regexp
)
from models import Lead, User
from datetime import date, datetime

class LoginForm(FlaskForm):
    """ログインフォーム"""
    username = StringField('ユーザー名', 
        validators=[
            DataRequired(message='ユーザー名を入力してください'),
            Length(min=2, max=20, message='ユーザー名は2〜20文字で入力してください')
        ],
        render_kw={"placeholder": "ユーザー名を入力"}
    )
    password = PasswordField('パスワード', 
        validators=[
            DataRequired(message='パスワードを入力してください')
        ],
        render_kw={"placeholder": "パスワードを入力"}
    )
    submit = SubmitField('ログイン')

class RegistrationForm(FlaskForm):
    """ユーザー登録フォーム"""
    username = StringField('ユーザー名',
        validators=[
            DataRequired(message='ユーザー名を入力してください'),
            Length(min=2, max=20, message='ユーザー名は2〜20文字で入力してください'),
            Regexp(r'^[\w\-]+$', message='ユーザー名は半角英数字とハイフンのみ使用できます')
        ],
        render_kw={"placeholder": "ユーザー名を入力"}
    )
    email = StringField('メールアドレス',
        validators=[
            DataRequired(message='メールアドレスを入力してください'),
            Email(message='有効なメールアドレスを入力してください')
        ],
        render_kw={"placeholder": "example@example.com"}
    )
    password = PasswordField('パスワード',
        validators=[
            DataRequired(message='パスワードを入力してください'),
            Length(min=8, message='パスワードは8文字以上で入力してください')
        ],
        render_kw={"placeholder": "パスワードを入力（8文字以上）"}
    )
    confirm_password = PasswordField('パスワード（確認）',
        validators=[
            DataRequired(message='確認用パスワードを入力してください'),
            EqualTo('password', message='パスワードが一致しません')
        ],
        render_kw={"placeholder": "パスワードを再入力"}
    )
    submit = SubmitField('登録')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('このユーザー名は既に使用されています')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('このメールアドレスは既に登録されています')

class LeadForm(FlaskForm):
    """リード登録・編集フォーム"""
    name = StringField('名前',
        validators=[
            DataRequired(message='名前を入力してください'),
            Length(max=100, message='名前は100文字以内で入力してください')
        ]
    )
    email = StringField('メールアドレス',
        validators=[
            DataRequired(message='メールアドレスを入力してください'),
            Email(message='有効なメールアドレスを入力してください')
        ]
    )
    phone = StringField('電話番号',
        validators=[
            Optional(),
            Regexp(r'^\+?[\d\-\s]+$', message='有効な電話番号を入力してください')
        ]
    )
    status = SelectField('ステータス',
        choices=[
            ('New', '新規'),
            ('Contacted', '連絡済み'),
            ('Qualified', '適格'),
            ('Lost', '失注')
        ],
        validators=[DataRequired(message='ステータスを選択してください')]
    )
    score = FloatField('スコア',
        validators=[
            Optional(),
            NumberRange(min=0, max=100, message='スコアは0〜100の間で入力してください')
        ]
    )
    submit = SubmitField('保存')

    def validate_email(self, email):
        lead = Lead.query.filter_by(email=email.data).first()
        if lead and (not hasattr(self, 'id') or lead.id != self.id.data):
            raise ValidationError('このメールアドレスは既に登録されています')

class OpportunityForm(FlaskForm):
    """案件登録・編集フォーム"""
    name = StringField('案件名',
        validators=[
            DataRequired(message='案件名を入力してください'),
            Length(max=100, message='案件名は100文字以内で入力してください')
        ]
    )
    amount = FloatField('金額',
        validators=[
            DataRequired(message='金額を入力してください'),
            NumberRange(min=0.01, message='金額は0より大きい値を入力してください')
        ]
    )
    stage = SelectField('ステージ',
        choices=[
            ('Prospecting', '見込み'),
            ('Qualification', '適格性確認'),
            ('Proposal', '提案'),
            ('Negotiation', '交渉'),
            ('Closed Won', '成約'),
            ('Closed Lost', '失注')
        ]
    )
    close_date = DateField('完了予定日',
        validators=[DataRequired(message='完了予定日を入力してください')]
    )
    account = SelectField('取引先', coerce=int)
    lead = SelectField('リード',
        coerce=lambda x: int(x) if x else None,
        validators=[Optional()]
    )
    submit = SubmitField('保存')

    def validate_close_date(self, close_date):
        if close_date.data < date.today():
            raise ValidationError('完了予定日は今日以降の日付を指定してください')

class AccountForm(FlaskForm):
    """取引先登録・編集フォーム"""
    name = StringField('取引先名',
        validators=[
            DataRequired(message='取引先名を入力してください'),
            Length(max=100, message='取引先名は100文字以内で入力してください')
        ]
    )
    industry = StringField('業種',
        validators=[
            Optional(),
            Length(max=50, message='業種は50文字以内で入力してください')
        ]
    )
    website = StringField('Webサイト',
        validators=[
            Optional(),
            URL(message='有効なURLを入力してください')
        ]
    )
    submit = SubmitField('保存')

class ScheduleForm(FlaskForm):
    """スケジュール登録・編集フォーム"""
    title = StringField('タイトル',
        validators=[
            DataRequired(message='タイトルを入力してください'),
            Length(max=100, message='タイトルは100文字以内で入力してください')
        ]
    )
    description = TextAreaField('説明')
    start_time = DateTimeField('開始日時',
        format='%Y-%m-%dT%H:%M',
        validators=[DataRequired(message='開始日時を入力してください')]
    )
    end_time = DateTimeField('終了日時',
        format='%Y-%m-%dT%H:%M',
        validators=[DataRequired(message='終了日時を入力してください')]
    )
    user_id = SelectField('担当者',
        coerce=int,
        validators=[DataRequired(message='担当者を選択してください')]
    )
    account_id = SelectField('取引先',
        coerce=int,
        validators=[Optional()]
    )
    lead_id = SelectField('リード',
        coerce=int,
        validators=[Optional()]
    )
    opportunity_id = SelectField('案件',
        coerce=int,
        validators=[Optional()]
    )
    submit = SubmitField('保存')

    def validate_end_time(self, end_time):
        if end_time.data <= self.start_time.data:
            raise ValidationError('終了日時は開始日時より後に設定してください')

class TaskForm(FlaskForm):
    """タスク登録・編集フォーム"""
    title = StringField('タイトル',
        validators=[
            DataRequired(message='タイトルを入力してください'),
            Length(max=100, message='タイトルは100文字以内で入力してください')
        ]
    )
    description = TextAreaField('説明')
    due_date = DateTimeField('期限',
        format='%Y-%m-%dT%H:%M',
        validators=[DataRequired(message='期限を入力してください')]
    )
    completed = BooleanField('完了')
    user_id = SelectField('担当者',
        coerce=int,
        validators=[DataRequired(message='担当者を選択してください')]
    )
    lead_id = SelectField('リード',
        coerce=int,
        validators=[Optional()]
    )
    opportunity_id = SelectField('案件',
        coerce=int,
        validators=[Optional()]
    )
    account_id = SelectField('取引先',
        coerce=int,
        validators=[Optional()]
    )
    submit = SubmitField('保存')

    def validate_due_date(self, due_date):
        if due_date.data < datetime.now():
            raise ValidationError('期限は現在時刻以降に設定してください')