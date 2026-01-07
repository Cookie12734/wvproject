from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, View, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.urls import reverse_lazy
from django.http import JsonResponse, HttpResponseForbidden
from django.db.models import Count, Q, Case, When, FloatField, F
from .models import Recruitment, Comment, UserRating, Report, Announcement
from .forms import RecruitmentForm, CommentForm, ReportForm, AnnouncementForm
from accounts.models import Notification


class WriteBannedMixin:
    """書き込み禁止チェック用Mixin"""
    
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and request.user.is_write_banned():
            ban_status = request.user.get_ban_status()
            messages.error(request, f'現在、書き込みが禁止されています。（{ban_status}）')
            return redirect('wvapp:index')
        return super().dispatch(request, *args, **kwargs)


class IndexView(ListView):
    """トップページ - 募集一覧"""
    model = Recruitment
    template_name = 'wvapp/index.html'
    context_object_name = 'recruitments'
    paginate_by = 10
    
    def get_queryset(self):
        queryset = Recruitment.objects.all()
        
        # 検索フィルター
        search_query = self.request.GET.get('q', '').strip()
        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query) | Q(description__icontains=search_query)
            )
        
        # 並べ替え
        sort = self.request.GET.get('sort', 'newest')
        
        if sort == 'oldest':
            # 古い順
            queryset = queryset.order_by('created_at')
        elif sort == 'rating_count':
            # 評価数順（投稿者の受けた評価数）
            queryset = queryset.annotate(
                user_rating_count=Count('user__received_ratings')
            ).order_by('-user_rating_count', '-created_at')
        elif sort == 'good_rate':
            # Good率順（投稿者のGood評価率）
            queryset = queryset.annotate(
                total_ratings=Count('user__received_ratings'),
                good_ratings=Count('user__received_ratings', filter=Q(user__received_ratings__is_good=True)),
                good_rate=Case(
                    When(total_ratings=0, then=0.0),
                    default=F('good_ratings') * 100.0 / F('total_ratings'),
                    output_field=FloatField()
                )
            ).order_by('-good_rate', '-total_ratings', '-created_at')
        else:
            # 新しい順（デフォルト）
            queryset = queryset.order_by('-created_at')
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_sort'] = self.request.GET.get('sort', 'newest')
        context['search_query'] = self.request.GET.get('q', '')
        return context


class RecruitmentDetailView(DetailView):
    """募集詳細ビュー"""
    model = Recruitment
    template_name = 'wvapp/recruitment_detail.html'
    context_object_name = 'recruitment'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['comment_form'] = CommentForm()
        context['comments'] = self.object.comments.all()
        context['report_form'] = ReportForm()
        return context


class RecruitmentCreateView(LoginRequiredMixin, WriteBannedMixin, CreateView):
    """募集作成ビュー"""
    model = Recruitment
    form_class = RecruitmentForm
    template_name = 'wvapp/recruitment_form.html'
    success_url = reverse_lazy('wvapp:create_done')
    
    def dispatch(self, request, *args, **kwargs):
        # 既に募集を持っているかチェック
        if request.user.is_authenticated:
            if hasattr(request.user, 'recruitment'):
                messages.error(request, '募集は1人1件までです。既存の募集を編集または削除してください。')
                return redirect('wvapp:my_recruitment')
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)


class RecruitmentCreateDoneView(LoginRequiredMixin, TemplateView):
    """募集作成完了ビュー"""
    template_name = 'wvapp/recruitment_create_done.html'


class RecruitmentUpdateView(LoginRequiredMixin, WriteBannedMixin, UserPassesTestMixin, UpdateView):
    """募集編集ビュー"""
    model = Recruitment
    form_class = RecruitmentForm
    template_name = 'wvapp/recruitment_form.html'
    
    def test_func(self):
        recruitment = self.get_object()
        return self.request.user == recruitment.user
    
    def get_success_url(self):
        return reverse_lazy('wvapp:detail', kwargs={'pk': self.object.pk})


class RecruitmentDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """募集削除ビュー"""
    model = Recruitment
    template_name = 'wvapp/recruitment_confirm_delete.html'
    success_url = reverse_lazy('wvapp:index')
    
    def test_func(self):
        recruitment = self.get_object()
        return self.request.user == recruitment.user


class CommentCreateView(LoginRequiredMixin, WriteBannedMixin, View):
    """コメント投稿ビュー"""
    
    def post(self, request, pk):
        recruitment = get_object_or_404(Recruitment, pk=pk)
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.user = request.user
            comment.recruitment = recruitment
            comment.save()
            
            # 自分以外の投稿にコメントした場合、投稿者に通知を送る
            if recruitment.user != request.user:
                Notification.objects.create(
                    user=recruitment.user,
                    notification_type='comment',
                    title='新しいコメント',
                    message=f'{request.user.username}さんがあなたの募集「{recruitment.title[:20]}」にコメントしました。',
                        link=f'/recruitment/{recruitment.pk}/'
                )
        return redirect('wvapp:detail', pk=pk)


class CommentUpdateView(LoginRequiredMixin, WriteBannedMixin, View):
    """コメント編集ビュー（Ajax）"""
    
    def post(self, request, pk):
        comment = get_object_or_404(Comment, pk=pk)
        
        # 自分のコメントかチェック
        if comment.user != request.user:
            return JsonResponse({'success': False, 'error': '権限がありません'}, status=403)
        
        content = request.POST.get('content', '').strip()
        if not content:
            return JsonResponse({'success': False, 'error': 'コメント内容を入力してください'}, status=400)
        
        comment.content = content
        comment.save()
        
        return JsonResponse({'success': True, 'content': comment.content})


class CommentDeleteView(LoginRequiredMixin, View):
    """コメント削除ビュー"""
    
    def post(self, request, pk):
        comment = get_object_or_404(Comment, pk=pk)
        recruitment_pk = comment.recruitment.pk
        
        # 自分のコメントか管理者かチェック
        if comment.user != request.user and not request.user.is_staff:
            messages.error(request, 'このコメントを削除する権限がありません。')
            return redirect('wvapp:detail', pk=recruitment_pk)
        
        comment.delete()
        messages.success(request, 'コメントを削除しました。')
        return redirect('wvapp:detail', pk=recruitment_pk)


class UserRatingView(View):
    """ユーザー評価ビュー（Ajax）"""
    
    def post(self, request, user_id):
        from accounts.models import CustomUser
        rated_user = get_object_or_404(CustomUser, pk=user_id)
        is_good = request.POST.get('is_good') == 'true'
        reason = request.POST.get('reason', '').strip()
        
        if request.user.is_authenticated:
            # ログインユーザーの場合：ユーザーIDで重複チェック
            # 自分自身への評価は禁止
            if request.user == rated_user:
                return JsonResponse({
                    'success': False,
                    'error': '自分自身を評価することはできません'
                }, status=400)
            
            existing_rating = UserRating.objects.filter(
                rated_user=rated_user,
                rater=request.user
            ).first()
            
            if existing_rating:
                # 既存の評価を更新
                existing_rating.is_good = is_good
                existing_rating.reason = reason
                existing_rating.save()
            else:
                # 新規評価を作成（raterを設定）
                UserRating.objects.create(
                    rated_user=rated_user,
                    rater=request.user,
                    is_good=is_good,
                    reason=reason,
                    session_key=None
                )
        else:
            # 未ログインユーザーの場合：セッションキーで重複チェック
            if not request.session.session_key:
                request.session.create()
            session_key = request.session.session_key
            
            existing_rating = UserRating.objects.filter(
                rated_user=rated_user,
                session_key=session_key,
                rater__isnull=True
            ).first()
            
            if existing_rating:
                # 既存の評価を更新
                existing_rating.is_good = is_good
                existing_rating.save()
            else:
                # 新規評価を作成（session_keyを設定）
                UserRating.objects.create(
                    rated_user=rated_user,
                    rater=None,
                    is_good=is_good,
                    session_key=session_key
                )
        
        # 更新後の評価割合を返す
        rating_percentage = rated_user.get_rating_percentage()
        return JsonResponse({
            'success': True,
            'rating_percentage': rating_percentage
        })


class MyRecruitmentView(LoginRequiredMixin, TemplateView):
    """自分の募集ビュー"""
    template_name = 'wvapp/my_recruitment.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['recruitment'] = getattr(self.request.user, 'recruitment', None)
        return context


class ReportCreateView(LoginRequiredMixin, View):
    """通報作成ビュー"""
    
    def post(self, request, report_type, target_id):
        from accounts.models import CustomUser
        
        form = ReportForm(request.POST)
        if form.is_valid():
            report = form.save(commit=False)
            report.reporter = request.user
            report.report_type = report_type
            
            if report_type == 'recruitment':
                recruitment = get_object_or_404(Recruitment, pk=target_id)
                report.reported_user = recruitment.user
                report.recruitment = recruitment
            elif report_type == 'comment':
                comment = get_object_or_404(Comment, pk=target_id)
                report.reported_user = comment.user
                report.comment = comment
            elif report_type == 'user':
                reported_user = get_object_or_404(CustomUser, pk=target_id)
                report.reported_user = reported_user
            
            report.save()
            messages.success(request, '通報を送信しました。ご協力ありがとうございます。')
        else:
            messages.error(request, '通報の送信に失敗しました。')
        
        # リファラーに戻る、なければトップへ
        referer = request.META.get('HTTP_REFERER')
        if referer:
            return redirect(referer)
        return redirect('wvapp:index')


class StaffRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """管理者権限チェック用Mixin"""
    
    def test_func(self):
        return self.request.user.is_staff


class ReportListView(StaffRequiredMixin, ListView):
    """通報一覧ビュー（管理者用）"""
    model = Report
    template_name = 'wvapp/report_list.html'
    context_object_name = 'reports'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Report.objects.select_related(
            'reporter', 'reported_user', 'recruitment', 'comment'
        ).order_by('-created_at')
        
        # フィルター
        status = self.request.GET.get('status')
        if status == 'unresolved':
            queryset = queryset.filter(is_resolved=False)
        elif status == 'resolved':
            queryset = queryset.filter(is_resolved=True)
        
        report_type = self.request.GET.get('type')
        if report_type:
            queryset = queryset.filter(report_type=report_type)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['unresolved_count'] = Report.objects.filter(is_resolved=False).count()
        context['current_status'] = self.request.GET.get('status', '')
        context['current_type'] = self.request.GET.get('type', '')
        return context


class ReportDetailView(StaffRequiredMixin, DetailView):
    """通報詳細ビュー（管理者用）"""
    model = Report
    template_name = 'wvapp/report_detail.html'
    context_object_name = 'report'
    
    def get_queryset(self):
        return Report.objects.select_related(
            'reporter', 'reported_user', 'recruitment', 'comment', 'resolved_by'
        )


class ReportResolveView(StaffRequiredMixin, View):
    """通報対応済みにするビュー（管理者用）"""
    
    def post(self, request, pk):
        from django.utils import timezone
        
        report = get_object_or_404(Report, pk=pk)
        action = request.POST.get('action')
        resolution_note = request.POST.get('resolution_note', '')
        
        if action == 'resolve':
            report.is_resolved = True
            report.resolved_by = request.user
            report.resolved_at = timezone.now()
            report.resolution_note = resolution_note
            report.save()
            messages.success(request, '通報を対応済みにしました。')
        elif action == 'unresolve':
            report.is_resolved = False
            report.resolved_by = None
            report.resolved_at = None
            report.save()
            messages.success(request, '通報を未対応に戻しました。')
        
        return redirect('wvapp:report_detail', pk=pk)


class UserManageView(StaffRequiredMixin, View):
    """ユーザー管理ビュー（管理者用）"""
    
    def get(self, request, user_id):
        from accounts.models import CustomUser
        target_user = get_object_or_404(CustomUser, pk=user_id)
        
        context = {
            'target_user': target_user,
            'reports': Report.objects.filter(reported_user=target_user).order_by('-created_at')[:10],
            'report_count': Report.objects.filter(reported_user=target_user).count(),
        }
        return render(request, 'wvapp/user_manage.html', context)
    
    def post(self, request, user_id):
        from accounts.models import CustomUser
        from django.utils import timezone
        from datetime import timedelta
        
        target_user = get_object_or_404(CustomUser, pk=user_id)
        action = request.POST.get('action')
        ban_reason = request.POST.get('ban_reason', '')
        
        if action == 'ban_1day':
            target_user.banned_until = timezone.now() + timedelta(days=1)
            target_user.ban_reason = ban_reason
            target_user.save()
            messages.success(request, f'{target_user.username}を1日間の書き込み禁止にしました。')
        
        elif action == 'ban_7days':
            target_user.banned_until = timezone.now() + timedelta(days=7)
            target_user.ban_reason = ban_reason
            target_user.save()
            messages.success(request, f'{target_user.username}を7日間の書き込み禁止にしました。')
        
        elif action == 'ban_30days':
            target_user.banned_until = timezone.now() + timedelta(days=30)
            target_user.ban_reason = ban_reason
            target_user.save()
            messages.success(request, f'{target_user.username}を30日間の書き込み禁止にしました。')
        
        elif action == 'ban_permanent':
            target_user.is_banned = True
            target_user.ban_reason = ban_reason
            target_user.save()
            messages.success(request, f'{target_user.username}を永久BANしました。')
        
        elif action == 'unban':
            target_user.is_banned = False
            target_user.banned_until = None
            target_user.ban_reason = ''
            target_user.save()
            messages.success(request, f'{target_user.username}のBANを解除しました。')
        
        elif action == 'delete_recruitment':
            if hasattr(target_user, 'recruitment') and target_user.recruitment:
                target_user.recruitment.delete()
                messages.success(request, f'{target_user.username}の募集を削除しました。')
        
        elif action == 'delete_all_comments':
            count = target_user.comments.count()
            target_user.comments.all().delete()
            messages.success(request, f'{target_user.username}のコメント{count}件を削除しました。')
        
        return redirect('wvapp:user_manage', user_id=user_id)


class TermsView(TemplateView):
    """利用規約ページ"""
    template_name = 'wvapp/terms.html'


class PrivacyView(TemplateView):
    """プライバシーポリシーページ"""
    template_name = 'wvapp/privacy.html'


class AnnouncementListView(ListView):
    """公開中のお知らせ一覧（誰でも閲覧可）"""
    model = Announcement
    template_name = 'wvapp/announcement_list.html'
    context_object_name = 'announcements'
    paginate_by = 20

    def get_queryset(self):
        return Announcement.objects.filter(is_active=True).order_by('-created_at')


class AnnouncementCreateView(StaffRequiredMixin, CreateView):
    """管理者専用：お知らせ作成"""
    model = Announcement
    form_class = AnnouncementForm
    template_name = 'wvapp/announcement_form.html'

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('wvapp:announcement_list')


class AnnouncementUpdateView(StaffRequiredMixin, UpdateView):
    """管理者専用：お知らせ編集"""
    model = Announcement
    form_class = AnnouncementForm
    template_name = 'wvapp/announcement_form.html'

    def get_success_url(self):
        return reverse_lazy('wvapp:announcement_list')


class AnnouncementDeleteView(StaffRequiredMixin, DeleteView):
    """管理者専用：お知らせ削除（論理削除ではなく実削除）"""
    model = Announcement
    template_name = 'wvapp/announcement_confirm_delete.html'

    def get_success_url(self):
        return reverse_lazy('wvapp:announcement_list')
