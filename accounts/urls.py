from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'accounts'

urlpatterns = [
    path('signup/', views.SignUpView.as_view(), name='signup'),
    path('signup/done/', views.SignUpDoneView.as_view(), name='signup_done'),
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', views.CustomLogoutView.as_view(), name='logout'),
    path('mypage/', views.MyPageView.as_view(), name='mypage'),
    path('mypage/username/', views.UsernameChangeView.as_view(), name='username_change'),
    path('mypage/email/', views.EmailChangeView.as_view(), name='email_change'),
    path('mypage/email/done/', views.EmailChangeDoneView.as_view(), name='email_change_done'),
    path('user/<int:user_id>/', views.UserProfileView.as_view(), name='user_profile'),
    # パスワード変更（ログイン中）
    path('password_change/', auth_views.PasswordChangeView.as_view(
        template_name='accounts/password_change_form.html',
        success_url='/accounts/password_change/done/'
    ), name='password_change'),
    path('password_change/done/', auth_views.PasswordChangeDoneView.as_view(
        template_name='accounts/password_change_done.html'
    ), name='password_change_done'),
    # パスワードリセット
    path('password_reset/', auth_views.PasswordResetView.as_view(
        template_name='accounts/password_reset_form.html',
        email_template_name='accounts/password_reset_email.html',
        subject_template_name='accounts/password_reset_subject.txt',
        success_url='/accounts/password_reset/done/'
    ), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='accounts/password_reset_done.html'
    ), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='accounts/password_reset_confirm.html',
        success_url='/accounts/reset/done/'
    ), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(
        template_name='accounts/password_reset_complete.html'
    ), name='password_reset_complete'),
    # チャット
    path('chat/', views.ChatListView.as_view(), name='chat_list'),
    path('chat/with/<int:user_id>/', views.ChatWithView.as_view(), name='chat_with'),
    path('chat/room/<int:room_id>/', views.ChatRoomView.as_view(), name='chat_room'),
    path('chat/room/<int:room_id>/messages/', views.ChatMessagesAPIView.as_view(), name='chat_messages'),
    path('api/unread-count/', views.UnreadCountAPIView.as_view(), name='unread_count'),
    # ブロック
    path('block/<int:user_id>/', views.BlockUserView.as_view(), name='block_user'),
    path('unblock/<int:user_id>/', views.UnblockUserView.as_view(), name='unblock_user'),
    path('blocks/', views.BlockListView.as_view(), name='block_list'),
    # 通知
    path('notifications/', views.NotificationListView.as_view(), name='notification_list'),
    path('notifications/<int:pk>/read/', views.NotificationReadView.as_view(), name='notification_read'),
    path('notifications/mark-all-read/', views.MarkAllNotificationsReadView.as_view(), name='mark_all_read'),
    # アカウント削除
    path('delete/', views.AccountDeleteView.as_view(), name='account_delete'),
]
