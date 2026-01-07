from django.contrib import admin
from django.utils import timezone
from datetime import timedelta
from .models import Recruitment, Comment, UserRating, Report


@admin.register(Recruitment)
class RecruitmentAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'created_at', 'updated_at']
    list_filter = ['created_at', 'user']
    search_fields = ['title', 'description']


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['recruitment', 'user', 'content', 'created_at']
    list_filter = ['created_at', 'user']


@admin.register(UserRating)
class UserRatingAdmin(admin.ModelAdmin):
    list_display = ['rated_user', 'is_good', 'created_at']
    list_filter = ['is_good', 'created_at']


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ['id', 'report_type', 'reporter', 'reported_user', 'reason', 'is_resolved', 'created_at']
    list_filter = ['is_resolved', 'report_type', 'reason', 'created_at']
    search_fields = ['reporter__username', 'reported_user__username', 'detail']
    readonly_fields = ['reporter', 'report_type', 'reported_user', 'recruitment', 'comment', 'reason', 'detail', 'created_at']
    
    fieldsets = (
        ('通報情報', {
            'fields': ('reporter', 'report_type', 'reported_user', 'recruitment', 'comment', 'reason', 'detail', 'created_at')
        }),
        ('対応', {
            'fields': ('is_resolved', 'resolved_by', 'resolved_at', 'resolution_note')
        }),
    )
    
    actions = ['mark_resolved', 'ban_user_1day', 'ban_user_3days', 'ban_user_7days', 'ban_user_30days', 'ban_user_permanent']
    
    def mark_resolved(self, request, queryset):
        queryset.update(is_resolved=True, resolved_by=request.user, resolved_at=timezone.now())
        self.message_user(request, f'{queryset.count()}件の通報を対応済みにしました。')
    mark_resolved.short_description = '選択した通報を対応済みにする'
    
    def ban_user_1day(self, request, queryset):
        self._ban_users(request, queryset, days=1)
    ban_user_1day.short_description = '通報されたユーザーを1日間BAN'
    
    def ban_user_3days(self, request, queryset):
        self._ban_users(request, queryset, days=3)
    ban_user_3days.short_description = '通報されたユーザーを3日間BAN'
    
    def ban_user_7days(self, request, queryset):
        self._ban_users(request, queryset, days=7)
    ban_user_7days.short_description = '通報されたユーザーを7日間BAN'
    
    def ban_user_30days(self, request, queryset):
        self._ban_users(request, queryset, days=30)
    ban_user_30days.short_description = '通報されたユーザーを30日間BAN'
    
    def ban_user_permanent(self, request, queryset):
        self._ban_users(request, queryset, permanent=True)
    ban_user_permanent.short_description = '通報されたユーザーを永久BAN'
    
    def _ban_users(self, request, queryset, days=None, permanent=False):
        banned_users = set()
        for report in queryset:
            user = report.reported_user
            if user not in banned_users:
                if permanent:
                    user.is_banned = True
                    user.ban_reason = f'通報による永久BAN（通報ID: {report.id}）'
                else:
                    user.banned_until = timezone.now() + timedelta(days=days)
                    user.ban_reason = f'通報による{days}日間BAN（通報ID: {report.id}）'
                user.save()
                banned_users.add(user)
        
        # 通報を対応済みにする
        queryset.update(is_resolved=True, resolved_by=request.user, resolved_at=timezone.now())
        
        ban_type = '永久BAN' if permanent else f'{days}日間BAN'
        self.message_user(request, f'{len(banned_users)}人のユーザーを{ban_type}にしました。')
