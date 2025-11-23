# Security Policy

## Supported Versions

We release patches for security vulnerabilities in the following versions:

| Version | Supported          |
| ------- | ------------------ |
| 2.1.x   | :white_check_mark: |
| 2.0.x   | :white_check_mark: |
| < 2.0   | :x:                |

## Reporting a Vulnerability

We take the security of streamrip seriously. If you believe you have found a security vulnerability, please report it to us as described below.

### Where to Report

**Please DO NOT report security vulnerabilities through public GitHub issues.**

Instead, please report them via email to: [MAINTAINER_EMAIL_HERE]

You should receive a response within 48 hours. If for some reason you do not, please follow up via email to ensure we received your original message.

### What to Include

Please include the following information in your report:

- Type of vulnerability (e.g., SQL injection, credential exposure, etc.)
- Full paths of source file(s) related to the vulnerability
- Location of the affected source code (tag/branch/commit or direct URL)
- Step-by-step instructions to reproduce the issue
- Proof-of-concept or exploit code (if possible)
- Impact of the issue, including how an attacker might exploit it

### Response Process

1. **Acknowledgment** - We will acknowledge receipt of your vulnerability report within 48 hours
2. **Assessment** - We will investigate and validate the vulnerability
3. **Fix Development** - We will develop a fix and prepare a security advisory
4. **Disclosure** - We will coordinate disclosure timing with you
5. **Release** - We will release the fix and publish the security advisory

## Known Security Considerations

### Credential Storage

**Current Implementation:**
- Credentials are stored in `~/.config/streamrip/config.toml`
- Passwords are hashed using MD5 (reversible)
- Config file permissions are important to prevent unauthorized access

**Recommendations:**
- Protect your config file: `chmod 600 ~/.config/streamrip/config.toml` (Unix/Linux/macOS)
- Do not commit your config file to version control
- Do not share your config file with others
- Consider using encrypted home directories

**Future Improvements:**
- Migration to OS keyring/keychain for secure credential storage is planned
- See [CODEBASE_REVIEW.md](CODEBASE_REVIEW.md) for details

### SSL/TLS Verification

**Security Notice:**
The `--no-ssl-verify` flag disables SSL certificate verification and should **ONLY** be used in trusted environments or for debugging purposes.

**Risks:**
- Man-in-the-middle attacks
- Credential interception
- Data tampering

**When to use:**
- Corporate networks with SSL inspection (with proper authorization)
- Debugging certificate issues
- Development/testing only

**DO NOT use in production or on untrusted networks.**

### API Credentials and Tokens

**Important:**
- Never hardcode credentials in scripts or share them publicly
- Tokens and ARL cookies provide full access to your accounts
- Rotate credentials if you suspect they have been compromised
- Use separate accounts for testing when possible

### Legal Considerations

**Disclaimer:**
streamrip is intended for downloading content you have legal access to. Users are responsible for complying with:

- Terms of Service of streaming platforms (Qobuz, Tidal, Deezer, SoundCloud)
- Copyright laws in their jurisdiction
- Digital Rights Management (DRM) regulations
- Platform-specific licensing agreements

**By using streamrip, you agree to:**
- Only download content you have the legal right to access
- Respect intellectual property rights
- Use the tool responsibly and ethically

The maintainers are not responsible for how users choose to use this software.

### Hardcoded Cryptographic Keys

**Transparency Notice:**
This software contains hardcoded decryption keys for certain streaming services (e.g., Deezer Blowfish key). These keys are:

- Publicly available and widely known
- Used only for decrypting content you are legally authorized to access
- Not intended for circumventing DRM on unauthorized content
- Subject to the legal considerations mentioned above

**Location:** `streamrip/client/downloadable.py:30`

## Security Best Practices for Users

### 1. Keep Software Updated
```bash
pip install streamrip --upgrade
```

### 2. Verify Installation
```bash
pip show streamrip
# Verify version and source
```

### 3. Secure Your Configuration
```bash
# Unix/Linux/macOS
chmod 600 ~/.config/streamrip/config.toml

# Windows
# Right-click config.toml → Properties → Security → Advanced
# Ensure only your user account has access
```

### 4. Use Virtual Environments
```bash
python -m venv streamrip-env
source streamrip-env/bin/activate  # Unix/Linux/macOS
# or
streamrip-env\Scripts\activate  # Windows
pip install streamrip
```

### 5. Monitor for Suspicious Activity
- Check your streaming service account activity regularly
- Look for unexpected downloads or login locations
- Rotate credentials if anything seems suspicious

### 6. Network Security
- Use HTTPS only (default behavior)
- Avoid using `--no-ssl-verify` on public networks
- Consider using a VPN on untrusted networks

## Security Roadmap

We are actively working to improve security. Planned improvements include:

- [ ] Migration to OS keyring for credential storage
- [ ] Enhanced input validation and sanitization
- [ ] Improved error messages (without exposing sensitive data)
- [ ] Security-focused CI/CD scanning
- [ ] Regular dependency audits
- [ ] Security testing in CI pipeline

See [CODEBASE_REVIEW.md](CODEBASE_REVIEW.md) Phase 1 for details.

## Dependencies and Supply Chain Security

### Third-Party Dependencies

streamrip relies on several third-party libraries. We:

- Pin critical dependencies to specific versions
- Monitor for security advisories
- Update dependencies regularly
- Use CodeQL for security scanning

### Users Should:

1. **Verify Package Integrity**
   ```bash
   pip install streamrip --require-hashes
   # Use hashes from PyPI
   ```

2. **Check for Known Vulnerabilities**
   ```bash
   pip install safety
   safety check
   ```

3. **Use Trusted Sources**
   - Install only from official PyPI
   - Verify GitHub repository authenticity
   - Check GPG signatures when available

## Incident Response

If a security incident is confirmed:

1. **Immediate Actions**
   - Assess the scope and impact
   - Develop and test a fix
   - Prepare security advisory

2. **User Notification**
   - GitHub Security Advisory
   - Release notes
   - Direct notification for critical issues

3. **Post-Incident**
   - Root cause analysis
   - Process improvements
   - Documentation updates

## Security Hall of Fame

We thank the following security researchers for responsible disclosure:

_(No reports yet)_

## Contact

Security Email: [MAINTAINER_EMAIL_HERE]
GitHub: https://github.com/nathom/streamrip

## Additional Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Python Security Best Practices](https://python.readthedocs.io/en/latest/library/security_warnings.html)
- [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework)

---

**Last Updated:** 2025-11-23
**Policy Version:** 1.0
