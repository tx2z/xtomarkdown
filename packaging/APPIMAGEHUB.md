# Publishing to AppImageHub

AppImageHub is the central directory for AppImage applications. It helps users discover your app and provides automatic update information.

## Overview

- **Platform**: Linux (all distributions)
- **Cost**: Free
- **Review time**: Usually within 24-48 hours
- **Requirements**: GitHub repository with releases

## What is AppImageHub?

AppImageHub (https://appimage.github.io) is not a download host - it's a catalog that links to your AppImage releases. Users discover your app there, but download directly from your GitHub releases.

## Prerequisites

1. **Working AppImage** - Build and test locally:
   ```bash
   ./packaging/linux/build-appimage.sh
   ./build/appimage/XtoMarkdown-1.0.0-x86_64.AppImage
   ```

2. **GitHub repository** with your source code

3. **GitHub Release** with the AppImage attached

## Submission Process

### Step 1: Create a GitHub Release

1. Tag your release:
   ```bash
   git tag -a v1.0.0 -m "Release 1.0.0"
   git push origin v1.0.0
   ```

2. Go to your GitHub repo → Releases → "Create a new release"

3. Select your tag and upload the AppImage file:
   - `XtoMarkdown-1.0.0-x86_64.AppImage`

4. Add release notes describing changes

### Step 2: Add AppStream Metadata (Recommended)

AppImageHub reads metadata from your AppImage. Ensure your build includes:

1. **Desktop file** at `usr/share/applications/`:
   ```ini
   [Desktop Entry]
   Name=XtoMarkdown
   Comment=Convert documents to Markdown
   Exec=xtomarkdown
   Icon=com.github.tx2z.XtoMarkdown
   Type=Application
   Categories=Office;TextTools;Utility;
   ```

2. **AppStream metadata** at `usr/share/metainfo/`:
   - Already included in build: `com.github.tx2z.XtoMarkdown.metainfo.xml`

3. **Icon** at `usr/share/icons/`:
   - Already included in build

### Step 3: Submit to AppImageHub

1. Go to https://github.com/AppImage/appimage.github.io

2. Fork the repository

3. Add your app entry in the `data/` directory. Create a file named `XtoMarkdown.md`:
   ```markdown
   ---
   layout: app
   name: XtoMarkdown
   description: Convert documents to Markdown with ease
   icons:
     - XtoMarkdown/icons/512x512/com.github.tx2z.XtoMarkdown.png
   screenshots:
     - XtoMarkdown/screenshot.png
   authors:
     - name: tx2z
       url: https://github.com/tx2z
   links:
     - type: GitHub
       url: https://github.com/tx2z/xtomarkdown
     - type: Download
       url: https://github.com/tx2z/xtomarkdown/releases
   desktop:
     Desktop Entry:
       Name: XtoMarkdown
       Comment: Convert documents to Markdown
       Exec: xtomarkdown
       Icon: com.github.tx2z.XtoMarkdown
       Type: Application
       Categories: Office;TextTools;Utility;
   AppImage:
     url: https://github.com/tx2z/xtomarkdown/releases
     signature: null
   ---

   Convert DOCX, PDF, PPTX and more to clean Markdown format.
   ```

4. Submit a Pull Request

### Step 4: Alternative - Automatic Detection

AppImageHub can automatically detect your app if:

1. Your GitHub repo has "appimage" as a topic
2. You publish releases with AppImage files
3. The AppImage contains proper metadata

To add the topic:
1. Go to your GitHub repo
2. Click the gear icon next to "About"
3. Add "appimage" to Topics

## After Acceptance

### Your App Page

Once listed, your app appears at:
`https://appimage.github.io/XtoMarkdown/`

### Releasing Updates

1. Build new AppImage with updated version
2. Create new GitHub Release with the AppImage attached
3. AppImageHub automatically updates the listing

### Update Information (Optional)

To enable automatic updates in your AppImage, embed update information:

```bash
# When building with appimagetool, add:
ARCH=x86_64 appimagetool-x86_64.AppImage \
    --updateinformation "gh-releases-zsync|tx2z|xtomarkdown|latest|XtoMarkdown-*-x86_64.AppImage.zsync" \
    AppDir XtoMarkdown-1.0.0-x86_64.AppImage
```

This allows tools like AppImageUpdate to check for and apply updates.

## Best Practices

### Naming Convention

Use consistent naming for your AppImage files:
- `AppName-version-architecture.AppImage`
- Example: `XtoMarkdown-1.0.0-x86_64.AppImage`

### Signing (Optional but Recommended)

Sign your AppImage for authenticity:
```bash
# Generate a key (once)
gpg --gen-key

# Sign the AppImage
gpg --detach-sign XtoMarkdown-1.0.0-x86_64.AppImage
```

Upload both the `.AppImage` and `.AppImage.sig` files to your release.

### Screenshots

- Add screenshots to your GitHub repo
- Reference them in your AppImageHub entry
- Show the app in action

### Testing

Before releasing, test on multiple distributions:
- Ubuntu/Debian
- Fedora
- Arch Linux
- openSUSE

Use a tool like Docker to test on different systems:
```bash
docker run -it ubuntu:22.04 bash
# Then test your AppImage inside
```

## Troubleshooting

### AppImage Won't Run

- Ensure FUSE is installed: `sudo apt install libfuse2`
- Check execute permissions: `chmod +x *.AppImage`
- Try extracting: `./XtoMarkdown-*.AppImage --appimage-extract`

### Not Appearing on AppImageHub

- Verify the PR was merged
- Check that your AppImage URL is accessible
- Ensure metadata is properly embedded

### Metadata Not Detected

Run `./XtoMarkdown-*.AppImage --appimage-extract` and verify:
- `squashfs-root/usr/share/applications/*.desktop` exists
- `squashfs-root/usr/share/metainfo/*.xml` exists
- Icon files are present

## Resources

- AppImageHub: https://appimage.github.io/
- AppImage documentation: https://docs.appimage.org/
- AppImage packaging guide: https://docs.appimage.org/packaging-guide/
- Submission repo: https://github.com/AppImage/appimage.github.io
