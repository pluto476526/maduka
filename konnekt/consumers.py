import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from konnekt.models import Conversation, ConversationItem, ConversationReadStatus
from django.db.models import Max
from konnekt.models import UserStatus
from datetime import datetime


User = get_user_model()

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.conv_id = self.scope['url_route']['kwargs']['conv_id']
        self.room_group_name = f'chat_{self.conv_id}'

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)

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

            message = data['message']
            sender_id = data.get('sender_id')
            sender = data.get('sender')
            timestamp = data.get('timestamp')
            attachment_url = data.get('attachment_url')
            attachment_type = data.get('attachment_type')

            # Save to DB
            await self.save_message(sender_id, message)

            # Broadcast chat message
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'send_chat_message',
                    'message': message,
                    'sender_id': sender_id,
                    'sender': sender,
                    'timestamp': timestamp,
                    'attachment_url': attachment_url,
                    'attachment_type': attachment_type,
                }
            )

            # Notify recent chats update
            conversation = await self.get_conversation()
            participants = await self.get_participants(conversation)
            for user in participants:
                await self.channel_layer.group_send(
                    f'recent_chats_{user.id}',
                    {'type': 'send_chat_updated'}
                )

        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({'error': 'Invalid JSON'}))
        except Exception as e:
            await self.send(text_data=json.dumps({'error': f"Error: {str(e)}"}))


    async def send_chat_message(self, event):
        await self.send(text_data=json.dumps({
            'message': event['message'],
            'sender_id': event['sender_id'],
            'sender': event['sender'],
            'timestamp': event['timestamp'],
            'attachment_url': event['attachment_url'],
            'attachment_type': event['attachment_type'],
        }))

    async def send_read_status(self, event):
        await self.send(text_data=json.dumps({
            'type': 'read_status.update',
            'convo_id': event['convo_id'],
            'user_id': event['user_id'],
            'timestamp': event['timestamp'],
        }))


    @database_sync_to_async
    def save_message(self, sender_id, message):
        sender = User.objects.get(id=sender_id)
        conversation = Conversation.objects.get(conv_id=self.conv_id)
        return ConversationItem.objects.create(
            conversation=conversation,
            sender=sender,
            body=message
        )

    @database_sync_to_async
    def get_conversation(self):
        return Conversation.objects.get(conv_id=self.conv_id)

    @database_sync_to_async
    def get_participants(self, conversation):
        return list(conversation.participants.all())


    @database_sync_to_async
    def update_read_status(self, user_id, timestamp):
        user = User.objects.get(id=user_id)
        conversation = Conversation.objects.get(conv_id=self.conv_id)
        r_status, _ = ConversationReadStatus.objects.get_or_create(
            conversation=conversation,
            user=user
        )
        r_status.last_read_at = datetime.now()
        r_status.save()


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
                unread_count = convo.messages.filter(timestamp__gt=last_read_at).count()
            else:
                unread_count = convo.messages.count()


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
                'lm_sender': lm_sender.id,
                'timestamp': last_message.timestamp.isoformat() if last_message else "",
                'participants': [
                    {
                        'userID': str(p.id),
                        'username': p.username,
                        'avatar_url': p.profile.avatar.url
                    }
                    for p in convo.participants.exclude(id=self.user.id)
                ]
            })

        return sorted(recent_chats, key=lambda x: x['timestamp'] or "", reverse=True)
