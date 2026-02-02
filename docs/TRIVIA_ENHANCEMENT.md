# Trivia Database Enhancement

## Overview

The `broaden_trivia.py` script is a maintenance tool for importing trivia questions from external sources into the bot's local trivia database. The bot uses this database for:
- **Automated trivia airdrops** - Claiming trivia drops from tip.cc
- **Interactive trivia games** - Users can play trivia via the `play_trivia` tool
- **Learning system** - Records unknown questions and learns from successful answers

## Current Database Status

As of last update:
- **48,841 questions** across **35 categories**
- **84 trivia attempts** recorded
- Top categories: General Knowledge (7,179), Geography (6,006), Entertainment: Music (5,826)

## Usage

### Quick Commands

```bash
# Show current database statistics
python broaden_trivia.py --stats-only

# Import from all sources (OpenTDB + GitHub)
python broaden_trivia.py

# Import from OpenTDB only
python broaden_trivia.py --skip-github

# Import from GitHub only
python broaden_trivia.py --skip-opentdb

# Verbose mode with sample questions
python broaden_trivia.py --verbose
```

### Command-Line Options

- `--stats-only` - Display database statistics without importing
- `--skip-opentdb` - Skip importing from OpenTDB API
- `--skip-github` - Skip importing from GitHub OpenTriviaQA
- `--verbose, -v` - Show detailed progress and sample questions
- `--help, -h` - Show help message

## Data Sources

### 1. OpenTDB (Open Trivia Database)
- **URL**: https://opentdb.com
- **Format**: JSON API with session tokens
- **Categories**: ~24 categories covering general knowledge, entertainment, science, etc.
- **Rate Limiting**: 5-second delay between category requests
- **Batch Size**: 50 questions per category per run

### 2. GitHub OpenTriviaQA
- **Repository**: uberspot/OpenTriviaQA
- **Format**: Text files with `#Q` (question) and `^` (answer) markers
- **Categories**: 20+ categories mapped to standard names
- **Processing**: Chunks of 500 questions to prevent database locking

## Features

### Smart Duplicate Detection
The script automatically skips questions that already exist in the database, preventing duplicates while still allowing you to re-run the script safely.

### Statistics Tracking
After each run, the script displays:
- Total questions added
- Categories added
- Breakdown by source (OpenTDB vs GitHub)
- Number of duplicates skipped
- Any errors encountered

### Progress Reporting
- Real-time category processing updates
- Before/after comparison
- Top categories listing
- Detailed summary at completion

## How It Works

1. **Database Check**: Retrieves current database statistics
2. **Source Processing**:
   - Fetches categories from each enabled source
   - Downloads questions in batches
   - Normalizes category names and formats
   - HTML-unescapes question/answer text
3. **Import**: Bulk imports questions with duplicate checking
4. **Summary**: Displays comprehensive statistics and changes

## Category Mapping

The script maps GitHub category names to standard database categories:

- `animals` → Animals
- `brain-teasers` → Brain Teasers
- `entertainment` → Entertainment: General
- `geography` → Geography
- `history` → History
- `movies` → Entertainment: Film
- `music` → Entertainment: Music
- `science-technology` → Science & Nature
- `sports` → Sports
- `television` → Entertainment: Television
- `video-games` → Entertainment: Video Games

## When to Run

### Run this script when:
- ✅ You want to refresh the database with new questions
- ✅ External sources have been updated
- ✅ You need more variety in trivia categories
- ✅ Certain categories are running low on questions

### Don't run when:
- ❌ The database already has sufficient questions (48K+ is very comprehensive)
- ❌ You're actively using the bot (to avoid database locking)
- ❌ You just ran it recently (questions don't change frequently)

## Error Handling

The script includes comprehensive error handling:
- **Rate Limiting**: Automatic delays to respect API limits
- **Timeout Handling**: Graceful handling of slow/failed requests
- **Keyboard Interrupt**: Clean exit with partial results summary
- **Database Errors**: Transaction rollback and detailed logging
- **Network Errors**: Continues processing other categories on failure

## Technical Details

### Database Structure
- **trivia_categories**: Category metadata
- **trivia_questions**: Questions with answers, difficulty, source tracking
- **trivia_stats**: Usage statistics and performance metrics
- **trivia_cache**: Cached question sets for performance

### Performance
- Async/await for concurrent operations
- Chunked processing to avoid memory issues
- ThreadPoolExecutor for database operations
- 5-second politeness delay between OpenTDB requests
- 1-second delay between GitHub requests

## Troubleshooting

### "Imported 0 questions"
This is normal when:
- All questions from that source already exist in the database
- The database has been recently updated
- External source hasn't added new questions

**Solution**: This is expected behavior. The database is already well-populated.

### Network Errors
**Solution**: Check internet connection and try again. The script will continue processing other categories.

### Database Locked Errors
**Solution**: Ensure the bot isn't running while importing questions.

## Example Output

```
======================================================================
Trivia Database Enhancement Starting
======================================================================
Before - Categories: 35, Questions: 48841
Top categories: General Knowledge (7179), Geography (6006), Entertainment: Music (5826)
======================================================================

[1/2] Processing OpenTDB (Open Trivia Database)
----------------------------------------------------------------------
Found 24 categories to process from OpenTDB
  [1/24] General Knowledge
  Imported 0/50 questions for General Knowledge from OpenTDB (50 duplicates)
  ...

[2/2] Processing GitHub OpenTriviaQA
----------------------------------------------------------------------
Found 20 categories to process from GitHub
  [1/20] animals
  Imported 142/500 questions for Animals from GitHub (358 duplicates)
  ...

======================================================================
ENHANCEMENT COMPLETE - SUMMARY
======================================================================
Questions Added: 142 (from 48841 to 48983)
Categories Added: 0 (from 35 to 35)

Breakdown:
  - OpenTDB imports: 0
  - GitHub imports: 142
  - Duplicates skipped: 1158
  - Errors encountered: 0

Top categories after enhancement:
  - General Knowledge: 7179 questions
  - Geography: 6006 questions
  - Entertainment: Music: 5826 questions
  - Entertainment: Television: 5417 questions
  - Entertainment: Film: 4544 questions
======================================================================
```

## Related Files

- `data/trivia_database.py` - Database management class
- `utils/trivia_manager.py` - Runtime trivia manager for bot
- `data/trivia.db` - SQLite database file
- `bot/client.py` - Trivia airdrop automation
- `tools/tool_manager.py` - play_trivia tool implementation

## Future Enhancements

Potential improvements:
- [ ] Additional trivia sources (Jeopardy!, Sporcle, etc.)
- [ ] Category-specific import (import only certain categories)
- [ ] Question difficulty analysis and balancing
- [ ] Automated scheduled imports
- [ ] Export functionality for sharing question sets
- [ ] Web scraping for real-time trivia sources
