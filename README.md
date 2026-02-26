# Azure Multi-Tenant Governance Platform

A lightweight, cost-effective platform for managing Azure/M365 governance across multiple tenants. Built with Python, FastAPI, HTMX, and Tailwind CSS.

## Features

- **Cost Optimization**: Aggregate cost visibility, anomaly detection, idle resource identification
- **Compliance Monitoring**: Policy compliance tracking, secure score aggregation, drift detection
- **Resource Management**: Cross-tenant inventory, tagging compliance, orphaned resource detection
- **Identity Governance**: Privileged access reporting, guest user management, MFA compliance

## Quick Start

### Prerequisites

- Python 3.11+
- Azure subscriptions with appropriate permissions
- App registrations in each tenant (or Azure Lighthouse delegation)

### Installation

```bash
# Clone the repository
git clone https://github.com/your-org/azure-governance-platform.git
cd azure-governance-platform

# Create virtual environment
uv venv --index-url https://pypi.ci.artifacts.walmart.com/artifactory/api/pypi/external-pypi/simple --allow-insecure-host pypi.ci.artifacts.walmart.com
source .venv/bin/activate  # or `.venv\Scripts\activate` on Windows

# Install dependencies
uv pip install -e . --index-url https://pypi.ci.artifacts.walmart.com/artifactory/api/pypi/external-pypi/simple --allow-insecure-host pypi.ci.artifacts.walmart.com

# Copy and configure environment
cp .env.example .env
# Edit .env with your Azure credentials

# Run the application
uvicorn app.main:app --reload
```

### Azure Setup

#### Option A: Azure Lighthouse (Recommended)

1. Deploy Lighthouse delegation template to each managed tenant
2. Configure a single app registration in the managing tenant
3. Set `AZURE_TENANT_ID`, `AZURE_CLIENT_ID`, `AZURE_CLIENT_SECRET` in `.env`

#### Option B: Per-Tenant App Registrations

1. Create an app registration in each tenant
2. Grant required permissions (see docs/PERMISSIONS.md)
3. Store credentials in Azure Key Vault
4. Configure `KEY_VAULT_URL` in `.env`

## API Documentation

Once running, access the interactive API docs:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Project Structure

```
azure-governance-platform/
├── app/
│   ├── api/
│   │   ├── routes/          # API endpoints
│   │   └── services/        # Business logic
│   ├── core/                # Config, DB, scheduler
│   ├── models/              # SQLAlchemy models
│   ├── schemas/             # Pydantic schemas
│   ├── templates/           # Jinja2 templates
│   └── static/              # CSS, JS assets
├── docs/                    # Documentation
├── tests/                   # Test suite
├── scripts/                 # Utility scripts
└── data/                    # SQLite database (gitignored)
```

## Configuration

| Variable | Description | Default |
|----------|-------------|--------|
| `AZURE_TENANT_ID` | Managing tenant ID | Required |
| `AZURE_CLIENT_ID` | App registration client ID | Required |
| `AZURE_CLIENT_SECRET` | Client secret | Required |
| `DATABASE_URL` | SQLite connection string | `sqlite:///./data/governance.db` |
| `COST_SYNC_INTERVAL_HOURS` | Cost sync frequency | `24` |
| `COMPLIANCE_SYNC_INTERVAL_HOURS` | Compliance sync frequency | `4` |

See `.env.example` for all configuration options.

## Development

```bash
# Install dev dependencies
uv pip install -e ".[dev]" --index-url https://pypi.ci.artifacts.walmart.com/artifactory/api/pypi/external-pypi/simple --allow-insecure-host pypi.ci.artifacts.walmart.com

# Run linting
ruff check .

# Run type checking
mypy app/

# Run tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html
```

## Deployment

### Azure App Service (Minimal Cost)

```bash
# Build and deploy
az webapp up --name governance-platform --sku B1 --runtime "PYTHON:3.11"
```

Estimated cost: ~$13/month

### Docker

```bash
docker build -t governance-platform .
docker run -p 8000:8000 --env-file .env governance-platform
```

## Cost Estimates

| Deployment | Monthly Cost |
|------------|-------------|
| App Service B1 | ~$13 |
| Key Vault (optional) | ~$1 |
| **Total MVP** | **~$15-20** |

## Roadmap

- [x] MVP: Cost, Compliance, Resources, Identity dashboards
- [ ] Automated remediation suggestions
- [ ] Custom compliance frameworks
- [ ] Power BI embedding
- [ ] Teams bot integration
- [ ] Access review workflows

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linting
5. Submit a pull request

## License

MIT License - see LICENSE file for details.
