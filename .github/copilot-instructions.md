# MSM (MCP Server Manager) - AI Agent Instructions

## Project Overview
MSM is a command-line tool for managing multiple Docker-containerized MCP (Model Context Protocol) Server instances across distributed servers. It provides lifecycle management (start/stop/restart), status monitoring, and log viewing for container-based MCP servers.

## Architecture Understanding

### Three-Layer Architecture
- **CLI Interface** (`src/msm/entrypoint/cli/`) - Command parsing and user interaction
- **Core Management** (`src/msm/core/`) - Container lifecycle, status monitoring, remote connections
- **Data Layer** (`src/msm/data/`) - Configuration and state persistence using Pydantic models

### Key Components Status
- ✅ **Data Models**: Complete Pydantic models with YAML serialization in `src/msm/data/models.py`
- 🚧 **Core Layer**: `ContainerManager` implementation in progress
- 🚧 **CLI Commands**: Extensible command framework exists, needs MCP-specific commands

## Development Patterns

### Data Model Conventions
- All models extend Pydantic `BaseModel` with strict validation
- YAML serialization via `to_yaml()` and `from_yaml()` class methods
- Models in `src/msm/data/models.py` include: `MCPServerConfig`, `ContainerInfo`, `ContainerLogs`, `ResourceUsage`, `MCPServerStatus`, `ServerRegistry`
- Use `Field()` with descriptive `description` parameters for all model fields

### CLI Command Structure
```python
# Follow this pattern in src/msm/entrypoint/cli/commands/
class MyCommand(BaseCommand):
    @property
    def definition(self) -> CommandDefinition:
        return CommandDefinition(name="cmd", description="...", arguments=[...])
    
    async def execute(self, args: List[str], cli: "FenixaosCLI") -> bool:
        # Implementation
```

### Error Handling & Messaging
- Use Rich console for formatted output: `cli.console.print("[green]✓ Success[/green]")`
- Backend operations return `Optional[Dict[str, Any]]` with status/error patterns
- Follow established patterns in `BackendOperations` class for consistent error handling

## Critical Implementation Guidelines

### Container Management (Priority: HIGH)
The `ContainerManager` class in `src/msm/core/container_manager.py` is the foundation. Implement these methods:
```python
# Lifecycle operations
def start_container(self, config: MCPServerConfig) -> bool
def stop_container(self, container_id: str) -> bool  
def restart_container(self, container_id: str) -> bool

# Information retrieval
def get_container_info(self, container_id: str) -> Optional[ContainerInfo]
def get_container_logs(self, container_id: str) -> ContainerLogs
def get_container_status(self, container_id: str) -> ContainerStatus
```

### Target CLI Commands
Implement these MCP-specific commands (reference `docs/demand.md`):
- `mcp start <name> [--all]` - Start containers
- `mcp stop <name> [--all]` - Stop containers  
- `mcp restart <name> [--all]` - Restart containers
- `mcp get <name>` - Show config/status/logs
- `mcp log <name>` - Show container logs
- `mcp list` - List all registered servers
- `mcp add <name> --command "<docker_command>" [--host <ip>]` - Register new server
- `mcp remove <name>` - Unregister server

### Testing Approach
- Unit tests in `tests/model/` follow pattern `test_<modelname>.py`
- Test YAML serialization for all models
- Use example patterns from `examples/demo_registry_crud.py` for integration tests
- Run tests with: `uv run pytest`

## Development Workflow

### Setup
```bash
uv sync
uv pip install -e .
```

### Key Files to Understand
- `docs/demand.md` - Complete requirements and architecture specification
- `src/msm/data/models.py` - All data models and validation logic
- `examples/demo_registry_crud.py` - Working example of registry operations  
- `src/msm/entrypoint/cli/commands/base.py` - Command framework base class

### Dependencies Context
- **docker**: Container management via Docker API
- **pydantic**: Data validation and serialization
- **rich**: Terminal formatting and tables
- **fastapi**: Future web API (server component)
- **paramiko**: SSH for remote server connections
- **pyyaml**: Configuration file management

## Current Priorities
1. Complete `ContainerManager` implementation with Docker API integration
2. Add MCP lifecycle management commands to CLI
3. Implement `StatusMonitor` for container health checking
4. Create `RemoteManager` for distributed server support

## Anti-Patterns to Avoid
- Don't bypass the Pydantic model validation - use proper field validation
- Don't hardcode Docker commands - use the configurable `docker_command` from `MCPServerConfig`
- Don't create new CLI patterns - extend the existing `BaseCommand` framework
- Don't skip YAML serialization tests - the persistence layer depends on this

When implementing new features, always check existing patterns in the codebase first, especially the working examples in the `examples/` directory.
