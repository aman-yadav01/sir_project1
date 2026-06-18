"""
Web Push Notification Views
Save subscriptions and send push notifications
"""
import json
import base64
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.conf import settings

from .models import PushSubscription, User


# ==================== VAPID CONFIG ====================

VAPID_PUBLIC_KEY  = settings.VAPID_PUBLIC_KEY
VAPID_PRIVATE_PEM = base64.b64decode(settings.VAPID_PRIVATE_PEM_B64).decode()
VAPID_CLAIMS      = {"sub": "mailto:admin@axsem.com"}


# ==================== CREATE IN-APP NOTIFICATION ====================

def create_notification(user, title, message, notif_type='general', url='/'):
    """Create a DB notification for a user"""
    from .models import Notification
    Notification.objects.create(
        user=user, title=title, message=message,
        notif_type=notif_type, url=url
    )


# ==================== SAVE SUBSCRIPTION ====================

@login_required
@require_POST
def save_subscription(request):
    """Save browser push subscription to DB"""
    try:
        data = json.loads(request.body)
        endpoint = data.get('endpoint')
        p256dh   = data.get('keys', {}).get('p256dh', '')
        auth     = data.get('keys', {}).get('auth', '')

        if not endpoint:
            return JsonResponse({'success': False, 'error': 'No endpoint'}, status=400)

        PushSubscription.objects.update_or_create(
            endpoint=endpoint,
            defaults={
                'user':   request.user,
                'p256dh': p256dh,
                'auth':   auth,
            }
        )
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


# ==================== DELETE SUBSCRIPTION ====================

@login_required
@require_POST
def delete_subscription(request):
    """Remove subscription (when user denies permission)"""
    try:
        data = json.loads(request.body)
        endpoint = data.get('endpoint')
        PushSubscription.objects.filter(endpoint=endpoint, user=request.user).delete()
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


# ==================== VAPID PUBLIC KEY ====================

def get_vapid_public_key(request):
    """Return VAPID public key to browser"""
    return JsonResponse({'publicKey': VAPID_PUBLIC_KEY})


# ==================== SEND PUSH HELPER ====================

def send_push_to_user(user, title, body, url='/'):
    """
    Send push notification to all subscriptions of a user.
    Call this from any view when you want to notify.
    """
    try:
        from pywebpush import webpush, WebPushException
    except ImportError:
        return

    subscriptions = PushSubscription.objects.filter(user=user)
    payload = json.dumps({'title': title, 'body': body, 'url': url})

    for sub in subscriptions:
        try:
            webpush(
                subscription_info={
                    'endpoint': sub.endpoint,
                    'keys': {
                        'p256dh': sub.p256dh,
                        'auth':   sub.auth,
                    }
                },
                data=payload,
                vapid_private_key=VAPID_PRIVATE_PEM,
                vapid_claims=VAPID_CLAIMS,
            )
        except Exception:
            # If subscription is expired/invalid, remove it
            sub.delete()


def send_push_to_employee(employee, title, body, url='/'):
    """Send push + create DB notification for employee"""
    # Always create DB notification (works without HTTPS)
    create_notification(employee.user, title, body, url=url)
    # Also try web push (works on HTTPS/localhost)
    send_push_to_user(employee.user, title, body, url)


# ==================== IN-APP NOTIFICATION VIEWS ====================

@login_required
def get_notification_count(request):
    """Return unread notification count (for bell badge)"""
    from .models import Notification
    count = Notification.objects.filter(user=request.user, is_read=False).count()
    return JsonResponse({'count': count})


@login_required
def get_notifications(request):
    """Return last 20 notifications as JSON"""
    from .models import Notification
    notifs = Notification.objects.filter(user=request.user).order_by('-created_at')[:20]
    data = [{
        'id':      n.id,
        'title':   n.title,
        'message': n.message,
        'type':    n.notif_type,
        'url':     n.url,
        'is_read': n.is_read,
        'time':    n.created_at.strftime('%d %b, %I:%M %p'),
    } for n in notifs]
    return JsonResponse({'notifications': data})


@login_required
@require_POST
def mark_notifications_read(request):
    """Mark all notifications as read"""
    from .models import Notification
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    return JsonResponse({'success': True})


@login_required
@require_POST
def mark_one_read(request, notif_id):
    """Mark single notification as read"""
    from .models import Notification
    Notification.objects.filter(id=notif_id, user=request.user).update(is_read=True)
    return JsonResponse({'success': True})
