# JakeySelfBot 🤖

A production-ready Discord self-bot showcasing advanced full-stack development with AI integration, professional image generation, and enterprise-grade architecture. This project demonstrates comprehensive software engineering skills including async programming, API integration, database design, testing, and deployment automation.

## About 📖

This project represents a significant milestone in my journey as an app developer, showcasing the ability to build and deploy a complex, production-ready application from the ground up. Key achievements include:

### 🏗️ **Architecture & Design**
- **Microservices Architecture**: MCP memory server with HTTP API and dynamic port assignment
- **Async-First Design**: Full async/await implementation with aiohttp and aiosqlite
- **Dependency Injection**: Clean architecture with centralized service management
- **Resilience Engineering**: Multi-provider failover, graceful degradation, and automatic recovery

### 🤖 **AI & Machine Learning Integration**
- **Multi-Provider AI System**: Primary Pollinations API with OpenRouter fallback
- **Professional Image Generation**: 49 artistic styles via Arta API with 9 aspect ratios
- **Tool-Augmented AI**: Function calling system with 12 specialized tools
- **Response Uniqueness**: Advanced anti-repetition system preventing duplicate responses

### 🛠️ **Full-Stack Development**
- **Backend**: Python async services, REST APIs, database operations
- **Frontend**: Discord bot interface with rich command system (35 commands)
- **Database**: SQLite with async operations and comprehensive data modeling
- **APIs**: Integration with 6+ external services (CoinMarketCap, SearXNG, tip.cc, etc.)

### 🧪 **Quality Assurance**
- **81 Unit Tests**: Comprehensive test coverage including integration tests
- **CI/CD Ready**: Automated testing, linting, and deployment scripts
- **Production Monitoring**: Health checks, logging, and performance metrics
- **Error Handling**: Robust error recovery and user-friendly messaging

### 🚀 **DevOps & Deployment**
- **Multi-Platform Deployment**: Systemd services, PM2 process management, Docker support
- **Configuration Management**: Environment-based config with 70+ customizable parameters
- **Self-Hosted Infrastructure**: SearXNG search engine, MCP memory server
- **Production Hardening**: Rate limiting, security validation, backup systems

### 📊 **Advanced Features**
- **Real-Time Systems**: Webhook relays, reaction roles, automated airdrop claiming
- **Financial Integration**: Cryptocurrency tipping with balance tracking and transaction history
- **Memory Systems**: Persistent user preferences with MCP protocol implementation
- **Gambling Utilities**: Keno generation, bonus schedules, financial calculations

This project demonstrates enterprise-level development practices applied to a Discord bot, proving the ability to handle complex requirements, integrate multiple APIs, ensure reliability, and maintain production-quality code.

## 📋 Table of Contents

- [About 📖](#about-)
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

## 🚀 Production Status

[![Tests](https://img.shields.io/badge/tests-81%2F81%20passing-brightgreen)](https://github.com/brokechubb/JakeySelfBot)
[![Python](https://img.shields.io/badge/python-3.8+-blue)](https://www.python.org/)
[![Discord.py-self](https://img.shields.io/badge/discord.py--self-2.0+-purple)](https://github.com/dolfies/discord.py-self)

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
JakeySelfBot/
├── main.py                 # Application entry point with DI container
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

### 🤖 Advanced AI Integration
- **Multi-Provider AI**: Pollinations primary + OpenRouter fallback with automatic failover
- **Professional Art Generation**: 49 artistic styles via Arta API (Van Gogh, Fantasy, Watercolor, etc.)
- **Tool-Augmented Responses**: 12 specialized tools (crypto prices, web search, calculations)
- **Memory System**: MCP protocol implementation for persistent user preferences
- **Response Uniqueness**: Advanced anti-repetition system preventing duplicate outputs

### 💰 Financial & Gambling Features
- **tip.cc Integration**: Full cryptocurrency tipping with balance tracking and transaction history
- **Automated Airdrop Claiming**: Smart claiming system with retry logic and database tracking
- **Crypto Price Tools**: Real-time prices via CoinMarketCap API
- **Gambling Utilities**: Keno generation, bonus schedules, financial calculations

### 🛠️ Enterprise-Grade Architecture
- **Async-First Design**: Full async/await with aiohttp and aiosqlite
- **Microservices**: MCP memory server with HTTP API and dynamic port assignment
- **Resilience Engineering**: Multi-provider failover, graceful degradation, health monitoring
- **Production Monitoring**: Comprehensive logging, rate limiting, performance metrics

### 🔧 Developer Experience
- **81 Unit Tests**: Complete test coverage with integration and MCP memory tests
- **Comprehensive Documentation**: 20+ detailed docs covering all features
- **Multi-Platform Deployment**: Systemd, PM2, Docker support with automated scripts
- **Configuration Management**: 70+ environment variables with sensible defaults

## Setup

1. Create a virtual environment:

    ```bash
    python -m venv venv
    ```

2. Activate the virtual environment:

    ```bash
    source venv/bin/activate  # Linux/Mac
    venv\Scripts\activate     # Windows
    ```

3. Install dependencies:

    ```bash
    pip install -r requirements.txt
    ```

4. Configure the bot by editing `.env` file with your Discord token and other settings.

5. Run the bot:
    ```bash
    python main.py
    ```

Or use the preferred startup script:

```bash
./jakey.sh
```

## 🎮 Command System

Jakey features 35 comprehensive commands across 8 categories, all with built-in help and error handling:

| Category | Commands | Description |
|----------|----------|-------------|
| **Core** | 8 commands | Help, stats, ping, model management, time/date |
| **AI & Media** | 4 commands | Image generation, audio synthesis, image analysis |
| **Memory** | 2 commands | User preference storage, friend management |
| **Gambling** | 7 commands | Keno, bonus schedules, airdrop status, utilities |
| **Financial** | 3 commands | tip.cc balance tracking, transactions, statistics |
| **Admin** | 8 commands | Tipping, airdrops, user management, history clearing |
| **Roles** | 4 commands | Gender roles, reaction role management |

**Example Usage:**
- `%image a beautiful sunset in van gogh style` - Generate artistic images
- `%bal` - Check cryptocurrency balances with USD conversion
- `%remember favorite_color blue` - Store user preferences
- `%keno` - Generate random Keno numbers with visual board

## ⚙️ Configuration

70+ configurable parameters via environment variables with sensible defaults. Key areas:

- **Discord**: Token, presence, admin controls, guild blacklists
- **AI**: Model preferences, rate limits, provider failover settings
- **Financial**: tip.cc integration, airdrop claiming parameters
- **Memory**: MCP server settings, conversation history limits
- **Tools**: API keys for external services (CoinMarketCap, SearXNG, etc.)

See [`config.py`](config.py) and [Configuration Guide](docs/CONFIGURATION.md) for complete documentation.

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
   git clone https://github.com/brokechubb/JakeySelfBot.git
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
   ./jakey.sh              # Full production startup
   python main.py          # Simple development startup
   ./jakey.sh --skip-mcp   # Without MCP memory server
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
- **AI**: Pollinations (primary), OpenRouter (fallback), Arta (artistic images)
- **Financial**: CoinMarketCap (crypto prices), tip.cc (tipping)
- **Search**: Self-hosted SearXNG instance
- **Memory**: MCP protocol implementation

### Documentation
Complete documentation suite in [`docs/`](docs/) covering all features, APIs, and configuration options.

## ⚠️ Important Notes

- **CRITICAL**: Uses `discord.py-self` (NOT regular `discord.py`) - never add `intents=` parameter
- **Self-Bot**: Runs on user accounts, not bot applications
- **Educational**: For learning and personal use only

---

**Built with ❤️ by [brokechubb](https://github.com/brokechubb)**
