// ===== AXSEM Web Push Notification Manager =====

const PUSH_SW_URL    = '/static/sw.js';
const PUSH_KEY_URL   = '/push/vapid-public-key/';
const PUSH_SAVE_URL  = '/push/save-subscription/';
const PUSH_DEL_URL   = '/push/delete-subscription/';

// Convert base64 to Uint8Array (required for VAPID public key)
function urlBase64ToUint8Array(base64String) {
    const padding = '='.repeat((4 - base64String.length % 4) % 4);
    const base64  = (base64String + padding).replace(/-/g, '+').replace(/_/g, '/');
    const raw     = window.atob(base64);
    return Uint8Array.from([...raw].map(c => c.charCodeAt(0)));
}

// Get CSRF token
function getCookie(name) {
    const val = `; ${document.cookie}`.split(`; ${name}=`);
    if (val.length === 2) return val.pop().split(';').shift();
}

async function initPushNotifications() {
    // Browser support check
    if (!('serviceWorker' in navigator) || !('PushManager' in window)) {
        console.log('Push notifications not supported');
        return;
    }

    try {
        // Register service worker
        const reg = await navigator.serviceWorker.register(PUSH_SW_URL, { scope: '/' });
        await navigator.serviceWorker.ready;

        // Check current permission
        const permission = Notification.permission;

        if (permission === 'denied') return;

        // Get existing subscription
        let subscription = await reg.pushManager.getSubscription();

        if (!subscription) {
            // Ask for permission and subscribe
            const granted = await Notification.requestPermission();
            if (granted !== 'granted') return;

            // Get VAPID public key
            const keyRes  = await fetch(PUSH_KEY_URL);
            const keyData = await keyRes.json();
            const appKey  = urlBase64ToUint8Array(keyData.publicKey);

            subscription = await reg.pushManager.subscribe({
                userVisibleOnly:      true,
                applicationServerKey: appKey,
            });
        }

        // Save subscription to server
        await fetch(PUSH_SAVE_URL, {
            method:  'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken':  getCookie('csrftoken'),
            },
            body: JSON.stringify(subscription.toJSON()),
        });

        console.log('Push subscription saved ✅');

    } catch (err) {
        console.warn('Push init error:', err);
    }
}

// Auto-init when page loads
document.addEventListener('DOMContentLoaded', initPushNotifications);
