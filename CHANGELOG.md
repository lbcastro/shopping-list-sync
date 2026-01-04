# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-01-04

### Added
- Initial release of Shopping List Sync
- Automatic shopping list categorization using OpenAI
- Configurable supermarket aisle sections via YAML
- Real-time monitoring with configurable sync intervals
- Multiple deployment options (pip, Docker, systemd)
- Health check command for verifying configuration
- One-time sync mode for on-demand organization
- Comprehensive CLI with argument parsing
- Smart duplicate detection and removal
- Configurable error handling (logging, task creation, or both)
- State management for efficient change detection
- Retry logic with exponential backoff for API calls
- Comprehensive documentation and examples

### Extracted
- Core functionality from [mir-lca/chef](https://github.com/mir-lca/chef) repository
- Focused solely on shopping list organization
- Removed meal planning and PDF processing features
- Refactored hardcoded sections to YAML configuration

## [Unreleased]

### Planned Features
- Web UI for configuration and monitoring
- Support for local LLMs (Ollama, LM Studio)
- Multi-language support for non-English shopping lists
- Learning from user corrections to improve categorization
- Support for multiple shopping projects
- Mobile companion app
