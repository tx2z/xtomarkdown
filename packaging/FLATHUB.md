# Publishing to Flathub

Flathub is the main repository for Flatpak applications on Linux. Publishing here makes your app available to millions of Linux users across all distributions.

## Overview

- **Platform**: Linux (all distributions)
- **Cost**: Free
- **Review time**: 1-2 weeks for initial submission
- **Requirements**: GitHub account, Flatpak manifest

## Prerequisites

1. **Working Flatpak build** - Test locally first:
   ```bash
   ./packaging/linux/build-flatpak.sh
   flatpak install build/flatpak/com.github.tx2z.XtoMarkdown-1.0.0.flatpak
   ```

2. **GitHub account** - Flathub uses GitHub for submissions

3. **Familiarity with Git** - You'll submit via pull request

## Submission Process

### Step 1: Fork the Flathub Repository

1. Go to https://github.com/flathub/flathub
2. Click "Fork" to create your own copy

### Step 2: Create Your App Repository

1. In your fork, create a new branch:
   ```bash
   git clone https://github.com/YOUR_USERNAME/flathub.git
   cd flathub
   git checkout -b new-pr
   ```

2. Create a file named `com.github.tx2z.XtoMarkdown.json` or copy your YAML manifest

### Step 3: Prepare the Manifest

Your manifest needs some adjustments for Flathub:

1. **Use stable sources** - Point to release tags, not branches:
   ```yaml
   sources:
     - type: archive
       url: https://github.com/tx2z/xtomarkdown/archive/refs/tags/v1.0.0.tar.gz
       sha256: YOUR_SHA256_HERE
   ```

2. **Generate SHA256**:
   ```bash
   curl -sL https://github.com/tx2z/xtomarkdown/archive/refs/tags/v1.0.0.tar.gz | sha256sum
   ```

3. **Remove network access** - Flathub builds must be offline. Use `flatpak-pip-generator` to pre-download Python packages:
   ```bash
   pip install flatpak-pip-generator
   flatpak-pip-generator PySide6==6.7.0 platformdirs pypandoc "markitdown[all]" hatchling Pillow
   ```
   This generates a JSON file with all package sources.

### Step 4: Required Metadata Files

Ensure these files exist in your project:

1. **AppStream metadata** (`com.github.tx2z.XtoMarkdown.metainfo.xml`):
   - App description
   - Screenshots (hosted URLs)
   - Release notes
   - Categories

2. **Desktop file** (`com.github.tx2z.XtoMarkdown.desktop`):
   - App name and icon
   - Categories
   - Executable command

### Step 5: Submit Pull Request

1. Commit your manifest:
   ```bash
   git add com.github.tx2z.XtoMarkdown.json
   git commit -m "Add com.github.tx2z.XtoMarkdown"
   git push origin new-pr
   ```

2. Go to https://github.com/flathub/flathub and create a Pull Request

3. Fill in the PR template with:
   - App description
   - Link to source code
   - Confirmation you have rights to publish

### Step 6: Review Process

1. **Automated checks** - Flathub bot will test your manifest
2. **Manual review** - Maintainers check for:
   - Proper metadata
   - No bundled libraries that should use runtime
   - Security concerns
   - Quality standards

3. **Address feedback** - Reviewers may request changes

4. **Approval** - Once approved, your app gets its own repo at `https://github.com/flathub/com.github.tx2z.XtoMarkdown`

## After Acceptance

### Your App Repository

Once accepted, Flathub creates a dedicated repository for your app. You'll have push access to update it.

### Releasing Updates

1. Clone your app's Flathub repo:
   ```bash
   git clone git@github.com:flathub/com.github.tx2z.XtoMarkdown.git
   ```

2. Update the manifest with new version:
   - Change source URL to new release tag
   - Update SHA256
   - Update version in metainfo.xml

3. Push changes:
   ```bash
   git commit -am "Update to version X.Y.Z"
   git push
   ```

4. Flathub automatically builds and publishes (usually within hours)

## Best Practices

### Screenshots

- Host on a reliable CDN or your GitHub repo
- Use PNG format, 16:9 aspect ratio recommended
- Show actual app functionality
- Include both light and dark mode if supported

### Release Notes

Add to `metainfo.xml` for each release:
```xml
<releases>
  <release version="1.0.0" date="2024-01-15">
    <description>
      <p>Initial release with support for:</p>
      <ul>
        <li>DOCX, PDF, PPTX conversion</li>
        <li>Multiple conversion engines</li>
        <li>Drag and drop interface</li>
      </ul>
    </description>
  </release>
</releases>
```

### Verification

To verify your app ID ownership:
- For `com.github.tx2z.*` - You must own the `tx2z` GitHub account
- For custom domains - Add a `.well-known/org.flathub.VerifiedApps.txt` file to your website

## Troubleshooting

### Build Fails on Flathub

- Check the build logs in the PR
- Ensure all sources are available and checksums match
- Verify offline build works (no network in build phase)

### App Not Appearing

- After merge, wait 1-2 hours for initial publication
- Check https://flathub.org/apps/com.github.tx2z.XtoMarkdown

## Resources

- Flathub documentation: https://docs.flathub.org/
- App submission guidelines: https://docs.flathub.org/docs/for-app-authors/submission
- Flatpak manifest format: https://docs.flatpak.org/en/latest/manifests.html
- AppStream metadata: https://www.freedesktop.org/software/appstream/docs/
