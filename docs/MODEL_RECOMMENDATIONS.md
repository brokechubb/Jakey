# Model Recommendations for JakeySelfBot

## Local Models (OpenAI-Compatible @ localhost:8317)

### ✅ RECOMMENDED - Full Tool Support

**Best for production use - these models support all 42 function/tool calls without issues:**

1. **`qwen3-coder-plus`** ⭐ BEST OVERALL
   - Fast responses (2-4s)
   - Coherent output
   - Full tool support ✅
   - Good for: General conversation, tool usage, coding

2. **`qwen3-max`** ⭐ HIGH QUALITY
   - Excellent for complex tasks
   - Full tool support ✅
   - Slower but more accurate
   - Good for: Complex reasoning, detailed responses

3. **`gemini-2.5-flash`** ⭐ FAST
   - Very quick responses
   - Reliable and stable
   - Full tool support ✅
   - Good for: Quick answers, simple tasks

### 🔧 RECOMMENDED - Without Tools

**These models work well but CANNOT use function calling (tools disabled automatically):**

4. **`glm-4.6`**
   - Stable and coherent
   - No tool support 🔧
   - Good for: Conversation only, no web search/crypto prices

5. **`deepseek-v3` / `deepseek-v3.1` / `deepseek-v3.2`**
   - Very intelligent
   - **CORRUPTED with tools** - tools disabled automatically ❌
   - Good for: Conversation only when tools aren't needed

### ❌ AVOID - Broken/Unstable

**DO NOT USE these models - they produce garbled output:**

- **`qwen3-coder-flash`** - Produces complete garbage with tools
- **`glm4.5-air`** - Unstable, random corruption

---

## OpenRouter Models (Fallback)

Use these when local endpoint is unavailable:

1. **`tngtech/deepseek-r1t2-chimera:free`** - 671B MoE, strong reasoning
2. **`qwen/qwen3-coder:free`** - 480B MoE, best for coding
3. **`openai/gpt-oss-120b:free`** - 120B MoE, native function calling
4. **`meta-llama/llama-3.3-70b-instruct:free`** - 70B, reliable multilingual

---

## How Tool Support Works

### Automatic Detection

The bot automatically detects model capabilities:

```python
# In bot/client.py
model_supports_tools = self._model_supports_tools(self.current_model)
if not model_supports_tools:
    logger.info(f"Model '{self.current_model}' does not support tools, disabling function calling")
    available_tools = None
```

### Blacklist (No Tools)

Models in this list will NEVER receive tool definitions:

- `qwen3-coder-flash`
- `deepseek-v3`, `deepseek-v3.1`, `deepseep-v3.2`
- `glm4.5-air`

### Whitelist (Tools Enabled)

Models in this list are trusted with full tool access:

- `qwen3-coder-plus`
- `qwen3-max`
- `gemini-2.5-flash`
- All OpenRouter models with "instruct", "chat", "gpt", "claude", etc.

---

## Usage Examples

### Switch to Best Model
```
%model qwen3-coder-plus
```

### Check Available Models
```
%models
```

### Use Model Without Tools (for conversation only)
```
%model glm-4.6
```

---

## Troubleshooting

### Getting Garbled Output?

1. Check current model: `%model`
2. Switch to recommended model: `%model qwen3-coder-plus`
3. Check logs for "blacklist" messages

### Model Not Using Tools?

This is **intentional** if the model is blacklisted. Some models produce garbage when given tool definitions.

To verify:
```bash
tail -f /home/chubb/bots/JakeySelfBot/logs/jakey_selfbot.log | grep -E "blacklist|does not support tools"
```

You should see:
```
INFO bot.client Model 'deepseek-v3' is blacklisted from using tools
INFO bot.client Model 'deepseek-v3' does not support tools, disabling function calling
```

### Want to Force Tools On a Blacklisted Model?

**DON'T!** The blacklist exists because these models produce corrupted output with tools. Use a whitelisted model instead.

---

## Default Model

Current default: **`qwen3-coder-plus`** (set in `.env`)

```bash
OPENAI_COMPAT_DEFAULT_MODEL=qwen3-coder-plus
```

---

Last Updated: 2026-02-02
