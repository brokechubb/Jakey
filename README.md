# Jakey 🤖

[![Tests](https://img.shields.io/badge/tests-81%2F81%20passing-brightgreen)](https://github.com/brokechubb/Jakey)
[![Python](https://img.shields.io/badge/python-3.8+-blue)](https://www.python.org/)
[![Discord.py-self](https://img.shields.io/badge/discord.py--self-2.0+-purple)](https://github.com/dolfies/discord.py-self)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)

The chaotically brilliant Discord assistant that fuses enterprise-grade engineering with sharp wit. This isn't your average chat bot—it's a full-stack powerhouse capable of tracking your crypto portfolio, scouring the web for answers, and recalling your preferences while providing insightful responses. Built on AI and a bold personality, Jakey is a production-ready package that actually works.

## 📖 A Loopy Language Model 📖

This project is my passion project - a journey through full-stack development that resulted in a production-ready Discord bot. I started this as an experiment with my Discord community and ended up building something that could run a small business. Here's what makes Jakey tick:

### 🏗️ **The Tech Stack That Could**

- **Microservices Madness**: MCP memory server with HTTP APIs and fancy port magic
- **Async Everything**: Because waiting is for losers - full async/await with aiohttp and aiosqlite
- **Dependency Injection**: Clean architecture that doesn't suck (most of the time)
- **Resilience Engineering**: Shit breaks? No problem - automatic failover and recovery

### 🤖 **AI That Actually Works**

- **Free AI Models**: qwen3-max, deepseek-v3, and 40+ others from [iflow.cn](https://platform.iflow.cn) - all completely free
- **OpenAI-Compatible API**: Accessed via [CLIProxyAPI](https://github.com/router-for-me/CLIProxyAPI) which wraps iflow.cn's CLI tools into standard OpenAI API endpoints
- **Smart Failover**: Automatically switches from qwen3-max (with safety filters) to deepseek-v3 (uncensored) when content filtering triggers
- **Art Gallery in Your Discord**: 49 artistic styles from Van Gogh to anime waifus
- **Tool Belt**: 12 specialized tools for crypto prices, web search, math, and more
- **Anti-Repetition Tech**: Advanced system so Jakey doesn't repeat himself like a broken record

### 🛠️ **Full-Stack Chaos**

- **Backend**: Python async services, REST APIs, database wizardry
- **Frontend**: Discord interface with 35 commands that actually work
- **Database**: SQLite with async ops and proper data modeling
- **APIs**: Integrated with CoinMarketCap, SearXNG, tip.cc, and more

### 🧪 **Testing That Actually Happens**

- **81 Unit Tests**: Yeah, I actually wrote tests and they all pass
- **Integration Tests**: Makes sure all the APIs talk to each other nicely
- **MCP Memory Tests**: 10 tests just for the memory system
- **Error Handling**: Graceful failures because crashes are embarrassing

### 🚀 **DevOps That Scales**

- **Multi-Platform**: Systemd, PM2, Docker - deploy anywhere
- **Config Management**: 70+ settings because customization is key
- **Self-Hosted Infra**: SearXNG search, MCP memory server
- **Production Hardening**: Rate limiting, security, backups

### 🎰 **The Fun Stuff**

- **Crypto Tipping**: tip.cc integration with balance tracking
- **Airdrop Automation**: Smart claiming system with server whitelist support, retry logic, and trivia auto-answering
- **Gambling Tools**: Keno generator, bonus schedules, financial calcs
- **Memory System**: Remembers your shit so conversations make sense

**Bottom line**: Jakey proves enterprise-level software can be built while keeping it innovative and fun. Everything is designed for reliability, but the code works! 🎰

## 🎯 What Jakey Can Do For You

Jakey isn't just another Discord bot - he's your research assistant, financial advisor, and entertainment system all in one. He excels at:

- **🔍 Research & Info**: Web search, crypto prices, AI conversations, image analysis, and audio generation
- **💰 Finance & Crypto**: Live price tracking, tip.cc integration, transaction history, airdrop automation, and financial calculations
- **🎮 Entertainment**: Professional art generation (49 styles), gambling tools, time/date features, random generators, and persistent memory
- **🤖 AI Features**: Contextual conversations, tool integration, multi-modal capabilities, and error recovery
- **🛠️ Server Management**: Reaction roles, gender recognition, admin tools, webhook relays, and channel analytics

**In short**: Jakey transforms your Discord server into a research lab, financial dashboard, entertainment center, and AI assistant. 🎰🔍💰

*See [Key Features](#-key-features) below for detailed technical specifications.*

## ⚠️ Important Warnings

### 🤖 AI Model & Content

- **Uncensored AI**: Jakey uses uncensored AI models that can generate explicit, offensive, or controversial content
- **No Content Filtering**: Unlike mainstream AI services, Jakey has minimal content restrictions
- **User Responsibility**: All generated content is the responsibility of the user - use discretion
- **Degenerate Personality**: Jake's responses are offensive and reflect his cynical, gambling-obsessed persona

### 🚨 Self-Bot Risks & Legal Notice

**Self-botting violates Discord's Terms of Service and can result in account suspension or permanent bans.**

- **Account Risks**: Using self-bots can lead to Discord account termination
- **Legal Gray Area**: Self-botting exists in a legal gray area and is not officially supported
- **Educational Use Only**: This project is for educational and personal use only
- **No Warranty**: Use at your own risk - the developers are not responsible for account issues
- **Rate Limiting**: Discord actively detects and blocks self-bot behavior
- **API Changes**: Discord frequently updates their API, potentially breaking self-bot functionality

**Bottom line**: Self-botting is risky business. Use Jakey responsibly and be prepared for potential consequences. Everything is rigged, but at least you were warned! ⚠️🚫

## 📋 Table of Contents

- [About 📖](#-a-loopy-language-model-)
- [What Jakey Can Do For You 🎯](#-what-jakey-can-do-for-you)
- [Important Warnings ⚠️](#️-important-warnings)
- [Production Status 🚀](#-production-status)
- [Project Structure 📁](#-project-structure)
- [Key Features ✨](#-key-features)
- [Command System 🎮](#-command-system)
- [Configuration ⚙️](#️-configuration)
- [Security & Admin Features 🔐](#-security--admin-features)
- [Advanced Systems 🧠](#-advanced-systems)
- [Quick Start 🚀](#-quick-start)
- [Database & Testing 🗄️](#️-database--testing)
- [Documentation & Dependencies 📚](#-documentation--dependencies)
- [Contributing 🤝](#-contributing-)
- [Donations 💰](#-donations)
- [License 📄](#-license)

## 🚀 Production Status

- **✅ Tests**: 81/81 passing (including 10 MCP integration tests)
- **🎯 Commands**: 35 registered and functional across 8 categories
- **🛠️ Tools**: 12 AI tools with function calling capabilities
- **🔗 APIs**: 6+ external service integrations (Pollinations, OpenRouter, Arta, CoinMarketCap, SearXNG, tip.cc)
- **💾 Database**: Async SQLite with connection pooling and comprehensive data modeling
- **📊 Monitoring**: Enhanced logging, health checks, and performance metrics
- **🧠 Memory**: MCP protocol implementation with dynamic port assignment
- **🔒 Security**: Input validation, rate limiting, and admin controls

## 📁 Project Structure

```
Jakey/
├── main.py                # Application entry point with DI container
├── config.py              # 70+ configuration parameters
├── bot/                   # Discord client & 35 command handlers
├── ai/                    # Multi-provider AI (Pollinations + OpenRouter)
├── tools/                 # MCP memory server & tool system
├── data/                  # Async SQLite database operations
├── utils/                 # Helper functions & integrations
├── tests/                 # 81 comprehensive unit tests
├── docs/                  # Complete documentation suite
└── resilience/            # Failover & recovery systems
```

## ✨ Key Features

### 🤖 AI-Powered Assistant

- **Conversational AI**: Natural language chat with personality and memory
- **Research Tools**: Web search, calculations, data analysis, and information retrieval
- **Creative Generation**: Professional artistic images and audio synthesis
- **Smart Memory**: Remembers user preferences and conversation context
- **Multi-Modal**: Text, image, and audio capabilities

### 💰 Financial & Crypto Suite

- **Live Market Data**: Real-time cryptocurrency prices and market information
- **Tipping System**: tip.cc integration for seamless crypto transactions
- **Financial Tracking**: Balance monitoring, transaction history, and earnings analytics
- **Airdrop Automation**: Intelligent claiming with retry logic, success tracking, and trivia auto-answering
- **Investment Tools**: Price alerts, portfolio tracking, and market analysis

### 🛠️ Production-Ready Infrastructure

- **Enterprise Architecture**: Microservices, async processing, and scalable design
- **Reliability**: Multi-provider failover, error recovery, and health monitoring
- **Security**: Input validation, rate limiting, and admin controls
- **Performance**: Optimized for speed with comprehensive testing (81/81 tests passing)
- **Deployment**: Multiple deployment options (PM2, Systemd, Docker)

### 🔧 Developer Experience

- **81 Unit Tests**: Complete test coverage with integration and MCP memory tests
- **Comprehensive Documentation**: 20+ detailed docs covering all features
- **Multi-Platform Deployment**: Systemd, PM2, Docker support with automated scripts
- **Configuration Management**: 70+ environment variables with sensible defaults

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Discord user account token
- API keys for external services (optional)

### Installation & Setup

1. **Clone & Install:**

    ```bash
    git clone https://github.com/brokechubb/Jakey.git
    cd JakeySelfBot
    pip install -r requirements.txt
    ```

2. **Configure:**

    ```bash
    cp .env.example .env
    # Edit .env with your Discord token and API keys
    ```

3. **Run:**

    ```bash
    ./scripts/jakey.sh              # Full production startup (recommended)
    python main.py                  # Simple development startup
    ./scripts/jakey.sh --skip-mcp   # Without MCP memory server
    ```

### Production Deployment

**PM2 (Recommended):**

```bash
pm2 start pm2-ecosystem.yml
pm2 logs jakey-self-bot
```

**Systemd:**

```bash
./setup_systemd.sh
./service_control.sh start
./check_status.sh
```

## 🎮 Command System

Jakey features 35 comprehensive commands across 8 categories, all with built-in help and error handling:

| Category       | Commands   | Description                                          |
| -------------- | ---------- | ---------------------------------------------------- |
| **Core**       | 8 commands | Help, stats, ping, model management, time/date       |
| **AI & Media** | 4 commands | Image generation, audio synthesis, image analysis    |
| **Memory**     | 2 commands | User preference storage, friend management           |
| **Gambling**   | 10 commands | Keno, bonus schedules, airdrop status, trivia, utilities |
| **Financial**  | 3 commands | tip.cc balance tracking, transactions, statistics    |
| **Admin**      | 8 commands | Tipping, airdrops, user management, history clearing |
| **Roles**      | 4 commands | Gender roles, reaction role management               |

**Example Usage:**

- `%image a beautiful sunset in van gogh style` - Generate professional artistic images
- `%bal` - Check cryptocurrency balances with USD conversion (admin only)
- `%remember favorite_color blue` - Store user preferences
- `%keno [count]` - Generate random Keno numbers with visual board (optional count 3-10)
- `%triviastats` - Show trivia database statistics and health
- `%clearstats` - Clear all tip.cc transaction history (admin only)

## ⚙️ Configuration

70+ configurable parameters via environment variables with sensible defaults. Key areas:

- **Discord**: Token, presence, admin controls, guild blacklists
- **AI**: Model preferences, rate limits, provider failover settings
- **Financial**: tip.cc integration, airdrop claiming parameters
- **Memory**: MCP server settings, conversation history limits
- **Tools**: API keys for external services (CoinMarketCap, SearXNG, etc.)

See [`config.py`](config.py) and [Configuration Guide](docs/CONFIGURATION.md) for complete documentation.

### 🧠 AI Provider Setup

Jakey uses a sophisticated dual-model approach for maximum reliability:

**The Setup**
- **Model Source**: [iflow.cn](https://platform.iflow.cn) (Xinliu Open Platform) - provides 42+ AI models completely free
- **API Access**: [CLIProxyAPI](https://github.com/router-for-me/CLIProxyAPI) - converts iflow.cn's CLI tools into OpenAI-compatible REST API endpoints
- **Local Endpoint**: `http://localhost:8317/v1/chat/completions`

**Primary Model: qwen3-max**
- Source: Free from iflow.cn
- Access: Via CLIProxyAPI OpenAI-compatible endpoint
- Features: Full tool support (42 tools), Qwen3Guard safety filtering, excellent reasoning
- Note: Has content filtering that can trigger on edgy content

**Fallback Model: deepseek-v3**
- Source: Also free from iflow.cn
- Purpose: Automatic fallback when qwen3-max content filtering triggers
- Features: No safety filters, completely uncensored, conversation-only (no tool support)
- Trigger: HTTP 400 DataInspectionFailed errors automatically switch to this model

**Why This Setup?**
- All models are **100% free** through iflow.cn's generous API
- CLIProxyAPI provides a standard OpenAI-compatible interface (no custom code needed)
- qwen3-max has safety filters but excellent tool calling
- deepseek-v3 has zero filtering but limited tool support
- Automatic failover ensures Jakey always responds

**Available Models (all free via iflow.cn through CLIProxyAPI):**
42+ models including qwen3-max, deepseek-v3/v3.1/v3.2, gemini-2.5-flash, kimi-k2, glm-4.6, and more. See the full list with `curl http://localhost:8317/v1/models` when CLIProxyAPI is running.

## 🔐 Security & Admin Features

- **Admin Controls**: Restricted commands with user ID validation
- **Rate Limiting**: Built-in throttling to prevent abuse
- **Input Validation**: Comprehensive sanitization of all user inputs
- **Guild Blacklisting**: Selective response controls per server
- **Audit Logging**: Complete action tracking and error reporting

**Admin Setup:**

```bash
# In .env file
ADMIN_USER_IDS=123456789,987654321
```

## 🧠 Advanced Systems

### MCP Memory Server

HTTP-based memory service with dynamic port assignment for persistent user data storage.

### Gender Role Recognition

Automatic pronoun usage based on Discord role mappings with real-time updates.

### Reaction Role System

Automated role assignment through emoji reactions on designated messages.

### Conversation Context

Configurable AI memory with token limits and channel-specific context windows.

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Discord user account token
- API keys for external services (optional)

### Installation & Setup

1. **Clone & Install:**

    ```bash
    git clone https://github.com/brokechubb/Jakey.git
    cd JakeySelfBot
    pip install -r requirements.txt
    ```

2. **Configure:**

    ```bash
    cp .env.example .env
    # Edit .env with your Discord token and API keys
    ```

3. **Run:**
    ```bash
    ./scripts/jakey.sh              # Full production startup
    python main.py                  # Simple development startup
    ./scripts/jakey.sh --skip-mcp   # Without MCP memory server
    ```

### Production Deployment

**PM2 (Recommended):**

```bash
pm2 start pm2-ecosystem.yml
pm2 logs jakey-self-bot
```

**Systemd:**

```bash
./setup_systemd.sh
./service_control.sh start
./check_status.sh
```

## 🗄️ Database & Testing

### Database

Async SQLite with connection pooling storing conversations, user preferences, financial transactions, and airdrop records.

**Utilities:**

```bash
python utils/flush_db.py  # Clear all database data
```

### Testing Suite

81 comprehensive tests covering all functionality with 100% pass rate.

**Run Tests:**

```bash
python -m tests.test_runner          # All tests
python -m tests.test_mcp_memory_integration  # MCP memory tests
python -m unittest tests.test_commands.TestCommands.test_help  # Specific test
```

**Test Coverage:** Core functionality, API integrations, database operations, MCP memory system, and error handling.

## 📚 Documentation & Dependencies

### Core Dependencies

- **discord.py-self**: Discord self-bot framework
- **aiohttp**: Async HTTP client for API integrations
- **aiosqlite**: Async SQLite database operations
- **python-dotenv**: Environment configuration management

### External APIs

- **AI**: [iflow.cn](https://platform.iflow.cn) free models (qwen3-max, deepseek-v3, etc.) via [CLIProxyAPI](https://github.com/router-for-me/CLIProxyAPI) OpenAI-compatible endpoints
- **Image Generation**: Arta (49 artistic styles), Pollinations
- **Financial**: CoinMarketCap (crypto prices), tip.cc (tipping)
- **Search**: Self-hosted SearXNG instance
- **Memory**: MCP protocol implementation

### Documentation

Complete documentation suite in [`docs/`](docs/) covering all features, APIs, and configuration options.

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details on how to get started.

For bugs, features, or questions, use [GitHub Discussions](https://github.com/brokechubb/Jakey/discussions).

## ⚠️ Important Notes

- **CRITICAL**: Uses `discord.py-self` (NOT regular `discord.py`) - never add `intents=` parameter
- **Self-Bot**: Runs on user accounts, not bot applications
- **Educational**: For learning and personal use only
- **Uncensored AI**: Generates explicit/controversial content - user discretion advised
- **Account Risk**: Self-botting violates Discord ToS - use at your own risk
- **No Warranty**: Developers not responsible for account suspensions or bans

## 📄 License

This project is licensed under the GNU General Public License v3.0. See the [LICENSE](LICENSE) file for details.

### What this means:

- ✅ **Freedom**: You can use, modify, and distribute the software
- ✅ **Open Source**: All source code is available and transparent
- ✅ **Copyleft**: Derivative works must also be licensed under GPLv3
- ✅ **No Warranty**: Software is provided "as is" without guarantees
- ✅ **Community**: Contributions and improvements are welcome

For more information about GPLv3, visit [https://www.gnu.org/licenses/gpl-3.0](https://www.gnu.org/licenses/gpl-3.0)

## 📞 Support & Feedback

Have questions, found a bug, or want to share feedback? Head over to our [GitHub Discussions](https://github.com/brokechubb/Jakey/discussions) to connect with the community and developers!

Don't forget to ⭐ star the project if you find it useful - it helps others discover Jakey and keeps the motivation high!

## 💰 Donations

If you find Jakey useful and want to support continued development, consider buying me a coffee with crypto! Every little bit helps keep the project alive and add new features.

**SOL (Solana):**
```
FVDejAWbUGsgnziRvFi4eGkJZuH6xuLviuTdi2g4Ut3o
```

**LTC (Litecoin):**
```
ltc1qlace3x54t6ktzsvv7jr59xknrj5twvp99w2sze
```

**BTC (Bitcoin):**
```
bc1q526y8dz3utguacc3d4rrk4xjecg9kl4e9etex0
```

Thank you for your support! 🎰💎

---

## 🙏 Acknowledgment

This project takes inspiration from the original [JakeyBot](https://github.com/zavocc/JakeyBot) by [zavocc](https://github.com/zavocc). While this implementation is built from the ground up with completely different architecture and features, I acknowledge that the name "Jakey" and the general concept of an AI-powered Discord assistant originated from that project. The Jakey Self-Bot project has evolved into a distinct implementation with self-botting capabilities, MCP memory systems, and advanced tool integration that differ significantly from the original.

---

**Built with ❤️ by [brokechubb](https://github.com/brokechubb)**
