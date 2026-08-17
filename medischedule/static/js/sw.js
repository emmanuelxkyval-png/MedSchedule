self.addEventListener('push', function(event) {
    const data = event.data.json();
    const title = data.head || 'MediSchedule';
    const options = {
        body: data.body || 'You have a new notification',
        icon: '/static/img/icon.png',
        badge: '/static/img/icon.png',
    };
    event.waitUntil(
        self.registration.showNotification(title, options)
    );
});

self.addEventListener('notificationclick', function(event) {
    event.notification.close();
    event.waitUntil(
        clients.openWindow('/')
    );
});