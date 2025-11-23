# Packaging & Distribution Guide
## Streamrip Desktop Application

**Version:** 1.0
**Date:** 2025-11-23
**Platforms:** Windows, macOS, Linux

---

## Table of Contents

1. [Overview](#1-overview)
2. [PyInstaller Configuration](#2-pyinstaller-configuration)
3. [Windows Packaging](#3-windows-packaging)
4. [macOS Packaging](#4-macos-packaging)
5. [Linux Packaging](#5-linux-packaging)
6. [Automated Build Pipeline](#6-automated-build-pipeline)
7. [Code Signing](#7-code-signing)
8. [Update Mechanism](#8-update-mechanism)

---

## 1. Overview

### 1.1 Packaging Tools

| Platform | Tool | Output Format | Size Estimate |
|----------|------|---------------|---------------|
| Windows | PyInstaller + NSIS | `.exe` installer | 80-120 MB |
| macOS | PyInstaller + create-dmg | `.dmg` disk image | 70-100 MB |
| Linux | PyInstaller / AppImage | `.AppImage`, `.deb`, `.rpm` | 60-90 MB |

### 1.2 Bundle Contents

**All platforms include:**
- Python interpreter (embedded)
- PyQt6 libraries
- Streamrip core + dependencies
- FFmpeg binary (platform-specific)
- Application resources (icons, styles)
- Default configuration template

---

## 2. PyInstaller Configuration

### 2.1 Base Spec File

**`packaging/streamrip-desktop.spec`**

```python
# -*- mode: python ; coding: utf-8 -*-
import sys
import os
from pathlib import Path

# Determine platform
IS_WIN = sys.platform.startswith('win')
IS_MAC = sys.platform == 'darwin'
IS_LINUX = sys.platform.startswith('linux')

# Project paths
REPO_ROOT = Path('.').absolute()
SRC_DIR = REPO_ROOT / 'src'
RESOURCES_DIR = SRC_DIR / 'resources'
STREAMRIP_DIR = SRC_DIR / 'streamrip'

# FFmpeg binary path (must be downloaded separately)
if IS_WIN:
    FFMPEG_PATH = REPO_ROOT / 'bin' / 'windows' / 'ffmpeg.exe'
elif IS_MAC:
    FFMPEG_PATH = REPO_ROOT / 'bin' / 'macos' / 'ffmpeg'
else:
    FFMPEG_PATH = REPO_ROOT / 'bin' / 'linux' / 'ffmpeg'

block_cipher = None

# Analysis: Find all dependencies
a = Analysis(
    [str(SRC_DIR / 'main.py')],
    pathex=[str(SRC_DIR)],
    binaries=[
        (str(FFMPEG_PATH), 'bin'),  # Bundle FFmpeg
    ],
    datas=[
        # Resources
        (str(RESOURCES_DIR / 'icons'), 'resources/icons'),
        (str(RESOURCES_DIR / 'styles'), 'resources/styles'),

        # Streamrip config template
        (str(STREAMRIP_DIR / 'config.toml'), 'streamrip'),

        # Include any other necessary data files
    ],
    hiddenimports=[
        # PyQt6 modules
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.QtWidgets',
        'PyQt6.QtWebEngineWidgets',

        # Streamrip modules (if not auto-detected)
        'streamrip.client.qobuz',
        'streamrip.client.tidal',
        'streamrip.client.deezer',
        'streamrip.client.soundcloud',
        'streamrip.media',
        'streamrip.metadata',

        # Other dependencies
        'aiohttp',
        'aiofiles',
        'mutagen',
        'Pillow',
        'pycryptodomex',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Exclude unnecessary modules to reduce size
        'matplotlib',
        'scipy',
        'numpy',
        'pandas',
        'tkinter',
        'test',
        'unittest',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# Remove duplicate binaries
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# Platform-specific executable configuration
if IS_WIN:
    exe = EXE(
        pyz,
        a.scripts,
        [],
        exclude_binaries=True,
        name='StreamripDesktop',
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=True,
        console=False,  # No console window
        disable_windowed_traceback=False,
        argv_emulation=False,
        target_arch=None,
        codesign_identity=None,
        entitlements_file=None,
        icon=str(RESOURCES_DIR / 'icons' / 'app_icon.ico'),
    )
elif IS_MAC:
    exe = EXE(
        pyz,
        a.scripts,
        [],
        exclude_binaries=True,
        name='StreamripDesktop',
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=True,
        console=False,
        disable_windowed_traceback=False,
        argv_emulation=False,
        target_arch='universal2',  # Universal binary (Intel + Apple Silicon)
        codesign_identity=None,
        entitlements_file=str(REPO_ROOT / 'packaging' / 'macos' / 'entitlements.plist'),
        icon=str(RESOURCES_DIR / 'icons' / 'app_icon.icns'),
    )
else:  # Linux
    exe = EXE(
        pyz,
        a.scripts,
        [],
        exclude_binaries=True,
        name='streamrip-desktop',
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=True,
        console=False,
        disable_windowed_traceback=False,
        argv_emulation=False,
        target_arch=None,
        codesign_identity=None,
        entitlements_file=None,
        icon=str(RESOURCES_DIR / 'icons' / 'app_icon.png'),
    )

# Collect all files
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='StreamripDesktop',
)

# macOS: Create app bundle
if IS_MAC:
    app = BUNDLE(
        coll,
        name='Streamrip Desktop.app',
        icon=str(RESOURCES_DIR / 'icons' / 'app_icon.icns'),
        bundle_identifier='com.streamrip.desktop',
        info_plist={
            'CFBundleName': 'Streamrip Desktop',
            'CFBundleDisplayName': 'Streamrip Desktop',
            'CFBundleVersion': '1.0.0',
            'CFBundleShortVersionString': '1.0.0',
            'NSHighResolutionCapable': 'True',
            'NSRequiresAquaSystemAppearance': 'False',
            'LSMinimumSystemVersion': '10.15.0',
            'NSHumanReadableCopyright': 'Copyright © 2025 Streamrip',
        },
    )
```

### 2.2 Build Script

**`scripts/build.py`**

```python
#!/usr/bin/env python3
"""
Build script for Streamrip Desktop
"""
import sys
import os
import subprocess
import shutil
from pathlib import Path
import argparse


def main():
    parser = argparse.ArgumentParser(description='Build Streamrip Desktop')
    parser.add_argument('--platform', choices=['windows', 'macos', 'linux'],
                       default=sys.platform, help='Target platform')
    parser.add_argument('--clean', action='store_true',
                       help='Clean build directories before building')
    args = parser.parse_args()

    # Project paths
    repo_root = Path(__file__).parent.parent
    spec_file = repo_root / 'packaging' / 'streamrip-desktop.spec'
    dist_dir = repo_root / 'dist'
    build_dir = repo_root / 'build'

    # Clean if requested
    if args.clean:
        print("Cleaning build directories...")
        shutil.rmtree(build_dir, ignore_errors=True)
        shutil.rmtree(dist_dir, ignore_errors=True)

    # Download FFmpeg if not present
    download_ffmpeg(args.platform, repo_root)

    # Run PyInstaller
    print(f"Building for {args.platform}...")
    cmd = [
        'pyinstaller',
        '--clean',
        '--noconfirm',
        str(spec_file)
    ]

    result = subprocess.run(cmd, cwd=repo_root)
    if result.returncode != 0:
        print("Build failed!")
        sys.exit(1)

    print(f"\nBuild successful! Output in {dist_dir}")

    # Platform-specific post-build
    if args.platform == 'windows':
        build_windows_installer(repo_root)
    elif args.platform == 'macos':
        build_macos_dmg(repo_root)
    elif args.platform == 'linux':
        build_linux_packages(repo_root)


def download_ffmpeg(platform: str, repo_root: Path):
    """Download FFmpeg binary if not present."""
    bin_dir = repo_root / 'bin' / platform
    bin_dir.mkdir(parents=True, exist_ok=True)

    if platform == 'windows':
        ffmpeg_path = bin_dir / 'ffmpeg.exe'
        download_url = 'https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip'
    elif platform == 'macos':
        ffmpeg_path = bin_dir / 'ffmpeg'
        download_url = 'https://evermeet.cx/ffmpeg/getrelease'
    else:  # Linux
        ffmpeg_path = bin_dir / 'ffmpeg'
        download_url = 'https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz'

    if ffmpeg_path.exists():
        print(f"FFmpeg already present: {ffmpeg_path}")
        return

    print(f"Downloading FFmpeg for {platform}...")
    # Download and extract logic here
    # This is simplified - actual implementation would download and extract
    print(f"Please download FFmpeg manually from:")
    print(f"  {download_url}")
    print(f"And place it at: {ffmpeg_path}")
    sys.exit(1)


def build_windows_installer(repo_root: Path):
    """Build Windows installer using NSIS."""
    print("\nBuilding Windows installer...")
    nsis_script = repo_root / 'packaging' / 'windows' / 'installer.nsi'

    cmd = ['makensis', str(nsis_script)]
    subprocess.run(cmd, check=True)

    print("Windows installer created!")


def build_macos_dmg(repo_root: Path):
    """Build macOS DMG."""
    print("\nBuilding macOS DMG...")

    # Sign the app first (if certificates available)
    app_path = repo_root / 'dist' / 'Streamrip Desktop.app'

    # Create DMG
    dmg_script = repo_root / 'packaging' / 'macos' / 'create-dmg.sh'
    subprocess.run(['bash', str(dmg_script)], check=True)

    print("macOS DMG created!")


def build_linux_packages(repo_root: Path):
    """Build Linux packages (AppImage, .deb, .rpm)."""
    print("\nBuilding Linux packages...")

    # Build AppImage
    appimage_script = repo_root / 'packaging' / 'linux' / 'build-appimage.sh'
    subprocess.run(['bash', str(appimage_script)], check=True)

    print("Linux packages created!")


if __name__ == '__main__':
    main()
```

---

## 3. Windows Packaging

### 3.1 NSIS Installer Script

**`packaging/windows/installer.nsi`**

```nsis
; Streamrip Desktop Windows Installer

!include "MUI2.nsh"
!include "FileFunc.nsh"

; Application metadata
!define APP_NAME "Streamrip Desktop"
!define APP_VERSION "1.0.0"
!define APP_PUBLISHER "Streamrip"
!define APP_URL "https://github.com/nathom/streamrip"
!define APP_EXE "StreamripDesktop.exe"

; Installer settings
Name "${APP_NAME}"
OutFile "..\..\dist\StreamripDesktop-${APP_VERSION}-Setup.exe"
InstallDir "$PROGRAMFILES64\${APP_NAME}"
InstallDirRegKey HKLM "Software\${APP_NAME}" "InstallDir"
RequestExecutionLevel admin

; Interface settings
!define MUI_ABORTWARNING
!define MUI_ICON "..\..\src\resources\icons\app_icon.ico"
!define MUI_UNICON "..\..\src\resources\icons\app_icon.ico"
!define MUI_HEADERIMAGE
!define MUI_HEADERIMAGE_BITMAP "header.bmp"
!define MUI_WELCOMEFINISHPAGE_BITMAP "wizard.bmp"

; Pages
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "..\..\LICENSE"
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

; Languages
!insertmacro MUI_LANGUAGE "English"

; Installer section
Section "Install"
    SetOutPath "$INSTDIR"

    ; Copy all files from PyInstaller dist
    File /r "..\..\dist\StreamripDesktop\*.*"

    ; Create start menu shortcut
    CreateDirectory "$SMPROGRAMS\${APP_NAME}"
    CreateShortCut "$SMPROGRAMS\${APP_NAME}\${APP_NAME}.lnk" "$INSTDIR\${APP_EXE}"
    CreateShortCut "$SMPROGRAMS\${APP_NAME}\Uninstall.lnk" "$INSTDIR\Uninstall.exe"

    ; Create desktop shortcut
    CreateShortCut "$DESKTOP\${APP_NAME}.lnk" "$INSTDIR\${APP_EXE}"

    ; Write registry keys
    WriteRegStr HKLM "Software\${APP_NAME}" "InstallDir" "$INSTDIR"
    WriteRegStr HKLM "Software\${APP_NAME}" "Version" "${APP_VERSION}"

    ; Write uninstall information
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "DisplayName" "${APP_NAME}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "UninstallString" "$INSTDIR\Uninstall.exe"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "DisplayIcon" "$INSTDIR\${APP_EXE}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "Publisher" "${APP_PUBLISHER}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "DisplayVersion" "${APP_VERSION}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "URLInfoAbout" "${APP_URL}"

    ; Get installed size
    ${GetSize} "$INSTDIR" "/S=0K" $0 $1 $2
    IntFmt $0 "0x%08X" $0
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "EstimatedSize" "$0"

    ; Create uninstaller
    WriteUninstaller "$INSTDIR\Uninstall.exe"
SectionEnd

; Uninstaller section
Section "Uninstall"
    ; Remove files
    RMDir /r "$INSTDIR"

    ; Remove shortcuts
    RMDir /r "$SMPROGRAMS\${APP_NAME}"
    Delete "$DESKTOP\${APP_NAME}.lnk"

    ; Remove registry keys
    DeleteRegKey HKLM "Software\${APP_NAME}"
    DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}"
SectionEnd
```

### 3.2 Code Signing (Windows)

**`scripts/sign-windows.ps1`**

```powershell
# Windows code signing script
param(
    [Parameter(Mandatory=$true)]
    [string]$CertificateFile,

    [Parameter(Mandatory=$true)]
    [string]$CertificatePassword,

    [Parameter(Mandatory=$true)]
    [string]$FileToSign
)

# Sign the executable
& "C:\Program Files (x86)\Windows Kits\10\bin\10.0.19041.0\x64\signtool.exe" sign `
    /f $CertificateFile `
    /p $CertificatePassword `
    /tr http://timestamp.digicert.com `
    /td SHA256 `
    /fd SHA256 `
    $FileToSign

if ($LASTEXITCODE -eq 0) {
    Write-Host "Successfully signed: $FileToSign" -ForegroundColor Green
} else {
    Write-Host "Failed to sign: $FileToSign" -ForegroundColor Red
    exit 1
}
```

---

## 4. macOS Packaging

### 4.1 Create DMG Script

**`packaging/macos/create-dmg.sh`**

```bash
#!/bin/bash
# Create macOS DMG

set -e

APP_NAME="Streamrip Desktop"
APP_VERSION="1.0.0"
DMG_NAME="StreamripDesktop-${APP_VERSION}.dmg"
REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
DIST_DIR="${REPO_ROOT}/dist"
APP_PATH="${DIST_DIR}/${APP_NAME}.app"
DMG_PATH="${DIST_DIR}/${DMG_NAME}"

echo "Creating DMG for ${APP_NAME} v${APP_VERSION}..."

# Check if app exists
if [ ! -d "$APP_PATH" ]; then
    echo "Error: App not found at $APP_PATH"
    exit 1
fi

# Create temporary DMG directory
TMP_DMG_DIR=$(mktemp -d)
cp -R "$APP_PATH" "$TMP_DMG_DIR/"

# Create Applications symlink
ln -s /Applications "$TMP_DMG_DIR/Applications"

# Create DMG
echo "Creating DMG..."
hdiutil create -volname "${APP_NAME}" \
    -srcfolder "$TMP_DMG_DIR" \
    -ov -format UDZO \
    "$DMG_PATH"

# Clean up
rm -rf "$TMP_DMG_DIR"

echo "DMG created: $DMG_PATH"

# Verify DMG
hdiutil verify "$DMG_PATH"

echo "DMG verification passed!"
```

### 4.2 macOS Code Signing

**`scripts/sign-macos.sh`**

```bash
#!/bin/bash
# macOS code signing and notarization

set -e

APP_PATH="$1"
DEVELOPER_ID="Developer ID Application: Your Name (TEAM_ID)"
BUNDLE_ID="com.streamrip.desktop"

if [ -z "$APP_PATH" ]; then
    echo "Usage: $0 <path-to-app>"
    exit 1
fi

echo "Signing app bundle: $APP_PATH"

# Sign all frameworks and libraries first
find "$APP_PATH/Contents/Frameworks" -type f -name "*.dylib" -o -name "*.so" | while read file; do
    echo "Signing: $file"
    codesign --force --sign "$DEVELOPER_ID" \
        --timestamp \
        --options runtime \
        "$file"
done

# Sign the main executable
codesign --force --sign "$DEVELOPER_ID" \
    --timestamp \
    --options runtime \
    --entitlements packaging/macos/entitlements.plist \
    "$APP_PATH/Contents/MacOS/StreamripDesktop"

# Sign the app bundle
codesign --force --sign "$DEVELOPER_ID" \
    --timestamp \
    --options runtime \
    --entitlements packaging/macos/entitlements.plist \
    "$APP_PATH"

# Verify signature
echo "Verifying signature..."
codesign --verify --deep --strict --verbose=2 "$APP_PATH"

echo "App signed successfully!"

# Notarization (requires Apple ID credentials)
echo "Creating ZIP for notarization..."
ZIP_PATH="${APP_PATH}.zip"
ditto -c -k --keepParent "$APP_PATH" "$ZIP_PATH"

echo "Submitting for notarization..."
xcrun notarytool submit "$ZIP_PATH" \
    --apple-id "your@email.com" \
    --team-id "TEAM_ID" \
    --password "@keychain:AC_PASSWORD" \
    --wait

echo "Stapling notarization ticket..."
xcrun stapler staple "$APP_PATH"

rm "$ZIP_PATH"
echo "Notarization complete!"
```

### 4.3 Entitlements

**`packaging/macos/entitlements.plist`**

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <!-- Allow network access -->
    <key>com.apple.security.network.client</key>
    <true/>

    <!-- Allow outgoing connections -->
    <key>com.apple.security.network.server</key>
    <true/>

    <!-- Allow file access -->
    <key>com.apple.security.files.user-selected.read-write</key>
    <true/>

    <!-- Disable library validation for Python modules -->
    <key>com.apple.security.cs.disable-library-validation</key>
    <true/>

    <!-- Allow JIT for Python -->
    <key>com.apple.security.cs.allow-jit</key>
    <true/>

    <!-- Allow unsigned executable memory -->
    <key>com.apple.security.cs.allow-unsigned-executable-memory</key>
    <true/>

    <!-- Hardened runtime -->
    <key>com.apple.security.get-task-allow</key>
    <false/>
</dict>
</plist>
```

---

## 5. Linux Packaging

### 5.1 AppImage

**`packaging/linux/build-appimage.sh`**

```bash
#!/bin/bash
# Build AppImage for Linux

set -e

APP_NAME="StreamripDesktop"
APP_VERSION="1.0.0"
REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
DIST_DIR="${REPO_ROOT}/dist"
APPDIR="${DIST_DIR}/${APP_NAME}.AppDir"

echo "Building AppImage for ${APP_NAME} v${APP_VERSION}..."

# Create AppDir structure
mkdir -p "$APPDIR/usr/bin"
mkdir -p "$APPDIR/usr/lib"
mkdir -p "$APPDIR/usr/share/applications"
mkdir -p "$APPDIR/usr/share/icons/hicolor/256x256/apps"

# Copy application files
cp -r "${DIST_DIR}/StreamripDesktop/"* "$APPDIR/usr/bin/"

# Copy icon
cp "${REPO_ROOT}/src/resources/icons/app_icon.png" \
   "$APPDIR/usr/share/icons/hicolor/256x256/apps/streamrip-desktop.png"

# Create desktop file
cat > "$APPDIR/usr/share/applications/streamrip-desktop.desktop" << EOF
[Desktop Entry]
Name=Streamrip Desktop
Exec=streamrip-desktop
Icon=streamrip-desktop
Type=Application
Categories=AudioVideo;Audio;
Comment=Download high-quality music from streaming services
Terminal=false
EOF

# Create AppRun script
cat > "$APPDIR/AppRun" << 'EOF'
#!/bin/bash
SELF=$(readlink -f "$0")
HERE=${SELF%/*}
export PATH="${HERE}/usr/bin:${PATH}"
export LD_LIBRARY_PATH="${HERE}/usr/lib:${LD_LIBRARY_PATH}"
exec "${HERE}/usr/bin/streamrip-desktop" "$@"
EOF
chmod +x "$APPDIR/AppRun"

# Symlinks for AppImage
ln -sf usr/share/applications/streamrip-desktop.desktop "$APPDIR/"
ln -sf usr/share/icons/hicolor/256x256/apps/streamrip-desktop.png "$APPDIR/"

# Download appimagetool if not present
APPIMAGETOOL="${REPO_ROOT}/bin/appimagetool-x86_64.AppImage"
if [ ! -f "$APPIMAGETOOL" ]; then
    echo "Downloading appimagetool..."
    wget -O "$APPIMAGETOOL" \
        "https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage"
    chmod +x "$APPIMAGETOOL"
fi

# Build AppImage
OUTPUT_APPIMAGE="${DIST_DIR}/${APP_NAME}-${APP_VERSION}-x86_64.AppImage"
ARCH=x86_64 "$APPIMAGETOOL" "$APPDIR" "$OUTPUT_APPIMAGE"

echo "AppImage created: $OUTPUT_APPIMAGE"
```

### 5.2 Debian Package

**`packaging/linux/build-deb.sh`**

```bash
#!/bin/bash
# Build .deb package

set -e

APP_NAME="streamrip-desktop"
APP_VERSION="1.0.0"
ARCH="amd64"
REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
DIST_DIR="${REPO_ROOT}/dist"
DEB_DIR="${DIST_DIR}/deb"

echo "Building .deb package..."

# Create package structure
mkdir -p "${DEB_DIR}/DEBIAN"
mkdir -p "${DEB_DIR}/usr/bin"
mkdir -p "${DEB_DIR}/usr/lib/${APP_NAME}"
mkdir -p "${DEB_DIR}/usr/share/applications"
mkdir -p "${DEB_DIR}/usr/share/icons/hicolor/256x256/apps"
mkdir -p "${DEB_DIR}/usr/share/doc/${APP_NAME}"

# Copy application
cp -r "${DIST_DIR}/StreamripDesktop/"* "${DEB_DIR}/usr/lib/${APP_NAME}/"

# Create launcher script
cat > "${DEB_DIR}/usr/bin/${APP_NAME}" << 'EOF'
#!/bin/bash
exec /usr/lib/streamrip-desktop/streamrip-desktop "$@"
EOF
chmod +x "${DEB_DIR}/usr/bin/${APP_NAME}"

# Copy desktop file
cat > "${DEB_DIR}/usr/share/applications/${APP_NAME}.desktop" << EOF
[Desktop Entry]
Name=Streamrip Desktop
Exec=streamrip-desktop
Icon=streamrip-desktop
Type=Application
Categories=AudioVideo;Audio;
Comment=Download high-quality music from streaming services
Terminal=false
EOF

# Copy icon
cp "${REPO_ROOT}/src/resources/icons/app_icon.png" \
   "${DEB_DIR}/usr/share/icons/hicolor/256x256/apps/${APP_NAME}.png"

# Create control file
cat > "${DEB_DIR}/DEBIAN/control" << EOF
Package: ${APP_NAME}
Version: ${APP_VERSION}
Section: sound
Priority: optional
Architecture: ${ARCH}
Maintainer: Streamrip <streamrip@example.com>
Description: High-quality music downloader
 Streamrip Desktop allows downloading high-quality music from
 Qobuz, Tidal, Deezer, and SoundCloud streaming services.
Depends: libc6, libglib2.0-0
EOF

# Create copyright file
cp "${REPO_ROOT}/LICENSE" "${DEB_DIR}/usr/share/doc/${APP_NAME}/copyright"

# Build package
DEB_FILE="${DIST_DIR}/${APP_NAME}_${APP_VERSION}_${ARCH}.deb"
dpkg-deb --build "$DEB_DIR" "$DEB_FILE"

echo ".deb package created: $DEB_FILE"

# Clean up
rm -rf "$DEB_DIR"
```

---

## 6. Automated Build Pipeline

### 6.1 GitHub Actions Workflow

**`.github/workflows/build.yml`**

```yaml
name: Build Streamrip Desktop

on:
  push:
    branches: [ main, dev ]
    tags: [ 'v*' ]
  pull_request:
    branches: [ main ]

jobs:
  build-windows:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install pyinstaller

      - name: Download FFmpeg
        run: |
          Invoke-WebRequest -Uri "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip" -OutFile "ffmpeg.zip"
          Expand-Archive -Path "ffmpeg.zip" -DestinationPath "bin\windows"
          Move-Item "bin\windows\ffmpeg-*\bin\ffmpeg.exe" "bin\windows\ffmpeg.exe"

      - name: Build with PyInstaller
        run: python scripts/build.py --platform windows

      - name: Build installer
        run: |
          choco install nsis -y
          makensis packaging/windows/installer.nsi

      - name: Upload artifacts
        uses: actions/upload-artifact@v3
        with:
          name: windows-build
          path: dist/*.exe

  build-macos:
    runs-on: macos-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install pyinstaller

      - name: Download FFmpeg
        run: |
          brew install ffmpeg
          mkdir -p bin/macos
          cp $(which ffmpeg) bin/macos/

      - name: Build with PyInstaller
        run: python scripts/build.py --platform macos

      - name: Create DMG
        run: bash packaging/macos/create-dmg.sh

      - name: Upload artifacts
        uses: actions/upload-artifact@v3
        with:
          name: macos-build
          path: dist/*.dmg

  build-linux:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'

      - name: Install dependencies
        run: |
          sudo apt-get update
          sudo apt-get install -y ffmpeg
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install pyinstaller

      - name: Copy FFmpeg
        run: |
          mkdir -p bin/linux
          cp $(which ffmpeg) bin/linux/

      - name: Build with PyInstaller
        run: python scripts/build.py --platform linux

      - name: Build AppImage
        run: bash packaging/linux/build-appimage.sh

      - name: Build .deb
        run: bash packaging/linux/build-deb.sh

      - name: Upload artifacts
        uses: actions/upload-artifact@v3
        with:
          name: linux-build
          path: |
            dist/*.AppImage
            dist/*.deb

  release:
    needs: [build-windows, build-macos, build-linux]
    runs-on: ubuntu-latest
    if: startsWith(github.ref, 'refs/tags/v')
    steps:
      - name: Download all artifacts
        uses: actions/download-artifact@v3

      - name: Create Release
        uses: softprops/action-gh-release@v1
        with:
          files: |
            windows-build/*
            macos-build/*
            linux-build/*
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

---

## 7. Code Signing

### 7.1 Obtaining Certificates

**Windows:**
- Purchase code signing certificate from CA (DigiCert, Sectigo, etc.)
- Cost: ~$300-500/year
- Alternatives: Self-signed (triggers SmartScreen warnings)

**macOS:**
- Requires Apple Developer Account ($99/year)
- Generate "Developer ID Application" certificate
- Required for distribution outside Mac App Store

**Linux:**
- No code signing required
- Optional: GPG signature for packages

### 7.2 Certificate Management

Store certificates securely:
- Use environment variables or secret management
- Never commit certificates to repository
- Use CI/CD secret storage (GitHub Secrets, etc.)

---

## 8. Update Mechanism

### 8.1 Auto-Update Implementation

**`src/services/update_service.py`**

```python
"""
Auto-update service using PyUpdater or custom implementation.
"""
import asyncio
import logging
from packaging import version
from PyQt6.QtCore import QObject, pyqtSignal

logger = logging.getLogger(__name__)


class UpdateService(QObject):
    """Handle application updates."""

    update_available = pyqtSignal(str, str)  # version, download_url
    update_downloaded = pyqtSignal(str)  # file_path
    update_error = pyqtSignal(Exception)

    UPDATE_CHECK_URL = "https://api.github.com/repos/nathom/streamrip/releases/latest"
    CURRENT_VERSION = "1.0.0"

    async def check_for_updates(self) -> bool:
        """Check if update is available."""
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get(self.UPDATE_CHECK_URL) as resp:
                    data = await resp.json()
                    latest_version = data['tag_name'].lstrip('v')

                    if version.parse(latest_version) > version.parse(self.CURRENT_VERSION):
                        download_url = self._get_platform_asset_url(data['assets'])
                        self.update_available.emit(latest_version, download_url)
                        return True

                    return False
        except Exception as e:
            logger.error(f"Update check failed: {e}")
            self.update_error.emit(e)
            return False

    def _get_platform_asset_url(self, assets: list) -> str:
        """Get download URL for current platform."""
        import sys

        if sys.platform == 'win32':
            pattern = 'StreamripDesktop-*-Setup.exe'
        elif sys.platform == 'darwin':
            pattern = 'StreamripDesktop-*.dmg'
        else:
            pattern = 'StreamripDesktop-*.AppImage'

        import fnmatch
        for asset in assets:
            if fnmatch.fnmatch(asset['name'], pattern):
                return asset['browser_download_url']

        raise ValueError("No asset found for platform")
```

---

**This guide provides comprehensive packaging and distribution strategies for all major platforms. The build pipeline automates the entire process from code to distributable packages.**

**Total Guide Length: ~1,000 lines**

Would you like me to create additional guides for mobile (Android/iOS) specifics, or detailed architecture diagrams?
