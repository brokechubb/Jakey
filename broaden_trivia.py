import asyncio
import aiohttp
import html
import logging
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from data.trivia_database import TriviaDatabase

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("TriviaEnhancer")

class TriviaEnhancer:
    def __init__(self):
        self.db = TriviaDatabase()
        self.opentdb_url = "https://opentdb.com"
        self.github_base_url = "https://raw.githubusercontent.com/uberspot/OpenTriviaQA/master/categories"
        self.session_token = None
        
        # Map GitHub categories to our DB categories
        self.github_category_map = {
            "animals": "Animals",
            "brain-teasers": "Brain Teasers",
            "celebrities": "Celebrities",
            "entertainment": "Entertainment: General",
            "for-kids": "General Knowledge",
            "general": "General Knowledge",
            "geography": "Geography",
            "history": "History",
            "hobbies": "Hobbies",
            "humanities": "Humanities",
            "literature": "Entertainment: Books",
            "movies": "Entertainment: Film",
            "music": "Entertainment: Music",
            "people": "General Knowledge", # People is broad
            "religion-faith": "Religion & Mythology",
            "science-technology": "Science & Nature",
            "sports": "Sports",
            "television": "Entertainment: Television",
            "video-games": "Entertainment: Video Games",
            "world": "Geography"
        }

    # OpenTDB Methods
    async def get_session_token(self, session: aiohttp.ClientSession):
        try:
            async with session.get(f"{self.opentdb_url}/api_token.php?command=request") as resp:
                data = await resp.json()
                if data['response_code'] == 0:
                    self.session_token = data['token']
                    logger.info(f"Got OpenTDB session token: {self.session_token}")
        except Exception as e:
            logger.error(f"Failed to get OpenTDB session token: {e}")

    async def fetch_opentdb_categories(self, session: aiohttp.ClientSession) -> List[Dict]:
        try:
            async with session.get(f"{self.opentdb_url}/api_category.php") as resp:
                data = await resp.json()
                return data['trivia_categories']
        except Exception as e:
            logger.error(f"Failed to fetch OpenTDB categories: {e}")
            return []

    async def fetch_opentdb_questions(self, session: aiohttp.ClientSession, category_id: int, amount: int = 50) -> List[Dict]:
        url = f"{self.opentdb_url}/api.php?amount={amount}&category={category_id}"
        if self.session_token:
            url += f"&token={self.session_token}"
        
        try:
            async with session.get(url) as resp:
                if resp.status == 429:
                    logger.warning("Rate limited by OpenTDB. Waiting 5 seconds...")
                    await asyncio.sleep(5)
                    return await self.fetch_opentdb_questions(session, category_id, amount)
                
                data = await resp.json()
                response_code = data['response_code']
                
                if response_code == 0:
                    return data['results']
                elif response_code in [1, 4]: # No Results or Token Empty
                    return []
                elif response_code == 3: # Token Not Found
                    await self.get_session_token(session)
                    return await self.fetch_opentdb_questions(session, category_id, amount)
                else:
                    return []
        except Exception as e:
            logger.error(f"Error fetching OpenTDB questions: {e}")
            return []

    async def process_opentdb_category(self, session: aiohttp.ClientSession, category: Dict):
        cat_id = category['id']
        cat_name = category['name']
        
        logger.info(f"Processing OpenTDB category: {cat_name}")
        questions_accumulated = []
        
        # Fetch 1 batch of 50 for now (we did more previously)
        questions = await self.fetch_opentdb_questions(session, cat_id, 50)
        
        if questions:
            for q in questions:
                question_text = html.unescape(q['question'])
                answer_text = html.unescape(q['correct_answer'])
                difficulty_map = {'easy': 1, 'medium': 2, 'hard': 3}
                difficulty = difficulty_map.get(q['difficulty'], 1)
                
                questions_accumulated.append({
                    'category': cat_name,
                    'question': question_text,
                    'answer': answer_text,
                    'difficulty': difficulty,
                    'source': 'OpenTDB',
                    'external_id': None 
                })
            
            count = await self.db.bulk_import_questions(questions_accumulated)
            logger.info(f"Imported {count} questions for {cat_name} from OpenTDB")
            await asyncio.sleep(5) # Politeness
        else:
            logger.info(f"No questions for {cat_name} from OpenTDB")

    # GitHub OpenTriviaQA Methods
    async def process_github_category(self, session: aiohttp.ClientSession, github_cat: str):
        db_cat_name = self.github_category_map.get(github_cat, github_cat.replace('-', ' ').title())
        url = f"{self.github_base_url}/{github_cat}"
        
        logger.info(f"Processing GitHub category: {github_cat} -> {db_cat_name}")
        
        try:
            async with session.get(url) as resp:
                if resp.status == 200:
                    # Try UTF-8 first, then fallback to latin-1
                    try:
                        content = await resp.text(encoding='utf-8')
                    except UnicodeDecodeError:
                        logger.warning(f"UTF-8 decode failed for {github_cat}, trying latin-1")
                        content = await resp.text(encoding='latin-1')
                        
                    questions = self.parse_github_content(content, db_cat_name)
                    
                    if questions:
                        # Process in chunks of 500 to avoid locking DB for too long
                        chunk_size = 500
                        total_imported = 0
                        for i in range(0, len(questions), chunk_size):
                            chunk = questions[i:i + chunk_size]
                            count = await self.db.bulk_import_questions(chunk)
                            total_imported += count
                        logger.info(f"Imported {total_imported} questions for {db_cat_name} from GitHub")
                    else:
                        logger.info(f"No questions parsed for {github_cat}")
                else:
                    logger.warning(f"Failed to fetch GitHub category {github_cat}: Status {resp.status}")
        except Exception as e:
            logger.error(f"Error processing GitHub category {github_cat}: {e}")

    def parse_github_content(self, content: str, category_name: str) -> List[Dict]:
        questions = []
        lines = content.strip().splitlines()
        
        current_q = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            if line.startswith('#Q'):
                current_q = line[2:].strip()
            elif line.startswith('^') and current_q:
                answer = line[1:].strip()
                questions.append({
                    'category': category_name,
                    'question': current_q,
                    'answer': answer,
                    'difficulty': 2, # Default to medium
                    'source': 'OpenTriviaQA_GitHub',
                    'external_id': None
                })
                current_q = None # Reset
                
        return questions

    async def run(self):
        stats_before = await self.db.get_database_stats()
        logger.info("="*50)
        logger.info(f"Stats Before: {stats_before}")
        logger.info("="*50)
        
        async with aiohttp.ClientSession() as session:
            # 1. Process OpenTDB (Just one pass to keep it light if rerunning)
            await self.get_session_token(session)
            await asyncio.sleep(1)
            opentdb_cats = await self.fetch_opentdb_categories(session)
            # Limit OpenTDB processing to first 5 categories for speed in this run, 
            # or remove limit for full run. User asked to broaden, so let's do 5 random ones?
            # Or just do them all but small batch.
            # I'll do all of them, 1 batch each.
            for cat in opentdb_cats:
                await self.process_opentdb_category(session, cat)

            # 2. Process GitHub OpenTriviaQA
            github_cats = list(self.github_category_map.keys())
            for cat in github_cats:
                await self.process_github_category(session, cat)
                await asyncio.sleep(1)

        stats_after = await self.db.get_database_stats()
        logger.info("="*50)
        logger.info(f"Stats After: {stats_after}")
        logger.info("="*50)
        
        self.db.close()

if __name__ == "__main__":
    enhancer = TriviaEnhancer()
    try:
        asyncio.run(enhancer.run())
    except KeyboardInterrupt:
        logger.info("Enhancement interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
