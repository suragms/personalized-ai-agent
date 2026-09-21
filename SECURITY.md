# Security Policy

## Supported Versions

We release security updates for the following versions:

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

## Reporting a Vulnerability

**Please do not report security vulnerabilities through public GitHub issues.**

If you discover a security vulnerability, please send an email to **security@yourproject.com** (replace with actual email) with the following information:

1. **Type of vulnerability** (e.g., XSS, SQL injection, authentication bypass)
2. **Full paths** of source file(s) related to the vulnerability
3. **Location** of the affected source code (tag/branch/commit or direct URL)
4. **Step-by-step instructions** to reproduce the issue
5. **Proof-of-concept or exploit code** (if possible)
6. **Impact** of the vulnerability and how an attacker might exploit it

### What to Expect

- **Initial Response**: Within 48 hours, we'll acknowledge receipt of your report
- **Status Updates**: We'll keep you informed about our progress
- **Disclosure Timeline**: We aim to disclose vulnerabilities within 90 days of the initial report
- **Credit**: With your permission, we'll credit you in our security advisory

## Security Best Practices

### For Production Deployments

1. **Environment Variables**
   - Generate a strong `SECRET_KEY` (use `backend/scripts/generate_secret_key.py`)
   - Never commit `.env` files to version control
   - Use different secrets for development and production
   - Rotate secrets regularly

2. **Database Security**
   - Use strong passwords for database users
   - Restrict database access to backend services only
   - Enable SSL/TLS for database connections
   - Regular backups with encryption

3. **API Security**
   - Enable rate limiting in production
   - Use HTTPS only (set `SECURE_SSL_REDIRECT=True`)
   - Set `DEBUG=False` in production
   - Configure `ALLOWED_HOSTS` properly
   - Enable CSRF protection (default in Django)

4. **Authentication**
   - Use strong JWT secrets
   - Configure appropriate token expiration times
   - Implement account lockout after failed login attempts
   - Enable 2FA for sensitive accounts

5. **Dependencies**
   - Regularly update dependencies
   - Use `pip-audit` and `npm audit` to check for vulnerabilities
   - Pin dependency versions in production

6. **Access Control**
   - Follow principle of least privilege
   - Use role-based access control (RBAC)
   - Audit user permissions regularly
   - Disable or remove unused accounts

### For Development

1. **Code Review**
   - All code changes require review before merging
   - Security-sensitive changes require additional review
   - Use static analysis tools (Ruff, ESLint)

2. **Secrets in Development**
   - Use `.env.example` template
   - Never commit real secrets
   - Use separate credentials for development

3. **Testing**
   - Write security tests for authentication/authorization
   - Test input validation and sanitization
   - Test for common vulnerabilities (OWASP Top 10)

## Known Security Considerations

### Current Implementation

1. **AI Provider Keys**: When using real AI providers (OpenAI, Gemini), API keys are stored in environment variables. Ensure these are secured.

2. **OAuth Flow**: GitHub/Google OAuth uses manual code exchange. Ensure redirect URIs are properly configured in production.

3. **JWT Storage**: Frontend stores JWT tokens in memory (React context). They're not persisted in localStorage to reduce XSS risk.

4. **CORS**: Configured for localhost in development. Update `CORS_ALLOWED_ORIGINS` for production.

5. **File Uploads**: If adding file upload features, implement:
   - File type validation
   - Size limits
   - Virus scanning
   - Secure storage

## Security Update Process

1. **Patch Release**: Critical vulnerabilities trigger immediate patch releases
2. **Advisory**: We publish security advisories on GitHub
3. **Notification**: Security updates are announced via:
   - GitHub Security Advisories
   - Repository README
   - Release notes

## Vulnerability Disclosure Policy

We follow coordinated vulnerability disclosure:

1. **Report received** → Acknowledgment sent
2. **Validation** → Confirm and assess severity
3. **Fix developed** → Create patch in private
4. **Testing** → Verify fix resolves issue
5. **Release** → Deploy patch and publish advisory
6. **Public disclosure** → 90 days after initial report (or sooner if fix is deployed)

## Security Checklist for Contributors

Before submitting security-related changes:

- [ ] Input validation is implemented
- [ ] Output encoding prevents XSS
- [ ] Authentication is required where needed
- [ ] Authorization checks are in place
- [ ] Secrets are not hardcoded
- [ ] Sensitive data is encrypted
- [ ] Error messages don't leak information
- [ ] Dependencies are up to date
- [ ] Tests cover security requirements

## Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Django Security](https://docs.djangoproject.com/en/stable/topics/security/)
- [React Security Best Practices](https://reactjs.org/docs/security.html)
- [JWT Best Practices](https://tools.ietf.org/html/rfc8725)

## Contact

For security inquiries: **security@yourproject.com** (update this)

For general questions: Open a [GitHub Discussion](../../discussions)

---

**Thank you for helping keep Personal AI Agent secure!**
