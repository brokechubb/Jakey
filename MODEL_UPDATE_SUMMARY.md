# Model Configuration Update Summary

**Date**: 2026-01-29
**Purpose**: Fix invalid model references and update recommended models with valid OpenRouter free models

## Default Model

**arcee-ai/trinity-mini:free** 🔶
- **Size**: 26B Mixture-of-Experts (3B active parameters)
- **Context**: 131,072 tokens
- **Architecture**: text->text
- **Specialty**: Sparse MoE with efficient inference
- **Status**: Current default model (set in .env)

## Issues Found

### Invalid Models Removed
1. **xiaomi/mimo-v2-flash:free** ❌
   - This model exists but is NOT free (it's a paid model: $0.09/1M tokens)
   - Was incorrectly listed in FUNCTION_CALLING_MODELS, WORKING_MODELS, FALLBACK_MODELS

2. **mistralai/devstral-2512:free** ❌
   - This model exists but is NOT free (it's a paid model: $0.22/1M tokens)
   - Was incorrectly listed in WORKING_MODELS and FALLBACK_MODELS

## Changes Made

### 1. FUNCTION_CALLING_MODELS (config.py)
**Before:**
```python
[
    "xiaomi/mimo-v2-flash:free",          # ❌ NOT FREE
    "nvidia/nemotron-nano-12b-v2-vl:free",
    "nvidia/nemotron-nano-9b-v2:free",
    "openai/gpt-oss-120b:free",
    "qwen/qwen3-coder:free",
]
```

**After:**
```python
[
    "arcee-ai/trinity-mini:free",          # ✅ 🔶 Default model - 26B MoE
    "qwen/qwen3-coder:free",              # ✅ 480B MoE coder - excellent for tools
    "nvidia/nemotron-nano-12b-v2-vl:free", # ✅ Multimodal with vision
    "nvidia/nemotron-nano-9b-v2:free",    # ✅ Compact 9B instruction model
    "openai/gpt-oss-120b:free",           # ✅ Large 120B MoE
    "meta-llama/llama-3.3-70b-instruct:free", # ✅ Reliable
]
```

### 2. WORKING_MODELS (config.py)
**Before:**
```python
[
    "meta-llama/llama-3.3-70b-instruct:free",
    "xiaomi/mimo-v2-flash:free",          # ❌ NOT FREE
    "openai/gpt-oss-120b:free",
    "mistralai/devstral-2512:free",       # ❌ NOT FREE
]
```

**After:**
```python
[
    "arcee-ai/trinity-mini:free",          # ✅ 🔶 Default model
    "meta-llama/llama-3.3-70b-instruct:free", # ✅ Reliable
    "qwen/qwen3-coder:free",              # ✅ MoE coder
    "nvidia/nemotron-3-nano-30b-a3b:free", # ✅ 30B MoE with 256k context
    "openai/gpt-oss-120b:free",           # ✅ 120B MoE
    "nvidia/nemotron-nano-9b-v2:free",    # ✅ Compact fallback
]
```

### 3. FALLBACK_MODELS (config.py)
**Before:**
```python
[
    "nvidia/nemotron-nano-9b-v2:free",
    "meta-llama/llama-3.3-70b-instruct:free",
    "xiaomi/mimo-v2-flash:free",          # ❌ NOT FREE
    "openai/gpt-oss-120b:free",
    "mistralai/devstral-2512:free",       # ❌ NOT FREE
]
```

**After:**
```python
[
    "arcee-ai/trinity-mini:free",          # ✅ 🔶 Default model fallback
    "nvidia/nemotron-nano-9b-v2:free",    # ✅ Most reliable fallback
    "meta-llama/llama-3.3-70b-instruct:free", # ✅ Quality fallback
    "qwen/qwen3-coder:free",              # ✅ Tool-calling fallback
    "openai/gpt-oss-120b:free",           # ✅ Large model fallback
    "nvidia/nemotron-nano-12b-v2-vl:free", # ✅ Multimodal fallback
]
```

### 4. RECOMMENDED_MODELS (config.py)
**Before:**
```python
[
    ("meta-llama/llama-3.3-70b-instruct:free", "Jakey's default - reliable, clean responses"),
    ("xiaomi/mimo-v2-flash:free", "Fast reasoning model..."),              # ❌
    ("nvidia/nemotron-nano-12b-v2-vl:free", "NVIDIA's compact multimodal model"),
    ("nvidia/nemotron-nano-9b-v2:free", "NVIDIA's compact 9B instruction model"),
    ("openai/gpt-oss-120b:free", "Large 120B parameter open-source model"),
    ("mistralai/devstral-2512:free", "Mistral's development model..."),    # ❌
]
```

**After:**
```python
[
    ("arcee-ai/trinity-mini:free", "Jakey's current default - 26B MoE with 3B active parameters"),
    ("meta-llama/llama-3.3-70b-instruct:free", "Reliable 70B model - clean responses, great for general use"),
    ("qwen/qwen3-coder:free", "Mixture-of-Experts coder - excellent for tool calling and coding"),
    ("nvidia/nemotron-nano-12b-v2-vl:free", "NVIDIA's multimodal model with vision support"),
    ("nvidia/nemotron-nano-9b-v2:free", "NVIDIA's compact 9B instruction model"),
    ("openai/gpt-oss-120b:free", "Large 120B parameter MoE open-source model"),
    ("nvidia/nemotron-3-nano-30b-a3b:free", "NVIDIA's 30B MoE model with 256k context"),
    ("nousresearch/hermes-3-llama-3.1-405b:free", "Hermes 3 - improved Llama 405B model"),
    ("meta-llama/llama-3.1-405b-instruct:free", "Meta's massive 405B parameter model"),
]
```

### 5. QUICK_MODEL_SUGGESTIONS (config.py)
**Before:**
```python
[
    "nvidia/nemotron-nano-9b-v2:free",
    "meta-llama/llama-3.3-70b-instruct:free",
    "xiaomi/mimo-v2-flash:free",          # ❌
]
```

**After:**
```python
[
    "arcee-ai/trinity-mini:free",         # ✅ 🔶 Default
    "nvidia/nemotron-nano-9b-v2:free",
    "meta-llama/llama-3.3-70b-instruct:free",
    "qwen/qwen3-coder:free",
]
```

## New Model Details

### arcee-ai/trinity-mini:free 🔶
- **Size**: 26B Mixture-of-Experts (3B active parameters)
- **Context**: 131,072 tokens
- **Architecture**: text->text
- **Specialty**: Sparse MoE with efficient inference
- **Why added**: Current default model, fast and efficient for general use

### qwen/qwen3-coder:free
- **Size**: 480B Mixture-of-Experts (35B active parameters)
- **Context**: 262,000 tokens
- **Architecture**: text->text
- **Specialty**: Code generation and tool calling
- **Why added**: Excellent function calling capabilities, replaces xiaomi/mimo-v2-flash

### nvidia/nemotron-3-nano-30b-a3b:free
- **Size**: 30B Mixture-of-Experts
- **Context**: 256,000 tokens
- **Architecture**: text->text
- **Specialty**: High efficiency, largest context window
- **Why added**: Excellent fallback with massive context

### nousresearch/hermes-3-llama-3.1-405b:free
- **Size**: 405B parameters
- **Context**: 131,072 tokens
- **Architecture**: text->text
- **Specialty**: General purpose, improved over Llama 3.1
- **Why added**: High-quality large model option

### meta-llama/llama-3.1-405b-instruct:free
- **Size**: 405B parameters
- **Context**: 131,072 tokens
- **Architecture**: text->text
- **Specialty**: Meta's flagship open model
- **Why added**: Massive parameter model for complex tasks

## Verification

All models have been verified against OpenRouter's API:
- ✅ All configured models are valid and available
- ✅ All models are truly free (no token costs)
- ✅ All models have context windows >= 128k tokens
- ✅ All models support function calling where needed

## Impact

### Positive Changes
1. **No more failed requests** due to invalid model references
2. **Better tool calling** with qwen/qwen3-coder:free
3. **More fallback options** with valid free models
4. **Better %models command** with accurate model list

### Model Quality Improvements
- **Replaced**: 2 invalid paid models with 3 high-quality free models
- **Added**: MoE models (qwen3-coder, gpt-oss-120b, nemotron-3-nano)
- **Added**: Large context models (256k, 262k token context)
- **Added**: Massive parameter models (405B for complex tasks)

## Testing Recommendations

1. **Test %models command**: Verify updated recommended models display correctly
2. **Test tool calling**: Try commands that require multiple tools (web_search, discord_*)
3. **Test fallback**: Verify WORKING_MODELS and FALLBACK_MODELS work correctly
4. **Test model switching**: Use %setmodel to try different models
5. **Monitor logs**: Check for any model-related errors

## Current Model Statistics

**Total Free Models Configured**: 9
**Function Calling Models**: 6
**Working Fallback Models**: 6
**Recommended Models**: 9
**Quick Suggestions**: 4
**Default Model**: arcee-ai/trinity-mini:free (set in .env)

## Model Distribution

### By Size
- **Compact**: arcee-ai/trinity-mini:free (26B MoE, 3B active)
- **Small**: nvidia/nemotron-nano-9b-v2:free (9B)
- **Medium**: meta-llama/llama-3.3-70b-instruct:free (70B)
- **Large**: openai/gpt-oss-120b:free (120B), nvidia/nemotron-nano-12b-v2-vl:free (12B multimodal)
- **Extra Large**: nvidia/nemotron-3-nano-30b-a3b:free (30B MoE), meta-llama/llama-3.1-405b-instruct:free (405B), nousresearch/hermes-3-llama-3.1-405b:free (405B)
- **Coders**: qwen/qwen3-coder:free (480B MoE coder)

### By Context Window
- **262k tokens**: qwen/qwen3-coder:free
- **256k tokens**: nvidia/nemotron-3-nano-30b-a3b:free
- **131k tokens**: arcee-ai/trinity-mini:free, meta-llama/llama-3.3-70b-instruct:free, openai/gpt-oss-120b:free, nousresearch/hermes-3-llama-3.1-405b:free, meta-llama/llama-3.1-405b-instruct:free
- **128k tokens**: nvidia/nemotron-nano-12b-v2-vl:free, nvidia/nemotron-nano-9b-v2:free

## Notes

- The 🔶 marker indicates the current default model (`arcee-ai/trinity-mini:free`)
- The default model is set in `.env` as `OPENROUTER_DEFAULT_MODEL=arcee-ai/trinity-mini:free`
- All models support minimum 128k context window required for complex conversations
- All function calling models are verified to support tool usage
- `meta-llama/llama-3.3-70b-instruct:free` remains Jakey's default recommended model
- All models support the minimum 128k context window required for complex conversations
- All function calling models are verified to support tool usage
