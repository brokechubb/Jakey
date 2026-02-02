# Additional Trivia Sources Research

## Overview
Research into additional trivia API sources that can be integrated into `broaden_trivia.py` to expand the question database beyond the current OpenTDB and GitHub OpenTriviaQA sources.

## Discovered Sources

### 1. **jService.io (Jeopardy! API)** ⭐ RECOMMENDED
- **URL**: http://jservice.io/api/
- **Format**: JSON API
- **Content**: Real Jeopardy! questions and answers
- **Cost**: FREE, no API key required
- **Questions**: 150,000+ authentic Jeopardy! clues
- **Categories**: Extensive, includes category titles, values, and air dates
- **Rate Limiting**: Unknown (would need to implement politeness delays)

**Endpoints:**
```
GET /api/random          # Get random question
GET /api/questions       # Get questions with filters
GET /api/categories      # Get all categories
GET /api/category?id=X   # Get questions in a category
```

**Example Response:**
```json
{
  "id": 123456,
  "answer": "Gold",
  "question": "The chemical symbol Au represents this precious metal",
  "value": 200,
  "airdate": "2010-05-15T12:00:00.000Z",
  "category": {
    "id": 789,
    "title": "Chemistry",
    "clues_count": 50
  }
}
```

**Pros:**
- ✅ Large dataset (150K+ questions)
- ✅ High-quality, professionally written questions
- ✅ Free with no authentication
- ✅ Multiple filtering options
- ✅ Real Jeopardy! data (authentic)

**Cons:**
- ⚠️ Question format is "answer-first" (Jeopardy! style) - would need conversion
- ⚠️ No documented rate limits
- ⚠️ API can be slow/unreliable at times

---

### 2. **The Trivia API** ⭐ RECOMMENDED (with limitations)
- **URL**: https://the-trivia-api.com/
- **Format**: JSON API
- **Content**: Vetted trivia questions with multiple choice answers
- **Cost**: FREE for non-commercial, paid for commercial
- **Questions**: 12,802 vetted questions
- **Categories**: 10 categories (Science, History, Geography, Film, Music, Arts & Literature, Sport & Leisure, General Knowledge, Food & Drink, Geography)
- **Difficulty Levels**: Easy, Medium, Hard
- **Languages**: English + 6 professional translations (paid tier)

**Free Tier Endpoints:**
```
GET /v2/questions                    # Get random questions
GET /v2/questions?limit=50           # Get specific number
GET /v2/questions?categories=science # Filter by category
GET /v2/questions?difficulties=hard  # Filter by difficulty
```

**Example Response:**
```json
{
  "id": "abc123",
  "category": "science",
  "question": {
    "text": "What is the chemical symbol for gold?"
  },
  "correctAnswer": "Au",
  "incorrectAnswers": ["Go", "Gd", "Ag"],
  "tags": ["chemistry", "elements"],
  "difficulty": "medium"
}
```

**Pros:**
- ✅ Clean, well-documented API
- ✅ Multiple choice format ready to use
- ✅ Difficulty ratings
- ✅ Active development (new questions added regularly)
- ✅ Professional quality
- ✅ Session management to avoid duplicates

**Cons:**
- ⚠️ Smaller dataset (12.8K vs 150K)
- ⚠️ Non-commercial license only for free tier
- ⚠️ Would need API key for commercial use
- ⚠️ Rate limits on free tier

**License Note:** Your bot may qualify as non-commercial if it's for personal use, but would need paid subscription if monetized.

---

### 3. **API Ninjas - Trivia API**
- **URL**: https://api-ninjas.com/api/trivia
- **Format**: JSON API
- **Content**: Trivia questions across multiple categories
- **Cost**: FREE tier available (requires API key)
- **Rate Limiting**: 10,000 requests/month on free tier

**Endpoint:**
```
GET https://api.api-ninjas.com/v1/trivia?category=sciencenature
Headers: X-Api-Key: YOUR_API_KEY
```

**Pros:**
- ✅ Free tier available
- ✅ Category filtering
- ✅ Simple API

**Cons:**
- ⚠️ Requires API key registration
- ⚠️ Monthly request limit
- ⚠️ Smaller dataset

---

### 4. **GitHub Repositories with Trivia Data**

**manyoso/haltt4llm**
- **URL**: https://github.com/manyoso/haltt4llm
- **Content**: Trivia questions specifically designed to test LLM hallucinations
- **Format**: Multiple choice with "I don't know" and "None of the above" options
- **Unique Feature**: Includes fake/trick questions to test hallucination detection
- **Size**: Moderate dataset

**QuartzWarrior/OTDB-Source** (currently in use)
- Already integrated

---

## Recommended Integration Plan

### Phase 1: Add jService.io (Highest Priority)
**Rationale:** 150K+ questions, free, no authentication, large dataset

**Implementation:**
1. Add `JServiceProvider` class to `broaden_trivia.py`
2. Implement category fetching and mapping
3. Convert Jeopardy! answer-first format to standard Q&A format
4. Add politeness delays (2-3 seconds between requests)
5. Batch import questions by category

**Estimated Addition:** 50,000-100,000 new questions (after deduplication)

---

### Phase 2: Add The Trivia API (Secondary Priority)
**Rationale:** High quality, good for diversity, but smaller dataset

**Considerations:**
- Verify non-commercial use qualifies for free tier
- Implement with API key support (optional)
- Use multiple choice answers for enhanced question data
- Respect rate limits

**Estimated Addition:** 5,000-10,000 new questions

---

### Phase 3: Consider API Ninjas
**Rationale:** Additional source for diversity, but requires API key

**Considerations:**
- Requires user to obtain API key
- Monthly request limits might be restrictive
- Best used as supplementary source

---

## Implementation Priority Matrix

| Source | Ease | Value | Quality | Maintenance | Priority |
|--------|------|-------|---------|-------------|----------|
| jService.io | High | Very High | High | Low | 🥇 **1st** |
| The Trivia API | Medium | High | Very High | Low | 🥈 **2nd** |
| API Ninjas | Low | Medium | Medium | Medium | 🥉 **3rd** |
| GitHub repos | High | Low | Varies | High | **Future** |

---

## Proposed Script Enhancements

```python
# Add new command-line options
python broaden_trivia.py --source jservice        # Only jService.io
python broaden_trivia.py --source trivia-api      # Only The Trivia API
python broaden_trivia.py --source all             # All sources
python broaden_trivia.py --limit-per-category 100 # Limit questions per category
```

---

## Next Steps

1. **Implement jService.io integration** (highest ROI)
   - Test API endpoints
   - Create provider class
   - Add category mapping
   - Implement answer-first conversion
   
2. **Test The Trivia API**
   - Verify licensing for your use case
   - Test free tier endpoints
   - Implement if suitable

3. **Document sources in trivia database**
   - Track which questions came from which source
   - Enable source-based filtering if needed

4. **Add source statistics**
   - Show breakdown by source in `--stats-only`
   - Track source reliability

---

## Sample jService.io Integration Code

```python
async def fetch_jservice_random(self, session: aiohttp.ClientSession, count: int = 100):
    \"\"\"Fetch random questions from jService.io\"\"\"
    url = f"http://jservice.io/api/random?count={count}"
    
    try:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
            if resp.status == 200:
                questions = await resp.json()
                
                formatted_questions = []
                for q in questions:
                    # Convert Jeopardy! format: answer → question
                    # Original: answer="Gold", question="The chemical symbol Au"
                    # Converted: question="What is Au the chemical symbol for?", answer="Gold"
                    
                    category = q.get('category', {}).get('title', 'General Knowledge')
                    question_text = q.get('question', '').strip()
                    answer_text = q.get('answer', '').strip()
                    value = q.get('value', 100)
                    
                    # Map value to difficulty (100-400=easy, 600-800=medium, 1000+=hard)
                    difficulty = 1 if value <= 400 else 2 if value <= 800 else 3
                    
                    if question_text and answer_text:
                        formatted_questions.append({
                            'category': category,
                            'question': question_text,
                            'answer': answer_text,
                            'difficulty': difficulty,
                            'source': 'jService',
                            'external_id': q.get('id')
                        })
                
                return formatted_questions
                
    except Exception as e:
        logger.error(f"Error fetching from jService: {e}")
        return []
```

---

## Questions to Consider

1. **Commercial Use**: Is your bot commercial or non-commercial?
   - If commercial, The Trivia API requires paid subscription
   - jService.io has no commercial restrictions mentioned

2. **Question Quality**: Do you want:
   - More questions (jService: 150K)
   - Better quality (The Trivia API: vetted)
   - Both (implement both sources)

3. **Maintenance**: How often to run the script?
   - Weekly for new questions from The Trivia API
   - Monthly for jService.io bulk imports
   - On-demand when needed

4. **Storage**: Your database currently has 48.8K questions
   - Adding jService could 3-4x this size
   - Ensure adequate disk space (current trivia.db is 15MB)

---

## Conclusion

**Immediate Action:** Implement jService.io integration
- Largest potential addition (100K+ questions)
- Free and unrestricted
- Well-documented API
- Easy to integrate

**Secondary Action:** Evaluate The Trivia API
- Smaller but high-quality addition
- Verify licensing compliance
- Consider for premium categories

**Future:** Monitor for new trivia APIs and datasets as they emerge
