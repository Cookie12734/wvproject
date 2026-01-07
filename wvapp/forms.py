from django import forms
from .models import Recruitment, Comment, Report, Announcement


class RecruitmentForm(forms.ModelForm):
    """募集作成・編集フォーム"""
    
    class Meta:
        model = Recruitment
        fields = ['title', 'description']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['title'].widget.attrs['class'] = 'form-control'
        self.fields['title'].widget.attrs['placeholder'] = '募集タイトルを入力してください'
        self.fields['description'].widget.attrs['class'] = 'form-control'
        self.fields['description'].widget.attrs['placeholder'] = '募集の詳細を入力してください'
        self.fields['description'].widget.attrs['rows'] = 5


class CommentForm(forms.ModelForm):
    """コメント投稿フォーム"""
    
    class Meta:
        model = Comment
        fields = ['content']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['content'].widget.attrs['class'] = 'form-control'
        self.fields['content'].widget.attrs['placeholder'] = 'コメントを入力してください'
        self.fields['content'].widget.attrs['rows'] = 3
        self.fields['content'].label = 'コメント'


class ReportForm(forms.ModelForm):
    """通報フォーム"""
    
    class Meta:
        model = Report
        fields = ['reason', 'detail']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['reason'].widget.attrs['class'] = 'form-select'
        self.fields['detail'].widget.attrs['class'] = 'form-control'
        self.fields['detail'].widget.attrs['placeholder'] = '詳細を入力してください（任意）'
        self.fields['detail'].widget.attrs['rows'] = 3
        self.fields['detail'].label = '詳細（任意）'


class AnnouncementForm(forms.ModelForm):
    """お知らせ作成フォーム（管理者用）"""

    class Meta:
        model = Announcement
        fields = ['title', 'content', 'is_active']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['title'].widget.attrs['class'] = 'form-control'
        self.fields['title'].widget.attrs['placeholder'] = 'お知らせのタイトルを入力してください'
        self.fields['content'].widget.attrs['class'] = 'form-control'
        self.fields['content'].widget.attrs['placeholder'] = 'お知らせの内容を入力してください'
        self.fields['content'].widget.attrs['rows'] = 6
        # is_active は checkbox のため form-check-input クラスを付与
        self.fields['is_active'].widget.attrs.update({'class': 'form-check-input'})
