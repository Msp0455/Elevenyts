# ==============================================================================
# _thumbnails.py - Cinematic Thumbnail Generator (Elevenyts Ultimate)
# ==============================================================================

import os
import re
import asyncio
import aiohttp
import base64
from PIL import Image, ImageDraw, ImageFilter, ImageFont

from Elevenyts import config
from Elevenyts.helpers import Track


# =========================
# 🔐 DECODE FUNCTION
# =========================
def decode_text(encoded: str) -> str:
    return base64.b64decode(encoded).decode("utf-8")


# =========================
# 🎯 TEXT WIDTH CONTROL
# =========================
def trim_to_width(text: str, font: ImageFont.FreeTypeFont, max_w: int) -> str:
    ellipsis = "…"
    if font.getlength(text) <= max_w:
        return text
    for i in range(len(text) - 1, 0, -1):
        if font.getlength(text[:i] + ellipsis) <= max_w:
            return text[:i] + ellipsis
    return ellipsis


class Thumbnail:
    def __init__(self):
        try:
            self.title_font = ImageFont.truetype(
                "Elevenyts/helpers/Raleway-Bold.ttf", 40)

            self.regular_font = ImageFont.truetype(
                "Elevenyts/helpers/Inter-Light.ttf", 22)

            # 🔥 4X BIG WATERMARK
            self.watermark_font = ImageFont.truetype(
                "Elevenyts/helpers/Raleway-Bold.ttf", 72)

            self.small_font = ImageFont.truetype(
                "Elevenyts/helpers/Inter-Light.ttf", 18)

        except OSError:
            self.title_font = self.regular_font = self.watermark_font = self.small_font = ImageFont.load_default()

    async def save_thumb(self, output_path: str, url: str) -> str:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                with open(output_path, "wb") as f:
                    f.write(await resp.read())
        return output_path

    async def generate(self, song: Track, size=(1280, 720)) -> str:
        try:
            temp = f"cache/temp_{song.id}.jpg"
            output = f"cache/{song.id}_modern.png"

            if os.path.exists(output):
                return output

            await self.save_thumb(temp, song.thumbnail)

            return await asyncio.get_event_loop().run_in_executor(
                None, self._generate_sync, temp, output, song, size
            )

        except Exception:
            return config.DEFAULT_THUMB

    def _generate_sync(self, temp: str, output: str, song: Track, size=(1280, 720)) -> str:
        try:
            with Image.open(temp) as temp_img:
                base = temp_img.resize(size).convert("RGBA")

            bg = base.filter(ImageFilter.GaussianBlur(3))
            draw = ImageDraw.Draw(bg)

            # =========================
            # 🔐 ENCODED WATERMARK
            # =========================
            left_encoded = "QVJUSVNU"          # ARTIST
            right_encoded = "RUxFVkVOWVRT"     # ELEVENYTS

            left_text = decode_text(left_encoded)
            right_text = decode_text(right_encoded)

            # =========================
            # 🌈 GRADIENT TEXT + BG
            # =========================
            def draw_gradient_text_with_bg(draw, position, text, font):
                x, y = position

                text_w = font.getlength(text)
                text_h = font.size

                padding_x = 20
                padding_y = 10

                bg_box = [
                    x - padding_x,
                    y - padding_y,
                    x + text_w + padding_x,
                    y + text_h + padding_y
                ]

                draw.rounded_rectangle(
                    bg_box,
                    radius=20,
                    fill=(0, 0, 0, 150)
                )

                colors = [(255, 0, 150), (0, 200, 255), (255, 200, 0)]

                for i, char in enumerate(text):
                    color = colors[i % len(colors)]
                    draw.text((x, y), char, font=font, fill=color)
                    x += font.getlength(char)

            # LEFT WATERMARK
            draw_gradient_text_with_bg(draw, (40, 30), left_text, self.watermark_font)

            # RIGHT WATERMARK (👇 niche)
            text_w = self.watermark_font.getlength(right_text)
            draw_gradient_text_with_bg(
                draw,
                (1280 - text_w - 40, 90),
                right_text,
                self.watermark_font
            )

            # =========================
            # 🌑 BOTTOM GRADIENT
            # =========================
            gradient = Image.new("L", (1, 300))
            for y in range(300):
                gradient.putpixel((0, y), int(255 * (y / 300)))

            alpha_gradient = gradient.resize((1280, 300))
            black_img = Image.new("RGBA", (1280, 300), (0, 0, 0, 200))
            black_img.putalpha(alpha_gradient)

            bg.paste(black_img, (0, 420), black_img)

            # =========================
            # 🖼️ THUMB PREVIEW
            # =========================
            thumb = base.resize((180, 180))
            mask = Image.new("L", thumb.size, 0)
            ImageDraw.Draw(mask).rounded_rectangle((0, 0, 180, 180), 25, fill=255)
            bg.paste(thumb, (60, 450), mask)

            # =========================
            # 🎵 TITLE + META
            # =========================
            clean_title = re.sub(r"\W+", " ", song.title).title()

            draw.text(
                (260, 470),
                trim_to_width(clean_title, self.title_font, 800),
                fill="white",
                font=self.title_font
            )

            draw.text(
                (260, 530),
                f"YouTube • {song.view_count or 'Unknown'}",
                fill="lightgray",
                font=self.regular_font
            )

            # =========================
            # ⏳ PROGRESS BAR
            # =========================
            BAR_X = 260
            BAR_Y = 600

            draw.line([(BAR_X, BAR_Y), (BAR_X + 500, BAR_Y)], fill="gray", width=5)
            draw.line([(BAR_X, BAR_Y), (BAR_X + 220, BAR_Y)], fill="red", width=6)

            draw.ellipse([
                (BAR_X + 220 - 8, BAR_Y - 8),
                (BAR_X + 220 + 8, BAR_Y + 8)
            ], fill="red")

            draw.text((BAR_X, BAR_Y + 15), "00:00", fill="white", font=self.small_font)

            end_text = getattr(song, 'duration', '00:00')
            draw.text((BAR_X + 430, BAR_Y + 15), end_text, fill="white", font=self.small_font)

            # =========================
            # 💾 SAVE
            # =========================
            bg.save(output)

            try:
                os.remove(temp)
            except OSError:
                pass

            return output

        except Exception:
            return config.DEFAULT_THUMB
