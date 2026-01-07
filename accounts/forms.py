from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.utils import timezone
from .models import CustomUser


class CustomUserCreationForm(UserCreationForm):
    # ユーザー登録用フォーム
    
    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'password1', 'password2')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs['class'] = 'form-control'
        self.fields['username'].widget.attrs['placeholder'] = 'ユーザー名'
        self.fields['email'].widget.attrs['class'] = 'form-control'
        self.fields['email'].widget.attrs['placeholder'] = 'メールアドレス'
        self.fields['password1'].widget.attrs['class'] = 'form-control'
        self.fields['password1'].widget.attrs['placeholder'] = 'パスワード'
        self.fields['password2'].widget.attrs['class'] = 'form-control'
        self.fields['password2'].widget.attrs['placeholder'] = 'パスワード（確認）'


class UsernameChangeForm(forms.ModelForm):
    # ユーザー名変更フォーム
    
    class Meta:
        model = CustomUser
        fields = ['username']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs['class'] = 'form-control'
        self.fields['username'].widget.attrs['placeholder'] = '新しいユーザー名'
    
    def clean(self):
        cleaned_data = super().clean()
        if not self.instance.can_change_username():
            next_change_date = self.instance.get_next_username_change_date()
            raise forms.ValidationError(
                f'ユーザー名の変更は3日に1回までです。次回変更可能日時: {next_change_date.strftime("%Y/%m/%d %H:%M")}'
            )
        return cleaned_data
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.username_changed_at = timezone.now()
        if commit:
            user.save()
        return user


class EmailChangeForm(forms.Form):
    # メールアドレス変更フォーム
    new_email = forms.EmailField(
        label='新しいメールアドレス',
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': '新しいメールアドレス'
        })
    )
    password = forms.CharField(
        label='現在のパスワード',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': '確認のためパスワードを入力'
        })
    )
    
    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
    
    def clean_new_email(self):
        new_email = self.cleaned_data.get('new_email')
        # 同じメールアドレスかチェック
        if new_email == self.user.email:
            raise forms.ValidationError('現在と同じメールアドレスです。')
        # 既に使用されているかチェック
        if CustomUser.objects.filter(email=new_email).exclude(pk=self.user.pk).exists():
            raise forms.ValidationError('このメールアドレスは既に使用されています。')
        return new_email
    
    def clean_password(self):
        password = self.cleaned_data.get('password')
        if not self.user.check_password(password):
            raise forms.ValidationError('パスワードが正しくありません。')
        return password
