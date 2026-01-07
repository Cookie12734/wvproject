from .models import Report
from accounts.models import Notification


def unresolved_report_count(request):
    """未対応の通報数をコンテキストに追加（管理者のみ）"""
    if request.user.is_authenticated and request.user.is_staff:
        return {
            'unresolved_report_count': Report.objects.filter(is_resolved=False).count()
        }
    return {}


def notifications(request):
    """通知関連のコンテキストを提供"""
    context = {}
    
    if request.user.is_authenticated:
        # 未読通知数
        context['unread_notification_count'] = Notification.objects.filter(
            user=request.user,
            is_read=False
        ).count()
        
        # 最新5件の通知（ドロップダウン用）
        context['recent_notifications'] = Notification.objects.filter(
            user=request.user
        ).order_by('-created_at')[:5]
    
    return context
