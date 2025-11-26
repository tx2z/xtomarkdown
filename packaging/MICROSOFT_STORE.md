# Publishing to the Microsoft Store

The Microsoft Store is Windows' official app marketplace. Publishing here provides easy discovery, automatic updates, and trusted distribution to Windows users worldwide.

## Overview

- **Platform**: Windows 10/11
- **Cost**: One-time $19 registration fee (individuals) or $99 (companies)
- **Review time**: 1-5 business days
- **Revenue share**: Microsoft takes 15% (reduced from previous 30%)

## Prerequisites

### 1. Microsoft Partner Center Account

1. Go to https://partner.microsoft.com/dashboard
2. Click "Sign up" or sign in with your Microsoft account
3. Choose account type:
   - **Individual** - $19 one-time fee
   - **Company** - $99 one-time fee (requires business verification)
4. Complete identity verification
5. Pay registration fee
6. Wait for approval (usually 1-2 days)

### 2. Get Your Publisher ID

After registration:
1. Go to Partner Center → Account Settings → Organization profile
2. Find your **Publisher ID** (format: `CN=XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX`)
3. Save this - you'll need it for the app manifest

### 3. Development Environment

- Windows 10/11 computer
- Python 3.10+ installed and in PATH
- Windows 10 SDK installed:
  - Via Visual Studio Installer → Individual Components → "Windows 10 SDK"
  - Or download from https://developer.microsoft.com/windows/downloads/windows-sdk/
- PyInstaller: `pip install pyinstaller`

### 4. Code Signing Certificate (Optional but Recommended)

For testing locally before Store submission:
- Purchase from a Certificate Authority (DigiCert, Sectigo, etc.)
- Or use a self-signed certificate for development

## Building for the Microsoft Store

### Step 1: Configure Your Publisher ID

Edit `packaging/windows/AppxManifest.xml`:
```xml
<Identity Name="XtoMarkdown"
          Publisher="CN=YOUR-PUBLISHER-ID-HERE"
          Version="1.0.0.0" />
```

Or set it as an environment variable before building:
```powershell
$env:PUBLISHER_ID = "CN=XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX"
```

### Step 2: Build the MSIX Package

```powershell
cd C:\path\to\xtomarkdown
.\packaging\windows\build-msix.bat
```

Or with PowerShell directly:
```powershell
.\packaging\windows\build-msix.ps1
```

Output: `build\windows\XtoMarkdown-1.0.0.0.msix`

### Step 3: Test Locally

Enable Developer Mode to install unsigned packages:
1. Settings → Update & Security → For developers
2. Enable "Developer mode"

Install and test:
```powershell
Add-AppPackage -Path "build\windows\XtoMarkdown-1.0.0.0.msix"
```

Launch from Start Menu to verify it works.

## Partner Center Setup

### Step 1: Create Your App

1. Go to https://partner.microsoft.com/dashboard
2. Navigate to Apps and Games
3. Click "New product" → "App"
4. Reserve your app name: "XtoMarkdown"
   - Name must be unique in the Store
   - You can reserve multiple names
5. Click "Reserve product name"

### Step 2: App Identity

After reserving, note these values (under Product Identity):
- **Package/Identity/Name**
- **Package/Identity/Publisher**
- **Package/Properties/PublisherDisplayName**

Update your `AppxManifest.xml` to match exactly.

### Step 3: Prepare Submission

#### Properties
- **Category**: Utilities & tools
- **Privacy policy URL**: Link to your privacy policy
- **Website**: Your product website
- **Support contact**: Email or support URL

#### Age Ratings
- Complete the IARC questionnaire
- XtoMarkdown should qualify for "Everyone" rating

#### Pricing and Availability
- **Base price**: Set your price or choose "Free"
- **Markets**: Select countries for distribution
- **Sale pricing**: Optional promotional pricing
- **Visibility**: Public or Private (for testing)

### Step 4: Store Listing

Create a compelling Store presence:

#### Product Description
See `MARKETING_DESCRIPTIONS.md` for copy.

#### Screenshots (Required)
- Minimum: 1 screenshot
- Recommended: 4-8 screenshots
- Sizes:
  - Desktop: 1366 x 768 (minimum)
  - Recommended: 1920 x 1080 or higher
- Show key features and UI
- PNG or JPG format

#### App Features (Recommended)
List up to 20 features:
- Convert DOCX to Markdown
- Convert PDF to Markdown
- Drag and drop support
- Multiple conversion engines
- Batch conversion
- Clean, simple interface

#### Search Terms
- Up to 7 terms, 30 characters each
- Examples: `markdown`, `converter`, `docx`, `document`, `export`

#### Logos
- **1:1 logo**: 300 x 300 px (required)
- **2:1 wide logo**: 672 x 336 px (optional)
- Use your app icon

## Uploading Your Package

### Step 1: Go to Packages Section

1. In Partner Center, open your app submission
2. Navigate to "Packages"
3. Click "Browse your files"
4. Select your `.msix` file

### Step 2: Upload and Validate

- Partner Center validates your package
- Fix any errors before proceeding
- Common issues:
  - Publisher ID mismatch
  - Missing required assets
  - Invalid manifest

### Step 3: Device Family Availability

Select supported platforms:
- ☑ Windows 10/11 Desktop
- ☐ Xbox (if applicable)
- ☐ HoloLens (if applicable)

## Certification Requirements

Microsoft reviews apps for:

### Technical Requirements
- Must install and launch without errors
- Must work on declared Windows versions
- Cannot interfere with system stability
- Must handle common scenarios gracefully

### Content Requirements
- Accurate description and screenshots
- No misleading claims
- Appropriate content rating
- Privacy policy if collecting data

### Security Requirements
- No malware or unwanted software
- Clear permissions requests
- Secure data handling
- No deceptive practices

### Common Rejection Reasons

1. **Package validation errors** - Fix manifest issues
2. **Crashes on launch** - Test on clean Windows install
3. **Missing functionality** - App must work as described
4. **Inaccurate metadata** - Screenshots must match actual app
5. **Privacy policy missing** - Required if app accesses internet

## Submitting for Review

### Pre-submission Checklist

- [ ] Package uploads without errors
- [ ] All Store listing fields completed
- [ ] Screenshots uploaded
- [ ] Age rating questionnaire completed
- [ ] Pricing set
- [ ] Privacy policy URL added (if needed)

### Submit

1. Review all sections show green checkmarks
2. Click "Submit to the Store"
3. Add notes for certification (optional):
   - Test accounts if needed
   - Special testing instructions
4. Confirm submission

### After Submission

- Status changes to "In certification"
- Review typically takes 1-5 business days
- You'll receive email updates
- Monitor status in Partner Center

## Handling Rejection

If your app fails certification:

1. **Read the report** - Partner Center shows specific failures
2. **Fix issues** - Address each point
3. **Update package** - Build new MSIX with fixes
4. **Resubmit** - Upload new package and submit again

### Appeal Process

If you believe rejection was incorrect:
1. Go to submission report
2. Click "Contact support"
3. Explain why you disagree
4. Provide evidence if applicable

## After Approval

### Release Options

- **Immediately** - Publish as soon as certified
- **Manual** - You control release timing
- **Scheduled** - Set specific date/time

### Your App in the Store

Once published, your app appears at:
`https://apps.microsoft.com/store/detail/xtomarkdown/YOUR_PRODUCT_ID`

Share this link for promotion!

### Monitoring

Partner Center provides:
- **Acquisitions report** - Downloads and installs
- **Health report** - Crashes and errors
- **Reviews** - User feedback
- **Usage** - Active users and sessions

### Responding to Reviews

1. Go to Reviews section
2. Click "Respond" on a review
3. Write helpful, professional response
4. Response is public

## Publishing Updates

### Version Updates

1. Increment version in `AppxManifest.xml`:
   ```xml
   Version="1.1.0.0"
   ```
   Note: Version must always increase (e.g., 1.0.0.0 → 1.0.1.0 → 1.1.0.0)

2. Build new MSIX package

3. In Partner Center:
   - Create new submission
   - Upload new package
   - Update "What's new" section
   - Submit for certification

### Store Listing Updates

- Can update description, screenshots, etc. without new package
- Create new submission
- Make changes
- Submit for certification

## MSIX vs Traditional EXE

### MSIX Advantages (Store)
- Automatic updates
- Clean install/uninstall
- Sandboxed (more secure)
- Easy discovery in Store
- Trust from Microsoft

### EXE Advantages (Direct Distribution)
- No Store fees
- Faster releases (no review)
- More system access
- Works on older Windows

Consider offering both:
- MSIX on Microsoft Store
- EXE download on your website

## Resources

- Partner Center: https://partner.microsoft.com/dashboard
- MSIX documentation: https://docs.microsoft.com/windows/msix/
- Store policies: https://docs.microsoft.com/windows/uwp/publish/store-policies
- App certification: https://docs.microsoft.com/windows/uwp/publish/the-app-certification-process
- Windows SDK: https://developer.microsoft.com/windows/downloads/windows-sdk/
