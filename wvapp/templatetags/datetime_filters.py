"""
Discord風の日時表示フィルター
- 今日: HH:mm
- 昨日: 昨日 HH:mm
- それ以前: YYYY/MM/DD HH:mm
"""
from django import template
from django.utils import timezone
from datetime import timedelta

register = template.Library()


@register.filter(name='discord_datetime')
def discord_datetime(value):
    """
    Discord風の日時表示フィルター
    
    Usage: {{ some_datetime|discord_datetime }}
    """
    if value is None:
        return ''
    
    now = timezone.localtime(timezone.now())
    local_value = timezone.localtime(value)
    
    # 今日の開始時刻
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    # 昨日の開始時刻
    yesterday_start = today_start - timedelta(days=1)
    
    if local_value >= today_start:
        # 今日の投稿: HH:mm
        return local_value.strftime('%H:%M')
    elif local_value >= yesterday_start:
        # 昨日の投稿: 昨日 HH:mm
        return '昨日 ' + local_value.strftime('%H:%M')
    else:
        # それ以前: YYYY/MM/DD HH:mm
        return local_value.strftime('%Y/%m/%d %H:%M')


@register.filter(name='discord_datetime_short')
def discord_datetime_short(value):
    """
    Discord風の日時表示（短縮版、チャット用）
    
    Usage: {{ some_datetime|discord_datetime_short }}
    """
    if value is None:
        return ''
    
    now = timezone.localtime(timezone.now())
    local_value = timezone.localtime(value)
    
    # 今日の開始時刻
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    # 昨日の開始時刻
    yesterday_start = today_start - timedelta(days=1)
    
    if local_value >= today_start:
        # 今日: HH:mm
        return local_value.strftime('%H:%M')
    elif local_value >= yesterday_start:
        # 昨日: 昨日 HH:mm
        return '昨日 ' + local_value.strftime('%H:%M')
    else:
        # それ以前: MM/DD HH:mm (年なし短縮版)
        return local_value.strftime('%m/%d %H:%M')
