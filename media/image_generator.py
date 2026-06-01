import urllib.parse
from typing import Optional
import importlib
import requests

try:
    arta_module = importlib.import_module('ai.arta')
    arta_api = getattr(arta_module, 'arta_api', None)
except ImportError:
    arta_api = None

POLLINATIONS_IMAGE_BASE = "https://image.pollinations.ai/prompt"

POLLINATIONS_MODELS = {
    "flux": "flux",
    "any": "any",
    "realistic": "realistic",
    "anime": "anime",
    "art": "art",
    "painting": "painting",
    "scenery": "scenery",
    "portrait": "portrait",
    "Photographic": "realistic",
    "Cinematic Art": "cinematic",
    "Professional": "realistic",
    "Surrealism": "surreal",
    "Watercolor": "watercolor",
    "Biomech": "3d",
    "Black Ink": "dark",
    "Flame design": "fire",
    "Neo-Traditional": "traditional",
    "Pixel Style": "pixel-art",
    "Clay Style": "clay",
    "Cute Cartoon Style": "cartoon",
    "Illustration Style": "illustration",
    "Stickers Style": "sticker",
}


class ImageGenerator:
    def __init__(self):
        self.api = arta_api
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "JakeySelfBot/1.0"
        })

    def generate_image(self, prompt: str, model: str = "Flux", width: int = 1024, height: int = 1024,
                      seed: Optional[int] = None, nologo: bool = True) -> str:
        """
        Generate an image using Arta API with Pollinations fallback
        Returns the image URL
        """
        result = self._generate_with_arta(prompt, model, width, height)
        if not result.startswith("Error:"):
            return result

        result = self._generate_with_pollinations(prompt, model, width, height, seed, nologo)
        if not result.startswith("Error:"):
            return result

        return "Error: Image generation failed - both Arta and Pollinations APIs are unavailable."

    def _generate_with_arta(self, prompt: str, model: str, width: int, height: int) -> str:
        """Generate image using Arta API"""
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

    def _generate_with_pollinations(self, prompt: str, model: str, width: int, height: int,
                                    seed: Optional[int] = None, nologo: bool = True) -> str:
        """Generate image using Pollinations API as fallback"""
        try:
            pollinations_model = POLLINATIONS_MODELS.get(model, "flux")

            params = {
                "width": width,
                "height": height,
                "model": pollinations_model,
                "nologo": str(nologo).lower(),
            }
            if seed is not None:
                params["seed"] = seed

            encoded_prompt = urllib.parse.quote(prompt)
            url = f"{POLLINATIONS_IMAGE_BASE}/{encoded_prompt}.png?{urllib.parse.urlencode(params)}"

            resp = self.session.head(url, timeout=10)
            if resp.status_code < 500:
                return url

            return f"Error: Pollinations API returned status {resp.status_code}"
        except Exception as e:
            return f"Error: Failed to generate image with Pollinations - {str(e)}"

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
        """Get list of available image styles"""
        arta_styles = []
        if self.api is not None:
            if hasattr(self.api, 'get_available_styles'):
                arta_styles = self.api.get_available_styles()

        combined = list(arta_styles)
        for name in POLLINATIONS_MODELS:
            if name not in combined:
                combined.append(name)
        return combined if combined else ["SDXL 1.0", "flux", "realistic", "anime"]


image_generator = ImageGenerator()
