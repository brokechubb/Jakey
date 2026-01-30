# Tool Optimization Plan

**Date**: 2026-01-29
**Status**: 📋 PLANNING PHASE (Awaiting Approval)
**Current State**: 42 tools passed to every AI request

---

## Executive Summary

**Problem**: Sending all 42 tools to every AI request creates:
- Large API payloads (~15-20KB per request)
- Slower model processing (more context to analyze)
- Higher error rates (OpenRouter 502 errors with large payloads)
- Reduced tool selection accuracy (too many choices)

**Goal**: Reduce tool payload size while maintaining all functionality
**Target**: 15-20 tools maximum (60% reduction from current 42)

---

## Current Tool Inventory (42 Tools)

| Category | Count | Tools |
|----------|--------|---------|
| **Core Utility** | 10 | calculate, get_current_time, web_search, company_research, crawling, generate_keno_numbers, search_user_memory, discord_timeout_user, discord_remove_timeout, discord_search_messages |
| **Memory & Reminders** | 6 | set_reminder, list_reminders, cancel_reminder, check_due_reminders, remember_user_info, remember_user_mcp |
| **Discord Info** | 6 | discord_get_user_info, discord_list_guilds, discord_list_channels, discord_read_channel, discord_get_user_roles, get_user_rate_limit_status |
| **Discord Messaging** | 2 | discord_send_message, discord_send_dm |
| **Discord Moderation** | 7 | discord_kick_user, discord_ban_user, discord_unban_user, discord_purge_messages, discord_pin_message, discord_unpin_message, discord_delete_message |
| **Image/Creative** | 2 | generate_image, analyze_image |
| **Crypto/Finance** | 5 | get_crypto_price, get_stock_price, tip_user, check_balance, get_bonus_schedule |
| **Trivia/Gaming** | 1 | play_trivia |
| **Rate Limiting/Admin** | 2 | get_system_rate_limit_stats, reset_user_rate_limits |

---

## Optimization Strategy: Hybrid Approach

### Phase 1: Intelligent Tool Selection (Immediate Impact)

**Concept**: Pass only relevant tools based on message context

**Implementation**:
1. Analyze user message for intent/patterns
2. Select tool category subset based on intent
3. Pass only 10-15 tools for common requests

**Tool Categories for Context-Aware Selection**:

#### A. Basic Request (10 tools)
**When**: General questions, simple queries, no Discord/gambling context
```python
[
    'web_search',
    'calculate',
    'get_current_time',
    'generate_image',
    'analyze_image',
    'remember_user_info',
    'search_user_memory',
    'get_crypto_price',
    'get_stock_price',
    'generate_keno_numbers'
]
```

#### B. Discord Management Request (16 tools)
**When**: User asks about servers, channels, members, or Discord operations
```python
[
    # Core + Discord Info
    'web_search', 'calculate', 'get_current_time',
    'discord_get_user_info', 'discord_list_guilds', 'discord_list_channels',
    'discord_read_channel', 'discord_search_messages', 'discord_list_guild_members',
    'discord_get_user_roles',
    # Discord Messaging
    'discord_send_message', 'discord_send_dm',
    # Memory
    'remember_user_info', 'search_user_memory'
]
```

#### C. Discord Moderation Request (20 tools)
**When**: User mentions kick, ban, timeout, purge, delete, pin
```python
[
    # Core
    'web_search', 'calculate', 'get_current_time',
    # All Discord tools (admin needs full access)
    'discord_get_user_info', 'discord_list_guilds', 'discord_list_channels',
    'discord_read_channel', 'discord_search_messages', 'discord_list_guild_members',
    'discord_get_user_roles', 'discord_send_message', 'discord_send_dm',
    # Moderation tools
    'discord_kick_user', 'discord_ban_user', 'discord_unban_user',
    'discord_timeout_user', 'discord_remove_timeout', 'discord_purge_messages',
    'discord_pin_message', 'discord_unpin_message', 'discord_delete_message',
    # Memory (for tracking moderation actions)
    'remember_user_info', 'search_user_memory'
]
```

#### D. Gambling/Finance Request (15 tools)
**When**: Mentions of stake, bitsler, tips, crypto prices
```python
[
    # Core
    'web_search', 'calculate', 'get_current_time',
    # Crypto/Finance
    'get_crypto_price', 'get_stock_price', 'tip_user', 'check_balance',
    'get_bonus_schedule', 'company_research',
    # Memory
    'remember_user_info', 'search_user_memory',
    # Gaming
    'play_trivia', 'generate_keno_numbers'
]
```

#### E. Reminder Request (10 tools)
**When**: Mentions alarm, timer, reminder, notify
```python
[
    # Core
    'web_search', 'calculate', 'get_current_time',
    # Reminders
    'set_reminder', 'list_reminders', 'cancel_reminder',
    'check_due_reminders',
    # Memory
    'remember_user_info', 'search_user_memory',
    # Discord messaging (for notifications)
    'discord_send_message', 'discord_send_dm'
]
```

**Implementation Details**:
```python
def get_context_aware_tools(message_content: str) -> List[Dict]:
    """Select relevant tools based on message content."""
    content = message_content.lower()

    # Check for moderation keywords
    moderation_keywords = ['kick', 'ban', 'timeout', 'mute', 'purge', 'delete', 'pin', 'unpin']
    if any(kw in content for kw in moderation_keywords):
        return get_tools_by_category('discord_moderation')

    # Check for gambling/finance keywords
    finance_keywords = ['stake', 'bitsler', 'tip', 'crypto', 'price', 'balance', 'bonus', 'stock']
    if any(kw in content for kw in finance_keywords):
        return get_tools_by_category('gambling_finance')

    # Check for reminder keywords
    reminder_keywords = ['alarm', 'timer', 'remind', 'notify', 'schedule']
    if any(kw in content for kw in reminder_keywords):
        return get_tools_by_category('reminder')

    # Check for Discord management keywords
    discord_keywords = ['server', 'guild', 'channel', 'member', 'my roles', 'my servers']
    if any(kw in content for kw in discord_keywords):
        return get_tools_by_category('discord_management')

    # Default: basic tool set
    return get_tools_by_category('basic')
```

**Benefits**:
- ✅ 60-75% reduction in average tool payload size
- ✅ Faster AI processing (less context to analyze)
- ✅ Better tool selection accuracy
- ✅ Reduced 502 error rate

**Drawbacks**:
- ⚠️ May miss edge cases initially
- ⚠️ Requires keyword tuning
- ⚠️ Adds complexity to tool selection logic

---

### Phase 2: Tool Consolidation (Medium Impact)

**Concept**: Merge similar tools into unified operations with action parameters

#### Consolidation 1: Memory Tools (6 → 2 tools)

**Current**:
- `remember_user_info` - Store user info in SQLite
- `search_user_memory` - Search user info in SQLite
- `remember_user_mcp` - Store user info in MCP
- `set_reminder` - Set reminder
- `list_reminders` - List reminders
- `cancel_reminder` - Cancel reminder

**Optimized**:
```python
'user_memory': {
    'description': 'Manage user information and reminders (read, write, search)',
    'parameters': {
        'action': {
            'type': 'string',
            'enum': ['store', 'retrieve', 'search'],
            'description': 'Action to perform'
        },
        'user_id': {'type': 'string'},
        'information_type': {'type': 'string'},
        'information': {'type': 'string'},
        'query': {'type': 'string'}
    }
}

'reminder_manage': {
    'description': 'Manage reminders (set, list, cancel, check)',
    'parameters': {
        'action': {
            'type': 'string',
            'enum': ['set', 'list', 'cancel', 'check'],
            'description': 'Reminder action'
        },
        'user_id': {'type': 'string'},
        'reminder_id': {'type': 'integer'},
        'reminder_type': {'type': 'string'},
        'title': {'type': 'string'},
        'description': {'type': 'string'},
        'trigger_time': {'type': 'string'},
        'channel_id': {'type': 'string'},
        'recurring_pattern': {'type': 'string'}
    }
}
```

**Reduction**: 6 → 2 tools (67% reduction)

---

#### Consolidation 2: Discord Moderation (7 → 2 tools)

**Current**:
- `discord_kick_user`, `discord_ban_user`, `discord_unban_user`, `discord_timeout_user`, `discord_remove_timeout`, `discord_purge_messages`, `discord_pin_message`, `discord_unpin_message`, `discord_delete_message`

**Optimized**:
```python
'discord_moderate_user': {
    'description': 'Moderate user with various actions (kick, ban, unban, timeout)',
    'parameters': {
        'action': {
            'type': 'string',
            'enum': ['kick', 'ban', 'unban', 'timeout', 'remove_timeout'],
            'description': 'Moderation action'
        },
        'guild_id': {'type': 'string'},
        'user_id': {'type': 'string'},
        'reason': {'type': 'string'},
        'delete_message_seconds': {'type': 'integer'},
        'duration_minutes': {'type': 'integer'}
    }
}

'discord_manage_messages': {
    'description': 'Manage messages (purge, pin, unpin, delete)',
    'parameters': {
        'action': {
            'type': 'string',
            'enum': ['purge', 'pin', 'unpin', 'delete'],
            'description': 'Message management action'
        },
        'channel_id': {'type': 'string'},
        'message_id': {'type': 'string'},
        'limit': {'type': 'integer'},
        'user_id': {'type': 'string'}
    }
}
```

**Reduction**: 7 → 2 tools (71% reduction)

---

#### Consolidation 3: Discord Info (6 → 2 tools)

**Current**:
- `discord_get_user_info`, `discord_list_guilds`, `discord_list_channels`, `discord_read_channel`, `discord_list_guild_members`, `discord_get_user_roles`

**Optimized**:
```python
'discord_get_info': {
    'description': 'Get Discord information (user info, guilds list, channels list, members list, user roles)',
    'parameters': {
        'target': {
            'type': 'string',
            'enum': ['user', 'guilds', 'channels', 'members', 'roles'],
            'description': 'Information to retrieve'
        },
        'guild_id': {'type': 'string'},
        'limit': {'type': 'number'},
        'include_roles': {'type': 'boolean'}
    }
}

'discord_read_content': {
    'description': 'Read Discord content (channel messages, message search)',
    'parameters': {
        'action': {
            'type': 'string',
            'enum': ['read_channel', 'search_messages'],
            'description': 'Reading action'
        },
        'channel_id': {'type': 'string'},
        'query': {'type': 'string'},
        'author_id': {'type': 'string'},
        'limit': {'type': 'number'}
    }
}
```

**Reduction**: 6 → 2 tools (67% reduction)

---

#### Consolidation 4: Crypto/Finance (5 → 2 tools)

**Current**:
- `get_crypto_price`, `get_stock_price`, `tip_user`, `check_balance`, `get_bonus_schedule`

**Optimized**:
```python
'get_market_price': {
    'description': 'Get price for cryptocurrency or stock',
    'parameters': {
        'asset_type': {
            'type': 'string',
            'enum': ['crypto', 'stock'],
            'description': 'Type of asset'
        },
        'symbol': {'type': 'string'},
        'currency': {'type': 'string', 'default': 'USD'}
    }
}

'tipcc_manage': {
    'description': 'Manage tip.cc operations (tip user, check balance, get bonus schedule)',
    'parameters': {
        'action': {
            'type': 'string',
            'enum': ['tip', 'balance', 'bonus_schedule'],
            'description': 'Tip.cc operation'
        },
        'user_id': {'type': 'string'},
        'amount': {'type': 'string'},
        'currency': {'type': 'string'},
        'site': {'type': 'string'},
        'frequency': {'type': 'string'}
    }
}
```

**Reduction**: 5 → 2 tools (60% reduction)

---

**Total Consolidation Impact**:
- **Before**: 42 tools
- **After**: 15 tools
- **Reduction**: 27 tools (64% overall reduction)

---

### Phase 3: Conditional Tool Loading (Advanced)

**Concept**: Only load tools when they're actually needed

**Implementation**:
```python
class LazyToolManager:
    """Load tools on-demand based on request type"""

    def __init__(self):
        # Always-loaded core tools
        self.core_tools = self._load_core_tools()

        # Lazy-loaded tool categories
        self._discord_tools = None
        self._moderation_tools = None
        self._finance_tools = None

    def get_tools_for_context(self, context: str) -> List[Dict]:
        """Get only tools needed for current context"""
        tools = self.core_tools.copy()

        if context == 'discord_management':
            if self._discord_tools is None:
                self._discord_tools = self._load_discord_tools()
            tools.extend(self._discord_tools)

        elif context == 'moderation':
            if self._moderation_tools is None:
                self._moderation_tools = self._load_moderation_tools()
            tools.extend(self._moderation_tools)

        return tools
```

**Benefits**:
- ✅ Memory efficiency (only load needed tools)
- ✅ Faster initialization
- ✅ Reduced payload for simple requests

---

## Implementation Plan

### Step 1: Quick Win - Context-Aware Selection (Week 1)
**Priority**: HIGH
**Effort**: LOW
**Impact**: MEDIUM-HIGH

**Tasks**:
1. Create `get_context_aware_tools()` function in `tool_manager.py`
2. Define tool categories (basic, discord, moderation, gambling, reminder)
3. Update `client.py` to use context-aware selection
4. Add logging for selected tool category
5. Test with various request types
6. Monitor error rate reduction

**Estimated Impact**:
- Tool payload: 42 → 10-20 tools (50-75% reduction)
- API errors: Expect 30-40% reduction in 502 errors
- Response time: 10-20% faster on average

---

### Step 2: Tool Consolidation (Week 2-3)
**Priority**: MEDIUM
**Effort**: HIGH
**Impact**: HIGH

**Tasks**:
1. Consolidate memory/reminder tools (6 → 2)
2. Consolidate moderation tools (7 → 2)
3. Consolidate Discord info tools (6 → 2)
4. Consolidate finance tools (5 → 2)
5. Update backend handlers for consolidated tools
6. Update system prompt to reflect new tool names
7. Test all consolidated operations thoroughly

**Estimated Impact**:
- Tool payload: 10-20 → 15 tools maximum
- Code complexity: Reduced (fewer tool handlers)
- Maintenance: Easier (fewer tools to maintain)

---

### Step 3: Advanced Optimization (Week 4)
**Priority**: LOW
**Effort**: HIGH
**Impact**: MEDIUM

**Tasks**:
1. Implement `LazyToolManager` class
2. Add tool usage analytics
3. Implement dynamic tool caching
4. A/B test against context-aware approach
5. Keep best performing approach

**Estimated Impact**:
- Memory: 20-30% reduction
- Startup time: 10-15% faster

---

## Risk Assessment

### Technical Risks

| Risk | Probability | Impact | Mitigation |
|-------|-------------|--------|-------------|
| AI doesn't select correct tool | Medium | High | Add fallback to full tool set on errors |
| Consolidated tools fail | Low | High | Keep original tools as backup |
| Context detection misses intent | Medium | Medium | Log mismatches, tune keywords |
| User confusion with new tool names | Low | Medium | Update system prompt with examples |

### Business Risks

| Risk | Probability | Impact | Mitigation |
|-------|-------------|--------|-------------|
| Feature regression | Low | High | Comprehensive testing before deploy |
| User complaints about tool changes | Medium | Low | Clear communication of changes |

---

## Success Metrics

### Performance Targets

- **Tool Payload Size**: 15-20 tools average (60% reduction)
- **502 Error Rate**: Reduce by 40% (from current levels)
- **Response Time**: 15% faster on average
- **Tool Selection Accuracy**: >95% correct category selection

### Monitoring Metrics

```python
# Add to logging in tool_manager.py
logger.info(f"Tool Selection: context={context}, category={category}, count={len(tools)}")
logger.info(f"Tool Selection: model={model}, payload_size_kb={len(json.dumps(tools))/1024:.1f}")
```

---

## Recommended Approach

### Option A: Conservative (Recommended) ⭐
**Implement**: Phase 1 only (Context-Aware Selection)
**Timeline**: 1 week
**Risk**: LOW
**Benefits**:
- Quick win
- Minimal code changes
- Easy to rollback
- Significant impact (50-75% tool reduction)

**When to choose**:
- Want quick improvement
- Concerned about breaking changes
- Want to validate approach

---

### Option B: Aggressive
**Implement**: Phase 1 + Phase 2 (Context + Consolidation)
**Timeline**: 3 weeks
**Risk**: MEDIUM
**Benefits**:
- Maximum optimization
- Cleanest architecture
- Best long-term solution
- 64% total tool reduction

**When to choose**:
- Ready for larger refactoring
- Want maximum benefit
- Have time for thorough testing

---

### Option C: Phased
**Implement**: All phases sequentially (1 → 2 → 3)
**Timeline**: 4 weeks
**Risk**: LOW-MEDIUM
**Benefits**:
- Incremental improvements
- Continuous testing
- Learn from each phase
- Flexible adaptation

**When to choose**:
- Want best of both worlds
- Can allocate time across multiple weeks
- Want to optimize further based on results

---

## Next Steps

1. **Review this plan** with stakeholders
2. **Choose approach** (Conservative/Aggressive/Phased)
3. **Approve implementation** or request modifications
4. **Begin development** once approved
5. **Monitor metrics** and iterate based on results

---

## Appendices

### Appendix A: Tool Size Analysis

| Tool Category | Current | After Phase 1 | After Phase 2 | After Phase 3 |
|---------------|----------|-----------------|-----------------|-----------------|
| Core Utility | 10 | 7-8 | 4-5 | 4-5 |
| Memory/Reminders | 6 | 4-5 | 2 | 2 |
| Discord Info | 6 | 4-5 | 2 | 2 |
| Discord Messaging | 2 | 2 | 2 | 2 |
| Discord Moderation | 7 | 5-6 | 2 | 2 |
| Image/Creative | 2 | 2 | 2 | 2 |
| Crypto/Finance | 5 | 4-5 | 2 | 2 |
| Trivia/Gaming | 1 | 1 | 1 | 1 |
| Rate Limiting | 2 | 2 | 2 | 2 |
| **TOTAL** | **42** | **30-36** | **19** | **19** |

### Appendix B: Sample Context Detection

```python
def detect_message_context(message: str) -> str:
    """Detect message context/category from content."""
    content_lower = message.lower()

    # Priority 1: Moderation (most specific)
    if any(kw in content_lower for kw in
       ['kick', 'ban', 'timeout', 'mute', 'purge', 'delete', 'pin', 'unpin']):
        return 'moderation'

    # Priority 2: Gambling/Finance
    if any(kw in content_lower for kw in
       ['stake', 'bitsler', 'freebitco', 'fortunejack', 'tip', 'crypto', 'price',
        'balance', 'bonus', 'stock', 'keno']):
        return 'gambling_finance'

    # Priority 3: Reminders
    if any(kw in content_lower for kw in
       ['alarm', 'timer', 'remind', 'notify', 'schedule', 'wake me']):
        return 'reminder'

    # Priority 4: Discord Management
    if any(kw in content_lower for kw in
       ['server', 'guild', 'channel', 'member', 'my roles', 'my servers',
        'list channels', 'list servers']):
        return 'discord_management'

    # Priority 5: Image generation
    if any(kw in content_lower for kw in ['image', 'picture', 'photo', 'draw', 'generate']):
        return 'image'

    # Default: Basic request
    return 'basic'
```

### Appendix C: Testing Checklist

- [ ] Test basic questions (no Discord/gambling context)
- [ ] Test Discord management queries
- [ ] Test moderation commands (kick, ban, timeout)
- [ ] Test crypto price lookups
- [ ] Test tipping operations
- [ ] Test reminder setting/listing
- [ ] Test image generation
- [ ] Test web search
- [ ] Verify error rate reduction
- [ ] Measure response time improvement
- [ ] Check tool selection accuracy logs

---

**Status**: 📋 Awaiting review and approval
