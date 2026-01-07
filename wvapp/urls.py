from django.urls import path
from . import views

app_name = 'wvapp'

urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    path('recruitment/<int:pk>/', views.RecruitmentDetailView.as_view(), name='detail'),
    path('recruitment/create/', views.RecruitmentCreateView.as_view(), name='create'),
    path('recruitment/create/done/', views.RecruitmentCreateDoneView.as_view(), name='create_done'),
    path('recruitment/<int:pk>/edit/', views.RecruitmentUpdateView.as_view(), name='edit'),
    path('recruitment/<int:pk>/delete/', views.RecruitmentDeleteView.as_view(), name='delete'),
    path('recruitment/<int:pk>/comment/', views.CommentCreateView.as_view(), name='comment'),
    path('comment/<int:pk>/edit/', views.CommentUpdateView.as_view(), name='comment_edit'),
    path('comment/<int:pk>/delete/', views.CommentDeleteView.as_view(), name='comment_delete'),
    path('user/<int:user_id>/rate/', views.UserRatingView.as_view(), name='rate_user'),
    path('my-recruitment/', views.MyRecruitmentView.as_view(), name='my_recruitment'),
    path('report/<str:report_type>/<int:target_id>/', views.ReportCreateView.as_view(), name='report'),
    # 管理者用通報管理
    path('staff/reports/', views.ReportListView.as_view(), name='report_list'),
    path('staff/reports/<int:pk>/', views.ReportDetailView.as_view(), name='report_detail'),
    path('staff/reports/<int:pk>/resolve/', views.ReportResolveView.as_view(), name='report_resolve'),
    path('staff/user/<int:user_id>/', views.UserManageView.as_view(), name='user_manage'),
    # 静的ページ
    path('terms/', views.TermsView.as_view(), name='terms'),
    path('privacy/', views.PrivacyView.as_view(), name='privacy'),
    # お知らせ
    path('announcements/', views.AnnouncementListView.as_view(), name='announcement_list'),
    path('staff/announcements/create/', views.AnnouncementCreateView.as_view(), name='announcement_create'),
    path('staff/announcements/<int:pk>/edit/', views.AnnouncementUpdateView.as_view(), name='announcement_edit'),
    path('staff/announcements/<int:pk>/delete/', views.AnnouncementDeleteView.as_view(), name='announcement_delete'),
]
