from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils import timezone
from datetime import timedelta
from .models import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ['username', 'email', 'is_staff', 'is_banned', 'get_ban_status', 'date_joined']
    list_filter = ['is_staff', 'is_superuser', 'is_banned', 'is_active']
    
    fieldsets = UserAdmin.fieldsets + (
        ('BAN設定', {
            'fields': ('is_banned', 'banned_until', 'ban_reason')
        }),
        ('その他', {
            'fields': ('username_changed_at',)
        }),
    )
    
    actions = ['ban_1day', 'ban_3days', 'ban_7days', 'ban_30days', 'ban_permanent', 'unban']
    
    def ban_1day(self, request, queryset):
        self._ban_users(queryset, days=1)
        self.message_user(request, f'{queryset.count()}人のユーザーを1日間BANしました。')
    ban_1day.short_description = '選択したユーザーを1日間BAN'
    
    def ban_3days(self, request, queryset):
        self._ban_users(queryset, days=3)
        self.message_user(request, f'{queryset.count()}人のユーザーを3日間BANしました。')
    ban_3days.short_description = '選択したユーザーを3日間BAN'
    
    def ban_7days(self, request, queryset):
        self._ban_users(queryset, days=7)
        self.message_user(request, f'{queryset.count()}人のユーザーを7日間BANしました。')
    ban_7days.short_description = '選択したユーザーを7日間BAN'
    
    def ban_30days(self, request, queryset):
        self._ban_users(queryset, days=30)
        self.message_user(request, f'{queryset.count()}人のユーザーを30日間BANしました。')
    ban_30days.short_description = '選択したユーザーを30日間BAN'
    
    def ban_permanent(self, request, queryset):
        queryset.update(is_banned=True, ban_reason='管理者による永久BAN')
        self.message_user(request, f'{queryset.count()}人のユーザーを永久BANしました。')
    ban_permanent.short_description = '選択したユーザーを永久BAN'
    
    def unban(self, request, queryset):
        queryset.update(is_banned=False, banned_until=None, ban_reason='')
        self.message_user(request, f'{queryset.count()}人のユーザーのBANを解除しました。')
    unban.short_description = '選択したユーザーのBANを解除'
    
    def _ban_users(self, queryset, days):
        ban_until = timezone.now() + timedelta(days=days)
        queryset.update(banned_until=ban_until, ban_reason=f'管理者による{days}日間BAN')
