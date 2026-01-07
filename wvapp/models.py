from django.db import models
from accounts.models import CustomUser


class Announcement(models.Model):
    """サイト全体向けのお知らせ（管理者が追加）"""
    title = models.CharField(verbose_name='タイトル', max_length=200)
    content = models.TextField(verbose_name='本文')
    created_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='作成者',
        related_name='announcements'
    )
    created_at = models.DateTimeField(verbose_name='作成日時', auto_now_add=True)
    is_active = models.BooleanField(verbose_name='公開フラグ', default=True)

    class Meta:
        verbose_name = 'お知らせ'
        verbose_name_plural = 'お知らせ'
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class Recruitment(models.Model):
    """ゲーム募集モデル"""
    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        verbose_name='投稿者',
        related_name='recruitment'
    )
    title = models.CharField(verbose_name='タイトル', max_length=200)
    description = models.TextField(verbose_name='詳細')
    created_at = models.DateTimeField(verbose_name='作成日時', auto_now_add=True)
    updated_at = models.DateTimeField(verbose_name='更新日時', auto_now=True)
    
    class Meta:
        verbose_name = '募集'
        verbose_name_plural = '募集'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title


class Comment(models.Model):
    """コメントモデル"""
    recruitment = models.ForeignKey(
        Recruitment,
        on_delete=models.CASCADE,
        verbose_name='募集',
        related_name='comments'
    )
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        verbose_name='投稿者',
        related_name='comments'
    )
    content = models.TextField(verbose_name='コメント内容')
    created_at = models.DateTimeField(verbose_name='作成日時', auto_now_add=True)
    updated_at = models.DateTimeField(verbose_name='更新日時', auto_now=True)
    
    class Meta:
        verbose_name = 'コメント'
        verbose_name_plural = 'コメント'
        ordering = ['created_at']
    
    def is_edited(self):
        """編集されたかどうかを判定"""
        if self.updated_at and self.created_at:
            # 1秒以上の差があれば編集されたとみなす
            return (self.updated_at - self.created_at).total_seconds() > 1
        return False
    
    def __str__(self):
        return f'{self.user.username}: {self.content[:20]}'


class UserRating(models.Model):
    """ユーザー評価モデル"""
    rated_user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        verbose_name='評価されたユーザー',
        related_name='received_ratings'
    )
    # ログインユーザーの場合は評価者を記録
    rater = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        verbose_name='評価者',
        related_name='given_ratings',
        null=True,
        blank=True
    )
    is_good = models.BooleanField(verbose_name='グッド評価')
    reason = models.TextField(
        verbose_name='評価理由',
        blank=True
    )
    created_at = models.DateTimeField(verbose_name='評価日時', auto_now_add=True)
    # 未ログインユーザーの場合はセッションキーで重複評価を防止
    session_key = models.CharField(verbose_name='セッションキー', max_length=40, null=True, blank=True)
    
    class Meta:
        verbose_name = '評価'
        verbose_name_plural = '評価'
    
    def __str__(self):
        rating_type = 'グッド' if self.is_good else 'バッド'
        rater_name = self.rater.username if self.rater else '匿名'
        return f'{rater_name}から{self.rated_user.username}への{rating_type}'


class Report(models.Model):
    """通報モデル"""
    REPORT_TYPE_CHOICES = [
        ('recruitment', '募集'),
        ('comment', 'コメント'),
        ('user', 'ユーザー'),
    ]
    
    REASON_CHOICES = [
        ('spam', 'スパム・宣伝'),
        ('harassment', '嫌がらせ・誹謗中傷'),
        ('inappropriate', '不適切な内容'),
        ('fraud', '詐欺・なりすまし'),
        ('other', 'その他'),
    ]
    
    reporter = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        verbose_name='通報者',
        related_name='sent_reports'
    )
    report_type = models.CharField(
        verbose_name='通報対象タイプ',
        max_length=20,
        choices=REPORT_TYPE_CHOICES
    )
    reported_user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        verbose_name='通報されたユーザー',
        related_name='received_reports'
    )
    recruitment = models.ForeignKey(
        Recruitment,
        on_delete=models.CASCADE,
        verbose_name='通報された募集',
        null=True,
        blank=True,
        related_name='reports'
    )
    comment = models.ForeignKey(
        Comment,
        on_delete=models.CASCADE,
        verbose_name='通報されたコメント',
        null=True,
        blank=True,
        related_name='reports'
    )
    reason = models.CharField(
        verbose_name='通報理由',
        max_length=20,
        choices=REASON_CHOICES
    )
    detail = models.TextField(
        verbose_name='詳細',
        blank=True
    )
    is_resolved = models.BooleanField(
        verbose_name='対応済み',
        default=False
    )
    resolved_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        verbose_name='対応した管理者',
        null=True,
        blank=True,
        related_name='resolved_reports'
    )
    resolved_at = models.DateTimeField(
        verbose_name='対応日時',
        null=True,
        blank=True
    )
    resolution_note = models.TextField(
        verbose_name='対応メモ',
        blank=True
    )
    created_at = models.DateTimeField(
        verbose_name='通報日時',
        auto_now_add=True
    )
    
    class Meta:
        verbose_name = '通報'
        verbose_name_plural = '通報'
        ordering = ['-created_at']
    
    def __str__(self):
        return f'{self.reporter.username}による{self.get_report_type_display()}の通報'
