from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import CreateView, TemplateView, UpdateView, DetailView, ListView, View, FormView
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.http import JsonResponse
from django.db.models import Q
from django.utils import timezone
from datetime import timedelta
from .forms import CustomUserCreationForm, UsernameChangeForm, EmailChangeForm
from .models import CustomUser, ChatRoom, ChatMessage, Block, Notification


def format_discord_datetime(dt):
    # 日時フォーマット
    if dt is None:
        return ''
    now = timezone.localtime(timezone.now())
    local_dt = timezone.localtime(dt)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    yesterday_start = today_start - timedelta(days=1)
    
    if local_dt >= today_start:
        return local_dt.strftime('%H:%M')
    elif local_dt >= yesterday_start:
        return '昨日 ' + local_dt.strftime('%H:%M')
    else:
        return local_dt.strftime('%Y/%m/%d %H:%M')


def format_discord_datetime_short(dt):
    # 日時フォーマット
    if dt is None:
        return ''
    now = timezone.localtime(timezone.now())
    local_dt = timezone.localtime(dt)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    yesterday_start = today_start - timedelta(days=1)
    
    if local_dt >= today_start:
        return local_dt.strftime('%H:%M')
    elif local_dt >= yesterday_start:
        return '昨日 ' + local_dt.strftime('%H:%M')
    else:
        return local_dt.strftime('%m/%d %H:%M')


class SignUpView(CreateView):
    # ユーザー登録ビュー
    form_class = CustomUserCreationForm
    template_name = 'accounts/signup.html'
    success_url = reverse_lazy('accounts:signup_done')


class SignUpDoneView(TemplateView):
    # ユーザー登録完了ビュー
    template_name = 'accounts/signup_done.html'


class CustomLoginView(LoginView):
    # ログインビュー
    template_name = 'accounts/login.html'
    redirect_authenticated_user = True


class CustomLogoutView(LogoutView):
    # ログアウトビュー
    next_page = reverse_lazy('wvapp:index')
    
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            messages.success(request, 'ログアウトしました。')
        return super().dispatch(request, *args, **kwargs)


class MyPageView(LoginRequiredMixin, TemplateView):
    # マイページビュー
    template_name = 'accounts/mypage.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context['can_change_username'] = user.can_change_username()
        context['next_change_date'] = user.get_next_username_change_date()
        # 募集があるかどうかをチェック
        context['has_recruitment'] = hasattr(user, 'recruitment') and user.recruitment is not None
        try:
            context['recruitment'] = user.recruitment
        except:
            context['recruitment'] = None
        context['comments_count'] = user.comments.count()
        # 受けた評価一覧（ログインユーザーからの評価のみ）
        context['received_ratings'] = user.received_ratings.filter(rater__isnull=False).order_by('-created_at')[:20]
        return context


class UsernameChangeView(LoginRequiredMixin, UpdateView):
    # ユーザー名変更ビュー
    form_class = UsernameChangeForm
    template_name = 'accounts/username_change.html'
    success_url = reverse_lazy('accounts:mypage')
    
    def get_object(self):
        return self.request.user


class EmailChangeView(LoginRequiredMixin, FormView):
    # メールアドレス変更ビュー
    form_class = EmailChangeForm
    template_name = 'accounts/email_change.html'
    success_url = reverse_lazy('accounts:email_change_done')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        user = self.request.user
        user.email = form.cleaned_data['new_email']
        user.save()
        return super().form_valid(form)


class EmailChangeDoneView(LoginRequiredMixin, TemplateView):
    # メールアドレス変更完了ビュー
    template_name = 'accounts/email_change_done.html'


class UserProfileView(DetailView):
    # ユーザープロフィールビュー（公開）
    model = CustomUser
    template_name = 'accounts/user_profile.html'
    context_object_name = 'profile_user'
    pk_url_kwarg = 'user_id'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        profile_user = self.object
        
        # 募集情報
        context['has_recruitment'] = hasattr(profile_user, 'recruitment') and profile_user.recruitment is not None
        try:
            context['recruitment'] = profile_user.recruitment
        except:
            context['recruitment'] = None
        
        # アクティビティ
        context['comments_count'] = profile_user.comments.count()
        context['ratings_count'] = profile_user.received_ratings.count()
        
        # 受けた評価一覧（ログインユーザーからの評価のみ）
        context['received_ratings'] = profile_user.received_ratings.filter(rater__isnull=False).order_by('-created_at')[:20]
        
        # 自分自身かどうか
        context['is_own_profile'] = self.request.user == profile_user
        
        # ブロック状態
        if self.request.user.is_authenticated and self.request.user != profile_user:
            context['is_blocked'] = Block.objects.filter(
                blocker=self.request.user,
                blocked=profile_user
            ).exists()
            context['is_blocked_by'] = Block.objects.filter(
                blocker=profile_user,
                blocked=self.request.user
            ).exists()
        else:
            context['is_blocked'] = False
            context['is_blocked_by'] = False
        
        return context


class ChatListView(LoginRequiredMixin, ListView):
    # チャット一覧ビュー
    model = ChatRoom
    template_name = 'accounts/chat_list.html'
    context_object_name = 'chat_rooms'
    
    def get_queryset(self):
        rooms = ChatRoom.objects.filter(
            participants=self.request.user
        ).order_by('-updated_at')
        
        # 各ルームに追加情報を付与
        for room in rooms:
            room.other_user = room.get_other_user(self.request.user)
            room.unread_count = room.get_unread_count(self.request.user)
        
        return rooms


class ChatWithView(LoginRequiredMixin, View):
    # 特定ユーザーとのチャットを開始/開くビュー
    
    def get(self, request, user_id):
        other_user = get_object_or_404(CustomUser, pk=user_id)
        
        # 自分自身とはチャットできない
        if other_user == request.user:
            return redirect('accounts:chat_list')
        
        # ブロック関係をチェック
        if Block.objects.filter(blocker=request.user, blocked=other_user).exists():
            messages.error(request, 'このユーザーをブロックしています。チャットするにはブロックを解除してください。')
            return redirect('accounts:user_profile', user_id=user_id)
        
        if Block.objects.filter(blocker=other_user, blocked=request.user).exists():
            messages.error(request, 'このユーザーにブロックされているため、チャットできません。')
            return redirect('accounts:user_profile', user_id=user_id)
        
        # 既存のチャットルームを検索
        room = ChatRoom.objects.filter(
            participants=request.user
        ).filter(
            participants=other_user
        ).first()
        
        # なければ新規作成
        if not room:
            room = ChatRoom.objects.create()
            room.participants.add(request.user, other_user)
        
        return redirect('accounts:chat_room', room_id=room.pk)


class ChatRoomView(LoginRequiredMixin, DetailView):
    # チャットルームビュー
    model = ChatRoom
    template_name = 'accounts/chat_room.html'
    context_object_name = 'room'
    pk_url_kwarg = 'room_id'
    
    def get_queryset(self):
        # 自分が参加しているチャットルームのみ
        return ChatRoom.objects.filter(participants=self.request.user)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        other_user = self.object.get_other_user(self.request.user)
        context['other_user'] = other_user
        context['chat_messages'] = self.object.messages.order_by('created_at')
        
        # ブロック状態を確認
        context['is_blocked'] = Block.objects.filter(
            blocker=self.request.user, blocked=other_user
        ).exists()
        context['is_blocked_by'] = Block.objects.filter(
            blocker=other_user, blocked=self.request.user
        ).exists()
        
        # 相手からのメッセージを既読にする
        self.object.messages.filter(is_read=False).exclude(
            sender=self.request.user
        ).update(is_read=True)
        
        return context
    
    def post(self, request, room_id):
        room = self.get_object()
        other_user = room.get_other_user(request.user)
        content = request.POST.get('content', '').strip()
        
        if content:
            # BAN中は送信不可
            if request.user.is_write_banned():
                return JsonResponse({
                    'success': False,
                    'error': '現在、書き込みが禁止されています。'
                }, status=403)
            
            # ブロック関係をチェック
            if Block.objects.filter(blocker=request.user, blocked=other_user).exists():
                return JsonResponse({
                    'success': False,
                    'error': 'このユーザーをブロックしています。'
                }, status=403)
            
            if Block.objects.filter(blocker=other_user, blocked=request.user).exists():
                return JsonResponse({
                    'success': False,
                    'error': 'このユーザーにブロックされています。'
                }, status=403)
            
            message = ChatMessage.objects.create(
                room=room,
                sender=request.user,
                content=content
            )
            # ルームの更新日時を更新
            room.save()
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': {
                        'id': message.pk,
                        'content': message.content,
                        'sender': message.sender.username,
                        'sender_id': message.sender.pk,
                        'created_at': format_discord_datetime_short(message.created_at)
                    }
                })
        
        return redirect('accounts:chat_room', room_id=room_id)


class ChatMessagesAPIView(LoginRequiredMixin, View):
    # チャットメッセージ取得API
    
    def get(self, request, room_id):
        room = get_object_or_404(
            ChatRoom.objects.filter(participants=request.user),
            pk=room_id
        )
        
        # 最後に取得したメッセージID以降のメッセージを取得
        last_id = request.GET.get('last_id', 0)
        try:
            last_id = int(last_id)
        except:
            last_id = 0
        
        messages = room.messages.filter(pk__gt=last_id).order_by('created_at')
        
        # 相手からのメッセージを既読にする
        messages.filter(is_read=False).exclude(
            sender=request.user
        ).update(is_read=True)
        
        return JsonResponse({
            'messages': [
                {
                    'id': msg.pk,
                    'content': msg.content,
                    'sender': msg.sender.username,
                    'sender_id': msg.sender.pk,
                    'created_at': format_discord_datetime_short(msg.created_at),
                    'is_mine': msg.sender == request.user
                }
                for msg in messages
            ]
        })


class UnreadCountAPIView(LoginRequiredMixin, View):
    # 未読メッセージ数取得API
    
    def get(self, request):
        count = ChatMessage.objects.filter(
            room__participants=request.user,
            is_read=False
        ).exclude(sender=request.user).count()
        
        return JsonResponse({'unread_count': count})


class BlockUserView(LoginRequiredMixin, View):
    # ユーザーをブロックするビュー
    
    def post(self, request, user_id):
        target_user = get_object_or_404(CustomUser, pk=user_id)
        
        # 自分自身はブロックできない
        if target_user == request.user:
            messages.error(request, '自分自身をブロックすることはできません。')
            return redirect('accounts:user_profile', user_id=user_id)
        
        # 既にブロックしているかチェック
        block, created = Block.objects.get_or_create(
            blocker=request.user,
            blocked=target_user
        )
        
        if created:
            messages.success(request, f'{target_user.username}をブロックしました。')
        else:
            messages.info(request, f'{target_user.username}は既にブロックしています。')
        
        return redirect('accounts:user_profile', user_id=user_id)


class UnblockUserView(LoginRequiredMixin, View):
    # ユーザーのブロックを解除するビュー
    
    def post(self, request, user_id):
        target_user = get_object_or_404(CustomUser, pk=user_id)
        
        # ブロックを解除
        deleted, _ = Block.objects.filter(
            blocker=request.user,
            blocked=target_user
        ).delete()
        
        if deleted:
            messages.success(request, f'{target_user.username}のブロックを解除しました。')
        else:
            messages.info(request, f'{target_user.username}はブロックしていません。')
        
        return redirect('accounts:user_profile', user_id=user_id)


class BlockListView(LoginRequiredMixin, ListView):
    # ブロックリスト一覧ビュー
    model = Block
    template_name = 'accounts/block_list.html'
    context_object_name = 'blocks'
    
    def get_queryset(self):
        return Block.objects.filter(blocker=self.request.user).select_related('blocked')


class AccountDeleteView(LoginRequiredMixin, TemplateView):
    # アカウント削除確認ビュー
    template_name = 'accounts/account_delete.html'
    
    def post(self, request):
        user = request.user
        # パスワード確認
        password = request.POST.get('password', '')
        if not user.check_password(password):
            messages.error(request, 'パスワードが正しくありません。')
            return redirect('accounts:account_delete')
        
        # ログアウトしてからアカウント削除
        from django.contrib.auth import logout
        logout(request)
        user.delete()
        
        messages.success(request, 'アカウントを削除しました。ご利用ありがとうございました。')
        return redirect('wvapp:index')


class NotificationListView(LoginRequiredMixin, ListView):
    # 通知一覧ビュー
    model = Notification
    template_name = 'accounts/notification_list.html'
    context_object_name = 'notifications'
    paginate_by = 20
    
    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user).order_by('-created_at')


class NotificationReadView(LoginRequiredMixin, View):
    # 通知を既読にして、リンク先にリダイレクトするビュー
    
    def get(self, request, pk):
        notification = get_object_or_404(Notification, pk=pk, user=request.user)
        notification.is_read = True
        notification.save()
        
        if notification.link:
            return redirect(notification.link)
        return redirect('accounts:notification_list')


class MarkAllNotificationsReadView(LoginRequiredMixin, View):
    # 全ての通知を既読にするビュー
    
    def post(self, request):
        Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        messages.success(request, 'すべての通知を既読にしました。')
        return redirect('accounts:notification_list')
