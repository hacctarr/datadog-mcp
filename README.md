# Datadog MCP Server

A Model Context Protocol (MCP) server that provides comprehensive Datadog monitoring capabilities through Claude Desktop and other MCP clients.

## Features

This MCP server enables Claude to:

- **CI/CD Pipeline Management**: List CI pipelines, extract fingerprints
- **Service Logs Analysis**: Retrieve and analyze service logs with environment and time filtering  
- **Metrics Monitoring**: Fetch service metrics with statistical analysis across multiple time ranges
- **Team Management**: List teams, view member details, and manage team information

## Quick Start

Choose your preferred method to run the Datadog MCP server:

### 🚀 Docker Hub (Recommended - Fastest)
```bash
docker run -e DD_API_KEY="your-datadog-api-key" -e DD_APP_KEY="your-datadog-application-key" -i magistersart/datadog-mcp:latest
```

### ⚡ GitHub Direct (Latest Code)
```bash
docker run -e DD_API_KEY="your-datadog-api-key" -e DD_APP_KEY="your-datadog-application-key" -i $(docker build -q https://github.com/magistersart/dd-mcp.git)
```

### 🛠️ UV Quick Run (Python)
```bash
export DD_API_KEY="your-datadog-api-key" DD_APP_KEY="your-datadog-application-key"
git clone https://github.com/magistersart/dd-mcp.git /tmp/dd-mcp && cd /tmp/dd-mcp && uv run server.py
```

### 📦 Docker Compose
```bash
export DD_API_KEY="your-datadog-api-key" DD_APP_KEY="your-datadog-application-key"
git clone https://github.com/magistersart/dd-mcp.git && cd dd-mcp && docker-compose up
```

**Method Comparison:**

| Method | Speed | Latest Code | Multiarch | Disk Usage | Best For |
|--------|-------|-------------|-----------|------------|----------|
| 🚀 Docker Hub | ⚡⚡⚡ | ✅ (tagged) | ✅ | Minimal | Production, Quick Setup |
| ⚡ GitHub Direct | ⚡⚡ | ✅ (bleeding edge) | ❌ | Minimal | Testing Latest Changes |
| 🛠️ UV Quick Run | ⚡ | ✅ (bleeding edge) | ✅ | Minimal | Python Development |
| 📦 Docker Compose | ⚡⚡ | ✅ (bleeding edge) | ❌ | Medium | Development, Orchestration |

## Requirements

### For Docker Methods
- Docker (and Docker Compose for compose method)
- Datadog API Key and Application Key

### For UV/Python Methods  
- Python 3.13+
- UV package manager
- Datadog API Key and Application Key

## Claude Desktop Integration

### Using Docker Hub Image (Recommended)

First, set your environment variables:
```bash
export DD_API_KEY="your-datadog-api-key"
export DD_APP_KEY="your-datadog-application-key"
```

Then add to Claude Desktop configuration:
```json
{
  "mcpServers": {
    "datadog": {
      "command": "docker",
      "args": ["run", "-i", "magistersart/datadog-mcp:latest"],
      "env": {
        "DD_API_KEY": "${DD_API_KEY}",
        "DD_APP_KEY": "${DD_APP_KEY}"
      }
    }
  }
}
```

### Using Local Installation

First, set your environment variables:
```bash
export DD_API_KEY="your-datadog-api-key"
export DD_APP_KEY="your-datadog-application-key"
```

Then add to Claude Desktop configuration:
```json
{
  "mcpServers": {
    "datadog": {
      "command": "python",
      "args": ["/path/to/dd-mcp/server.py"],
      "env": {
        "DD_API_KEY": "${DD_API_KEY}",
        "DD_APP_KEY": "${DD_APP_KEY}"
      }
    }
  }
}
```

## Detailed Installation Options

### Docker Installation

#### Option 1: Use Pre-built Image from Docker Hub

```bash
docker run -e DD_API_KEY="your-datadog-api-key" -e DD_APP_KEY="your-datadog-application-key" -i magistersart/datadog-mcp:latest
```

**Supported Architectures:** The Docker image supports both AMD64 and ARM64 architectures, automatically selecting the correct one for your platform.

#### Option 2: Run Directly from GitHub

Build and run directly from the GitHub repository without cloning:

```bash
docker run -e DD_API_KEY="your-datadog-api-key" -e DD_APP_KEY="your-datadog-application-key" -i $(docker build -q https://github.com/magistersart/dd-mcp.git)
```

Or use Docker Buildx for multiarch support:

```bash
docker buildx build --platform linux/amd64,linux/arm64 -t my-datadog-mcp https://github.com/magistersart/dd-mcp.git --load
docker run -e DD_API_KEY="your-datadog-api-key" -e DD_APP_KEY="your-datadog-application-key" -i my-datadog-mcp
```

#### Option 3: Build from Source

1. **Clone the repository:**
   ```bash
   git clone https://github.com/magistersart/dd-mcp.git
   cd dd-mcp
   ```

2. **Build and run with Docker Compose:**
   ```bash
   export DD_API_KEY="your-datadog-api-key"
   export DD_APP_KEY="your-datadog-application-key"
   docker-compose up --build
   ```

3. **Or build and run with Docker:**
   ```bash
   docker build -t datadog-mcp .
   docker run -e DD_API_KEY="your-datadog-api-key" -e DD_APP_KEY="your-datadog-application-key" -i datadog-mcp
   ```

### Manual Installation

#### Quick Start with UV (Recommended)

If you have UV installed, you can run directly from GitHub:

```bash
export DD_API_KEY="your-datadog-api-key"
export DD_APP_KEY="your-datadog-application-key"

# Clone and run in one command
git clone https://github.com/magistersart/dd-mcp.git /tmp/dd-mcp && cd /tmp/dd-mcp && uv run server.py
```

Or for a more permanent setup:

```bash
export DD_API_KEY="your-datadog-api-key"
export DD_APP_KEY="your-datadog-application-key"
uvx --from git+https://github.com/magistersart/dd-mcp.git --spec server.py datadog-mcp
```

#### Traditional Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/magistersart/dd-mcp.git
   cd dd-mcp
   ```

2. **Install dependencies:**
   ```bash
   uv sync
   ```

3. **Set environment variables:**
   ```bash
   export DD_API_KEY="your-datadog-api-key"
   export DD_APP_KEY="your-datadog-application-key"
   ```

4. **Run the server:**
   ```bash
   python server.py
   ```

## Tools

The server provides these tools to Claude:

### `list_ci_pipelines`
Lists all CI pipelines registered in Datadog with filtering options.

**Arguments:**
- `repository` (optional): Filter by repository name
- `pipeline_name` (optional): Filter by pipeline name  
- `format` (optional): Output format - "table", "json", or "summary"

### `get_pipeline_fingerprints` 
Extracts pipeline fingerprints for use in Terraform service definitions.

**Arguments:**
- `repository` (optional): Filter by repository name
- `pipeline_name` (optional): Filter by pipeline name
- `format` (optional): Output format - "table", "json", or "summary"

### `get_service_logs`
Retrieves service logs with comprehensive filtering capabilities.

**Arguments:**
- `service_name` (required): Name of the service
- `time_range` (required): "1h", "4h", "8h", "1d", "7d", "14d", "30d"
- `environment` (optional): "prod", "staging", "backoffice"
- `log_level` (optional): "INFO", "ERROR", "WARN", "DEBUG"
- `format` (optional): "table", "text", "json", "summary"

### `get_service_metrics`
Fetches service metrics with statistical analysis.

**Arguments:**
- `metric_name` (required): Datadog metric name
- `time_range` (required): "1h", "4h", "8h", "1d", "7d", "14d", "30d"
- `environment` (optional): "prod", "staging", "backoffice"
- `format` (optional): "table", "summary", "json", "timeseries"

### `get_teams`
Lists teams and their members.

**Arguments:**
- `team_name` (optional): Filter by team name
- `include_members` (optional): Include member details (default: false)
- `format` (optional): "table", "json", "summary"

## Examples

Ask Claude to help you with:

```
"Show me all CI pipelines for the shelf-api repository"

"Get error logs for the content service in the last 4 hours"

"What are the latest metrics for log ingestion bytes?"

"List all teams and their members"

"Extract pipeline fingerprints for Terraform configuration"
```

## Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `DD_API_KEY` | Datadog API Key | Yes |
| `DD_APP_KEY` | Datadog Application Key | Yes |

### Obtaining Datadog Credentials

1. Log in to your Datadog account
2. Go to **Organization Settings** → **API Keys**
3. Create or copy your **API Key** (this is your `DD_API_KEY`)
4. Go to **Organization Settings** → **Application Keys**
5. Create or copy your **Application Key** (this is your `DD_APP_KEY`)

**Note:** These are two different keys:
- **API Key**: Used for authentication with Datadog's API
- **Application Key**: Used for authorization and is tied to a specific user account

## License

This project is licensed under the MIT License.