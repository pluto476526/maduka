// self.addEventListener('push', function(event) {
//     const payload = event.data ? event.data.json() : {};
//     const title = payload.title || 'Notification';
//     const options = {
//         body: payload.message,
//         data: payload.data || {},
//         icon: '/static/images/notification-icon.png',
//         badge: '/static/images/notification-badge.png'
//     };

//     event.waitUntil(
//         self.registration.showNotification(title, options)
//     );
// });

// self.addEventListener('notificationclick', function(event) {
//     event.notification.close();
    
//     const conversationId = event.notification.data.conversation_id;
//     if (conversationId) {
//         event.waitUntil(
//             clients.openWindow(`/conversations/${conversationId}/`)
//         );
//     }
// });






self.addEventListener('push', function(event) {
    const payload = event.data ? event.data.json() : {};
    const title = payload.title || 'Notification';
    console.log('loades wkoker');
    
    // Enhanced notification options
    const options = {
        body: payload.message,
        data: payload.data || {},
        icon: payload.icon || '/static/konnekt/img/notification-icon.png',
        badge: payload.badge || '/static/konnekt/img/notification-badge.png',
        vibrate: payload.vibrate || [200, 100, 200, 100, 200], // Default vibration pattern
        requireInteraction: payload.requireInteraction || false, // Stay until clicked
        actions: payload.actions || [], // Notification actions
        renotify: payload.renotify || false, // Vibrate/sound on renotification
        silent: payload.silent || false, // No sound/vibration if true
        timestamp: payload.timestamp || Date.now() // Notification time
    };
    console.log('options:', options);

    event.waitUntil(
        self.registration.showNotification(title, options)
    );
});

self.addEventListener('notificationclick', function(event) {
    event.notification.close();
    
    // Handle action buttons
    if (event.action) {
        switch(event.action) {
            case 'view':
                // Handle view action
                const conversationId = event.notification.data.conversation_id;
                if (conversationId) {
                    event.waitUntil(
                        clients.openWindow(`/konnekt/${conversationId}/`)
                    );
                }
                break;
            case 'dismiss':
                // Handle dismiss action
                console.log('Notification dismissed');
                break;
            default:
                // Handle other actions
                event.waitUntil(
                    clients.openWindow('/notifications/')
                );
        }
    } else {
        // Default click behavior (no specific action clicked)
        const conversationId = event.notification.data.conversation_id;
        if (conversationId) {
            event.waitUntil(
                clients.openWindow(`/konnekt/${conversationId}/`)
            );
        } else {
            event.waitUntil(
                clients.openWindow('/notifications/')
            );
        }
    }
});

self.addEventListener('notificationclose', function(event) {
    // Handle when notification is closed/dismissed
    console.log('Notification closed:', event.notification);
    // You can send analytics here if needed
});