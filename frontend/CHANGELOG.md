# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Health check script for validating system setup (`scripts/health-check.sh`)
- SECRET_KEY generator utility (`backend/scripts/generate_secret_key.py`)
- CONTRIBUTING.md with comprehensive contribution guidelines
- SECURITY.md with security policy and best practices
- IMPROVEMENTS.md documenting current issues and enhancement opportunities
- Frontend bundle optimization with code splitting

### Fixed
- Database configuration: Updated .env to use correct port 5433 for Docker PostgreSQL
- Documentation: Corrected Python version requirement from 3.14+ to 3.12+
- Frontend bundle size optimization through manual chunk splitting (reduced main bundle)

### Changed
- Frontend routing now uses lazy loading for better performance
- Vite build configuration optimized with manual chunks for vendors

## [0.1.0] - 2024-08-03

### Added
- Initial release of Personal AI Agent platform
- 10 autonomous AI agents (GitHub, Productivity, Projects, Reports, LinkedIn, Resume, Portfolio, Learning, Analytics, Notifications)
- Django 6 REST API backend with Celery task scheduling
- React 19 frontend with TypeScript and Tailwind CSS v4
- PostgreSQL 17 with pgvector for semantic memory
- Provider-agnostic AI layer (mock, Ollama, OpenAI, Gemini)
- JWT authentication with GitHub/Google OAuth support
- Docker Compose setup for backing services
- Comprehensive documentation (SETUP, ARCHITECTURE, API, DEPLOY)
- Demo data seeding with 6 weeks of realistic data
- Natural language AI Assistant with command routing
- Multi-format report exports (Markdown, HTML, PDF, Excel, Word)
- SURAG-1.0 License

### Security
- JWT token-based authentication
- Role-based access control (owner, admin, viewer)
- CORS configuration for API security
- Environment-based secrets management

[Unreleased]: https://github.com/yourusername/personal-ai-agent/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/yourusername/personal-ai-agent/releases/tag/v0.1.0
