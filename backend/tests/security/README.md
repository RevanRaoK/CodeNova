# Security Testing Guide

## Overview

This directory contains comprehensive security tests to ensure the CodeNova platform is protected against common vulnerabilities and attacks.

## Test Suites

### 1. Authentication Security (`test_security.py`)

Tests authentication mechanisms:
- **Unauthenticated Access**: Verify protected endpoints require auth
- **Invalid Tokens**: Reject malformed or invalid tokens
- **Expired Tokens**: Reject expired authentication tokens
- **Password Requirements**: Enforce strong password policies
- **SQL Injection in Login**: Prevent SQL injection attacks

### 2. Authorization Security

Tests access control:
- **Role-Based Access**: Users cannot access admin endpoints
- **Data Isolation**: Users cannot access other users' data
- **Cross-User Modification**: Prevent unauthorized data modification
- **Team Isolation**: Team leads cannot access other teams

### 3. File Upload Security

Tests file upload safety:
- **Malicious File Types**: Reject executables and scripts
- **File Size Limits**: Enforce maximum file size
- **Path Traversal**: Prevent directory traversal attacks
- **MIME Type Validation**: Verify file content matches type

### 4. Injection Prevention

Tests against injection attacks:
- **SQL Injection**: Prevent SQL injection in all inputs
- **XSS Prevention**: Sanitize user input to prevent XSS
- **Command Injection**: Prevent command execution attacks

### 5. Data Privacy

Tests data protection:
- **Password Protection**: Never return passwords in API
- **API Key Encryption**: Encrypt sensitive keys at rest
- **Audit Logging**: Log access to sensitive data
- **User Data Isolation**: Proper data isolation between users

## Running Security Tests

### Run All Security Tests

```bash
# From backend directory
pytest tests/security/ -v -m security

# Or use the test runner script
./tests/run_e2e_tests.sh --security-only
```

### Run Specific Test Classes

```bash
# Authentication tests only
pytest tests/security/test_security.py::TestAuthenticationSecurity -v

# File upload security only
pytest tests/security/test_security.py::TestFileUploadSecurity -v
```

### Run Critical Security Tests

```bash
# Tests marked as critical
pytest tests/security/ -v -m "security and critical"
```

## Security Checklist

### Authentication & Authorization

- [ ] All protected endpoints require authentication
- [ ] Invalid tokens are rejected
- [ ] Expired tokens are rejected
- [ ] Strong password requirements enforced
- [ ] SQL injection in login prevented
- [ ] Users cannot access admin endpoints
- [ ] Users cannot access other users' data
- [ ] Role-based access control works correctly

### Input Validation

- [ ] File type validation works
- [ ] File size limits enforced
- [ ] Path traversal prevented
- [ ] MIME type validation works
- [ ] SQL injection prevented in all inputs
- [ ] XSS attacks prevented
- [ ] Command injection prevented

### Data Protection

- [ ] Passwords never returned in API
- [ ] Sensitive data encrypted at rest
- [ ] Sensitive operations logged
- [ ] User data properly isolated
- [ ] API keys encrypted
- [ ] PII handled according to policy

## Common Vulnerabilities Tested

### OWASP Top 10 Coverage

1. **Broken Access Control** ✓
   - Tests: Authorization security suite
   - Coverage: Role-based access, data isolation

2. **Cryptographic Failures** ✓
   - Tests: Data privacy suite
   - Coverage: Password hashing, API key encryption

3. **Injection** ✓
   - Tests: Injection prevention suite
   - Coverage: SQL, XSS, command injection

4. **Insecure Design** ✓
   - Tests: Throughout all suites
   - Coverage: Security by design principles

5. **Security Misconfiguration** ✓
   - Tests: Authentication security
   - Coverage: Default credentials, error messages

6. **Vulnerable Components** ⚠️
   - Manual: Dependency scanning required
   - Tools: `pip-audit`, `safety`

7. **Authentication Failures** ✓
   - Tests: Authentication security suite
   - Coverage: Token validation, session management

8. **Data Integrity Failures** ✓
   - Tests: Input validation
   - Coverage: File validation, data verification

9. **Logging Failures** ✓
   - Tests: Audit logging tests
   - Coverage: Security event logging

10. **Server-Side Request Forgery** ⚠️
    - Manual: Code review required
    - Tests: Limited automated coverage

## Attack Scenarios Tested

### 1. Authentication Bypass

```python
# Attempt to access protected endpoint without auth
response = client.get("/api/v1/analysis/direct/history")
assert response.status_code == 401

# Attempt with invalid token
headers = {"Authorization": "Bearer fake_token"}
response = client.get("/api/v1/analysis/direct/history", headers=headers)
assert response.status_code == 401
```

### 2. Privilege Escalation

```python
# Regular user attempts to access admin endpoint
response = authenticated_client.get("/api/v1/admin/users")
assert response.status_code == 403
```

### 3. SQL Injection

```python
# Attempt SQL injection in search
response = admin_client.get("/api/v1/admin/users?search=' OR 1=1--")
assert response.status_code in [200, 400]
# Verify no unauthorized data returned
```

### 4. File Upload Attack

```python
# Attempt to upload malicious file
files = {"files": ("malware.exe", b"MZ\x90\x00", "application/x-msdownload")}
response = authenticated_client.post("/api/v1/files/upload-batch", files=files)
assert response.status_code == 400
```

### 5. Cross-Site Scripting (XSS)

```python
# Attempt XSS in feedback comment
feedback_data = {
    "issue_id": issue_id,
    "feedback_type": "accept",
    "comment": "<script>alert('XSS')</script>"
}
response = authenticated_client.post("/api/v1/feedback/submit", json=feedback_data)
# Verify script tags are sanitized
```

## Security Testing Best Practices

### 1. Test Both Positive and Negative Cases

```python
# Positive: Valid input should work
response = client.post("/api/endpoint", json=valid_data)
assert response.status_code == 200

# Negative: Invalid input should be rejected
response = client.post("/api/endpoint", json=malicious_data)
assert response.status_code == 400
```

### 2. Test Edge Cases

- Empty inputs
- Very long inputs
- Special characters
- Unicode characters
- Null bytes

### 3. Test Multiple Attack Vectors

For each vulnerability, test:
- Direct attacks
- Encoded attacks (URL encoding, base64, etc.)
- Nested attacks
- Timing attacks

### 4. Verify Error Messages

```python
# Error messages should not leak sensitive info
response = client.post("/api/auth/login", data=invalid_creds)
assert "user not found" not in response.json()["detail"].lower()
assert "invalid password" not in response.json()["detail"].lower()
# Should be generic: "Invalid credentials"
```

## Manual Security Testing

Some security aspects require manual testing:

### 1. Dependency Vulnerabilities

```bash
# Check for known vulnerabilities
pip-audit
safety check

# Update vulnerable packages
pip install --upgrade package_name
```

### 2. SSL/TLS Configuration

```bash
# Test SSL configuration
nmap --script ssl-enum-ciphers -p 443 your-domain.com

# Check certificate
openssl s_client -connect your-domain.com:443
```

### 3. Security Headers

```bash
# Check security headers
curl -I https://your-domain.com

# Should include:
# - Strict-Transport-Security
# - X-Content-Type-Options
# - X-Frame-Options
# - Content-Security-Policy
```

### 4. Rate Limiting

```bash
# Test rate limiting
for i in {1..100}; do
  curl -X POST https://your-domain.com/api/auth/login
done
# Should see 429 Too Many Requests
```

## Penetration Testing

For comprehensive security assessment:

### Tools

1. **OWASP ZAP**: Automated security scanner
2. **Burp Suite**: Web application security testing
3. **SQLMap**: SQL injection testing
4. **Nikto**: Web server scanner

### Process

1. **Reconnaissance**: Gather information about the application
2. **Scanning**: Identify potential vulnerabilities
3. **Exploitation**: Attempt to exploit vulnerabilities
4. **Reporting**: Document findings and recommendations

## Security Incident Response

If a security test fails:

1. **Assess Severity**:
   - Critical: Authentication bypass, data exposure
   - High: Privilege escalation, injection vulnerabilities
   - Medium: Information disclosure, weak validation
   - Low: Minor configuration issues

2. **Immediate Actions**:
   - Document the vulnerability
   - Assess impact and exploitability
   - Implement temporary mitigation if needed

3. **Remediation**:
   - Fix the vulnerability
   - Add test to prevent regression
   - Review similar code for same issue

4. **Verification**:
   - Re-run security tests
   - Perform manual verification
   - Update security documentation

## Compliance

### GDPR Compliance

- [ ] User data can be exported
- [ ] User data can be deleted
- [ ] Consent is tracked
- [ ] Data processing is logged
- [ ] Data minimization practiced

### SOC 2 Compliance

- [ ] Access controls implemented
- [ ] Audit logging in place
- [ ] Data encryption at rest and in transit
- [ ] Security monitoring active
- [ ] Incident response plan exists

## Continuous Security

### Automated Security Scanning

```yaml
# GitHub Actions example
- name: Security Scan
  run: |
    pip install safety bandit
    safety check
    bandit -r app/
```

### Regular Security Reviews

- Weekly: Review security test results
- Monthly: Dependency vulnerability scan
- Quarterly: Penetration testing
- Annually: Comprehensive security audit

## Reporting Security Issues

If you discover a security vulnerability:

1. **Do Not** create a public issue
2. **Do** report privately to security team
3. **Include**:
   - Description of vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

## Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [OWASP Testing Guide](https://owasp.org/www-project-web-security-testing-guide/)
- [CWE Top 25](https://cwe.mitre.org/top25/)
- [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework)
