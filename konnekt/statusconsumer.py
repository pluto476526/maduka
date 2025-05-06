import json
import logging
import asyncio
import redis
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils.timezone import now
from konnekt.models import Contact

logger = logging.getLogger(__name__)

redis_client = redis.StrictRedis(host='localhost', port=6379, db=1, decode_responses=True)

class OnlineStatusConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        if not self.scope["user"].is_authenticated:
            await self.close()
            return

        self.user = self.scope["user"]
        self.user_id = str(self.user.id)

        await self.channel_layer.group_add(
            f"user_{self.user_id}_status",
            self.channel_name
        )

        contact_ids = await self.get_contact_user_ids()
        for contact_id in contact_ids:
            await self.channel_layer.group_add(
                f"user_{contact_id}_status",
                self.channel_name
            )

        await self.accept()
        await self.set_user_online()

        statuses = await self.get_contacts_statuses(contact_ids)
        for status in statuses:
            await self.send(text_data=json.dumps(status))

    async def disconnect(self, close_code):
        await self.set_user_offline()

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

            if data.get("type") == "get_initial_statuses":
                contact_ids = await self.get_contact_user_ids()
                statuses = await self.get_contacts_statuses(contact_ids)
                await self.send(text_data=json.dumps({
                    "type": "initial_statuses",
                    "statuses": statuses
                }))

        except json.JSONDecodeError:
            pass

    async def user_status(self, event):
        await self.send(text_data=json.dumps({
            "type": event["event_type"],
            "user_id": event["user_id"],
            "status": event["status"],
            "last_seen": event["last_seen"]
        }))

    @database_sync_to_async
    def get_contact_user_ids(self):
        return list(Contact.objects.filter(owner=self.user).values_list("contact_id", flat=True))

    @database_sync_to_async
    def get_contacts_statuses(self, contact_ids):
        statuses = []
        for contact_id in contact_ids:
            data = redis_client.hgetall(f"user_status:{contact_id}")
            statuses.append({
                "user_id": contact_id,
                "status": data.get("status", "offline"),
                "last_seen": data.get("last_seen")
            })
        return statuses

    @database_sync_to_async
    def set_user_online(self):
        timestamp = now().isoformat()
        key = f"user_status:{self.user_id}"
        redis_client.hmset(key, {
            "status": "online",
            "last_seen": timestamp,
            "last_ping": timestamp
        })
        redis_client.expire(key, 300)  # 5 minutes TTL

    @database_sync_to_async
    def set_user_offline(self):
        timestamp = now().isoformat()
        key = f"user_status:{self.user_id}"
        redis_client.hmset(key, {
            "status": "offline",
            "last_seen": timestamp
        })
        redis_client.expire(key, 300)  # Optional: still expire the record

    @database_sync_to_async
    def update_last_ping(self):
        key = f"user_status:{self.user_id}"
        redis_client.hset(key, "last_ping", now().isoformat())
        redis_client.expire(key, 300)  # Refresh TTL on ping
