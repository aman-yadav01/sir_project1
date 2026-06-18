// ===== AXSEM Service Worker - Push Notifications =====
self.addEventListener('push', function(event) {
    let data = {};
    try {
        data = event.data ? event.data.json() : {};
    } catch(e) {
        data = { title: 'AXSEM', body: event.data ? event.data.text() : 'New notification' };
    }

    const title   = data.title || 'AXSEM Notification';
    const options = {
        body:    data.body  || '',
        icon:    '/static/icon-192.png',
        badge:   '/static/icon-192.png',
        vibrate: [200, 100, 200],
        data:    { url: data.url || '/' },
        actions: [
            { action: 'open',    title: 'Open' },
            { action: 'dismiss', title: 'Dismiss' }
        ]
    };

    event.waitUntil(
        self.registration.showNotification(title, options)
    );
});

// Click pe notification band karo aur URL kholo
self.addEventListener('notificationclick', function(event) {
    event.notification.close();
    if (event.action === 'dismiss') return;

    const url = event.notification.data && event.notification.data.url
        ? event.notification.data.url
        : '/';

    event.waitUntil(
        clients.matchAll({ type: 'window', includeUncontrolled: true }).then(function(clientList) {
            for (let i = 0; i < clientList.length; i++) {
                const client = clientList[i];
                if (client.url.includes(self.location.origin) && 'focus' in client) {
                    client.navigate(url);
                    return client.focus();
                }
            }
            if (clients.openWindow) {
                return clients.openWindow(url);
            }
        })
    );
});

// Install & activate
self.addEventListener('install',  () => self.skipWaiting());
self.addEventListener('activate', e  => e.waitUntil(clients.claim()));
