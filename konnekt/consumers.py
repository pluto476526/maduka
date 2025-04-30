import json, string, secrets
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from django.db.models import Max
from konnekt.models import Conversation, ConversationItem

User = get_user_model()


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.conv_id = self.scope['url_route']['kwargs']['conv_id']
        self.room_group_name = f'chat_{self.conv_id}'

        # Join room group
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        message = data['message']
        sender_id = data['sender_id']
        sender = data['sender']
        timestamp = data['timestamp']

        await self.save_message(sender_id, message)

        # Broadcast to conversation group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message,
                'sender_id': sender_id,
                'sender': sender,
                'timestamp': timestamp,
            }
        )

        # Notify recent chats for all participants
        conversation = await self.get_conversation()
        participants = await self.get_participants(conversation)
        for user in participants:
            await self.channel_layer.group_send(
                f'user_{user.id}_recent_chats',
                {'type': 'chat_updated'}
            )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'message': event['message'],
            'sender_id': event['sender_id'],
            'sender': event['sender'],
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

class RecentChatsConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user_id = self.scope['url_route']['kwargs']['user_id']
        self.user = await self.get_user(self.user_id)

        if not self.user:
            await self.close()
            return

        self.group_name = f'user_{self.user.id}_recent_chats'
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

        recent_chats = await self.get_recent_chats()
        await self.send(text_data=json.dumps({'recent_chats': recent_chats}))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def chat_updated(self, event):
        recent_chats = await self.get_recent_chats()
        await self.send(text_data=json.dumps({'recent_chats': recent_chats}))

    @database_sync_to_async
    def get_user(self, user_id):
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            return None

    @database_sync_to_async
    def get_recent_chats(self):
        conversations = Conversation.objects.filter(
            participants=self.user,
            is_deleted=False
        ).annotate(
            last_message=Max('messages__timestamp')
        ).order_by('-last_message')

        result = []
        for convo in conversations:
            last_message = convo.messages.order_by('-timestamp').first()
            result.append({
                'conv_id': convo.conv_id,
                'is_group': convo.is_group,
                'title': convo.title,
                'last_message': last_message.body if last_message else "",
                'timestamp': last_message.timestamp.strftime('%I:%M %p') if last_message else "",
                'participants': [
                    {
                        'username': p.username.title(),
                        'avatar_url': p.profile.avatar.url if hasattr(p, 'profile') and p.profile.avatar else '/static/img/default.jpg'
                    } for p in convo.participants.exclude(id=self.user.id)
                ]
            })

        return result
