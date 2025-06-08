# /konnekt/consumers.py

import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from konnekt.models import Conversation, ConversationItem, ConversationReadStatus, MessageImage, PushSubscription
from django.db.models import Max
from konnekt.models import UserStatus
from datetime import datetime
import redis
from django.conf import settings

# Redis connection
redis_conn = redis.StrictRedis(host='localhost', port=6379, db=1)


logger = logging.getLogger(__name__)
User = get_user_model()



class RecentChatsConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user_id = self.scope['url_route']['kwargs']['user_id']
        self.user = await self.get_user(self.user_id)

        if not self.user:
            await self.close()
            return

        self.group_name = f'recent_chats_{self.user_id}'
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        await self.send_recent_chats()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    # Triggered by ChatConsumer via group_send
    async def send_chat_updated(self, event):
        await self.send_recent_chats()

    async def send_recent_chats(self):
        recent_chats = await self.get_recent_chats()
        # Send recent chats with online status information
        await self.send(text_data=json.dumps({
            'type': 'recent_chats',
            'recent_chats': recent_chats
        }))

    @database_sync_to_async
    def get_user(self, user_id):
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            return None

    @database_sync_to_async
    def get_recent_chats(self):
        conversations = Conversation.objects.filter(
            participants=self.user
        ).prefetch_related('participants', 'messages').distinct()

        recent_chats = []
        for convo in conversations:
            try:
                read_status = convo.read_statuses.get(user=self.user)
                last_read_at = read_status.last_read_at
            except ConversationReadStatus.DoesNotExist:
                last_read_at = None

            if last_read_at:
                unread_messages = convo.messages.filter(timestamp__gt=last_read_at).exclude(sender=self.user.id)
                unread_count = unread_messages.count()
                unread_image_count = MessageImage.objects.filter(message__in=unread_messages).count()
            else:
                unread_messages = convo.messages.all()
                unread_count = unread_messages.count()
                unread_image_count = MessageImage.objects.filter(message__in=unread_messages).count()

            last_message = convo.messages.order_by('-timestamp').first()
            lm_sender = convo.participants.exclude(id=self.user_id).first()

            recent_chats.append({
                'conv_id': str(convo.conv_id),
                'is_group': convo.is_group,
                'title': convo.title or ", ".join(
                    p.username for p in convo.participants.exclude(id=self.user.id)
                ),
                'last_message': last_message.body if last_message else "",
                'unread_count': unread_count,
                'unread_image_count': unread_image_count,
                'lm_sender': lm_sender.id,
                'timestamp': last_message.timestamp.isoformat() if last_message else "",
                'participants': [
                    {
                        'userID': str(p.id),
                        'username': p.username,
                        'avatar_url': p.profile.avatar.url,
                        'online': redis_conn.sismember("online_users", str(p.id))  # Check online status
                    }
                    for p in convo.participants.exclude(id=self.user.id)
                ]
            })

        return sorted(recent_chats, key=lambda x: x['timestamp'] or "", reverse=True)



class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Get conversation ID from URL
        self.conv_id = self.scope['url_route']['kwargs']['conv_id']
        self.room_group_name = f'chat_{self.conv_id}'
        self.user = self.scope["user"]
        
        if self.user.is_anonymous:
            await self.close()
            return
            
        self.user_group_name = f'user_{self.user.id}'  # Group by user ID for notifications

        # Join the room group and user group
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.channel_layer.group_add(self.user_group_name, self.channel_name)

        await self.accept()

    async def disconnect(self, close_code):
        # Leave the room group and user group on disconnect
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
        if hasattr(self, 'user_group_name'):
            await self.channel_layer.group_discard(self.user_group_name, self.channel_name)

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)

            # Handle push subscription
            if data.get('type') == 'push.subscribe':
                subscription = data.get('subscription')
                if subscription:
                    await self.save_push_subscription(self.user, subscription)
                    return


            # Handle read receipt
            if data.get('type') == 'read_status.send':
                convo_id = data['convo_id']
                user_id = data['user_id']
                timestamp = data['timestamp']

                await self.update_read_status(user_id, timestamp)

                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'send_read_status',
                        'convo_id': convo_id,
                        'user_id': user_id,
                        'timestamp': timestamp,
                    }
                )
                return

            # Handle normal message
            if 'message' not in data:
                await self.send(text_data=json.dumps({
                    'error': "Missing 'message' in the data"
                }))
                return

            # Extract message data
            message = data['message']
            sender_id = data.get('sender_id')
            sender = data.get('sender')
            timestamp = data.get('timestamp')
            image_urls = data.get('image_urls', [])
            uniqueMsgID = data.get('uniqueMsgID')

            # Save the message to the database
            message_obj = await self.save_message(sender_id, message, image_urls)

            # Broadcast the chat message to the group
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',  # Changed from send_chat_message
                    'message_id': message_obj.id,  # Include message ID
                    'message': message,
                    'sender_id': sender_id,
                    'sender': sender,
                    'timestamp': timestamp,
                    'image_urls': image_urls,
                    'uniqueMsgID': uniqueMsgID,
                }
            )

            # Update recent chats
            conversation = await self.get_conversation()
            participants = await self.get_participants(conversation)
            for user in participants:
                logger.debug(user)
                await self.channel_layer.group_send(
                    f'recent_chats_{user.id}',
                    {'type': 'send_chat_updated'}
                )

            # Handle notifications
            await self.handle_notifications(sender_id, sender)

        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({'error': 'Invalid JSON'}))
        except Exception as e:
            await self.send(text_data=json.dumps({'error': f"Error: {str(e)}"}))

    async def handle_notifications(self, sender_id, sender):
        """Separate method for handling notifications"""
        conversation = await self.get_conversation()
        participants = await self.get_participants(conversation)
        
        for user in participants:
            if str(user.id) == str(sender_id):
                continue
                
            # Send Web Push notification if available
            subscription = await self.get_push_subscription(user)
            logger.debug(f'subscription:{subscription}')
            if subscription:
                try:
                    logger.debug('>>>>>>>>>>>>>>>>>>>>>>>pushing')
                    await self.send_push_notification(
                        subscription,
                        "New Message",
                        f'New message from {sender}',
                        {'conversation_id': self.conv_id}
                    )
                    logger.debug('>>>>>>>>>>>>>>>>>>>>>>>>>pushed')
                except Exception as e:
                    logger.error(f"Failed to send push notification: {e}")

            # Send WebSocket notification
            await self.channel_layer.group_send(
                f'user_{user.id}',
                {
                    'type': 'notification_message',  # Changed from send_browser_notification
                    'notification_type': 'new_message',
                    'title': 'Konnekt',
                    'message': f'New text message from {sender}',
                    'data': {
                        'conversation_id': self.conv_id,
                        'sender_id': sender_id
                    }
                }
            )

    async def chat_message(self, event):
        """Handler for real chat messages"""
        await self.send(text_data=json.dumps({
            'type': 'chat_message',  # Explicit type
            'message_id': event['message_id'],
            'message': event['message'],
            'sender_id': event['sender_id'],
            'sender': event['sender'],
            'timestamp': event['timestamp'],
            'image_urls': event['image_urls'],
            'uniqueMsgID': event['uniqueMsgID'],
        }))

    async def notification_message(self, event):
        """Handler for notification messages"""
        await self.send(text_data=json.dumps({
            'type': 'notification',
            'notification_type': event['notification_type'],
            'title': event['title'],
            'message': event['message'],
            'data': event['data']
        }))

    async def send_read_status(self, event):
        """Handler for read receipts"""
        await self.send(text_data=json.dumps({
            'type': 'read_status',
            'convo_id': event['convo_id'],
            'user_id': event['user_id'],
            'timestamp': event['timestamp'],
        }))


    @database_sync_to_async
    def save_message(self, sender_id, message, image_urls=None):
        # Save the chat message to the database
        sender = User.objects.get(id=sender_id)
        conversation = Conversation.objects.get(conv_id=self.conv_id)
        item = ConversationItem.objects.create(
            conversation=conversation,
            sender=sender,
            body=message
        )
        if image_urls:
            for url in image_urls:
                img_path = url.split('/media/')[-1]
                msg_img = MessageImage.objects.get(image=img_path)
                msg_img.message = item
                msg_img.save()
        return item

    @database_sync_to_async
    def get_conversation(self):
        # Retrieve the conversation from the database
        return Conversation.objects.get(conv_id=self.conv_id)

    @database_sync_to_async
    def get_participants(self, conversation):
        # Get all participants of the conversation
        return list(conversation.participants.all())

    @database_sync_to_async
    def update_read_status(self, user_id, timestamp):
        # Update the read status of the conversation for a user
        user = User.objects.get(id=user_id)
        conversation = Conversation.objects.get(conv_id=self.conv_id)
        r_status, _ = ConversationReadStatus.objects.get_or_create(
            conversation=conversation,
            user=user
        )
        r_status.last_read_at = datetime.now()
        r_status.save()

    @database_sync_to_async
    def get_push_subscription(self, user):
        try:
            return PushSubscription.objects.filter(user=user).first()
        except PushSubscription.DoesNotExist:
            return None

    @database_sync_to_async
    def save_push_subscription(self, user, subscription):
        # Delete existing subscriptions for this user
        PushSubscription.objects.filter(user=user).delete()
        # Create new subscription
        return PushSubscription.objects.create(
            user=user,
            endpoint=subscription['endpoint'],
            keys=subscription['keys']
        )

    async def send_push_notification(self, subscription, title, message, data=None):
        from pywebpush import webpush, WebPushException
        from django.conf import settings
        
        vapid_private_key = getattr(settings, 'VAPID_PRIVATE_KEY')
        vapid_claims = {
            "sub": f"mailto:{settings.NOTIFICATION_EMAIL}"
        }
        
        notification_payload = {
            "title": title,
            "body": message,
            "requireInteraction": True,  # Keeps notification visible until clicked
            "vibrate": [200, 100, 200, 100, 200, 100, 200],  # Vibration pattern (ms)
            "actions": [
                {
                    "action": "view",
                    "title": "View"
                },
                {
                    "action": "dismiss",
                    "title": "Dismiss"
                }
            ],
            "badge": "/static/konnekt/img/badge-icon.png",  # Small icon for some platforms
            "icon": "/static/konnekt/img/notification-icon.png",  # Main notification icon
            "renotify": True,  # Vibrates/sounds again for grouped notifications
            "silent": False,  # Whether to suppress sound/vibration
            "timestamp": int(time.time() * 1000),  # When notification was created
            "data": data or {}  # Your custom data payload
        }
        logger.debug(notification_payload)
        
        try:
            webpush(
                subscription_info={
                    "endpoint": subscription.endpoint,
                    "keys": {
                        "p256dh": subscription.keys['p256dh'],
                        "auth": subscription.keys['auth']
                    }
                },
                data=json.dumps(notification_payload),
                vapid_private_key=vapid_private_key,
                vapid_claims=vapid_claims
            )
        except WebPushException as ex:
            if ex.response.status_code == 410:
                # Subscription is no longer valid, delete it
                await database_sync_to_async(subscription.delete)()
            else:
                raise


    # async def send_push_notification(self, subscription, title, message, data=None):
    #     from pywebpush import webpush, WebPushException
    #     from django.conf import settings
        
    #     vapid_private_key = getattr(settings, 'VAPID_PRIVATE_KEY')
    #     vapid_claims = {
    #         "sub": f"mailto:{settings.NOTIFICATION_EMAIL}"
    #     }
        
    #     try:
    #         webpush(
    #             subscription_info={
    #                 "endpoint": subscription.endpoint,
    #                 "keys": {
    #                     "p256dh": subscription.keys['p256dh'],
    #                     "auth": subscription.keys['auth']
    #                 }
    #             },
    #             data=json.dumps({
    #                 "title": title,
    #                 "message": message,
    #                 "data": data or {}
    #             }),
    #             vapid_private_key=vapid_private_key,
    #             vapid_claims=vapid_claims
    #         )
    #     except WebPushException as ex:
    #         if ex.response.status_code == 410:
    #             # Subscription is no longer valid, delete it
    #             await database_sync_to_async(subscription.delete)()
    #         else:
    #             raise
