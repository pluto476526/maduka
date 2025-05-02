import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils.timezone import now
from konnekt.models import UserStatus, Contact

logger = logging.getLogger(__name__)

# class OnlineStatusConsumer(AsyncWebsocketConsumer):
#     async def connect(self):
#         if not self.scope["user"].is_authenticated:
#             await self.close()
#             return

#         self.user = self.scope["user"]
#         self.group_name = f"user_{self.user.id}"

#         await self.accept()
#         await self.set_user_online()

#         # Join the user's notification group
#         await self.channel_layer.group_add(self.group_name, self.channel_name)

#         # Send current status to the user (self)
#         await self.send(text_data=json.dumps({
#             "user_id": self.user.id,
#             "username": self.user.username,
#             "status": "online",
#             "last_seen": None
#         }))

#         # Add contacts' groups and send their status updates
#         contact_ids = await self.get_contact_user_ids()
#         for contact_id in contact_ids:
#             await self.channel_layer.group_add(f"contact_{contact_id}", self.channel_name)

#         # Get and send contact statuses
#         contact_statuses = await self.get_contacts_statuses()
#         for c in contact_statuses:
#             await self.send(text_data=json.dumps(c))

#     async def disconnect(self, code):
#         await self.set_user_offline()
#         await self.channel_layer.group_discard(self.group_name, self.channel_name)

#         contact_ids = await self.get_contact_user_ids()
#         for contact_id in contact_ids:
#             await self.channel_layer.group_discard(f"contact_{contact_id}", self.channel_name)

#         # Send "offline" status to the contacts
#         await self.broadcast_status("offline")

#     async def receive(self, text_data):
#         try:
#             data = json.loads(text_data)
#             if data.get("type") == "ping":
#                 await self.update_last_ping()
#         except Exception as e:
#             logger.error(f"Receive error: {e}")

#     async def broadcast_status(self, status):
#         # Notify all contacts about this user's status
#         # This will send only to contacts that are online and connected
#         contact_ids = await self.get_contact_user_ids()
#         for contact_id in contact_ids:
#             await self.channel_layer.group_send(
#                 f"contact_{contact_id}",
#                 {
#                     "type": "user_status",
#                     "user_id": self.user.id,
#                     "username": self.user.username,
#                     "status": status,
#                     "last_seen": now().isoformat() if status == "offline" else None
#                 }
#             )

#     async def user_status(self, event):
#         # This will send status updates to the user
#         await self.send(text_data=json.dumps(event))

#     @database_sync_to_async
#     def get_contact_user_ids(self):
#         # Get list of contact user IDs for the current user
#         return list(Contact.objects.filter(owner=self.user, is_deleted=False).values_list("contact_id", flat=True))

#     @database_sync_to_async
#     def get_contacts_statuses(self):
#         # Retrieve the status of each contact
#         contacts = Contact.objects.filter(owner=self.user, is_deleted=False).select_related("contact")
#         statuses = []
#         for rel in contacts:
#             contact = rel.contact
#             try:
#                 status = UserStatus.objects.get(user=contact)
#                 statuses.append({
#                     "user_id": contact.id,
#                     "username": contact.username,
#                     "status": "online" if status.is_online else "offline",
#                     "last_seen": status.last_seen.isoformat() if status.last_seen else None
#                 })
#             except UserStatus.DoesNotExist:
#                 statuses.append({
#                     "user_id": contact.id,
#                     "username": contact.username,
#                     "status": "offline",
#                     "last_seen": None
#                 })
#         return statuses

#     @database_sync_to_async
#     def set_user_online(self):
#         # Mark the current user as online
#         obj, _ = UserStatus.objects.get_or_create(user=self.user)
#         obj.is_online = True
#         obj.last_seen = now()
#         obj.last_ping = now()
#         obj.save()

#     @database_sync_to_async
#     def set_user_offline(self):
#         # Mark the current user as offline
#         obj, _ = UserStatus.objects.get_or_create(user=self.user)
#         obj.is_online = False
#         obj.last_seen = now()
#         obj.save()

#     @database_sync_to_async
#     def update_last_ping(self):
#         # Update the last ping time for the user
#         UserStatus.objects.filter(user=self.user).update(last_ping=now())





class OnlineStatusConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        if not self.scope["user"].is_authenticated:
            await self.close()
            return

        self.user = self.scope["user"]
        self.user_id = str(self.user.id)
        
        # Join user's personal status group
        await self.channel_layer.group_add(
            f"user_{self.user_id}_status",
            self.channel_name
        )
        
        # Join groups for all contacts (users I'm watching)
        contact_ids = await self.get_contact_user_ids()
        for contact_id in contact_ids:
            await self.channel_layer.group_add(
                f"user_{contact_id}_status",
                self.channel_name
            )
        
        await self.accept()
        await self.set_user_online()
        
        # Send current status of all contacts
        contact_statuses = await self.get_contacts_statuses()
        for status in contact_statuses:
            await self.send(text_data=json.dumps(status))

    async def disconnect(self, close_code):
        await self.set_user_offline()
        
        # Leave all groups
        await self.channel_layer.group_discard(
            f"user_{self.user_id}_status",
            self.channel_name
        )
        
        contact_ids = await self.get_contact_user_ids()
        for contact_id in contact_ids:
            await self.channel_layer.group_discard(
                f"user_{contact_id}_status",
                self.channel_name
            )

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            if data.get("type") == "ping":
                logger.info(f"[PING] Received ping from user {self.user_id}")
                await self.update_last_ping()

                # Broadcast status update to all watchers
                await self.channel_layer.group_send(
                    f"user_{self.user_id}_status",
                    {
                        "type": "user.status",  # Django internal handler
                        "event_type": "status.update",  # send this to client
                        "user_id": self.user_id,
                        "status": "online",
                        "last_seen": now().isoformat()
                    }
                )
        except json.JSONDecodeError:
            pass

    async def user_status(self, event):
        logger.info(f"[STATUS] Sending status update to clients: {event}")
        await self.send(text_data=json.dumps({
            "type": event["event_type"],
            "user_id": event["user_id"],
            "status": event["status"],
            "last_seen": event["last_seen"]
        }))

    @database_sync_to_async
    def get_contact_user_ids(self):
        """Get IDs of users I'm watching (my contacts)"""
        return list(Contact.objects.filter(owner=self.user)
                    .values_list('contact_id', flat=True))

    @database_sync_to_async
    def get_contacts_statuses(self):
        """Get current status of all my contacts"""
        contacts = Contact.objects.filter(owner=self.user).select_related("contact")
        statuses = []
        
        for contact_rel in contacts:
            contact = contact_rel.contact
            try:
                status = UserStatus.objects.get(user=contact)
                statuses.append({
                    "user_id": str(contact.id),
                    "username": contact.username,
                    "status": "online" if status.is_online else "offline",
                    "last_seen": status.last_seen.isoformat() if status.last_seen else None
                })
            except UserStatus.DoesNotExist:
                statuses.append({
                    "user_id": str(contact.id),
                    "username": contact.username,
                    "status": "offline",
                    "last_seen": None
                })
        return statuses

    @database_sync_to_async
    def set_user_online(self):
        obj, created = UserStatus.objects.get_or_create(user=self.user)
        obj.is_online = True
        obj.last_seen = now()
        obj.last_ping = now()
        obj.save()

    @database_sync_to_async
    def set_user_offline(self):
        obj, created = UserStatus.objects.get_or_create(user=self.user)
        obj.is_online = False
        obj.last_seen = now()
        obj.save()

    @database_sync_to_async
    def update_last_ping(self):
        UserStatus.objects.filter(user=self.user).update(last_ping=now())