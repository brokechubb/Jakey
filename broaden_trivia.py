import asyncio
import aiohttp
import argparse
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
    def __init__(self, skip_opentdb=False, skip_github=False, skip_triviaapi=False, verbose=False):
        self.db = TriviaDatabase()
        self.opentdb_url = "https://opentdb.com"
        self.github_base_url = "https://raw.githubusercontent.com/uberspot/OpenTriviaQA/master/categories"
        self.triviaapi_url = "https://the-trivia-api.com/v2"
        self.session_token = None
        self.skip_opentdb = skip_opentdb
        self.skip_github = skip_github
        self.skip_triviaapi = skip_triviaapi
        self.verbose = verbose
        
        # Track statistics
        self.stats = {
            'opentdb_imported': 0,
            'github_imported': 0,
            'triviaapi_imported': 0,
            'duplicates_skipped': 0,
            'errors': 0
        }
        
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
        
        # Map The Trivia API categories to our DB categories
        self.triviaapi_category_map = {
            "arts_and_literature": "Entertainment: Books",
            "film_and_tv": "Entertainment: Film",
            "food_and_drink": "Food & Drink",
            "general_knowledge": "General Knowledge",
            "geography": "Geography",
            "history": "History",
            "music": "Entertainment: Music",
            "science": "Science & Nature",
            "society_and_culture": "Society & Culture",
            "sport_and_leisure": "Sports"
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
            
            before_count = len(questions_accumulated)
            count = await self.db.bulk_import_questions(questions_accumulated)
            duplicates = before_count - count
            
            self.stats['opentdb_imported'] += count
            self.stats['duplicates_skipped'] += duplicates
            
            logger.info(f"Imported {count}/{before_count} questions for {cat_name} from OpenTDB ({duplicates} duplicates)")
            if self.verbose and count > 0:
                logger.info(f"  Sample question: {questions_accumulated[0]['question'][:100]}...")
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
                        before_count = len(questions)
                        for i in range(0, len(questions), chunk_size):
                            chunk = questions[i:i + chunk_size]
                            count = await self.db.bulk_import_questions(chunk)
                            total_imported += count
                        
                        duplicates = before_count - total_imported
                        self.stats['github_imported'] += total_imported
                        self.stats['duplicates_skipped'] += duplicates
                        
                        logger.info(f"Imported {total_imported}/{before_count} questions for {db_cat_name} from GitHub ({duplicates} duplicates)")
                        if self.verbose and total_imported > 0:
                            logger.info(f"  Sample question: {questions[0]['question'][:100]}...")
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

    # The Trivia API Methods
    async def fetch_triviaapi_questions(self, session: aiohttp.ClientSession, category: str, limit: int = 50) -> List[Dict]:
        """Fetch questions from The Trivia API for a specific category"""
        url = f"{self.triviaapi_url}/questions"
        params = {
            'limit': min(limit, 50),  # API max is 50 per request
            'categories': category
        }
        
        try:
            async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status == 200:
                    return await resp.json()
                elif resp.status == 429:
                    logger.warning("Rate limited by The Trivia API. Waiting 5 seconds...")
                    await asyncio.sleep(5)
                    return await self.fetch_triviaapi_questions(session, category, limit)
                else:
                    logger.warning(f"The Trivia API returned status {resp.status}")
                    return []
        except asyncio.TimeoutError:
            logger.warning(f"Timeout fetching from The Trivia API for category: {category}")
            return []
        except Exception as e:
            logger.error(f"Error fetching from The Trivia API: {e}")
            return []
    
    async def process_triviaapi_category(self, session: aiohttp.ClientSession, api_category: str, db_category: str):
        """Process a category from The Trivia API"""
        logger.info(f"Processing The Trivia API category: {api_category} -> {db_category}")
        
        # Fetch multiple batches to get more questions per category
        all_questions = []
        for difficulty in ['easy', 'medium', 'hard']:
            url = f"{self.triviaapi_url}/questions"
            params = {
                'limit': 50,
                'categories': api_category,
                'difficulties': difficulty
            }
            
            try:
                async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    if resp.status == 200:
                        questions = await resp.json()
                        all_questions.extend(questions)
                        await asyncio.sleep(1)  # Be polite
                    elif resp.status == 429:
                        logger.warning("Rate limited, skipping remaining difficulties for this category")
                        break
            except Exception as e:
                logger.error(f"Error fetching {difficulty} questions for {api_category}: {e}")
                self.stats['errors'] += 1
        
        if all_questions:
            questions_accumulated = []
            difficulty_map = {'easy': 1, 'medium': 2, 'hard': 3}
            
            for q in all_questions:
                question_text = q.get('question', {}).get('text', '').strip()
                correct_answer = q.get('correctAnswer', '').strip()
                difficulty = difficulty_map.get(q.get('difficulty', 'medium'), 2)
                external_id = q.get('id')
                
                if question_text and correct_answer:
                    questions_accumulated.append({
                        'category': db_category,
                        'question': question_text,
                        'answer': correct_answer,
                        'difficulty': difficulty,
                        'source': 'TheTriviaAPI',
                        'external_id': external_id
                    })
            
            if questions_accumulated:
                before_count = len(questions_accumulated)
                count = await self.db.bulk_import_questions(questions_accumulated)
                duplicates = before_count - count
                
                self.stats['triviaapi_imported'] += count
                self.stats['duplicates_skipped'] += duplicates
                
                logger.info(f"Imported {count}/{before_count} questions for {db_category} from The Trivia API ({duplicates} duplicates)")
                if self.verbose and count > 0:
                    logger.info(f"  Sample question: {questions_accumulated[0]['question'][:100]}...")
            else:
                logger.info(f"No valid questions for {api_category}")
        else:
            logger.info(f"No questions retrieved for {api_category}")

    async def run(self):
        stats_before = await self.db.get_database_stats()
        logger.info("="*70)
        logger.info(f"Trivia Database Enhancement Starting")
        logger.info("="*70)
        logger.info(f"Before - Categories: {stats_before['total_categories']}, Questions: {stats_before['total_questions']}")
        top_cats = ', '.join([f"{c['name']} ({c['count']})" for c in stats_before['top_categories'][:3]])
        logger.info(f"Top categories: {top_cats}")
        logger.info("="*70)
        
        async with aiohttp.ClientSession() as session:
            # 1. Process OpenTDB if not skipped
            if not self.skip_opentdb:
                logger.info("\n[1/3] Processing OpenTDB (Open Trivia Database)")
                logger.info("-" * 70)
                await self.get_session_token(session)
                await asyncio.sleep(1)
                opentdb_cats = await self.fetch_opentdb_categories(session)
                logger.info(f"Found {len(opentdb_cats)} categories to process from OpenTDB")
                
                for i, cat in enumerate(opentdb_cats, 1):
                    logger.info(f"  [{i}/{len(opentdb_cats)}] {cat['name']}")
                    try:
                        await self.process_opentdb_category(session, cat)
                    except Exception as e:
                        logger.error(f"Error processing {cat['name']}: {e}")
                        self.stats['errors'] += 1
            else:
                logger.info("\n[1/3] Skipping OpenTDB (disabled)")

            # 2. Process GitHub OpenTriviaQA if not skipped
            if not self.skip_github:
                logger.info("\n[2/3] Processing GitHub OpenTriviaQA")
                logger.info("-" * 70)
                github_cats = list(self.github_category_map.keys())
                logger.info(f"Found {len(github_cats)} categories to process from GitHub")
                
                for i, cat in enumerate(github_cats, 1):
                    logger.info(f"  [{i}/{len(github_cats)}] {cat}")
                    try:
                        await self.process_github_category(session, cat)
                        await asyncio.sleep(1)
                    except Exception as e:
                        logger.error(f"Error processing {cat}: {e}")
                        self.stats['errors'] += 1
            else:
                logger.info("\n[2/3] Skipping GitHub (disabled)")
            
            # 3. Process The Trivia API if not skipped
            if not self.skip_triviaapi:
                logger.info("\n[3/3] Processing The Trivia API")
                logger.info("-" * 70)
                triviaapi_cats = list(self.triviaapi_category_map.items())
                logger.info(f"Found {len(triviaapi_cats)} categories to process from The Trivia API")
                
                for i, (api_cat, db_cat) in enumerate(triviaapi_cats, 1):
                    logger.info(f"  [{i}/{len(triviaapi_cats)}] {api_cat} -> {db_cat}")
                    try:
                        await self.process_triviaapi_category(session, api_cat, db_cat)
                        await asyncio.sleep(2)  # Be polite with free tier
                    except Exception as e:
                        logger.error(f"Error processing {api_cat}: {e}")
                        self.stats['errors'] += 1
            else:
                logger.info("\n[3/3] Skipping The Trivia API (disabled)")

        stats_after = await self.db.get_database_stats()
        
        # Calculate changes
        questions_added = stats_after['total_questions'] - stats_before['total_questions']
        categories_added = stats_after['total_categories'] - stats_before['total_categories']
        
        logger.info("\n" + "="*70)
        logger.info("ENHANCEMENT COMPLETE - SUMMARY")
        logger.info("="*70)
        logger.info(f"Questions Added: {questions_added} (from {stats_before['total_questions']} to {stats_after['total_questions']})")
        logger.info(f"Categories Added: {categories_added} (from {stats_before['total_categories']} to {stats_after['total_categories']})")
        logger.info(f"\nBreakdown:")
        logger.info(f"  - OpenTDB imports: {self.stats['opentdb_imported']}")
        logger.info(f"  - GitHub imports: {self.stats['github_imported']}")
        logger.info(f"  - The Trivia API imports: {self.stats['triviaapi_imported']}")
        logger.info(f"  - Duplicates skipped: {self.stats['duplicates_skipped']}")
        logger.info(f"  - Errors encountered: {self.stats['errors']}")
        logger.info(f"\nTop categories after enhancement:")
        for cat in stats_after['top_categories'][:5]:
            logger.info(f"  - {cat['name']}: {cat['count']} questions")
        logger.info("="*70)
        
        self.db.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Enhance trivia database with questions from external sources",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python broaden_trivia.py                      # Import from all sources
  python broaden_trivia.py --skip-opentdb       # Skip OpenTDB
  python broaden_trivia.py --skip-github        # Skip GitHub
  python broaden_trivia.py --skip-triviaapi     # Skip The Trivia API
  python broaden_trivia.py --only-triviaapi     # Only import from The Trivia API
  python broaden_trivia.py --verbose            # Show detailed progress
  python broaden_trivia.py --stats-only         # Just show current statistics
        """
    )
    parser.add_argument('--skip-opentdb', action='store_true', 
                        help='Skip importing from OpenTDB API')
    parser.add_argument('--skip-github', action='store_true',
                        help='Skip importing from GitHub OpenTriviaQA')
    parser.add_argument('--skip-triviaapi', action='store_true',
                        help='Skip importing from The Trivia API')
    parser.add_argument('--only-triviaapi', action='store_true',
                        help='Only import from The Trivia API (skip others)')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Show detailed progress and sample questions')
    parser.add_argument('--stats-only', action='store_true',
                        help='Only display database statistics, do not import')
    
    args = parser.parse_args()
    
    # Handle stats-only mode
    if args.stats_only:
        async def show_stats():
            db = TriviaDatabase()
            stats = await db.get_database_stats()
            logger.info("="*70)
            logger.info("TRIVIA DATABASE STATISTICS")
            logger.info("="*70)
            logger.info(f"Total Categories: {stats['total_categories']}")
            logger.info(f"Total Questions: {stats['total_questions']}")
            logger.info(f"Total Attempts: {stats['total_attempts']}")
            logger.info(f"\nTop Categories:")
            for cat in stats['top_categories']:
                logger.info(f"  - {cat['name']}: {cat['count']} questions")
            logger.info("="*70)
            db.close()
        
        asyncio.run(show_stats())
        sys.exit(0)
    
    # Handle --only-triviaapi flag
    if args.only_triviaapi:
        args.skip_opentdb = True
        args.skip_github = True
        args.skip_triviaapi = False
    
    enhancer = TriviaEnhancer(
        skip_opentdb=args.skip_opentdb,
        skip_github=args.skip_github,
        skip_triviaapi=args.skip_triviaapi,
        verbose=args.verbose
    )
    
    try:
        asyncio.run(enhancer.run())
    except KeyboardInterrupt:
        logger.info("\n\nEnhancement interrupted by user")
        total_imported = enhancer.stats['opentdb_imported'] + enhancer.stats['github_imported'] + enhancer.stats['triviaapi_imported']
        logger.info(f"Partial results: {total_imported} questions imported")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
