# Salon Assistant Documentation

Welcome to the Salon Assistant documentation. This index provides an overview of all documentation resources available for the project.

## Documentation Resources

### Core Documentation

- [English Documentation](README.md) - Complete technical documentation in English
- [Spanish Documentation](DOCUMENTACION.md) - Complete technical documentation in Spanish

### Development Resources

- [Contributing Guide](CONTRIBUTING.md) - How to contribute to the project
- [Code of Conduct](CODE_OF_CONDUCT.md) - Guidelines for participation

### Deployment and Operations

- [Deployment Guide](../DEPLOYMENT.md) - Instructions for deploying the application
- [Monitoring Guide](monitoring.md) - Information about monitoring and alerting

### API Documentation

The API documentation is automatically generated and available at:

- Development: `http://localhost:8000/docs` or `http://localhost:8000/redoc`
- Production: `https://your-domain.com/docs` or `https://your-domain.com/redoc`

## Components Documentation

Each major component is documented in the main documentation files (README.md and DOCUMENTACION.md), but here's a quick reference:

- **Authentication System** - User authentication and authorization
- **Appointment Management** - Core appointment booking and scheduling
- **Notification System** - Client reminders and communications
- **Service Management** - Salon service catalog management
- **Scheduling System** - Availability management and optimization

## FAQ and Troubleshooting

Common issues and their solutions can be found in the [Troubleshooting Guide](troubleshooting.md).

## Project Structure

The application follows a modular structure:

```
salon-assistant/
├── app/                    # Main application code
│   ├── api/                # API endpoints
│   ├── core/               # Core configuration
│   ├── db/                 # Database configuration
│   ├── middleware/         # HTTP middleware
│   ├── models/             # Database models
│   ├── schemas/            # Pydantic schemas
│   ├── services/           # Business logic
│   ├── tasks/              # Background tasks
│   └── utils/              # Utility functions
├── docs/                   # Documentation
├── scripts/                # Utility scripts
├── tests/                  # Test suite
├── alembic/                # Database migrations
└── requirements.txt        # Dependencies
```

## Getting Started

For new developers:

1. Review the [README.md](../README.md) file for an overview
2. Follow the [Contributing Guide](CONTRIBUTING.md) to set up your environment
3. Check the [English Documentation](README.md) or [Spanish Documentation](DOCUMENTACION.md) for detailed information

## Feedback and Support

If you have questions or feedback about the documentation:

1. For documentation improvements, please open an issue or pull request
2. For questions, please use the project's issue tracker

## Code Documentation

For detailed code reference documentation, you can generate it using the provided script:

```bash
# On Unix/Linux/Mac:
python scripts/generate_docs.py

# On Windows:
python scripts/generate_docs.py
```

This will create comprehensive code documentation in the `docs/code/` directory, including:
- Detailed class documentation
- Function documentation with signatures
- Module documentation
- Package overview

Thank you for using Salon Assistant! 