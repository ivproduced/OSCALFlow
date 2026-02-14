# LibreChat Frontend - Federal Customization

This directory contains the customized LibreChat frontend for federal FISMA Moderate environments.

## Overview

LibreChat is an open-source ChatGPT clone that we've customized with:
- Federal agency branding
- FISMA-compliant security controls
- Disabled external integrations
- Enhanced audit logging
- Custom authentication flows

## Customization

### Agency Branding

Edit the following files to customize for your agency:

1. **[config/librechat.yaml](config/librechat.yaml)** - Main configuration
   - Update `AGENCY_NAME`
   - Set primary/secondary colors
   - Configure logo paths

2. **[config/custom.css](config/custom.css)** - Styling
   - Modify CSS variables
   - Adjust colors, fonts, spacing

3. **assets/** - Replace with your agency assets
   - `agency-logo.png` - Main logo (300x60px recommended)
   - `favicon.ico` - Browser icon
   - `classification-banner.svg` - Classification markings

### Build Arguments

When building the Docker image, pass agency-specific arguments:

```bash
docker build \
  --build-arg AGENCY_NAME="Department of Example" \
  --build-arg AGENCY_PRIMARY_COLOR="#002868" \
  -t fedchat-librechat:latest \
  ./librechat
```

## Features

### Enabled Features
- ✅ Chat conversations
- ✅ File upload (PDF, DOCX, TXT)
- ✅ Conversation history
- ✅ Export conversations
- ✅ User feedback
- ✅ Multi-model selection

### Disabled Features
- ❌ Public registration
- ❌ Social login
- ❌ Plugins
- ❌ Web search
- ❌ Image generation
- ❌ Code interpreter
- ❌ External analytics

## Authentication

### Local Authentication
By default, uses email/password authentication with:
- Password requirements: 12+ characters, mixed case, numbers, symbols
- Session timeout: 8 hours
- Failed login lockout: 5 attempts

### SAML/SSO Integration

To enable SAML authentication:

1. Update `.env`:
```bash
ENABLE_SAML=true
SAML_IDP_ENTITY_ID=https://idp.agency.gov/saml
SAML_IDP_SSO_URL=https://idp.agency.gov/sso
```

2. Add certificates:
```bash
cp idp-cert.pem ./librechat/config/idp-cert.pem
cp sp-cert.pem ./librechat/config/sp-cert.pem
cp sp-key.pem ./librechat/config/sp-key.pem
```

3. Configure your IdP:
   - Entity ID: `https://fedchat.agency.gov`
   - ACS URL: `https://fedchat.agency.gov/api/auth/saml/callback`
   - Attributes: email, firstName, lastName, groups

## Security Features

### Classification Banners
Display system classification level at top and bottom of every page.

Edit in `config/custom.css`:
```css
.classification-banner {
  background-color: #5b8c5a; /* Change for different levels */
}
```

Standard colors:
- Unclassified: Green (#5b8c5a)
- CUI: Purple (#502b85)
- Secret: Red (#bf0a30)
- TS/SCI: Orange (#ff8c00)

### Terms of Service
Users must accept TOS on first login. Update:
- `config/librechat.yaml` - Set TOS URL
- Update `TOS_VERSION` in `.env` to force re-acceptance

### Audit Logging
All user actions logged to `/var/log/fedchat/librechat-audit.log`:
- Login/logout events
- Message sent/received
- File uploads
- Settings changes
- Error events

Format: JSON with timestamp, user ID, action, details

## Development

### Local Development

1. Install dependencies:
```bash
cd librechat
npm install
```

2. Start development server:
```bash
npm run dev
```

3. Access at `http://localhost:3000`

### Hot Reload
Development mode supports hot reload. Changes to:
- React components
- CSS files
- Configuration (requires restart)

## Configuration Reference

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `NODE_ENV` | Environment mode | `production` |
| `API_URL` | Backend API URL | `http://backend:8000` |
| `DATABASE_URL` | PostgreSQL connection | Required |
| `JWT_SECRET` | JWT signing key | Required |
| `SESSION_SECRET` | Session encryption | Required |
| `LIBRECHAT_TITLE` | Application title | `Federal AI Assistant` |
| `ALLOW_REGISTRATION` | Enable public signup | `false` |
| `ENABLE_SAML` | Enable SAML auth | `false` |

### librechat.yaml Structure

```yaml
version: 1.0.9
cache: true
interface: {...}
registration: {...}
endpoints: {...}
fileConfig: {...}
modelSpecs: {...}
rateLimits: {...}
securityHeaders: {...}
auditLog: {...}
customization: {...}
features: {...}
```

See [config/librechat.yaml](config/librechat.yaml) for full configuration.

## Troubleshooting

### Common Issues

**Login fails after restart**
- Check `JWT_SECRET` hasn't changed
- Verify database connection
- Check audit logs

**Styles not applying**
- Clear browser cache
- Rebuild Docker image
- Verify `custom.css` is mounted

**File upload fails**
- Check file size limit (50MB default)
- Verify MIME type is allowed
- Check backend connectivity

**SAML authentication error**
- Verify certificate validity
- Check IdP configuration
- Review SAML request/response in browser dev tools

### Debug Mode

Enable debug logging:
```bash
NODE_ENV=development
DEBUG=librechat:*
```

View logs:
```bash
docker-compose logs -f librechat
```

## Accessibility

LibreChat frontend meets WCAG 2.1 AA standards:
- Keyboard navigation
- Screen reader support
- High contrast mode
- Reduced motion support
- ARIA labels

Test with:
- NVDA (Windows)
- JAWS (Windows)
- VoiceOver (macOS)
- axe DevTools (Browser extension)

## Mobile Support

Responsive design supports:
- iOS Safari (12+)
- Android Chrome (80+)
- Tablet devices

Mobile-specific features:
- Touch-optimized UI
- Swipe gestures
- Adaptive layouts

## Deployment

### Production Checklist

- [ ] Set strong `JWT_SECRET` and `SESSION_SECRET`
- [ ] Disable registration (`ALLOW_REGISTRATION=false`)
- [ ] Enable HTTPS/TLS
- [ ] Configure SAML/SSO
- [ ] Set correct `AGENCY_NAME` and branding
- [ ] Add classification banners
- [ ] Configure rate limits
- [ ] Enable audit logging
- [ ] Test file upload limits
- [ ] Verify security headers
- [ ] Set data retention policies
- [ ] Configure backups

### Update Process

1. Pull new LibreChat version
2. Test in development
3. Review changelog for breaking changes
4. Update customizations
5. Rebuild Docker image
6. Deploy to staging
7. Run security scan
8. Deploy to production
9. Monitor logs

## Support

For LibreChat-specific issues:
- Documentation: https://docs.librechat.ai
- GitHub: https://github.com/danny-avila/LibreChat

For federal customization support:
- Contact your security team
- Review FISMA compliance documentation
