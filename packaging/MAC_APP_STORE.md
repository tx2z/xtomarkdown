# Publishing to the Mac App Store

The Mac App Store is Apple's official distribution platform for macOS applications. Publishing here provides visibility to millions of Mac users and handles licensing, payments, and updates automatically.

## Overview

- **Platform**: macOS
- **Cost**: $99/year (Apple Developer Program)
- **Review time**: 1-3 days (can be longer for first submission)
- **Revenue share**: Apple takes 30% (15% for small businesses under $1M/year)

## Prerequisites

### 1. Apple Developer Account

1. Go to https://developer.apple.com/programs/
2. Click "Enroll" and sign in with your Apple ID
3. Pay the $99/year fee
4. Wait for enrollment approval (usually 24-48 hours)

### 2. Required Certificates

Generate these in the Apple Developer portal (Certificates, Identifiers & Profiles):

1. **3rd Party Mac Developer Application** - Signs your app
2. **3rd Party Mac Developer Installer** - Signs the .pkg for upload

To create certificates:
1. Open Keychain Access on your Mac
2. Keychain Access → Certificate Assistant → Request a Certificate from a Certificate Authority
3. Save to disk (no email needed)
4. Upload to Apple Developer portal
5. Download and install the generated certificates

### 3. App ID Registration

1. Go to Certificates, Identifiers & Profiles → Identifiers
2. Click "+" to register a new App ID
3. Select "App IDs" and continue
4. Choose "App" type
5. Enter:
   - Description: `XtoMarkdown`
   - Bundle ID (Explicit): `com.xtomarkdown.XtoMarkdown`
6. Enable any required capabilities (none needed for basic app)
7. Register

### 4. Development Environment

- macOS computer (required for building and signing)
- Xcode installed: `xcode-select --install`
- Python 3.10+ installed
- PyInstaller: `pip install pyinstaller`

## Building for the App Store

### Step 1: Set Environment Variables

```bash
# Find your certificate names in Keychain Access
export APP_SIGN_ID="3rd Party Mac Developer Application: Your Name (TEAM_ID)"
export INSTALLER_ID="3rd Party Mac Developer Installer: Your Name (TEAM_ID)"
export TEAM_ID="XXXXXXXXXX"  # Your 10-character Team ID
```

### Step 2: Build the App

```bash
cd /path/to/xtomarkdown
./packaging/macos/build-macos.sh
```

This creates:
- `build/macos/dist/XtoMarkdown.app` - Signed application bundle
- `build/macos/XtoMarkdown-1.0.0.pkg` - Installer package for App Store

### Step 3: Verify the Build

```bash
# Check code signature
codesign --verify --deep --strict build/macos/dist/XtoMarkdown.app

# Check App Sandbox
codesign -d --entitlements :- build/macos/dist/XtoMarkdown.app

# Test the app
open build/macos/dist/XtoMarkdown.app
```

## App Store Connect Setup

### Step 1: Create Your App

1. Go to https://appstoreconnect.apple.com
2. Click "My Apps" → "+" → "New App"
3. Fill in:
   - **Platform**: macOS
   - **Name**: XtoMarkdown
   - **Primary Language**: English (or your choice)
   - **Bundle ID**: Select `com.xtomarkdown.XtoMarkdown`
   - **SKU**: `xtomarkdown-001` (unique identifier, not shown to users)
   - **User Access**: Full Access

### Step 2: App Information

Fill in the required metadata:

#### General Information
- **Category**: Utilities or Productivity
- **Content Rights**: Confirm you have rights to all content

#### Pricing
- Set your price tier (e.g., Tier 1 = $0.99/€0.99)
- Or choose "Free"
- Select availability by country

#### App Privacy
- **Privacy Policy URL**: Link to your privacy policy
- **Data Collection**: Declare what data your app collects (if any)

### Step 3: Prepare Store Listing

#### Screenshots (Required)
- At least one screenshot required
- Recommended sizes:
  - 1280 x 800 pixels
  - 1440 x 900 pixels
  - 2560 x 1600 pixels
  - 2880 x 1800 pixels
- Show the app's main features
- No device frames needed for Mac

#### App Preview Videos (Optional)
- Up to 30 seconds
- Show app functionality
- No device frames

#### Description
See `MARKETING_DESCRIPTIONS.md` for copy.

#### Keywords
- Maximum 100 characters total
- Comma-separated
- Example: `markdown,converter,docx,pdf,document,export,writer`

#### Support URL
- Link to your support page or GitHub issues

#### Marketing URL (Optional)
- Link to your product website

## Uploading Your App

### Option 1: Transporter (Recommended)

1. Download "Transporter" from the Mac App Store
2. Open Transporter and sign in with your Apple ID
3. Drag your `.pkg` file into the window
4. Click "Deliver"
5. Wait for upload and processing

### Option 2: Command Line

```bash
# Store your App Store Connect API key or app-specific password
xcrun altool --upload-app \
    -f build/macos/XtoMarkdown-1.0.0.pkg \
    -t macos \
    -u your@apple.id \
    -p @keychain:AC_PASSWORD
```

To set up the password:
1. Go to https://appleid.apple.com
2. Security → App-Specific Passwords → Generate
3. Store in Keychain:
   ```bash
   xcrun altool --store-password-in-keychain-item AC_PASSWORD \
       -u your@apple.id -p "your-app-specific-password"
   ```

### Option 3: Xcode

1. Open Xcode
2. Window → Organizer
3. Drag your `.pkg` file
4. Click "Distribute App"

## After Upload

### Processing Time

- Apple processes your upload (5-30 minutes)
- You'll receive an email when processing completes
- Check App Store Connect for any issues

### Select Build for Review

1. In App Store Connect, go to your app
2. Under "Build", click "Select a build"
3. Choose your uploaded build
4. Save changes

### Submit for Review

1. Fill in all required fields
2. Answer the review questions:
   - Sign-in required? (No)
   - Uses encryption? (If using HTTPS, select "Yes" but standard exemption applies)
   - Uses advertising identifier? (No)
3. Click "Submit for Review"

## App Review Guidelines

Apple reviews all apps for:

### Technical Requirements
- Must work on stated macOS versions
- No crashes or major bugs
- Proper App Sandbox implementation
- Valid code signature

### Content Guidelines
- Accurate description and screenshots
- No misleading claims
- Appropriate age rating
- Privacy policy if collecting data

### Common Rejection Reasons
1. **Crashes or bugs** - Test thoroughly
2. **Incomplete metadata** - Fill all required fields
3. **Misleading description** - Be accurate
4. **Missing functionality** - App must do what it claims
5. **Sandbox violations** - Only access permitted resources

## Handling Rejection

If rejected:
1. Read the rejection reason carefully
2. Fix the issues
3. Reply in Resolution Center if you need clarification
4. Upload a new build
5. Resubmit for review

## After Approval

### Release Options
- **Manual release** - You control when it goes live
- **Automatic release** - Goes live immediately after approval
- **Scheduled release** - Set a specific date

### Updates

1. Increment version in `Info.plist`:
   - `CFBundleShortVersionString`: User-visible version (1.1.0)
   - `CFBundleVersion`: Build number (increment each upload)
2. Build new `.pkg`
3. Upload via Transporter
4. Submit for review with release notes

### Monitoring

- Check App Store Connect for:
  - Sales and downloads
  - Crash reports
  - User reviews
- Respond to reviews professionally

## App Sandbox Considerations

Mac App Store apps must use App Sandbox. Your app can:

- Read/write files the user selects (Open/Save dialogs)
- Access files dropped via drag-and-drop
- Store settings in `~/Library/Containers/com.xtomarkdown.XtoMarkdown/`

Your app cannot:
- Access arbitrary files
- Access other apps' data
- Run background processes (without entitlement)

## Resources

- App Store Connect: https://appstoreconnect.apple.com
- App Store Review Guidelines: https://developer.apple.com/app-store/review/guidelines/
- Human Interface Guidelines: https://developer.apple.com/design/human-interface-guidelines/macos
- App Sandbox documentation: https://developer.apple.com/documentation/security/app_sandbox
- Transporter app: Available on Mac App Store
