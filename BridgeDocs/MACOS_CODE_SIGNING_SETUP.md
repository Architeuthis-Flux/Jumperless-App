# macOS Code Signing Setup Guide

This guide explains how to set up code signing for the Jumperless macOS app using GitHub secrets.

## Prerequisites

- Apple Developer Program membership
- macOS with Xcode installed
- Developer ID Application certificate in your Keychain

## Step 1: Export Your Certificate

1. Open **Keychain Access** on your Mac
2. Select **login** keychain and **My Certificates** category
3. Find your "Developer ID Application" certificate
4. Right-click and select **Export**
5. Choose **Personal Information Exchange (.p12)** format
6. Save as `Certificates.p12` and set a strong password
7. Remember this password - you'll need it for GitHub secrets

## Step 2: Prepare Certificate for GitHub

```bash
# Convert the .p12 file to base64 for GitHub secrets
base64 -i Certificates.p12 -o Certificates.p12.base64.txt

# The output file contains the base64-encoded certificate
cat Certificates.p12.base64.txt
```

## Step 3: Set Up GitHub Secrets

Go to your GitHub repository → Settings → Secrets and variables → Actions

Add these secrets:

### Required for Code Signing:
- `MACOS_CERTIFICATE`: Contents of `Certificates.p12.base64.txt`
- `MACOS_CERTIFICATE_PASSWORD`: Password you used when exporting the .p12 file
- `APPLE_TEAM_ID`: Your Apple Developer Team ID (found in Apple Developer Console)

### Optional for Notarization (disabled by default):
- `APPLE_ID`: Your Apple ID email
- `APPLE_ID_PASSWORD`: App-specific password (create in Apple ID settings)

**Note**: Notarization is disabled by default via the `DISABLE_MACOS_NOTARIZATION` environment variable. This is sufficient for direct distribution of developer tools.

To enable notarization, set `DISABLE_MACOS_NOTARIZATION: "false"` in the workflow environment variables.

## Step 4: Get Your Team ID

1. Go to [Apple Developer Console](https://developer.apple.com/account/)
2. Sign in with your Apple ID
3. Go to **Membership** tab
4. Copy your **Team ID** (10-character string)

## Step 5: Create App-Specific Password (Optional)

1. Go to [Apple ID Account Page](https://appleid.apple.com/)
2. Sign in and go to **Security** section
3. Under **App-Specific Passwords**, click **Generate Password**
4. Label it "GitHub Actions Notarization"
5. Save the generated password as `APPLE_ID_PASSWORD` secret

## Security Notes

- Never commit certificates or passwords to your repository
- Use strong, unique passwords for certificate export
- App-specific passwords are safer than your main Apple ID password
- Consider rotating secrets periodically

## Testing

After setting up secrets, the GitHub Actions workflow will automatically:
1. Import your certificate into the build environment
2. Sign the app bundle with your Developer ID
3. Optionally notarize the app (disabled by default, enable by setting `DISABLE_MACOS_NOTARIZATION=false`)

With code signing alone, most users will no longer need to use `xattr` commands to run your app!

## Troubleshooting

### "No signing identity found" error
- Verify `MACOS_CERTIFICATE` and `MACOS_CERTIFICATE_PASSWORD` are correct
- Ensure you exported the certificate with its private key

### Notarization fails
- Check `APPLE_ID` and `APPLE_ID_PASSWORD` are correct
- Verify the app is properly signed before notarization
- Check Apple Developer Console for any account issues

### Certificate expires
- Renew your Developer ID certificate in Apple Developer Console
- Export and re-encode the new certificate
- Update the `MACOS_CERTIFICATE` secret 