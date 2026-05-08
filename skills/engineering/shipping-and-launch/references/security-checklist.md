# Security Checklist

Reference file for security-and-hardening, code-review-and-quality, and shipping-and-launch skills.

## Pre-Commit Security Checks

- [ ] No secrets, API keys, or tokens in source code or commit history
- [ ] No hardcoded credentials (use environment variables or secret managers)
- [ ] `.gitignore` excludes `.env`, `*.key`, `*.pem`, and other sensitive files
- [ ] Dependencies audited for known vulnerabilities (`npm audit`, `pip audit`, `cargo audit`)

## Authentication

- [ ] Passwords hashed with bcrypt/scrypt/argon2 (salt rounds ≥ 12)
- [ ] Session tokens are `httpOnly`, `secure`, `sameSite`
- [ ] Login has rate limiting (e.g., 5 attempts per minute per IP)
- [ ] Password reset tokens expire within 1 hour
- [ ] Multi-factor authentication available for sensitive operations
- [ ] JWT tokens have reasonable expiry and are validated on every request

## Authorization

- [ ] Every endpoint checks user permissions (not just authentication)
- [ ] Users can only access their own resources (tenant isolation)
- [ ] Admin actions require admin role verification
- [ ] Principle of least privilege applied to service accounts
- [ ] No privilege escalation paths (horizontal or vertical)

## Input Validation

- [ ] All user input validated at the boundary (API layer)
- [ ] SQL queries are parameterized (never string concatenation)
- [ ] HTML output is encoded/escaped (XSS prevention)
- [ ] File uploads validated for type, size, and content
- [ ] Command arguments are escaped (OS command injection prevention)
- [ ] Input lengths bounded to prevent DoS

## Data Protection

- [ ] Sensitive data encrypted at rest (PII, financial data, health records)
- [ ] All data in transit over TLS 1.2+ (no HTTP for sensitive endpoints)
- [ ] No sensitive data in URLs, logs, or error messages
- [ ] Database connections use TLS
- [ ] Backup encryption enabled

## API Security

- [ ] CORS configured with specific origins (no `*` in production)
- [ ] Rate limiting on all public endpoints
- [ ] Request size limits enforced
- [ ] API versioning prevents breaking changes
- [ ] GraphQL query depth and complexity limits
- [ ] No exposed debug endpoints in production

## Infrastructure

- [ ] Security headers configured:
  - `Content-Security-Policy`
  - `X-Content-Type-Options: nosniff`
  - `X-Frame-Options: DENY`
  - `Strict-Transport-Security` (HSTS)
  - `Referrer-Policy: strict-origin-when-cross-origin`
- [ ] Container images use minimal base (distroless/alpine)
- [ ] Containers run as non-root user
- [ ] Network policies restrict pod-to-pod communication
- [ ] Secrets managed via vault (not environment variables in production)

## OWASP Top 10 Quick Check

| # | Risk | Key Check |
|---|------|-----------|
| A01 | Broken Access Control | Verify every endpoint enforces authorization |
| A02 | Cryptographic Failures | Sensitive data encrypted at rest and in transit |
| A03 | Injection | All inputs parameterized, never concatenated |
| A04 | Insecure Design | Threat model reviewed for critical flows |
| A05 | Security Misconfiguration | Default credentials changed, unused features disabled |
| A06 | Vulnerable Components | `npm audit` / `pip audit` passes with no critical/high |
| A07 | Auth Failures | MFA available, account lockout after failed attempts |
| A08 | Software/Data Integrity | CI/CD pipeline secured, dependencies verified |
| A09 | Logging Failures | Security events logged, no sensitive data in logs |
| A10 | SSRF | URL inputs validated, allowlist for external requests |

## Pre-Launch Security Review

1. Run dependency audit: `npm audit --production` (0 critical/high)
2. Run SAST scanner (Semgrep, CodeQL, or SonarQube)
3. Verify no secrets in git history: `git log -p | grep -iE '(password|secret|api_key|token)'`
4. Confirm all security headers present in production responses
5. Verify TLS certificate is valid and HSTS is enabled
6. Check that debug/health endpoints are not publicly accessible
7. Review IAM policies for least privilege
8. Confirm backup and disaster recovery procedures are tested

## Incident Response Preparation

- [ ] Logging captures security-relevant events (auth failures, access denied, input validation failures)
- [ ] Alerts configured for anomalous patterns (spike in 401s, unusual user agents)
- [ ] Runbook exists for common security incidents
- [ ] Contact list for security team is up to date
