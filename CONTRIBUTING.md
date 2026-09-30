# Contributing to Personal AI Agent

Thank you for your interest in contributing! This document provides guidelines for contributing to the Personal AI Agent platform.

## 🚀 Getting Started

1. **Fork the repository** and clone your fork
2. **Set up the development environment** following [docs/SETUP.md](docs/SETUP.md)
3. **Create a feature branch**: `git checkout -b feature/your-feature-name`
4. **Make your changes** with clear, descriptive commits
5. **Test your changes** thoroughly
6. **Submit a pull request** with a clear description

## 📋 Development Workflow

### Before You Start

- Check existing [issues](../../issues) and [pull requests](../../pulls) to avoid duplicates
- Open an issue to discuss major changes before implementing
- Review the [architecture documentation](docs/ARCHITECTURE.md)

### Setting Up Your Environment

```bash
# 1. Start backing services
docker compose -f infra/docker-compose.yml up -d

# 2. Backend setup
cd backend
python -m venv .venv
.venv/Scripts/activate  # Windows; source .venv/bin/activate on Unix
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser

# 3. Frontend setup
cd ../frontend
npm install
npm run dev
```

### Running Tests

```bash
# Backend tests
cd backend
.venv/Scripts/activate
python -m pytest

# Frontend tests
cd frontend
npm run test

# Type checking
npm run lint
```

### Code Style

#### Python (Backend)
- Follow [PEP 8](https://peps.python.org/pep-0008/)
- Use type hints where appropriate
- Maximum line length: 88 characters (Black formatter)
- Use docstrings for functions and classes

```python
def calculate_productivity_score(commits: int, prs: int) -> float:
    """Calculate productivity score based on commits and PRs.
    
    Args:
        commits: Number of commits in the period
        prs: Number of pull requests
        
    Returns:
        Score between 0 and 100
    """
    return min((commits * 2 + prs * 5) / 10, 100)
```

#### TypeScript/React (Frontend)
- Use functional components with hooks
- Prefer named exports over default exports (except for pages)
- Use TypeScript strictly (no `any` types)
- Follow the existing component structure

```typescript
interface UserStatsProps {
  commits: number;
  prs: number;
}

export function UserStats({ commits, prs }: UserStatsProps) {
  return (
    <div>
      <p>Commits: {commits}</p>
      <p>PRs: {prs}</p>
    </div>
  );
}
```

## 🎯 Contribution Guidelines

### Commit Messages

Use [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add real-time notification support
fix: correct database port in .env
docs: update setup instructions for Windows
refactor: extract GitHub API logic to service layer
test: add tests for productivity agent
chore: update dependencies
```

### Pull Request Process

1. **Update documentation** if you're changing functionality
2. **Add tests** for new features
3. **Ensure all tests pass** and there are no linting errors
4. **Update CHANGELOG.md** (if applicable)
5. **Request review** from maintainers

### PR Title Format

```
[Type] Brief description

Examples:
[Feature] Add WebSocket support for real-time updates
[Fix] Correct bundle size optimization
[Docs] Add API endpoint documentation
```

### PR Description Template

```markdown
## Description
Brief description of what this PR does

## Changes
- Change 1
- Change 2

## Testing
How has this been tested?

## Screenshots (if applicable)
Add screenshots for UI changes

## Checklist
- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] No linting errors
- [ ] Commits follow conventional commits format
```

## 🐛 Reporting Bugs

### Before Submitting a Bug Report

- Check the [existing issues](../../issues)
- Update to the latest version
- Check [docs/SETUP.md](docs/SETUP.md) for common issues

### Bug Report Template

```markdown
**Describe the bug**
A clear description of what the bug is.

**To Reproduce**
Steps to reproduce:
1. Go to '...'
2. Click on '...'
3. See error

**Expected behavior**
What you expected to happen.

**Screenshots**
If applicable, add screenshots.

**Environment:**
- OS: [e.g., Windows 11, Ubuntu 22.04, macOS 14]
- Python version: [e.g., 3.12.0]
- Node version: [e.g., 20.10.0]
- Docker version: [e.g., 24.0.6]

**Additional context**
Any other relevant information.
```

## 💡 Suggesting Features

### Feature Request Template

```markdown
**Is your feature request related to a problem?**
A clear description of the problem.

**Describe the solution you'd like**
What you want to happen.

**Describe alternatives you've considered**
Other solutions you've thought about.

**Additional context**
Any other relevant information, mockups, or examples.
```

## 🔒 Security

If you discover a security vulnerability, please follow our [Security Policy](SECURITY.md) and **do not** open a public issue.

## 📝 Documentation

- Update documentation for any user-facing changes
- Add JSDoc/docstrings for new functions
- Update API documentation if adding/changing endpoints
- Consider adding examples for complex features

## 🎨 UI/UX Guidelines

- Follow the existing design system
- Use shadcn/ui components where possible
- Ensure accessibility (WCAG 2.1 Level AA)
- Test on different screen sizes
- Support both light and dark themes

## 🧪 Testing Guidelines

### Backend Tests
- Write pytest tests for new services/agents
- Aim for >80% code coverage
- Test edge cases and error handling
- Mock external API calls

### Frontend Tests
- Write Vitest tests for utility functions
- Use React Testing Library for component tests
- Test user interactions
- Test error states

## 📦 Adding Dependencies

### When adding new dependencies:

1. **Justify the need** - explain why it's necessary
2. **Check alternatives** - consider existing solutions
3. **Verify license** - ensure compatible license
4. **Consider size** - especially for frontend dependencies
5. **Check maintenance** - ensure actively maintained

### Backend
```bash
pip install package-name
pip freeze > requirements.txt
```

### Frontend
```bash
npm install package-name
# Update package.json
```

## 🏗️ Architecture Decisions

For significant architectural changes:

1. Open an issue for discussion first
2. Consider impact on existing features
3. Update architecture documentation
4. Provide migration guide if needed

## 🤝 Code Review

### As a Reviewer
- Be constructive and respectful
- Explain the "why" behind suggestions
- Approve when ready or request changes with clear feedback

### As an Author
- Respond to all comments
- Don't take feedback personally
- Ask for clarification if needed
- Mark conversations as resolved

## 📜 License

By contributing, you agree that your contributions will be licensed under the SURAG-1.0 License.

## 🙏 Recognition

Contributors will be recognized in:
- README.md contributors section
- Release notes for significant contributions
- Project documentation

## 💬 Communication

- **Issues**: For bug reports and feature requests
- **Pull Requests**: For code contributions
- **Discussions**: For questions and general discussion

## ✨ First-Time Contributors

Look for issues labeled:
- `good first issue` - Good for newcomers
- `help wanted` - Extra attention needed
- `documentation` - Documentation improvements

Thank you for contributing to Personal AI Agent! 🚀
