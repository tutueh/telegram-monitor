import io
import logging
from PIL import Image
import pytesseract

logger = logging.getLogger(__name__)

class OCRProcessor:
    def __init__(self):
        self.configs = ['--psm 6', '--psm 7', '--psm 8']

    async def process_image(self, client, media):
        try:
            image_buffer = io.BytesIO()
            await client.download_media(media, file=image_buffer)
            image_buffer.seek(0)  # Fix para PIL

            image = Image.open(image_buffer)
            if image.mode != 'RGB':
                image = image.convert('RGB')

            for config in self.configs:
                try:
                    text = pytesseract.image_to_string(image, config=config)
                    if text.strip():
                        return text.strip()
                except pytesseract.TesseractError:
                    continue

            return None

        except Exception as e:
            logger.error(f"OCR processing failed: {e}")
            return None
