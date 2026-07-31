# Security policy

## Portfolio scope

This repository uses synthetic data and intentionally excludes production credentials, customer data, private infrastructure, and provider-specific ingestion logic.

## Reporting

If you identify a vulnerability or accidental disclosure, contact `bragin.arbitr@gmail.com`. Do not open a public issue containing secrets, personal data, or exploitable details.

## Secret handling

- Keep real values in an untracked `.env` or an approved secret manager.
- Do not store marketplace credentials in browser-accessible variables.
- Do not return provider secrets from API responses.
- Rotate any credential immediately if it is committed or logged.
