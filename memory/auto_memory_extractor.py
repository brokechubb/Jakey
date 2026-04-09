"""
Automatic Memory Extractor for Jakey

Analyzes conversations and automatically extracts and stores meaningful memories.
Uses both regex patterns and AI-powered extraction for comprehensive memory capture.
"""

import re
import json
import datetime
import asyncio
import logging
from typing import List, Dict, Any, Optional, Tuple
import hashlib

logger = logging.getLogger(__name__)

AI_MEMORY_EXTRACTION_ENABLED = True
AI_MEMORY_MIN_MESSAGE_LENGTH = 20
AI_MEMORY_SYSTEM_PROMPT = """You are a memory extraction system. Analyze the user's message and extract any meaningful personal information that would be useful to remember for future conversations.

Extract information in these categories:
- personal: name, age, location, birthday, occupation
- preferences: likes, dislikes, favorites, interests
- crypto: holdings, trading style, favorite coins, price targets
- gaming: games played, gaming platforms, streaming habits
- personality: traits, communication style, humor style
- relationships: family, friends, partners, pets
- discord: servers, roles, activity patterns
- financial: goals, situation, plans
- facts: important life events, plans, goals

Return ONLY a JSON array of extracted memories. Each memory should have:
- "category": one of the categories above
- "information": the actual fact/memory (concise, 1-2 sentences max)
- "confidence": 0.0-1.0 (how certain this is worth remembering)

If nothing worth remembering, return: []

Examples:
User: "I'm holding 100 SOL and hoping it hits $500"
Response: [{"category": "crypto", "information": "Holding 100 SOL, price target $500", "confidence": 0.9}]

User: "My name is Alex and I'm from Canada"
Response: [{"category": "personal", "information": "Name is Alex, from Canada", "confidence": 0.95}]

User: "lol nice"
Response: []"""


class AutoMemoryExtractor:
    """
    Extracts meaningful information from conversations for automatic memory storage.
    """

    PERSONAL_INFO_PATTERNS = {
        "name": [
            r"(?:my name is|i\'m|i am|call me)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)",
            r"i(?:\'m| am)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)",
            r"(?:people call me|friends call me|known as)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)",
        ],
        "location": [
            r"(?:i live in|i\'m from|from)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",
            r"(?:live in|located in|based in)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",
            r"(?:moved to|relocated to)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",
        ],
        "age": [
            r"(?:i am|i\'m)\s+(\d+)\s*(?:years? old|yrs? old)",
            r"age\s+(?:is|:)\s*(\d+)",
            r"turning\s+(\d+)\s+(?:this year|soon|next)",
        ],
        "birthday": [
            r"(?:my birthday|birthday)\s+(?:is|:)\s*([A-Za-z]+\s+\d{1,2}(?:st|nd|rd|th)?(?:,\s*\d{4})?)",
            r"born\s+(?:on|:)\s*([A-Za-z]+\s+\d{1,2}(?:st|nd|rd|th)?(?:,\s*\d{4})?)",
        ],
        "occupation": [
            r"(?:i work as|i\'m a|i am a|my job is)\s+([a-zA-Z\s]+?)(?:\.|,|$| and)",
            r"(?:occupation|job|profession)\s+(?:is|:)\s+([a-zA-Z\s]+?)(?:\.|,|$| and)",
            r"(?:work at|work for|working at)\s+([A-Z][a-zA-Z\s]+)",
        ],
        "hobbies": [
            r"(?:i like|i enjoy|my hobby is|hobbies? (?:include|are))\s+([a-zA-Z\s,]+?)(?:\.|,|$| and)",
            r"hobbies?:\s*([a-zA-Z\s,]+?)(?:\.|,|$)",
            r"(?:i\'m into|into)\s+([a-zA-Z\s,]+?)(?:\.|,|$| and)",
        ],
        "preferences": [
            r"(?:i love|i really like|i prefer)\s+([a-zA-Z\s]+?)(?:\.|,|$| and)",
            r"(?:favorite|fav(?:ourite)?)\s+([a-zA-Z\s]+?)(?:\.|,|$|is|are)",
            r"(?:big fan of|fan of)\s+([a-zA-Z\s]+?)(?:\.|,|$| and)",
        ],
        "dislikes": [
            r"(?:i hate|i dislike|i can\'t stand)\s+([a-zA-Z\s]+?)(?:\.|,|$| and)",
            r"(?:don\'t like|do not like)\s+([a-zA-Z\s]+?)(?:\.|,|$| and)",
            r"(?:can\'t stand|annoyed by)\s+([a-zA-Z\s]+?)(?:\.|,|$| and)",
        ],
    }

    CRYPTO_PATTERNS = {
        "crypto_holdings": [
            r"(?:i hold|i have|i own|i\'m holding)\s+(\d+(?:\.\d+)?)\s+(SOL|BTC|ETH|USDC|USDT|BNB|XRP|ADA|DOGE|SHIB)",
            r"(?:my\s+)?(SOL|BTC|ETH|USDC|USDT|BNB|XRP|ADA|DOGE|SHIB)\s+(?:bag|stack|holdings?|position)",
            r"(?:holding|own|have)\s+(\d+(?:\.\d+)?)\s+(?:sol|btc|eth)\b",
        ],
        "crypto_preferences": [
            r"(?:bullish on|believing? in)\s+(SOL|BTC|ETH|[A-Z]{2,5})",
            r"(?:my favorite coin|favorite crypto|fav token)\s+(?:is|:)\s*(SOL|BTC|ETH|[A-Z]{2,5})",
            r"(?:i trade|i\'m trading|trading)\s+(SOL|BTC|ETH|[A-Z]{2,5})",
        ],
        "trading_style": [
            r"(?:i\'m a|i am)\s+(bull|bear|degen|hodler|trader|swing trader|day trader)",
            r"(?:my strategy|strategy)\s+(?:is|:)\s*(DCA|hodl|swing|scalp|day trad)",
            r"(?:i\d+|paper)hands\b",
        ],
        "crypto_goals": [
            r"(?:my (?:crypto )?goal|target|price target)\s+(?:is|:)\s*\$?(\d+(?:,\d+)*(?:\.\d+)?)",
            r"(?:aiming for|targeting)\s+\$?(\d+(?:,\d+)*(?:\.\d+)?)\s+(?:on|for)\s+(SOL|BTC|ETH)",
            r"(?:make it|making it)\s+(?:at|on)\s+\$?(\d+(?:,\d+)*)",
        ],
    }

    GAMING_PATTERNS = {
        "games_played": [
            r"(?:i play|playing|played)\s+([A-Z][a-zA-Z\s:]+?)(?:\.|,|on|for|since|$)",
            r"(?:on)\s+(PlayStation|Xbox|PC|Switch|Steam|mobile)",
            r"(?:my main|main)\s+(?:game|is)\s+([A-Z][a-zA-Z\s]+)",
        ],
        "gaming_preferences": [
            r"(?:favorite game|fav game)\s+(?:is|:)\s*([A-Z][a-zA-Z\s]+)",
            r"(?:i love|i enjoy)\s+(?:playing\s+)?([A-Z][a-zA-Z\s]+?)(?:\.|,|$)",
            r"(?:genre|type of games?)\s+(?:is|:)\s*([a-zA-Z\s]+)",
        ],
        "gaming_habits": [
            r"(?:i stream|streaming)\s+(?:on\s+)?(Twitch|YouTube|Kick)",
            r"(?:hours?\s+(?:played|daily|weekly)|daily\s+(?:grind|session))",
            r"(?:rank|ranking)\s+(?:is|:)\s*([A-Za-z]+\s*\d*)",
        ],
    }

    PERSONALITY_PATTERNS = {
        "personality_traits": [
            r"(?:i\'m|i am)\s+(very\s+)?(introverted|extroverted|shy|outgoing|creative|analytical|logical|emotional|chill|anxious|ambitious|lazy|organized|messy)",
            r"(?:my personality|personality)\s+(?:is|:)\s*(very\s+)?(introverted|extroverted|shy|outgoing|creative|analytical|logical|emotional|chill|anxious|ambitious|lazy)",
        ],
        "communication_style": [
            r"(?:i\'m|i am)\s+(a\s+)?(night owl|early bird|morning person)",
            r"(?:i prefer|i like)\s+(texting|calling|voice chat|DMs)",
        ],
        "humor_style": [
            r"(?:my humor|humor)\s+(?:is|:)\s*(dark|dry|sarcastic|goofy|absurd|wholesome)",
            r"(?:i\'m|i am)\s+(very\s+)?(sarcastic|funny|serious|chill)",
        ],
    }

    DISCORD_PATTERNS = {
        "discord_servers": [
            r"(?:my server|server)\s+(?:is|:)\s*([A-Za-z\s]+?)(?:\.|,|with|$)",
            r"(?:i own|i admin|i mod)\s+(?:on\s+)?([A-Za-z\s]+?)(?:\.|,|$)",
            r"(?:in\s+)?([A-Za-z\s]+?)\s+(?:server|guild)",
        ],
        "discord_roles": [
            r"(?:my role|i\'m a|i am a)\s+(admin|mod|moderator|owner|dev|developer)",
            r"(?:role\s+(?:is|:))\s*([A-Za-z\s]+)",
        ],
        "discord_activity": [
            r"(?:active|usually on)\s+(?:daily|every day|weekends|evenings|mornings)",
            r"(?:discord\s+(?:since|for)|been on discord\s+(?:since|for))\s+(\d+\s*(?:years?|months?|days?))",
        ],
    }

    FINANCIAL_PATTERNS = {
        "financial_goals": [
            r"(?:my goal|goal)\s+(?:is|:)\s*(?:to\s+)?(?:make|earn|get|save)\s+\$?(\d+(?:,\d+)*(?:\.\d+)?)",
            r"(?:aiming for|target)\s+(?:is|:)\s*\$?(\d+(?:,\d+)*)",
            r"(?:financial\s+)?freedom\s+(?:at|by|number)\s+\$?(\d+(?:,\d+)*)",
        ],
        "financial_situation": [
            r"(?:broke|rich|wealthy|poor|comfortable|struggling)\s+(?:af|as fuck|financially)?",
            r"(?:my\s+)?financial\s+situation\s+(?:is|:)\s*([a-zA-Z\s]+)",
        ],
    }

    # Keywords that indicate important information
    IMPORTANCE_KEYWORDS = [
        "remember", "don't forget", "important", "note", "FYI", "for the record",
        "just so you know", "btw", "by the way", "fyi", "ps", "p.s.", "actually"
    ]

    # Topics that are generally worth remembering
    IMPORTANT_TOPICS = [
        "family", "work", "job", "school", "college", "university", "health",
        "relationship", "friend", "girlfriend", "boyfriend", "partner", "married",
        "birthday", "anniversary", "vacation", "holiday", "trip", "travel",
        "crypto", "bitcoin", "ethereum", "solana", "trading", "investing",
        "gaming", "game", "stream", "twitch", "discord",
        "goal", "plan", "dream", "ambition", "project",
        "pet", "dog", "cat", "car", "house", "apartment",
        "hobby", "interest", "passion", "project",
    ]

    # Patterns that indicate important context
    CONTEXT_PATTERNS = [
        r"(?:i have|i've got)\s+(\w+)\s+(?:who|that)",
        r"(?:my \w+ is|my \w+s are)",
        r"(?:i'm going|i am going|i will)\s+\w+\s+(?:to|for)",
        r"(?:i need|i must|i should)\s+\w+",
        r"(?:i want|i'd like)\s+\w+\s+to",
    ]

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    async def extract_memories_from_conversation(
        self, user_message: str, bot_response: str, user_id: str
    ) -> List[Dict[str, Any]]:
        """
        Extract meaningful memories from a conversation exchange.

        Returns a list of memory objects to be stored.
        """
        memories = []

        # Only analyse the user's own message — the bot response contains Jakey's
        # words, not facts about the user, and scanning it produces noise.
        user_text = user_message

        # Extract personal information
        personal_memories = self._extract_personal_info(user_text, user_id)
        memories.extend(personal_memories)

        # Extract crypto-related information
        crypto_memories = self._extract_crypto_info(user_text, user_id)
        memories.extend(crypto_memories)

        # Extract gaming information
        gaming_memories = self._extract_gaming_info(user_text, user_id)
        memories.extend(gaming_memories)

        # Extract personality traits
        personality_memories = self._extract_personality_info(user_text, user_id)
        memories.extend(personality_memories)

        # Extract Discord-specific information
        discord_memories = self._extract_discord_info(user_text, user_id)
        memories.extend(discord_memories)

        # Extract financial information
        financial_memories = self._extract_financial_info(user_text, user_id)
        memories.extend(financial_memories)

        # Extract important facts
        fact_memories = self._extract_important_facts(user_text, user_id)
        memories.extend(fact_memories)

        # Extract preferences and opinions
        preference_memories = self._extract_preferences(user_text, user_id)
        memories.extend(preference_memories)

        # Extract relationships
        relationship_memories = self._extract_relationships(user_text, user_id)
        memories.extend(relationship_memories)

        # AI-powered extraction for messages that are substantial enough
        if AI_MEMORY_EXTRACTION_ENABLED and len(user_text) >= AI_MEMORY_MIN_MESSAGE_LENGTH:
            try:
                ai_memories = await self._extract_memories_with_ai(user_text, user_id)
                if ai_memories:
                    existing_info = {m.get("information", "").lower() for m in memories}
                    for ai_mem in ai_memories:
                        ai_info = ai_mem.get("information", "").lower()
                        if not any(ai_info in existing or existing in ai_info for existing in existing_info):
                            memories.append(ai_mem)
            except Exception as e:
                logger.debug(f"AI memory extraction failed (non-critical): {e}")

        # Filter out memories that are too short or not meaningful
        filtered_memories = self._filter_memories(memories)
        for memory in filtered_memories:
            memory['id'] = self._generate_memory_id(memory, user_id)
            memory['timestamp'] = datetime.datetime.utcnow().isoformat()
            memory['confidence'] = memory.get('confidence', 1.0)

        return filtered_memories

    def _extract_personal_info(self, text: str, user_id: str) -> List[Dict[str, Any]]:
        """Extract personal information from text."""
        memories = []
        text_lower = text.lower()
        
        for info_type, patterns in self.PERSONAL_INFO_PATTERNS.items():
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    value = match.group(1).strip()
                    if len(value) > 2:  # Filter out very short matches
                        memories.append({
                            "type": "personal_info",
                            "category": info_type,
                            "information": value,
                            "source": "personal_info_pattern",
                            "confidence": 0.9
                        })
                        break  # Only take first match per type
        
        return memories

    def _extract_important_facts(self, text: str, user_id: str) -> List[Dict[str, Any]]:
        """Extract important facts from text."""
        memories = []
        text_lower = text.lower()
        
        # Check for importance indicators
        has_importance_indicator = any(keyword in text_lower for keyword in self.IMPORTANCE_KEYWORDS)
        
        # Check for important topics
        has_important_topic = any(topic in text_lower for topic in self.IMPORTANT_TOPICS)
        
        # Extract sentences that might contain important facts
        sentences = re.split(r'[.!?]+', text)
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) < 10:  # Skip very short sentences
                continue
                
            sentence_lower = sentence.lower()
            
            # Check if sentence contains important information
            important = (
                has_importance_indicator or
                has_important_topic or
                any(topic in sentence_lower for topic in self.IMPORTANT_TOPICS) or
                any(keyword in sentence_lower for keyword in self.IMPORTANCE_KEYWORDS) or
                re.search(r'(?:i have|i own|i bought|i got|i created)', sentence_lower) or
                re.search(r'(?:i will|i am going|i plan to)', sentence_lower)
            )
            
            if important:
                memories.append({
                    "type": "fact",
                    "category": "important_fact",
                    "information": sentence,
                    "source": "importance_detection",
                    "confidence": 0.7 if has_importance_indicator else 0.5
                })
        
        return memories

    def _extract_preferences(self, text: str, user_id: str) -> List[Dict[str, Any]]:
        """Extract user preferences and opinions."""
        memories = []
        
        # Preference patterns
        preference_patterns = [
            r"(?:i love|i really like|i enjoy|i prefer)\s+([^.!?]+)",
            r"(?:i hate|i dislike|i can't stand)\s+([^.!?]+)",
            r"(?:my favorite|favorite)\s+([^.!?]+)",
            r"(?:i think|i feel|i believe)\s+([^.!?]+)",
        ]
        
        for pattern in preference_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                preference = match.group(1).strip()
                if len(preference) > 3:
                    # Determine if it's a like or dislike
                    pref_text = match.group(0).lower()
                    if any(word in pref_text for word in ["love", "like", "enjoy", "prefer", "favorite"]):
                        category = "likes"
                    elif any(word in pref_text for word in ["hate", "dislike", "can't stand"]):
                        category = "dislikes"
                    else:
                        category = "opinion"
                    
                    memories.append({
                        "type": "preference",
                        "category": category,
                        "information": preference,
                        "source": "preference_pattern",
                        "confidence": 0.8
                    })
        
        return memories

    def _extract_context(self, text: str, user_id: str) -> List[Dict[str, Any]]:
        """Extract contextual information about what user is doing."""
        memories = []
        
        # Context patterns
        for pattern in self.CONTEXT_PATTERNS:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                context = match.group(0).strip()
                if len(context) > 10:
                    memories.append({
                        "type": "context",
                        "category": "user_context",
                        "information": context,
                        "source": "context_pattern",
                        "confidence": 0.6
                    })
        
        return memories

    def _extract_crypto_info(self, text: str, user_id: str) -> List[Dict[str, Any]]:
        """Extract crypto-related information from text."""
        memories = []

        for info_type, patterns in self.CRYPTO_PATTERNS.items():
            for pattern in patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    value = match.group(0).strip()
                    if len(value) > 3:
                        memories.append({
                            "type": "crypto",
                            "category": info_type,
                            "information": value,
                            "source": "crypto_pattern",
                            "confidence": 0.85
                        })

        return memories

    def _extract_gaming_info(self, text: str, user_id: str) -> List[Dict[str, Any]]:
        """Extract gaming-related information from text."""
        memories = []

        for info_type, patterns in self.GAMING_PATTERNS.items():
            for pattern in patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    value = match.group(0).strip()
                    if len(value) > 3:
                        memories.append({
                            "type": "gaming",
                            "category": info_type,
                            "information": value,
                            "source": "gaming_pattern",
                            "confidence": 0.8
                        })

        return memories

    def _extract_personality_info(self, text: str, user_id: str) -> List[Dict[str, Any]]:
        """Extract personality traits from text."""
        memories = []

        for info_type, patterns in self.PERSONALITY_PATTERNS.items():
            for pattern in patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    # Get the last group which contains the actual trait
                    groups = [g for g in match.groups() if g]
                    if groups:
                        value = groups[-1].strip()
                        if len(value) > 2:
                            memories.append({
                                "type": "personality",
                                "category": info_type,
                                "information": value,
                                "source": "personality_pattern",
                                "confidence": 0.75
                            })

        return memories

    def _extract_discord_info(self, text: str, user_id: str) -> List[Dict[str, Any]]:
        """Extract Discord-specific information from text."""
        memories = []

        for info_type, patterns in self.DISCORD_PATTERNS.items():
            for pattern in patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    value = match.group(0).strip()
                    if len(value) > 3:
                        memories.append({
                            "type": "discord",
                            "category": info_type,
                            "information": value,
                            "source": "discord_pattern",
                            "confidence": 0.8
                        })

        return memories

    def _extract_financial_info(self, text: str, user_id: str) -> List[Dict[str, Any]]:
        """Extract financial information from text."""
        memories = []

        for info_type, patterns in self.FINANCIAL_PATTERNS.items():
            for pattern in patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    value = match.group(0).strip()
                    if len(value) > 3:
                        memories.append({
                            "type": "financial",
                            "category": info_type,
                            "information": value,
                            "source": "financial_pattern",
                            "confidence": 0.75
                        })

        return memories

    def _extract_relationships(self, text: str, user_id: str) -> List[Dict[str, Any]]:
        """Extract information about relationships."""
        memories = []
        text_lower = text.lower()
        
        # Relationship keywords
        relationship_patterns = [
            r"(?:my \w+)\s+(?:is|are)\s+([^.!?]+)",
            r"(?:i have a|i have an)\s+(?:\w+\s+)?(friend|brother|sister|mother|father|son|daughter|husband|wife|partner|girlfriend|boyfriend)\s+([^.!?]+)?",
        ]
        
        for pattern in relationship_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                relationship_info = match.group(0).strip()
                if len(relationship_info) > 5:
                    memories.append({
                        "type": "relationship",
                        "category": "personal_relationship",
                        "information": relationship_info,
                        "source": "relationship_pattern",
                        "confidence": 0.7
                    })
        
        return memories

    async def _extract_memories_with_ai(
        self, user_text: str, user_id: str
    ) -> List[Dict[str, Any]]:
        """Use AI to extract memories that regex patterns might miss."""
        try:
            from ai.ai_provider_manager import AIProviderManager

            manager = AIProviderManager()
            messages = [
                {"role": "system", "content": AI_MEMORY_SYSTEM_PROMPT},
                {"role": "user", "content": user_text},
            ]

            response = await asyncio.wait_for(
                manager.generate_text(
                    messages=messages,
                    temperature=0.1,
                    max_tokens=500,
                    tools=None,
                    tool_choice="none",
                ),
                timeout=8.0,
            )

            if not response or response.get("error"):
                return []

            choices = response.get("choices", [])
            if not choices:
                return []

            content = choices[0].get("message", {}).get("content", "")
            if not content:
                return []

            content = content.strip()
            if content.startswith("```"):
                content = re.sub(r"^```\w*\n?", "", content)
                content = re.sub(r"\n?```$", "", content)
                content = content.strip()

            ai_memories = json.loads(content)
            if not isinstance(ai_memories, list):
                return []

            valid_memories = []
            for mem in ai_memories:
                if not isinstance(mem, dict):
                    continue
                info = mem.get("information", "").strip()
                if not info or len(info) < 3:
                    continue
                category = mem.get("category", "ai_extracted")
                confidence = float(mem.get("confidence", 0.6))
                confidence = max(0.0, min(1.0, confidence))

                valid_memories.append({
                    "type": category,
                    "category": category,
                    "information": info,
                    "source": "ai_extraction",
                    "confidence": confidence,
                })

            if valid_memories:
                logger.debug(
                    f"AI extracted {len(valid_memories)} memories from message ({len(user_text)} chars)"
                )

            return valid_memories

        except json.JSONDecodeError:
            logger.debug("AI memory extraction returned invalid JSON")
            return []
        except asyncio.TimeoutError:
            logger.debug("AI memory extraction timed out")
            return []
        except ImportError:
            logger.debug("AI provider not available for memory extraction")
            return []
        except Exception as e:
            logger.debug(f"AI memory extraction error: {e}")
            return []

    def _filter_memories(self, memories: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter out low-quality or duplicate memories."""
        filtered = []
        seen_content = set()
        
        for memory in memories:
            info = memory.get("information", "").strip()
            
            # Skip if too short
            if len(info) < 3:
                continue
            
            # Skip if likely too generic
            if info.lower() in ["yes", "no", "ok", "okay", "maybe", "thanks", "thank you", "hi", "hello"]:
                continue
            
            # Skip duplicate content
            content_hash = hashlib.md5(info.lower().encode()).hexdigest()
            if content_hash in seen_content:
                continue
            seen_content.add(content_hash)
            
            # Skip if confidence is too low
            if memory.get("confidence", 0) < 0.4:
                continue
            
            filtered.append(memory)
        
        return filtered

    def _generate_memory_id(self, memory: Dict[str, Any], user_id: str) -> str:
        """Generate a unique ID for a memory."""
        content = f"{user_id}{memory.get('type', '')}{memory.get('information', '')}{memory.get('timestamp', '')}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    async def store_memories(self, memories: List[Dict[str, Any]], user_id: str) -> List[bool]:
        """
        Store extracted memories using the unified memory backend.
        
        Returns a list of success indicators for each memory.
        """
        results = []
        
        try:
            # Import here to avoid circular dependencies
            from memory import memory_backend
            
            if memory_backend is None:
                logger.warning("Memory backend not available, skipping auto memory storage")
                return [False] * len(memories)
            
            for memory in memories:
                try:
                    # Key is derived from type+category+content hash so the same
                    # fact always maps to the same key and upserts instead of
                    # creating a new row on every extraction.
                    content_hash = hashlib.md5(memory.get("information", "").encode()).hexdigest()[:8]
                    memory_key = f"{memory['type']}_{memory['category']}_{content_hash}"
                    
                    # Store additional metadata
                    metadata = {
                        "source": memory.get("source", "auto_extracted"),
                        "confidence": memory.get("confidence", 1.0),
                        "extracted_at": datetime.datetime.utcnow().isoformat()
                    }
                    
                    # Store the memory
                    success = await memory_backend.store(
                        user_id=user_id,
                        key=memory_key,
                        value=memory.get("information", ""),
                        metadata=metadata
                    )
                    
                    results.append(success)
                    
                    if success:
                        logger.debug(f"Stored auto-extracted memory for user {user_id}: {memory_key}")
                    else:
                        logger.warning(f"Failed to store memory for user {user_id}: {memory_key}")
                        
                except Exception as e:
                    logger.error(f"Error storing individual memory: {e}")
                    results.append(False)
                    
        except ImportError as e:
            logger.error(f"Memory backend import error: {e}")
            return [False] * len(memories)
        except Exception as e:
            logger.error(f"Error in store_memories: {e}")
            return [False] * len(memories)
        
        return results


class MemoryCleanupManager:
    """
    Manages cleanup of old memories to prevent bloat.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    async def cleanup_old_memories(self, max_age_days: int = 365, confidence_threshold: float = 0.5):
        """
        Clean up old memories based on age and confidence.
        
        Args:
            max_age_days: Maximum age in days to keep memories
            confidence_threshold: Minimum confidence to keep memories
        """
        try:
            from memory import memory_backend
            
            if memory_backend is None:
                logger.warning("Memory backend not available for cleanup")
                return
            
            # Perform cleanup using the unified backend
            cleanup_result = await memory_backend.cleanup(max_age_days)
            
            total_cleaned = sum(cleanup_result.values())
            if total_cleaned > 0:
                self.logger.info(f"Cleaned up {total_cleaned} old memories")
                for backend, count in cleanup_result.items():
                    self.logger.info(f"  {backend}: {count}")
            else:
                self.logger.debug("No memories to clean up")
                
        except Exception as e:
            self.logger.error(f"Error during memory cleanup: {e}")