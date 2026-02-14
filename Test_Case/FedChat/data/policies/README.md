# Organizational Policies

This directory contains security and compliance policy documents for policy RAG integration.

## Policy Information

- **Demo Source**: https://github.com/0xdefendA/policies
- **License**: Mozilla Public License 2.0 (MPL-2.0)
- **Size**: ~100MB
- **Format**: Markdown (.md)

## Directory Structure

```
data/policies/
├── README.md (this file)
├── Information Security Policy.md
├── Incident Response Program.md
├── Vulnerability Management Program.md
├── data_classification_levels.png
├── mitigation_timeframes.png
└── nist.png
```

## Setup: Clone Demo Policies

```bash
# From the fedchat-system root directory
cd data/policies

# Clone the policies repository
git clone https://github.com/0xdefendA/policies.git temp_policies

# Copy policy files to this directory
cp temp_policies/*.md .
cp temp_policies/*.png . 2>/dev/null || true

# Clean up
rm -rf temp_policies

# Verify files
ls -lh
```

## Adding Your Organization's Policies

Replace the demo policies with your organization's actual policies:

```bash
cd data/policies

# Remove demo policies
rm *.md

# Copy your organization's policy documents
cp /path/to/your/policies/*.md .

# Supported formats:
# - Markdown (.md) - Preferred
# - Plain text (.txt) - Supported
# - PDF (.pdf) - Requires additional processing
```

## Policy Document Format

For best results, structure your policies as Markdown:

```markdown
# Policy Title

## Section 1: Purpose
Policy purpose content...

## Section 2: Scope
Policy scope content...

### Subsection 2.1
Detailed requirements...
```

### Best Practices

- **Use clear headings**: `##` for main sections, `###` for subsections
- **One policy per file**: E.g., `Information-Security-Policy.md`
- **Descriptive filenames**: Policy name should be clear from filename
- **Include metadata**: Date, version, approval authority at top
- **Consistent formatting**: Makes chunking and search more effective

## Policy Categories

The system automatically categorizes policies:

- **incident_response** - Incident handling and reporting
- **vulnerability_management** - Vulnerability scanning and patching
- **information_security** - General security requirements
- **data_security** - Data classification and handling
- **access_control** - Authentication and authorization
- **business_continuity** - BCP/DR procedures
- **acceptable_use** - Acceptable use policies (AUP)
- **general** - Other policies

Categorization is based on filename and content keywords.

## Configuration

Update your `.env` file to use local policies:

```bash
# Disable GitHub cloning, use local files
POLICY_USE_GITHUB=false
POLICY_LOCAL_PATH=/app/data/policies

# Cache directory for FAISS index
POLICY_RAG_CACHE_DIR=/app/data/policy-cache
```

## Docker Volume Mapping

The `docker-compose.yml` should include:

```yaml
services:
  backend:
    volumes:
      - ./data/policies:/app/data/policies:ro  # Read-only for policies
```

## Example Policies Included (Demo)

From 0xdefendA/policies repo:

1. **Information Security Policy.md**
   - Acceptable Use
   - Credential Management
   - Access Control
   - Data Retention
   - Vulnerability Remediation
   - Procurement
   - VPN/Remote Access
   - Change Management
   - Business Continuity

2. **Incident Response Program.md**
   - Preparation
   - Identification
   - Containment
   - Eradication
   - Recovery
   - Lessons Learned

3. **Vulnerability Management Program.md**
   - Risk Ratings
   - Mitigation Timelines
   - Data Classification
   - Data Threat Model (STRIDE)

## Policy Search Examples

Once policies are loaded, users can query:

- "What are our password requirements?"
- "What is the incident escalation procedure?"
- "What are the vulnerability remediation timeframes?"
- "What is our data classification system?"
- "What are acceptable use restrictions?"

## Updating Policies

To update policies after initial deployment:

```bash
# Method 1: Replace files directly
cd data/policies
cp /path/to/updated/policy.md .

# Method 2: Re-clone from GitHub
rm *.md
git clone <your-organization-policy-repo-url> temp
cp temp/*.md .
rm -rf temp

# Trigger re-indexing
curl -X POST http://localhost:8000/api/v1/policy/initialize \
  -H "Authorization: Bearer YOUR_API_KEY"
```

## Benefits of Local Policies

- ✅ **Air-gapped deployments** - No internet required
- ✅ **Faster startup** - No Git clone on first run
- ✅ **Version control** - Commit policies with application
- ✅ **Audit compliance** - Track policy changes in Git
- ✅ **Offline access** - Always available
- ✅ **Custom policies** - Easy to add organization-specific documents

## .gitignore Considerations

If policies contain sensitive information:

```bash
# Add to .gitignore
echo "data/policies/*.md" >> .gitignore
echo "!data/policies/README.md" >> .gitignore
```

Or use Git submodule for policy repository:

```bash
cd data
git submodule add <your-organization-policy-repo-url> policies
```

## Notes

- Demo policies are under MPL-2.0 license (open source)
- Replace demo policies with your organization's actual policies
- Keep policies in sync with official policy repository
- Re-index after updating policies for changes to take effect
- Consider access controls for sensitive policy documents
