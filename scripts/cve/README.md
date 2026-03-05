# CVE Security Scanning

This directory contains tools and scripts for scanning the IBM ODM Decision MCP Server project for Common Vulnerabilities and Exposures (CVEs).

## Overview

The project includes comprehensive CVE scanning capabilities using multiple security tools:

1. **pip-audit** - Python-specific CVE scanner using the PyPI Advisory Database
2. **Safety** - Checks dependencies against the Safety DB vulnerability database
3. **Bandit** - Static Application Security Testing (SAST) for Python code
4. **Trivy** - Comprehensive vulnerability scanner for dependencies and filesystem

## Quick Start

### Option 1: Using the Convenience Script (Recommended)

Run all CVE scans with a single command:

```bash
./scripts/cve/scan-cve.sh
```

View scan results:
```bash
./scripts/cve/scan-cve.sh --view
```

Clean up old results:
```bash
./scripts/cve/scan-cve.sh --clean
```

### Option 2: Using Docker Compose

Run all CVE scans using Docker Compose:

```bash
docker-compose -f scripts/cve/docker-compose.cve-scan.yaml up --build
```

This will:
- Build the scanning Docker image
- Run all security scanners
- Save results to `./scan-results/` directory
- Display results in the terminal

### Option 3: Using Docker Directly

Build the image:
```bash
docker build -f scripts/cve/Dockerfile.cve-scan -t python-cve-scanner .
```

Run the scan:
```bash
docker run --rm -v $(pwd)/scan-results:/app/scan-results python-cve-scanner
```

## Script Options

The `scan-cve.sh` script supports various options:

```bash
Usage: ./scripts/cve/scan-cve.sh [OPTIONS]

OPTIONS:
    -h, --help          Show help message
    -a, --all           Run all scanners (default)
    -p, --pip-audit     Run pip-audit only
    -s, --safety        Run Safety scan only
    -b, --bandit        Run Bandit SAST only
    -t, --trivy         Run Trivy scan only
    -c, --clean         Clean up scan results directory
    -v, --view          View existing scan results
    --no-cache          Build Docker image without cache

EXAMPLES:
    ./scripts/cve/scan-cve.sh                  # Run all scanners
    ./scripts/cve/scan-cve.sh --pip-audit      # Run only pip-audit
    ./scripts/cve/scan-cve.sh --clean          # Clean up results directory
    ./scripts/cve/scan-cve.sh --view           # View existing results
```

## Run Individual Scanners

You can run specific scanners by overriding the default command:

**pip-audit only:**
```bash
docker run --rm -v $(pwd)/scan-results:/app/scan-results python-cve-scanner \
  bash -c "uv tool run pip-audit --desc"
```

**Safety only:**
```bash
docker run --rm -v $(pwd)/scan-results:/app/scan-results python-cve-scanner \
  bash -c "uv tool run safety scan --detailed"
```

**Bandit only:**
```bash
docker run --rm -v $(pwd)/scan-results:/app/scan-results python-cve-scanner \
  bash -c "uv tool run bandit -r src/"
```

**Trivy only:**
```bash
docker run --rm -v $(pwd)/scan-results:/app/scan-results python-cve-scanner \
  bash -c "trivy fs --severity CRITICAL,HIGH,MEDIUM ."
```

## Scan Results

After running the scans, results are saved in the `scan-results/` directory:

- `pip-audit-report.json` - pip-audit findings in JSON format
- `safety-report.json` - Safety scan results in JSON format
- `bandit-report.json` - Bandit SAST findings in JSON format
- `trivy-report.json` - Trivy vulnerability scan results in JSON format

### Viewing Results

**Terminal output:**
All scanners display human-readable results in the terminal during execution.

**JSON reports:**
```bash
# View pip-audit results
cat scan-results/pip-audit-report.json | jq

# View Safety results
cat scan-results/safety-report.json | jq

# View Bandit results
cat scan-results/bandit-report.json | jq

# View Trivy results
cat scan-results/trivy-report.json | jq
```

## CI/CD Integration

The project also includes automated CVE scanning via GitHub Actions:

- **Workflow file:** `.github/workflows/cve-scan.yml`
- **Triggers:** Push to main, pull requests, daily schedule (2 AM UTC), manual dispatch
- **Features:**
  - Runs pip-audit, Safety, and Trivy scans
  - Uploads results as artifacts
  - Publishes SARIF results to GitHub Security tab
  - Creates GitHub issues for detected vulnerabilities

### Viewing CI/CD Results

1. Go to the **Actions** tab in your GitHub repository
2. Select the "CVE Security Scan" workflow
3. View the latest run for detailed results
4. Download artifacts for JSON reports
5. Check the **Security** tab for SARIF results

## Understanding Severity Levels

Vulnerabilities are typically classified as:

- **CRITICAL** - Immediate action required, severe security impact
- **HIGH** - Should be addressed urgently, significant security risk
- **MEDIUM** - Should be addressed in near term, moderate security risk
- **LOW** - Can be addressed in regular maintenance, minor security risk

## Remediation Steps

When vulnerabilities are found:

1. **Review the findings** - Check the scan reports for details
2. **Update dependencies** - Use `uv sync --upgrade` to update packages
3. **Check for patches** - Look for security patches in package changelogs
4. **Test thoroughly** - Ensure updates don't break functionality
5. **Re-scan** - Run the CVE scan again to verify fixes
6. **Document** - Record any exceptions or accepted risks

### Updating Dependencies

```bash
# Update all dependencies to latest compatible versions
uv sync --upgrade

# Update a specific package
uv add package-name@latest

# Lock dependencies after updates
uv lock
```

## Best Practices

1. **Run scans regularly** - Before releases and periodically during development
2. **Automate scanning** - Use CI/CD workflows for continuous monitoring
3. **Prioritize fixes** - Address CRITICAL and HIGH severity issues first
4. **Keep dependencies updated** - Regular updates reduce vulnerability exposure
5. **Review scan results** - Don't ignore warnings, investigate all findings
6. **Document exceptions** - If a vulnerability can't be fixed, document why

## Troubleshooting

### Docker build fails

Ensure Docker is running and you have internet connectivity:
```bash
docker info
```

### Scan results directory not created

Create it manually:
```bash
mkdir -p scan-results
```

### Permission issues with scan-results

Fix permissions:
```bash
chmod -R 755 scan-results
```

### False positives

Some scanners may report false positives. Review each finding carefully and:
- Check if the vulnerability applies to your usage
- Verify the affected code path is actually used
- Document accepted risks in your security policy

## Files in This Directory

- **scan-cve.sh** - Convenience script for running CVE scans
- **Dockerfile.cve-scan** - Docker image definition for CVE scanning tools
- **docker-compose.cve-scan.yaml** - Docker Compose configuration for running scans

## Additional Resources

- [pip-audit documentation](https://github.com/pypa/pip-audit)
- [Safety documentation](https://docs.pyup.io/docs/getting-started-with-safety-cli)
- [Bandit documentation](https://bandit.readthedocs.io/)
- [Trivy documentation](https://aquasecurity.github.io/trivy/)
- [NIST National Vulnerability Database](https://nvd.nist.gov/)
- [GitHub Security Advisories](https://github.com/advisories)
- [CVE Scanning Guide](../../docs/CVE-SCANNING.md) - Detailed documentation

## Support

For issues or questions about CVE scanning:
1. Check the scan output for specific error messages
2. Review this documentation
3. Consult the individual tool documentation
4. Open an issue in the project repository