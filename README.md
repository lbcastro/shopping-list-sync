# Shopping List Sync

Automatically organize your Todoist shopping list using AI-powered categorization. Never manually sort your shopping items by aisle again!

## Features

- 🤖 **AI-Powered Categorization**: Uses OpenAI to intelligently categorize items into supermarket aisles
- 🔄 **Real-Time Monitoring**: Automatically detects and processes new items as you add them
- ⚙️ **Highly Customizable**: Configure your own supermarket sections via YAML
- 🐳 **Multiple Deployment Options**: Run via pip, Docker, or systemd service
- 🪶 **Lightweight**: Minimal resource usage, runs efficiently in the background
- 📊 **Smart Deduplication**: Automatically removes duplicate shopping items
- 🔔 **Configurable Error Handling**: Choose between logging errors or creating Todoist tasks

## Quick Start

### Prerequisites

- Python 3.9 or higher
- [Todoist account](https://todoist.com) with API access
- [OpenAI API key](https://platform.openai.com/api-keys)

### Installation

#### Option 1: pip (Recommended)

```bash
pip install shopping-list-sync
```

#### Option 2: From Source

```bash
git clone https://github.com/lbcastro/shopping-list-sync.git
cd shopping-list-sync
pip install -e .
```

### Configuration

1. Copy the example environment file:
```bash
cp config/.env.example .env
```

2. Edit `.env` with your API keys:
```bash
# Required
TODOIST_API_KEY=your_todoist_api_key_here
OPENAI_API_KEY=your_openai_api_key_here

# Optional: Specify your shopping project
TODOIST_SHOPPING_PROJECT_NAME=shopping
TODOIST_SHOPPING_PROJECT_ID=your_project_id
```

3. Find your Todoist shopping project ID (if needed):
```bash
shopping-sync --check
```

### Usage

#### Run as Daemon (Default)

Start the background service that continuously monitors for changes:

```bash
shopping-sync
```

#### One-Time Sync

Organize your list once without starting the daemon:

```bash
shopping-sync --once
```

#### Health Check

Verify your configuration and API connectivity:

```bash
shopping-sync --check
```

#### Custom Sync Interval

Set a custom check interval (in seconds):

```bash
shopping-sync --interval 120  # Check every 2 minutes
```

#### Debug Mode

Enable detailed logging for troubleshooting:

```bash
shopping-sync --log-level DEBUG
```

## How It Works

1. **Monitoring**: Checks your Todoist shopping list project every 60 seconds (configurable)
2. **Detection**: Identifies new, uncategorized items
3. **Categorization**: Uses OpenAI to intelligently categorize items into supermarket aisles
4. **Organization**: Automatically moves items to appropriate sections
5. **State Management**: Tracks processed items to avoid redundant API calls

## Configuration

### Customizing Categories

Edit `config/categories.yaml` to match your supermarket's layout:

```yaml
categories:
  produce:
    emoji: "🥬"
    keywords: [vegetables, fruits, lettuce, tomato]
    priority: 1

  dairy:
    emoji: "🥛"
    keywords: [milk, cheese, yogurt, butter]
    priority: 2
```

### Environment Variables

See `config/.env.example` for all available options:

- **TODOIST_API_KEY** (required): Your Todoist API token
- **OPENAI_API_KEY** (required): Your OpenAI API key
- **TODOIST_SHOPPING_PROJECT_NAME**: Name of your shopping list project (default: "shopping")
- **SYNC_INTERVAL_SECONDS**: How often to check for changes (default: 60)
- **OPENAI_MODEL**: Which OpenAI model to use (default: "gpt-4o-mini")
- **LOG_LEVEL**: Logging verbosity (DEBUG, INFO, WARNING, ERROR)

## Deployment

### Docker

```bash
cd deployment/docker
cp ../../config/.env.example ../../.env
# Edit .env with your API keys
docker-compose up -d
```

View logs:
```bash
docker-compose logs -f
```

### Linux Systemd Service

```bash
# Edit the service file with your paths
sudo cp deployment/systemd/shopping-list-sync.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable shopping-list-sync
sudo systemctl start shopping-list-sync
```

Check status:
```bash
sudo systemctl status shopping-list-sync
```

## API Costs

Shopping List Sync uses OpenAI's API, which has associated costs:

- **Model**: gpt-4o-mini (default, most cost-effective)
- **Typical cost**: ~$0.01 per 100 items categorized
- **Monthly estimate**: $0.50-$2.00 for average household usage

You can monitor your usage in the [OpenAI dashboard](https://platform.openai.com/usage).

## Troubleshooting

### Health Check Fails

```bash
shopping-sync --check
```

Common issues:
- Invalid API keys
- Todoist project not found
- Network connectivity problems

### Items Not Being Categorized

1. Check logs with `--log-level DEBUG`
2. Verify OpenAI API key is valid
3. Ensure your shopping project has the correct name/ID
4. Check that sections exist in your Todoist project

### Permission Errors

Ensure your user has write permissions to the data directory:
```bash
mkdir -p data
chmod 755 data
```

## Development

### Setup Development Environment

```bash
git clone https://github.com/lbcastro/shopping-list-sync.git
cd shopping-list-sync
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -e ".[dev]"
```

### Run Tests

```bash
pytest
```

### Code Quality

```bash
black src/
ruff check src/
mypy src/
```

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](docs/contributing.md) for guidelines.

## License

MIT License - see [LICENSE](LICENSE) for details.

## Support

- **Issues**: [GitHub Issues](https://github.com/lbcastro/shopping-list-sync/issues)
- **Discussions**: [GitHub Discussions](https://github.com/lbcastro/shopping-list-sync/discussions)

## Acknowledgments

Extracted and adapted from the [chef](https://github.com/mir-lca/chef) project's shopping list organization components.

---

**Made with ❤️ by [Lourenço Castro](https://github.com/lbcastro)**
