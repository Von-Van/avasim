"""
Texture generation utilities for fantasy RPG UI.
Generates textures programmatically and converts them to base64 data URIs for QSS embedding.
"""

import base64
import random
from io import BytesIO
from PySide6.QtGui import QImage, QPainter, QColor, QPen, QBrush
from PySide6.QtCore import Qt, QByteArray, QBuffer


class TextureGenerator:
    """Generates textures for fantasy RPG UI elements."""

    @staticmethod
    def generate_parchment_texture(width: int = 200, height: int = 200,
                                   base_color: QColor = QColor(232, 220, 196)) -> str:
        """
        Generate a subtle parchment/paper texture.

        Args:
            width: Texture width in pixels
            height: Texture height in pixels
            base_color: Base parchment color

        Returns:
            Base64 encoded data URI string for CSS embedding
        """
        img = QImage(width, height, QImage.Format_ARGB32)
        img.fill(base_color)

        painter = QPainter(img)
        painter.setRenderHint(QPainter.Antialiasing, True)

        # Add subtle noise/grain for aged paper effect
        random.seed(42)  # Consistent pattern
        for _ in range(width * height // 8):
            x = random.randint(0, width - 1)
            y = random.randint(0, height - 1)
            # Vary opacity for more natural look
            opacity = random.randint(5, 25)
            noise_color = QColor(0, 0, 0, opacity)
            painter.setPen(noise_color)
            painter.drawPoint(x, y)

        # Add some lighter spots for variation
        for _ in range(width * height // 20):
            x = random.randint(0, width - 1)
            y = random.randint(0, height - 1)
            opacity = random.randint(5, 15)
            light_color = QColor(255, 255, 255, opacity)
            painter.setPen(light_color)
            painter.drawPoint(x, y)

        # Add subtle horizontal lines (like paper fibers)
        painter.setPen(QPen(QColor(0, 0, 0, 8), 1))
        for i in range(0, height, random.randint(15, 25)):
            y_offset = i + random.randint(-2, 2)
            painter.drawLine(0, y_offset, width, y_offset)

        painter.end()

        return TextureGenerator._image_to_base64_uri(img)

    @staticmethod
    def generate_stone_texture(width: int = 200, height: int = 200,
                               base_color: QColor = QColor(45, 37, 25)) -> str:
        """
        Generate a dark stone/leather texture for panels.

        Args:
            width: Texture width in pixels
            height: Texture height in pixels
            base_color: Base stone color

        Returns:
            Base64 encoded data URI string for CSS embedding
        """
        img = QImage(width, height, QImage.Format_ARGB32)
        img.fill(base_color)

        painter = QPainter(img)
        painter.setRenderHint(QPainter.Antialiasing, True)

        # Add darker and lighter spots for stone texture
        random.seed(123)
        for _ in range(width * height // 6):
            x = random.randint(0, width - 1)
            y = random.randint(0, height - 1)
            size = random.randint(1, 3)

            # Randomly darker or lighter
            if random.random() > 0.5:
                opacity = random.randint(10, 40)
                spot_color = QColor(0, 0, 0, opacity)
            else:
                opacity = random.randint(10, 30)
                spot_color = QColor(255, 255, 255, opacity)

            painter.setBrush(QBrush(spot_color))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(x, y, size, size)

        # Add some texture lines (like leather grain)
        painter.setPen(QPen(QColor(0, 0, 0, 15), 1))
        for i in range(0, height, random.randint(10, 20)):
            y_offset = i + random.randint(-3, 3)
            x_start = random.randint(0, 20)
            x_end = width - random.randint(0, 20)
            painter.drawLine(x_start, y_offset, x_end, y_offset)

        painter.end()

        return TextureGenerator._image_to_base64_uri(img)

    @staticmethod
    def generate_wood_grain(width: int = 200, height: int = 200,
                           base_color: QColor = QColor(61, 50, 38)) -> str:
        """
        Generate a wood grain texture for decorative elements.

        Args:
            width: Texture width in pixels
            height: Texture height in pixels
            base_color: Base wood color

        Returns:
            Base64 encoded data URI string for CSS embedding
        """
        img = QImage(width, height, QImage.Format_ARGB32)
        img.fill(base_color)

        painter = QPainter(img)
        painter.setRenderHint(QPainter.Antialiasing, True)

        # Add horizontal wood grain lines
        random.seed(456)
        for i in range(0, height, random.randint(5, 12)):
            y_offset = i + random.randint(-2, 2)
            opacity = random.randint(15, 40)

            # Alternate between darker and lighter lines
            if (i // 10) % 2 == 0:
                grain_color = QColor(0, 0, 0, opacity)
            else:
                grain_color = QColor(255, 255, 255, opacity // 2)

            painter.setPen(QPen(grain_color, random.randint(1, 2)))

            # Wavy line for natural grain
            y_wave = y_offset
            for x in range(0, width, 5):
                y_next = y_offset + random.randint(-1, 1)
                painter.drawLine(x, y_wave, x + 5, y_next)
                y_wave = y_next

        # Add some knots (darker circles)
        for _ in range(random.randint(2, 4)):
            x = random.randint(20, width - 20)
            y = random.randint(20, height - 20)
            radius = random.randint(5, 15)

            painter.setBrush(QBrush(QColor(0, 0, 0, 30)))
            painter.setPen(QPen(QColor(0, 0, 0, 50), 1))
            painter.drawEllipse(x - radius, y - radius, radius * 2, radius * 2)

        painter.end()

        return TextureGenerator._image_to_base64_uri(img)

    @staticmethod
    def generate_subtle_noise(width: int = 100, height: int = 100,
                             opacity: int = 10) -> str:
        """
        Generate a very subtle noise texture for overlay effects.

        Args:
            width: Texture width in pixels
            height: Texture height in pixels
            opacity: Noise opacity (0-255)

        Returns:
            Base64 encoded data URI string for CSS embedding
        """
        img = QImage(width, height, QImage.Format_ARGB32)
        img.fill(Qt.transparent)

        painter = QPainter(img)

        # Very subtle random noise
        random.seed(789)
        for _ in range(width * height // 4):
            x = random.randint(0, width - 1)
            y = random.randint(0, height - 1)

            if random.random() > 0.5:
                painter.setPen(QColor(0, 0, 0, opacity))
            else:
                painter.setPen(QColor(255, 255, 255, opacity))

            painter.drawPoint(x, y)

        painter.end()

        return TextureGenerator._image_to_base64_uri(img)

    @staticmethod
    def _image_to_base64_uri(image: QImage) -> str:
        """
        Convert QImage to base64 data URI for CSS embedding.

        Args:
            image: QImage to convert

        Returns:
            Base64 data URI string (e.g., "data:image/png;base64,...")
        """
        byte_array = QByteArray()
        buffer = QBuffer(byte_array)
        buffer.open(QBuffer.WriteOnly)
        image.save(buffer, "PNG")
        buffer.close()

        base64_data = base64.b64encode(byte_array.data()).decode('utf-8')
        return f"data:image/png;base64,{base64_data}"


# Cache for generated textures (avoid regenerating on every theme call)
_texture_cache = {}


def get_cached_texture(texture_name: str, generator_func, *args, **kwargs) -> str:
    """
    Get a texture from cache or generate it if not cached.

    Args:
        texture_name: Unique name for this texture
        generator_func: Function to call if texture needs to be generated
        *args, **kwargs: Arguments to pass to generator function

    Returns:
        Base64 data URI string
    """
    if texture_name not in _texture_cache:
        _texture_cache[texture_name] = generator_func(*args, **kwargs)
    return _texture_cache[texture_name]


def clear_texture_cache():
    """Clear the texture cache (useful for testing or theme changes)."""
    global _texture_cache
    _texture_cache = {}
