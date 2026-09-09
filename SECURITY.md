# Security

Do not report credentials, private footage, transcripts, or account data in public issues. For a suspected vulnerability, use this repository's GitHub **Security > Report a vulnerability** action when available. If private reporting is unavailable, contact the maintainers through an existing private support channel and request a secure reporting route before sending sensitive details.

Include the affected plugin version, client and version, expected and observed behavior, and a minimal reproduction with synthetic data. Redact authentication headers, signed upload or download URLs, and identifiers tied to real users.

The plugin connects to a hosted MCP service through browser authentication. Do not commit tokens or add them to plugin manifests. Review the skill instructions and MCP destination before installing an untrusted fork.

Use the latest published plugin version. Repository access and hosted-service access are separate; a successful install does not establish authorization to service data.
