# SSL Certificate Issue Workaround

**Date:** 2026-02-02  
**Status:** Temporary workaround in place

## Issue

The `%models` command was failing with:
```
Could not find a suitable TLS CA certificate bundle, invalid path: 
/home/chubb/bots/JakeySelfBot/venv/lib/python3.11/site-packages/certifi/cacert.pem
```

## Root Cause

The `curl_cffi` package (used as a dependency) had SSL certificate path issues:
- Upgraded from 0.13.0 to 0.14.0
- Issue persisted even after upgrade
- Error only occurs when fetching OpenRouter models list via certain code paths
- Local API (localhost:8317) works fine with `requests` package

## Workaround Applied

**File:** `bot/commands.py` (lines ~850-860)

**Change:** Commented out OpenRouter model listing in `%models` command

```python
# Show recommended OpenRouter models (commented out due to SSL issues)
# response += "**OPENROUTER MODELS**\n"
# response += "*Best for tool calling & conversation*\n\n"
# for model, desc in RECOMMENDED_MODELS:
#     response += f"`{model}` - {desc}\n"
```

## What Still Works

✅ **All bot functionality**:
- AI responses with local models
- AI responses with OpenRouter models (when used directly)
- Tool calling / function calling
- Model switching via `%model <name>`
- All other commands

✅ **%models command**:
- Shows local models (localhost:8317)
- Shows recommendations with tool support indicators
- Shows models to avoid

❌ **What's temporarily disabled**:
- OpenRouter model listing in `%models` output
- (Models still work, just don't show in the list)

## Testing

```bash
# This command now works without SSL errors:
%models

# Output shows only local models:
**LOCAL MODELS** (OpenAI-Compatible)
*Endpoint: http://localhost:8317/v1*

**⭐ RECOMMENDED:**
`qwen3-coder-plus` - Best overall - fast, coherent, tool support ✅
...
```

## Permanent Fix (Future)

To properly fix this issue, investigate:

1. **Why curl_cffi fails in Discord bot context** but works from command line
2. **Alternative packages**: Consider replacing curl_cffi dependency
3. **Environment variables**: Check if `CURL_CA_BUNDLE` or similar is needed
4. **OpenRouter API client**: Review if it's using curl_cffi directly

## Reverting the Workaround

When the permanent fix is found, uncomment lines in `bot/commands.py`:

```python
# Uncomment these lines:
response += "**OPENROUTER MODELS**\n"
response += "*Best for tool calling & conversation*\n\n"
for model, desc in RECOMMENDED_MODELS:
    response += f"`{model}` - {desc}\n"
```

## Related Files

- `bot/commands.py` - Contains the workaround
- `docs/BUGFIX_2026-02-02.md` - Full debugging session
- `docs/MODEL_RECOMMENDATIONS.md` - Model recommendations

---

*Note: Bot is fully functional with this workaround. OpenRouter models work fine when used directly, they just don't show in the `%models` listing.*
