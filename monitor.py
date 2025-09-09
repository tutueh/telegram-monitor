import os
import asyncio
import logging
from telethon import TelegramClient, events
from db import Database
from ocr import OCRProcessor

logger = logging.getLogger(__name__)

class TelegramMonitor:
    BRANDS = [
        'apple', 'samsung', 'nike', 'adidas', 'paypal', 'amazon', 
        'netflix', 'visa', 'mastercard', 'microsoft', 'google', 'facebook'
    ]

    def __init__(self, api_id, api_hash, phone, db_path):
        self.api_id = int(api_id)
        self.api_hash = api_hash
        self.phone = phone

        session_path = os.path.join(os.path.dirname(db_path), 'session')
        self.client = TelegramClient(session_path, self.api_id, self.api_hash)
        self.db = Database(db_path)
        self.ocr = OCRProcessor()
        self.monitored_groups = []

    def find_brand_mentions(self, text):
        if not text:
            return None
        text_lower = text.lower()
        for brand in self.BRANDS:
            if brand in text_lower:
                return brand
        return None

    async def setup_monitoring(self):
        try:
            await self.client.start(phone=self.phone)
            logger.info("Connected to Telegram")

            dialogs = await self.client.get_dialogs()
            groups = [d for d in dialogs if d.is_group or d.is_channel]

            if not groups:
                logger.warning("No groups found")
                return False

            print("Available groups:")
            for i, group in enumerate(groups, 1):
                print(f"{i}. {group.name}")

            selection = input("Select groups (comma-separated numbers): ")
            for num in selection.split(','):
                try:
                    idx = int(num.strip()) - 1
                    if 0 <= idx < len(groups):
                        self.monitored_groups.append(groups[idx].id)
                        logger.info(f"Added group: {groups[idx].name}")
                except ValueError:
                    pass

            return len(self.monitored_groups) > 0

        except Exception as e:
            logger.error(f"Setup failed: {e}")
            return False

    async def start_monitoring(self):
        if not self.monitored_groups:
            if not await self.setup_monitoring():
                return

        @self.client.on(events.NewMessage(chats=self.monitored_groups))
        async def message_handler(event):
            try:
                chat = await event.get_chat()
                sender = await event.get_sender()

                db_id = self.db.save_message(
                    event.id,
                    event.chat_id,
                    chat.title,
                    sender.id if sender else None,
                    event.text or "",
                    bool(event.media)
                )

                logger.debug(f"Message from {chat.title}: {(event.text or 'media')[:50]}")

                if event.text:
                    brand = self.find_brand_mentions(event.text)
                    if brand:
                        self.db.save_alert(db_id, event.chat_id, 'text', brand, event.text)
                        logger.warning(f"Brand detected: {brand} in {chat.title}")

                if event.media and hasattr(event.media, 'photo'):
                    ocr_text = await self.ocr.process_image(self.client, event.media)
                    if ocr_text:
                        brand = self.find_brand_mentions(ocr_text)
                        if brand:
                            self.db.save_alert(db_id, event.chat_id, 'image', brand, ocr_text)
                            logger.warning(f"Brand in image: {brand} in {chat.title}")

            except Exception as e:
                logger.error(f"Message handler error: {e}")

        logger.info(f"Monitoring {len(self.monitored_groups)} groups")
        await self.client.run_until_disconnected()
