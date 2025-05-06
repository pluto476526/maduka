# import json
# import logging
# from django.utils.timezone import now
# from channels.generic.websocket import AsyncWebsocketConsumer
# from channels.db import database_sync_to_async
# from konnekt.models import Contact
# import redis

# logger = logging.getLogger(__name__)

# # Redis client setup
# redis_client = redis.StrictRedis(host='localhost', port=6379, db=1, decode_responses=True)


# class OnlineStatusConsumer(AsyncWebsocketConsumer):
#     async def connect(self):
#         """Handles a new WebSocket connection."""
#         if not self.scope["user"].is_authenticated:
#             await self.close()
#             return

#         self.user = self.scope["user"]
#         self.user_id = str(self.user.id)

#         await self._subscribe_user_and_contacts()
#         await self.accept()
#         await self.set_user_online()

#         contact_ids = await self.get_contact_user_ids()
#         statuses = await self.get_contacts_statuses(contact_ids)
#         for status in statuses:
#             await self.send(text_data=json.dumps(status))

#     async def disconnect(self, close_code):
#         """Handles WebSocket disconnection."""
#         await self.set_user_offline()
#         await self._unsubscribe_user_and_contacts()

#     async def receive(self, text_data):
#         """Handles incoming messages."""
#         try:
#             data = json.loads(text_data)
#             if data.get("type") == "get_initial_statuses":
#                 contact_ids = await self.get_contact_user_ids()
#                 statuses = await self.get_contacts_statuses(contact_ids)
#                 await self.send(text_data=json.dumps({
#                     "type": "initial_statuses",
#                     "statuses": statuses
#                 }))
            
#         except json.JSONDecodeError:
#             logger.warning("Failed to decode JSON from WebSocket message.")

#     async def user_status(self, event):
#         """Sends status updates to WebSocket."""
#         await self.send(text_data=json.dumps({
#             "type": event["event_type"],
#             "user_id": event["user_id"],
#             "status": event["status"],
#             "last_seen": event["last_seen"]
#         }))

#     async def _subscribe_user_and_contacts(self):
#         """Subscribes to status updates for the user and their contacts."""
#         await self.channel_layer.group_add(f"user_{self.user_id}_status", self.channel_name)
#         contact_ids = await self.get_contact_user_ids()
#         for contact_id in contact_ids:
#             await self.channel_layer.group_add(f"user_{contact_id}_status", self.channel_name)

#     async def _unsubscribe_user_and_contacts(self):
#         """Unsubscribes from status updates."""
#         await self.channel_layer.group_discard(f"user_{self.user_id}_status", self.channel_name)
#         contact_ids = await self.get_contact_user_ids()
#         for contact_id in contact_ids:
#             await self.channel_layer.group_discard(f"user_{contact_id}_status", self.channel_name)

#     @database_sync_to_async
#     def get_contact_user_ids(self):
#         """Retrieves the IDs of the user's contacts."""
#         return list(Contact.objects.filter(owner=self.user).values_list("contact_id", flat=True))

#     @database_sync_to_async
#     def get_contacts_statuses(self, contact_ids):
#         """Fetches statuses of user's contacts from Redis."""
#         statuses = []
#         for contact_id in contact_ids:
#             key = f"user_status:{contact_id}"
#             data = redis_client.hgetall(key)
#             statuses.append({
#                 "user_id": contact_id,
#                 "status": data.get("status", "offline"),
#                 "last_seen": data.get("last_seen")
#             })
#         return statuses


#     @database_sync_to_async
#     def set_user_online(self):
#         """Marks the user as online in Redis."""
#         timestamp = now().isoformat()
#         key = f"user_status:{self.user_id}"
#         redis_client.hset(key, mapping={
#             "status": "online",
#             "last_seen": timestamp,
#             "last_ping": timestamp
#         })
#         redis_client.expire(key, 300)  # 5-minute TTL

#     @database_sync_to_async
#     def set_user_offline(self):
#         """Marks the user as offline in Redis."""
#         timestamp = now().isoformat()
#         key = f"user_status:{self.user_id}"
#         redis_client.hset(key, mapping={
#             "status": "offline",
#             "last_seen": timestamp
#         })
#         redis_client.expire(key, 300)

#     @database_sync_to_async
#     def update_last_ping(self):
#         """Refreshes the user's last_ping timestamp and TTL."""
#         key = f"user_status:{self.user_id}"
#         redis_client.hset(key, "last_ping", now().isoformat())
#         redis_client.expire(key, 300)






import json
import logging
from django.utils.timezone import now
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from konnekt.models import Contact
import redis

logger = logging.getLogger(__name__)

redis_client = redis.StrictRedis(host='localhost', port=6379, db=1, decode_responses=True)


class OnlineStatusConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        if not self.scope["user"].is_authenticated:
            await self.close()
            return

        self.user = self.scope["user"]
        self.user_id = str(self.user.id)

        await self._subscribe_user_and_contacts()
        await self.accept()
        await self.set_user_online()
        await self.broadcast_status("online")

        contact_ids = await self.get_contact_user_ids()
        statuses = await self.get_contacts_statuses(contact_ids)
        for status in statuses:
            await self.send(text_data=json.dumps(status))

    async def disconnect(self, close_code):
        await self.set_user_offline()
        await self.broadcast_status("offline")
        await self._unsubscribe_user_and_contacts()

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            if data.get("type") == "get_initial_statuses":
                contact_ids = await self.get_contact_user_ids()
                statuses = await self.get_contacts_statuses(contact_ids)
                await self.send(text_data=json.dumps({
                    "type": "initial_statuses",
                    "statuses": statuses
                }))
        except json.JSONDecodeError:
            logger.warning("Failed to decode JSON from WebSocket message.")

    async def user_status(self, event):
        await self.send(text_data=json.dumps({
            "type": event["event_type"],
            "user_id": event["user_id"],
            "status": event["status"],
            "last_seen": event["last_seen"]
        }))

    async def _subscribe_user_and_contacts(self):
        await self.channel_layer.group_add(f"user_{self.user_id}_status", self.channel_name)
        contact_ids = await self.get_contact_user_ids()
        for contact_id in contact_ids:
            await self.channel_layer.group_add(f"user_{contact_id}_status", self.channel_name)

    async def _unsubscribe_user_and_contacts(self):
        await self.channel_layer.group_discard(f"user_{self.user_id}_status", self.channel_name)
        contact_ids = await self.get_contact_user_ids()
        for contact_id in contact_ids:
            await self.channel_layer.group_discard(f"user_{contact_id}_status", self.channel_name)

    async def broadcast_status(self, status):
        """Broadcasts status update to all listening groups."""
        await self.channel_layer.group_send(
            f"user_{self.user_id}_status",
            {
                "type": "user_status",
                "event_type": "status_update",
                "user_id": self.user_id,
                "status": status,
                "last_seen": now().isoformat()
            }
        )

    @database_sync_to_async
    def get_contact_user_ids(self):
        return list(Contact.objects.filter(owner=self.user).values_list("contact_id", flat=True))

    @database_sync_to_async
    def get_contacts_statuses(self, contact_ids):
        statuses = []
        for contact_id in contact_ids:
            key = f"user_status:{contact_id}"
            data = redis_client.hgetall(key)
            statuses.append({
                "user_id": contact_id,
                "status": data.get("status", "offline"),
                "last_seen": data.get("last_seen")
            })
        return statuses

    @database_sync_to_async
    def set_user_online(self):
        timestamp = now().isoformat()
        redis_client.hset(f"user_status:{self.user_id}", mapping={
            "status": "online",
            "last_seen": timestamp
        })

    @database_sync_to_async
    def set_user_offline(self):
        timestamp = now().isoformat()
        redis_client.hset(f"user_status:{self.user_id}", mapping={
            "status": "offline",
            "last_seen": timestamp
        })

