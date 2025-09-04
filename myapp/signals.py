from django.dispatch import receiver
from django.contrib.auth.signals import user_logged_in
from .models import UserLog

@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    UserLog.objects.create(
        user=user,
        action="login",
        details=f"User {user.username} logged in from IP: {request.META.get('REMOTE_ADDR')}"
    )
