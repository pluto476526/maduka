self.addEventListener('push', function(event) {
    const payload = event.data ? event.data.json() : {};
    const title = payload.title || 'Notification';
    const options = {
        body: payload.message,
        data: payload.data || {},
        icon: '/static/images/notification-icon.png',
        badge: '/static/images/notification-badge.png'
    };

    event.waitUntil(
        self.registration.showNotification(title, options)
    );
});

self.addEventListener('notificationclick', function(event) {
    event.notification.close();
    
    const conversationId = event.notification.data.conversation_id;
    if (conversationId) {
        event.waitUntil(
            clients.openWindow(`/conversations/${conversationId}/`)
        );
    }
});