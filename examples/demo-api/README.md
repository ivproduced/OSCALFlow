# Demo Example: Node.js API with Security Features

This is a sample Node.js API that demonstrates various security implementations that `gh-oscal` can detect.

## Files in this Demo

- **package.json** - Contains security-related dependencies
- **Dockerfile** - Shows container isolation
- **.github/workflows/ci.yml** - CI/CD automation
- **src/auth.js** - Authentication implementation
- **src/logger.js** - Audit logging

## Run the Scanner

```bash
gh oscal scan examples/demo-api --output scan-results.json
```

## Expected Detections

The scanner should detect:
- ✓ SC-39: Container isolation (Dockerfile)
- ✓ CM-3: Change control (.github/workflows/)
- ✓ SA-11: Automated testing (.github/workflows/)
- ✓ IA-5: Password hashing (bcrypt in package.json)
- ✓ IA-2: Authentication (jsonwebtoken in package.json)
- ✓ AU-2: Audit logging (winston in package.json)
- ✓ SC-8: HTTPS headers (helmet in package.json)

## Integration with SSP

```bash
# Generate SSP
gh oscal generate --baseline moderate --system "Demo API" -o demo-ssp.json

# Scan and update SSP
gh oscal scan examples/demo-api --update demo-ssp.json

# Verify updates
cat demo-ssp.json | jq '.["system-security-plan"]["control-implementation"]["implemented-requirements"][] | select(.["control-id"] == "SC-39")'
```
