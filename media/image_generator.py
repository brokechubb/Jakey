from typing import Optional
import importlib

try:
    arta_module = importlib.import_module('ai.arta')
    arta_api = getattr(arta_module, 'arta_api', None)
except ImportError:
    arta_api = None


class ImageGenerator:
    def __init__(self):
        self.api = arta_api

    def generate_image(self, prompt: str, model: str = "Flux", width: int = 1024, height: int = 1024,
                      seed: Optional[int] = None, nologo: bool = True) -> str:
        """
        Generate an image using Arta API
        Returns the image URL
        """
        try:
            ratio = self._convert_dimensions_to_ratio(width, height)

            if self.api is not None and hasattr(self.api, 'get_available_styles'):
                available_styles = self.api.get_available_styles()
                style = model if model in available_styles else "SDXL 1.0"
            else:
                style = "SDXL 1.0"

            if self.api is not None and hasattr(self.api, 'generate_image'):
                image_url = self.api.generate_image(
                    prompt=prompt,
                    style=style,
                    ratio=ratio
                )
                return image_url if image_url else "Error: Failed to generate image - API returned no URL"
            else:
                return "Error: Arta API generate_image method not available"
        except Exception as e:
            return f"Error: Failed to generate image with Arta - {str(e)}"

    def _convert_dimensions_to_ratio(self, width: int, height: int) -> str:
        """Convert width/height dimensions to aspect ratio string"""
        def gcd(a, b):
            while b:
                a, b = b, a % b
            return a

        divisor = gcd(width, height)
        simplified_width = width // divisor
        simplified_height = height // divisor

        ratio = f"{simplified_width}:{simplified_height}"

        if self.api is not None and hasattr(self.api, 'get_available_ratios'):
            supported_ratios = self.api.get_available_ratios()
            if ratio in supported_ratios:
                return ratio

        return "1:1"

    def get_available_models(self) -> list:
        """Get list of available image styles from Arta"""
        if self.api is not None and hasattr(self.api, 'get_available_styles'):
            styles = self.api.get_available_styles()
            if styles:
                return styles
        return ["SDXL 1.0"]


image_generator = ImageGenerator()
