import re
import time
from typing import List, Optional

import requests

from utils.logging_config import get_logger

logger = get_logger(__name__)


class ArtaAPI:
    def __init__(self):
        self.base_url = "https://img-gen-prod.ai-arta.com/api/v1"
        self.auth_url = (
            "https://www.googleapis.com/identitytoolkit/v3/relyingparty/signupNewUser"
        )
        from config import ARTA_API_KEY

        self.api_key = ARTA_API_KEY

        # Available styles — fetched dynamically from the API (May 2026)
        self.styles = [
            "3D Logo", "3D Logo 2", "3d Render Style",
            "Abstract Logo", "Abstract Logo 2",
            "Anime tattoo", "Arcane Style",
            "Biomech", "Black Ink",
            "Chicano", "Christmas Doll Nano Style",
            "Christmas Postcard Nano Style", "Christmas Poster Nano Style",
            "Cinematic Filmstill Style", "Clay Style", "Coloring Book Style",
            "Combination Logo", "Combination Logo 2",
            "Crochet Amigurumi Style", "Cute Cartoon Style",
            "Death metal", "Devil Maycry Style", "Doll Nano Style", "Dotwork",
            "Elegant Logo", "Elegant Logo 2",
            "Emblem Logo", "Emblem Logo 2", "Embroidery tattoo", "Emoji Style",
            "Epic Logo", "Epic Logo 2",
            "F Dev", "F Pro",
            "F2 Analog Style", "F2 Klein 4B", "F2 Klein 9B",
            "F2 Logos Style", "F2 Pro", "F2 Turbo",
            "Film Grain Style", "Flame design", "Flux",
            "Futuristic Logo", "Futuristic Logo 2",
            "GPT4o", "GPT4o Ghibli",
            "Geometric Logo", "Geometric Logo 2",
            "Ghost Mannequin Style", "Gradient Logo", "Gradient Logo 2",
            "Graffiti", "Grunge Logo", "Grunge Logo 2",
            "Hand-drawn Logo", "Hand-drawn Logo 2", "High GPT4o", "Hunyuan Style",
            "Icons Style", "Isometric Flux Style",
            "Japanese_2",
            "Kawaii",
            "Low Poly",
            "Mascots Logo", "Mascots Logo 2", "Medieval",
            "Memes Style", "Mikkoph Style", "Mini tattoo",
            "Minimalistic Logo", "Minimalistic Logo 2",
            "Monogram Logo", "Monogram Logo 2",
            "Nano Banana 2 Style", "Nano Banana Pro Style", "Nano Banana Style",
            "Neo-traditional", "New School",
            "Old School", "Old school colored",
            "On limbs black", "On limbs color",
            "Phone Case Style", "Polaroid Style",
            "Postcard Nano Style", "Poster Nano Style", "Professional",
            "Random Text", "Realistic tattoo", "Red and Black", "RevAnimated",
            "Seedream Test", "Snapchat Style", "Stickers Style",
            "Studio Ghibli Style", "Surrealism",
            "Trash Polka",
            "Vincent Van Gogh",
            "Watercolor",
            "our_hunyuan_t2i", "our_hunyuan_t2i_1", "our_hunyuan_t2i_2", "our_hunyuan_t2i_3",
            "qa_t2i_test_gpt_image_2_v3", "qa_t2i_test_gpt_image_2_v5",
            "qa_t2i_test_gpt_image_2_v6", "qa_t2i_test_gpt_image_2_v7",
            "test_qa_t2i_our_flux2_klein_4b_1", "test_qa_t2i_our_flux2_klein_9b_1",
        ]

        # Available ratios from the arta.go file
        self.ratios = [
            "1:1",
            "2:3",
            "3:2",
            "3:4",
            "4:3",
            "9:16",
            "16:9",
            "9:21",
            "21:9",
        ]

    def generate_auth_token(self) -> Optional[str]:
        """
        Generate an authentication token using Firebase
        """
        try:
            url = f"{self.auth_url}?key={self.api_key}"
            headers = {
                "X-Android-Cert": "ADC09FCA89A2CE4D0D139031A2A587FA87EE4155",
                "X-Firebase-Gmpid": "1:713239656559:android:f9e37753e9ee7324cb759a",
                "X-Firebase-Client": "H4sIAAAAAAAA_6tWykhNLCpJSk0sKVayio7VUSpLLSrOzM9TslIyUqoFAFyivEQfAAAA",
                "X-Client-Version": "Android/Fallback/X22003001/FirebaseCore-Android",
                "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 15;)",
                "X-Android-Package": "ai.generated.art.maker.image.picture.photo.generator.painting",
                "Content-Type": "application/json",
            }

            payload = {"clientType": "CLIENT_TYPE_ANDROID"}

            response = requests.post(url, headers=headers, json=payload, timeout=15)
            response.raise_for_status()

            data = response.json()
            return data.get("idToken")

        except requests.exceptions.RequestException as e:
            logger.error(f"Error generating auth token: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error generating auth token: {e}")
            return None

    def generate_image(
        self,
        prompt: str,
        style: str = "Flux",
        ratio: str = "1:1",
        negative_prompt: str = "",
        count: str = "1",
        steps: str = "40",
    ) -> Optional[str]:
        """
        Generate an image using Arta API and return the image URL
        """
        try:
            # Sanitize prompt to remove special characters that might cause API errors
            # More comprehensive sanitization that preserves common punctuation but removes problematic characters
            sanitized_prompt = re.sub(
                r"[\x00-\x1f\x7f-\x9f]", "", prompt
            )  # Remove control characters
            sanitized_prompt = re.sub(
                r"[^\w\s.,!?\'\"@#\$%\^&*()\[\]{}\-:;/\\]", " ", sanitized_prompt
            )  # Keep common chars
            sanitized_prompt = re.sub(
                r"\s+", " ", sanitized_prompt
            ).strip()  # Normalize whitespace

            if sanitized_prompt != prompt:
                logger.info(f"Sanitized prompt: '{prompt}' -> '{sanitized_prompt}'")

            # Generate auth token
            token = self.generate_auth_token()
            if not token:
                logger.error("Failed to generate authentication token")
                return None

            # Validate style
            if style not in self.styles:
                logger.warning(f"Invalid style '{style}', using default 'SDXL 1.0'")
                style = "SDXL 1.0"

            # Validate ratio
            if ratio not in self.ratios:
                logger.warning(f"Invalid ratio '{ratio}', using default '1:1'")
                ratio = "1:1"

            # Prepare the image generation request
            url = f"{self.base_url}/text2image"
            headers = {
                "Authorization": token,
                "User-Agent": "AiArt/4.18.6 okHttp/4.12.0 Android R",
            }

            # Prepare form data as a dictionary (requests will handle multipart encoding)
            data = {
                "prompt": sanitized_prompt,
                "negative_prompt": negative_prompt,
                "style": style,
                "images_num": count,
                "cfg_scale": "7",
                "steps": steps,
                "aspect_ratio": ratio,
            }

            # Make the initial request to start image generation
            response = requests.post(url, headers=headers, data=data, timeout=30)
            response.raise_for_status()

            status_data = response.json()
            record_id = status_data.get("record_id")

            if not record_id:
                logger.error("Failed to get record_id from image generation request")
                return None

            # Poll for image generation status
            image_url = self._poll_for_image(record_id, token)
            return image_url

        except requests.exceptions.RequestException as e:
            response_body = ""
            if e.response is not None:
                try:
                    response_body = e.response.text[:500]
                except Exception:
                    pass
            logger.error(f"Error generating image: {e} | Response: {response_body}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error generating image: {e}")
            return None

    def _poll_for_image(self, record_id: str, token: str) -> Optional[str]:
        """
        Poll for image generation status and return the image URL when ready
        """
        url = f"{self.base_url}/text2image/{record_id}/status"
        headers = {
            "Authorization": token,
            "User-Agent": "AiArt/3.23.12 okHttp/4.12.0 Android VANILLA_ICE_CREAM",
        }

        # Poll for up to 5 minutes (300 seconds)
        max_wait_time = 300
        poll_interval = 5
        start_time = time.time()

        while time.time() - start_time < max_wait_time:
            try:
                response = requests.get(url, headers=headers, timeout=15)
                response.raise_for_status()

                status_data = response.json()
                status = status_data.get("status", "").upper()

                if status == "DONE":
                    # Image generation complete, return the first image URL
                    images = status_data.get("response", [])
                    if images:
                        return images[0].get("url")
                    else:
                        logger.error("No images found in response")
                        return None

                elif status in ["FAILED", "ERROR"]:
                    # Image generation failed
                    error_details = status_data.get("detail", [])
                    if error_details:
                        error_msg = error_details[0].get("msg", "Unknown error")
                        logger.error(f"Image generation failed: {error_msg}")
                    else:
                        logger.error("Image generation failed with no details")
                    return None

                elif status in ["QUEUED", "PROCESSING", "IN_QUEUE", "IN_PROGRESS"]:
                    # Still processing, wait and poll again
                    logger.info(f"Image generation status: {status}, waiting...")
                    time.sleep(poll_interval)
                    continue

                else:
                    # Unknown status
                    logger.warning(f"Unknown image generation status: {status}")
                    time.sleep(poll_interval)
                    continue

            except requests.exceptions.RequestException as e:
                logger.error(f"Error polling for image status: {e}")
                time.sleep(poll_interval)
                continue
            except Exception as e:
                logger.error(f"Unexpected error polling for image status: {e}")
                time.sleep(poll_interval)
                continue

        # Timeout reached
        logger.error("Image generation timed out")
        return None

    def get_available_styles(self) -> List[str]:
        """Get list of available artistic styles"""
        return self.styles.copy()

    def get_available_ratios(self) -> List[str]:
        """Get list of available aspect ratios"""
        return self.ratios.copy()


# Global Arta API instance
arta_api = ArtaAPI()
