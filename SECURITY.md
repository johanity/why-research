# Security Policy

## Reporting Vulnerabilities

If you discover a security vulnerability in this project, please report it
through one of the following channels:

- **GitHub Issues**: Open an issue at https://github.com/johanity/why/issues
- **Email**: johanity@users.noreply.github.com

Please include steps to reproduce the issue and any relevant details about
your environment. We aim to acknowledge reports within 48 hours.

## Secrets and API Keys

This repository never stores API keys, tokens, or credentials in source code.
All secrets must be provided via environment variables at runtime.

Contributors must not commit `.env` files, API keys, or any other sensitive
material. The `.gitignore` file is configured to exclude common secret files.

## Supported Versions

Security updates are applied to the latest release only.

## Responsible Disclosure

We ask that you give us reasonable time to address reported vulnerabilities
before public disclosure. We will credit reporters unless anonymity is
requested.
