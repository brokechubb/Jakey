"""
Helper utilities for JakeySelfBot
"""

import re
import unicodedata
import string
import logging

logger = logging.getLogger(__name__)

def sanitize_discord_embed_phrase(embed_description: str) -> str:
    """
    Sanitize phrase from Discord embed to prevent copy/paste detection.
    
    This function removes invisible characters and formatting that can cause
    "no copy and pasting" rejections in phrasedrop auto-claim functionality.
    
    Args:
        embed_description: Raw text from Discord embed description
        
    Returns:
        Cleaned phrase safe for submission
    """
    if not isinstance(embed_description, str):
        logger.warning(f"Invalid embed description type: {type(embed_description)}")
        return ""
    
    if not embed_description.strip():
        logger.warning("Empty embed description provided")
        return ""
    
    original_text = embed_description
    
    try:
        # Step 1: Remove common Discord formatting (but keep newlines for now)
        cleaned = embed_description.replace("**", "")
        cleaned = cleaned.replace("__", "").replace("~~", "").replace("||", "")
        
        # Step 2: Extract phrase between asterisks (robust parsing)
        phrase = extract_phrase_between_asterisks(cleaned)
        
        # Step 3: Remove invisible Unicode characters
        phrase = remove_invisible_characters(phrase)
        
        # Step 4: Normalize Unicode text
        phrase = unicodedata.normalize('NFKC', phrase)
        
        # Step 5: Now handle newlines and normalize whitespace
        phrase = phrase.replace("\n", " ")
        phrase = re.sub(r'\s+', ' ', phrase).strip()
        
        # Step 6: Validate result
        if not phrase or not phrase.strip():
            logger.warning(f"Empty phrase after sanitization: '{original_text}'")
            return ""
        
        # Log successful sanitization
        if phrase != original_text:
            logger.debug(f"Sanitized phrase: '{original_text}' -> '{phrase}'")
        
        return phrase
        
    except Exception as e:
        logger.error(f"Error sanitizing phrase '{embed_description}': {e}")
        return ""

def extract_phrase_between_asterisks(text: str) -> str:
    """
    Extract phrase between asterisks with robust parsing.
    
    Handles various formats:
    - *phrase*
    - **phrase**
    - * phrase *
    - text *phrase* more text
    """
    if not text:
        return ""
    
    # Try to extract content between asterisks
    asterisk_parts = text.split("*")
    
    if len(asterisk_parts) >= 3:
        # Format: *phrase* or text *phrase* more text
        phrase = asterisk_parts[1].strip()
        if phrase:
            return phrase
    
    # Fallback: use regex to find content between asterisks
    match = re.search(r'\*+([^*]+)\*+', text)
    if match:
        phrase = match.group(1).strip()
        if phrase:
            return phrase
    
    # Last fallback: remove all asterisks and strip
    phrase = text.replace("*", "").strip()
    
    return phrase

def remove_invisible_characters(text: str) -> str:
    """
    Remove invisible Unicode characters that trigger copy/paste detection.
    
    These characters are often added by Discord embeds or rich text formatting
    and can cause anti-copy/paste systems to reject the submission.
    """
    if not text:
        return ""
    
    # List of specific invisible characters to remove
    invisible_chars = [
        '\u200B',  # Zero Width Space
        '\u200C',  # Zero Width Non-Joiner
        '\u200D',  # Zero Width Joiner
        '\u2060',  # Word Joiner
        '\uFEFF',  # Zero Width No-Break Space (BOM)
        '\u00AD',  # Soft Hyphen
        '\u180E',  # Mongolian Vowel Separator
        '\u061C',  # Arabic Letter Mark
        '\u200E',  # Left-to-Right Mark
        '\u200F',  # Right-to-Left Mark
        '\u202A',  # Left-to-Right Embedding
        '\u202B',  # Right-to-Left Embedding
        '\u202C',  # Pop Directional Formatting
        '\u202D',  # Left-to-Right Override
        '\u202E',  # Right-to-Left Override
    ]
    
    # Remove specific invisible characters by replacing with space for better spacing
    for char in invisible_chars:
        text = text.replace(char, ' ')
    
    # Remove characters by Unicode category
    # Cf = Format characters (invisible)
    # Cc = Control characters (except common ones)
    # Cs = Surrogate characters
    cleaned_text = []
    for char in text:
        category = unicodedata.category(char)
        if category not in ['Cf', 'Cc', 'Cs']:
            cleaned_text.append(char)
        elif category == 'Cc' and char in ['\t', '\n', '\r']:
            # Keep common whitespace control characters
            cleaned_text.append(char)
    
    text = ''.join(cleaned_text)
    
    return text

def validate_phrase_for_submission(phrase: str) -> tuple[bool, str]:
    """
    Validate that a phrase is safe for submission.
    
    Args:
        phrase: The cleaned phrase
        
    Returns:
        tuple: (is_valid, error_message)
    """
    if not isinstance(phrase, str):
        return False, "Phrase must be a string"
    
    if not phrase.strip():
        return False, "Phrase cannot be empty"
    
    # Check for remaining invisible characters
    for char in phrase:
        category = unicodedata.category(char)
        if category in ['Cf', 'Cs']:
            return False, f"Phrase contains invisible character: {ord(char):04x}"
    
    # Check for suspicious patterns
    if re.search(r'[^\w\s\-.!,?;:\'"()]', phrase):
        return False, "Phrase contains suspicious characters"
    
    # Length validation
    if len(phrase) > 200:
        return False, "Phrase too long"
    
    return True, ""

def clean_phrase_comprehensive(embed_description: str) -> str:
    """
    Comprehensive phrase cleaning that combines all sanitization steps.
    
    This is the main function to use for phrasedrop auto-claim.
    """
    # Step 1: Basic sanitization
    phrase = sanitize_discord_embed_phrase(embed_description)
    
    if not phrase:
        return ""
    
    # Step 2: Validation
    is_valid, error = validate_phrase_for_submission(phrase)
    if not is_valid:
        logger.warning(f"Phrase validation failed: {error}")
        return ""
    
    return phrase