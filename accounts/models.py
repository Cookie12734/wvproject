from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from datetime import timedelta


class CustomUser(AbstractUser):
    """カスタムユーザーモデル"""
    username_changed_at = models.DateTimeField(
        verbose_name='ユーザー名変更日時',
        null=True,
        blank=True
    )
    is_banned = models.BooleanField(
        verbose_name='永久BAN',
        default=False
    )
    banned_until = models.DateTimeField(
        verbose_name='書き込み禁止期限',
        null=True,
        blank=True
    )
    ban_reason = models.TextField(
        verbose_name='BAN理由',
        blank=True
    )
    
    class Meta:
        verbose_name = 'ユーザー'
        verbose_name_plural = 'ユーザー'
    
    def get_rating_percentage(self):
        # グッド評価の割合を計算
        total_ratings = self.received_ratings.count()
        if total_ratings == 0:
            return None
        good_ratings = self.received_ratings.filter(is_good=True).count()
        return int((good_ratings / total_ratings) * 100)
    
    def can_change_username(self):
        # ユーザー名を変更できるかどうかを判定（3日に1回）
        if self.username_changed_at is None:
            return True
        return timezone.now() >= self.username_changed_at + timedelta(days=3)
    
    def get_next_username_change_date(self):
        # 次にユーザー名を変更できる日時を取得
        if self.username_changed_at is None:
            return None
        return self.username_changed_at + timedelta(days=3)
    
    def is_write_banned(self):
        # 書き込み禁止中かどうかを判定(管理者権限を持つアカウントは除外)
        if self.is_superuser:
            return False
        if self.is_banned:
            return True
        if self.banned_until and timezone.now() < self.banned_until:
            return True
        return False
    
    def get_ban_status(self):
        # BANステータスを取得
        if self.is_banned:
            return '永久BAN'
        if self.banned_until:
            if timezone.now() < self.banned_until:
                return f'書き込み禁止中（{self.banned_until.strftime("%Y/%m/%d %H:%M")}まで）'
            else:
                return None
        return None
    
    def __str__(self):
        return self.username


class ChatRoom(models.Model):
    # チャットルームモデル
    participants = models.ManyToManyField(
        CustomUser,
        verbose_name='参加者',
        related_name='chat_rooms'
    )
    created_at = models.DateTimeField(
        verbose_name='作成日時',
        auto_now_add=True
    )
    updated_at = models.DateTimeField(
        verbose_name='更新日時',
        auto_now=True
    )
    
    class Meta:
        verbose_name = 'チャットルーム'
        verbose_name_plural = 'チャットルーム'
        ordering = ['-updated_at']
    
    def __str__(self):
        return f'チャットルーム #{self.pk}'
    
    def get_other_user(self, user):
        """相手ユーザーを取得"""
        return self.participants.exclude(pk=user.pk).first()
    
    def get_last_message(self):
        """最新メッセージを取得"""
        return self.messages.order_by('-created_at').first()
    
    def get_unread_count(self, user):
        """未読メッセージ数を取得"""
        return self.messages.filter(is_read=False).exclude(sender=user).count()


class ChatMessage(models.Model):
    # チャットメッセージモデル
    room = models.ForeignKey(
        ChatRoom,
        on_delete=models.CASCADE,
        verbose_name='チャットルーム',
        related_name='messages'
    )
    sender = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        verbose_name='送信者',
        related_name='sent_messages'
    )
    content = models.TextField(
        verbose_name='メッセージ内容'
    )
    is_read = models.BooleanField(
        verbose_name='既読',
        default=False
    )
    created_at = models.DateTimeField(
        verbose_name='送信日時',
        auto_now_add=True
    )
    
    class Meta:
        verbose_name = 'チャットメッセージ'
        verbose_name_plural = 'チャットメッセージ'
        ordering = ['created_at']
    
    def __str__(self):
        return f'{self.sender.username}: {self.content[:20]}'


class Block(models.Model):
    # ブロックモデル
    blocker = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        verbose_name='ブロックした人',
        related_name='blocking'
    )
    blocked = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        verbose_name='ブロックされた人',
        related_name='blocked_by'
    )
    created_at = models.DateTimeField(
        verbose_name='ブロック日時',
        auto_now_add=True
    )
    
    class Meta:
        verbose_name = 'ブロック'
        verbose_name_plural = 'ブロック'
        unique_together = ['blocker', 'blocked']
        ordering = ['-created_at']
    
    def __str__(self):
        return f'{self.blocker.username} → {self.blocked.username}'


class Notification(models.Model):
    # 通知モデル
    NOTIFICATION_TYPES = [
        ('comment', 'コメント'),
        ('rating', '評価'),
        ('chat', 'チャット'),
    ]
    
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        verbose_name='通知先ユーザー',
        related_name='notifications'
    )
    notification_type = models.CharField(
        verbose_name='通知タイプ',
        max_length=20,
        choices=NOTIFICATION_TYPES
    )
    title = models.CharField(
        verbose_name='タイトル',
        max_length=100
    )
    message = models.TextField(
        verbose_name='メッセージ'
    )
    link = models.CharField(
        verbose_name='リンク先',
        max_length=200,
        blank=True
    )
    is_read = models.BooleanField(
        verbose_name='既読',
        default=False
    )
    created_at = models.DateTimeField(
        verbose_name='作成日時',
        auto_now_add=True
    )
    
    class Meta:
        verbose_name = '通知'
        verbose_name_plural = '通知'
        ordering = ['-created_at']
    
    def __str__(self):
        return f'{self.user.username}: {self.title}'
