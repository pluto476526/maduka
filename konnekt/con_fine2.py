import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from konnekt.models import Conversation, ConversationItem
from django.db.models import Max
from konnekt.models import UserStatus


User = get_user_model()

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.conv_id = self.scope['url_route']['kwargs']['conv_id']
        self.room_group_name = f'chat_{self.conv_id}'

        # Join the room group
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        try:
            # Parse the incoming JSON data
            data = json.loads(text_data)

            # Check if 'message' is in the incoming data
            if 'message' not in data:
                await self.send(text_data=json.dumps({
                    'error': "Missing 'message' in the data"
                }))
                return

            # Extract necessary fields
            message = data['message']
            sender_id = data.get('sender_id')
            sender = data.get('sender')
            timestamp = data.get('timestamp')

            # Save the message to the database
            await self.save_message(sender_id, message)

            # Broadcast to the conversation group
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'send_chat_message',
                    'message': message,
                    'sender_id': sender_id,
                    'sender': sender,
                    'timestamp': timestamp,
                }
            )

            # Notify all participants to update their recent chats
            conversation = await self.get_conversation()
            participants = await self.get_participants(conversation)
            for user in participants:
                await self.channel_layer.group_send(
                    f'user_{user.id}_recent_chats',  # Update the recent chats for each participant
                    {'type': 'send_chat_updated'}   # Trigger the update event
                )

        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({'error': 'Invalid JSON received'}))
        except Exception as e:
            await self.send(text_data=json.dumps({'error': f"Error processing message: {str(e)}"}))

    async def send_chat_message(self, event):
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

        self.group_name = f'recent_chats_{self.user_id}'
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        
        # Send initial recent chats
        await self.send_recent_chats()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    # Handle 'send_chat_updated' event to update recent chats
    async def receive(self, text_data):
        data = json.loads(text_data)
        logger.debug(data)
        logger.debug('>>>>>>>>>>>>>> sending recent chats')
        if data.get('type') == 'send_chat_updated':
            await self.send_recent_chats()  # Send updated recent chats

    async def send_chat_updated(self, event):
        """Send updated list of recent chats."""
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
            last_message = convo.messages.order_by('-timestamp').first()
            recent_chats.append({
                'conv_id': str(convo.conv_id),
                'is_group': convo.is_group,
                'title': convo.title or ", ".join(
                    p.username for p in convo.participants.exclude(id=self.user.id)
                ),
                'last_message': last_message.body if last_message else "",
                'timestamp': last_message.timestamp.isoformat() if last_message else "",
                'participants': [
                    {
                        'userID': str(p.id),
                        'username': p.username,
                        'avatar_url': p.profile.avatar.url if hasattr(p, 'profile') and p.profile.avatar else ""
                    }
                    for p in convo.participants.exclude(id=self.user.id)
                ]
            })
        
        # Sort by timestamp (newest first)
        return sorted(recent_chats, key=lambda x: x['timestamp'] or "", reverse=True)





# class RecentChatsConsumer(AsyncWebsocketConsumer):
#     async def connect(self):
#         self.user_id = self.scope['url_route']['kwargs']['user_id']
#         self.user = await self.get_user(self.user_id)

#         if not self.user:
#             await self.close()
#             return

#         self.group_name = f'user_{self.user.id}_recent_chats'
#         await self.channel_layer.group_add(self.group_name, self.channel_name)
#         await self.accept()

#         # Send the recent chats when the user connects
#         recent_chats = await self.get_recent_chats()
#         await self.send(text_data=json.dumps({'recent_chats': recent_chats}))

#     async def disconnect(self, close_code):
#         if hasattr(self, 'group_name'):
#             await self.channel_layer.group_discard(self.group_name, self.channel_name)

#     async def send_chat_updated(self, event):
#         """Send updated list of recent chats."""
#         recent_chats = await self.get_recent_chats()
#         await self.send(text_data=json.dumps({'recent_chats': recent_chats}))

#     @database_sync_to_async
#     def get_user(self, user_id):
#         try:
#             return User.objects.get(id=user_id)
#         except User.DoesNotExist:
#             return None

#     @database_sync_to_async
#     def get_recent_chats(self):
#         conversations = Conversation.objects.filter(
#             participants=self.user,
#             is_deleted=False
#         ).annotate(
#             last_message=Max('messages__timestamp')
#         ).order_by('-last_message')

#         result = []
#         for convo in conversations:
#             last_message = convo.messages.order_by('-timestamp').first()
#             result.append({
#                 'conv_id': convo.conv_id,
#                 'is_group': convo.is_group,
#                 'title': convo.title,
#                 'last_message': last_message.body if last_message else "",
#                 'timestamp': last_message.timestamp.strftime('%I:%M %p') if last_message else "",
#                 'participants': [
#                     {
#                         'username': p.username.title(),
#                         'userID': p.id,
#                         'avatar_url': p.profile.avatar.url
#                     } for p in convo.participants.exclude(id=self.user.id)
#                 ]
#             })
#         return result


