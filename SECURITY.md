# Security Policy

## Scope

UCIP is a Next.js frontend backed by Supabase (read-only public data) and a Python data
pipeline that runs against Google Earth Engine. There is no user authentication and no
user-submitted data path in the prototype — the main surfaces worth reporting on are:

- Supabase queries or environment handling that could leak credentials.
- Dependency vulnerabilities (npm or pip) with a known CVE.
- XSS or injection in any user-facing input (ward search, contribute form).

## Supported versions

UCIP is pre-release (no tagged versions yet). Only the `main` branch is supported.

## Reporting a vulnerability

**Do not open a public GitHub issue for security vulnerabilities.**

Report privately through
[GitHub Security Advisories](https://github.com/AnayDhawan/ucip/security/advisories/new).

Include:
- Description of the vulnerability
- Steps to reproduce
- Potential impact

### Response timeline

| Stage | Target |
|-------|--------|
| Acknowledgement | Within 48 hours |
| Status update | Within 7 days |
| Patch or mitigation | Within 30 days for critical; 90 days for moderate |

## Out of scope

- Vulnerabilities in third-party services (Supabase, Google Earth Engine, OpenStreetMap) —
  report to them directly.
- Theoretical vulnerabilities without a proof of concept.
