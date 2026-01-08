# logtap

[![PyPI version](https://badge.fury.io/py/logtap.svg)](https://badge.fury.io/py/logtap)
[![Tests](https://github.com/cainky/logtap/actions/workflows/tests.yml/badge.svg)](https://github.com/cainky/logtap/actions/workflows/tests.yml)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

**A CLI-first log access tool for Unix systems. Remote log file access without SSH.**

> The simplest way to access log files remotely. No database. No complex setup.

## Features

- **Remote Log Access** - Query log files via REST API without SSH
- **Beautiful CLI** - Colored output with rich formatting
- **Regex Search** - Powerful filtering with regex patterns
- **Real-time Streaming** - Follow logs like `tail -f` (WebSocket)
- **Lightweight** - No database required, minimal dependencies
- **Secure** - Optional API key authentication
- **Docker Ready** - One-command deployment

## Quick Start

### Installation

```bash
pip install logtap
```

Or with Docker:

```bash
docker pull cainky/logtap
```

### Start the Server

On the machine with log files:

```bash
logtap serve
```

With authentication:

```bash
logtap serve --api-key your-secret-key
```

### Query Logs

From anywhere:

```bash
# Basic query
logtap query syslog

# Search for errors
logtap query syslog --term "error"

# Regex search
logtap query auth.log --regex "Failed password.*root"

# Last 100 lines
logtap query syslog --limit 100

# From a remote server
logtap query syslog --server http://myserver:8000 --api-key secret
```

### List Available Files

```bash
logtap files
```

### Real-time Streaming

```bash
logtap tail syslog --follow
```

## CLI Commands

| Command | Description |
|---------|-------------|
| `logtap serve` | Start the API server |
| `logtap query <file>` | Query log files |
| `logtap tail <file>` | Tail logs (with `--follow` for streaming) |
| `logtap files` | List available log files |

### Common Options

```bash
# Server options
logtap serve --host 0.0.0.0 --port 8000
logtap serve --api-key mysecret --log-dir /var/log

# Client options
logtap query syslog --server http://host:8000 --api-key mysecret
logtap query syslog --term "error" --limit 50
logtap query syslog --regex "pattern" --ignore-case
logtap query syslog --output json  # json, plain, pretty
```

## API Reference

### GET /logs

Query log file contents.

**Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `filename` | string | `syslog` | Log file name |
| `term` | string | - | Substring to search for |
| `regex` | string | - | Regex pattern to match |
| `limit` | int | `50` | Number of lines (1-1000) |
| `case_sensitive` | bool | `true` | Case-sensitive search |

**Example:**
```bash
curl "http://localhost:8000/logs?filename=syslog&term=error&limit=10"
```

**Response:**
```json
{
  "lines": ["Jan 8 10:23:45 server error: connection failed", "..."],
  "count": 10,
  "filename": "syslog"
}
```

### GET /files

List available log files.

```bash
curl "http://localhost:8000/files"
```

### GET /health

Health check endpoint.

```bash
curl "http://localhost:8000/health"
```

### Authentication

If `LOGTAP_API_KEY` is set, all requests require the `X-API-Key` header:

```bash
curl -H "X-API-Key: your-secret" "http://localhost:8000/logs"
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `LOGTAP_HOST` | `0.0.0.0` | Server bind host |
| `LOGTAP_PORT` | `8000` | Server bind port |
| `LOGTAP_LOG_DIRECTORY` | `/var/log` | Log files directory |
| `LOGTAP_API_KEY` | - | API key (optional) |

### Using .env File

Create a `.env` file:

```env
LOGTAP_LOG_DIRECTORY=/var/log
LOGTAP_API_KEY=your-secret-key
```

## Docker Deployment

### Using Docker Compose

```yaml
version: "3.8"

services:
  logtap:
    image: cainky/logtap
    ports:
      - "8000:8000"
    volumes:
      - /var/log:/var/log:ro
    environment:
      - LOGTAP_API_KEY=your-secret-key
```

```bash
docker-compose up -d
```

### Using Docker Directly

```bash
docker run -d \
  -p 8000:8000 \
  -v /var/log:/var/log:ro \
  -e LOGTAP_API_KEY=your-secret \
  cainky/logtap
```

## Development

### Setup

```bash
# Clone the repository
git clone https://github.com/cainky/logtap.git
cd logtap

# Install dependencies
poetry install

# Run tests
poetry run pytest

# Run the server in development mode
poetry run logtap serve --reload
```

### Project Structure

```
logtap/
├── src/logtap/
│   ├── api/          # FastAPI server
│   ├── cli/          # Typer CLI commands
│   ├── core/         # Core business logic
│   └── models/       # Pydantic models
├── tests/
│   ├── unit/         # Unit tests
│   └── integration/  # API tests
├── Dockerfile
└── docker-compose.yml
```

### Running Tests

```bash
# All tests
poetry run pytest

# With coverage
poetry run pytest --cov=logtap

# Specific test file
poetry run pytest tests/unit/test_reader.py
```

## Security Considerations

- **Path Traversal Protection**: Filenames are validated to prevent `../` attacks
- **Input Validation**: Search terms limited to 100 chars, limits capped at 1000
- **Read-Only**: Log directory is mounted read-only in Docker
- **API Authentication**: Optional API key for production use

## License

GPL v3 License - see [LICENSE](LICENSE) for details.

## Contributing

Contributions are welcome! Please open an issue to discuss potential changes before submitting a pull request.

## Author

Kyle Cain - [@cainky](https://github.com/cainky)
