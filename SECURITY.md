# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.16.x  | ✅                |
| 1.15.x  | ✅                |
| 1.14.x  | ❌                |
| < 1.14  | ❌                |

## Reporting a Vulnerability

### Where to Report
Please report security vulnerabilities by creating a **private security advisory** on GitHub:
- Go to [Security tab](https://github.com/hipotures/todoit/security) 
- Click "Report a vulnerability"
- Use the private advisory form

### What to Include
1. **Description** - Detailed description of the vulnerability
2. **Impact** - Potential impact and affected systems
3. **Steps to Reproduce** - Clear reproduction steps
4. **Environment** - OS, Python version, TODOIT version
5. **Proof of Concept** - If applicable (avoid destructive examples)

### Response Timeline
- **Initial Response**: Within 48 hours
- **Assessment**: Within 1 week  
- **Fix & Release**: Within 2 weeks for critical issues

## Security Considerations

### Database Security
- **Local Storage**: TODOIT uses local SQLite database by default
- **File Permissions**: Database files should have restricted permissions (600/640)
- **Backup Security**: Ensure backup files are properly secured

### MCP Integration
- **Local Communication**: MCP server communicates locally with Claude Code
- **No Network Exposure**: No network ports opened by default
- **Process Isolation**: MCP server runs as separate process

### Input Validation
- **Pydantic Models**: All input validated through Pydantic schemas
- **SQL Injection**: Protected by SQLAlchemy ORM parameterized queries
- **Path Traversal**: File paths validated and restricted

### Environment Variables
- **Sensitive Data**: Avoid storing sensitive data in environment variables
- **TODOIT_DB_PATH**: Ensure database path is secure
- **Access Control**: Use environment isolation (FORCE_TAGS) appropriately

## Best Practices

### Production Deployment
```bash
# Secure database file permissions
chmod 600 $TODOIT_DB_PATH

# Use environment isolation
export TODOIT_FORCE_TAGS=production

# Run with minimal privileges
python -m interfaces.mcp_server
```

### Development Environment
```bash
# Use separate development database
export TODOIT_DB_PATH=/dev/todoit_dev.db

# Enable debug logging if needed
export TODOIT_DEBUG=1

# Use development environment tags
export TODOIT_FORCE_TAGS=dev
```

### Multi-User Considerations
- **Separate Databases**: Each user should have separate database file
- **File Permissions**: Ensure other users cannot read database files
- **Environment Isolation**: Use FORCE_TAGS for user/team separation

## Known Security Limitations

### Current Architecture
- **Single User**: Designed for single-user local usage
- **No Authentication**: No built-in user authentication system
- **Local File System**: Relies on OS file permissions for security

### Future Enhancements
- Multi-user authentication (planned for v2.0)
- API key authentication for MCP server
- Encrypted database storage option
- Audit logging for security events

## Security Updates

Security updates will be:
- **Released immediately** for critical vulnerabilities
- **Announced** in GitHub releases and CHANGELOG.md
- **Backported** to supported versions when possible

## Contact

For security-related questions or concerns:
- **GitHub**: Create private security advisory
- **General Questions**: Use [GitHub Discussions](https://github.com/hipotures/todoit/discussions)

---

*Last updated: August 10, 2025*