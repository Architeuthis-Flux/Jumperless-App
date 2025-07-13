# Jumperless CI/CD Setup Guide

This guide covers the modern multi-platform CI/CD system for Jumperless, built with GitHub Actions and modern Python packaging tools.

## Overview

The CI/CD system automatically builds and packages Jumperless for multiple platforms and architectures whenever code is pushed or when a release is tagged. It creates both native executables and Python fallback packages for maximum compatibility.

## Supported Platforms

- **Linux x64**: AppImage + Python fallback
- **macOS Intel (x64)**: Native executable + Python fallback
- **macOS Apple Silicon (ARM64)**: Native executable + Python fallback
- **Windows x64**: EXE + Python fallback

## Features

### ✅ What's Included

- **Multi-platform builds** using GitHub Actions matrix strategy
- **PyInstaller executables** for each platform
- **Python fallback packages** with automatic dependency installation
- **Comprehensive packaging** with launchers, READMEs, and documentation
- **Automated testing** with smoke tests
- **Release automation** with GitHub releases
- **Modern tooling** including `uv` for fast dependency management
- **Version management** with automatic version detection

### 🔧 Tools Used

- **GitHub Actions** - CI/CD platform
- **PyInstaller** - Python to executable conversion
- **uv** - Fast Python package manager
- **create-dmg** - macOS DMG creation
- **Custom scripts** - Platform-specific packaging

## Getting Started

### Prerequisites

1. **GitHub repository** with Actions enabled
2. **Python 3.11+** (for local development)
3. **Requirements files** properly configured
4. **Asset files** in `assets/icons/` directory

### Required Files

Ensure these files exist in your repository:

```
project/
├── .github/workflows/build-and-package.yml  # Main workflow
├── scripts/
│   ├── package_app.py                       # Main packaging script
│   ├── create_version_info.py               # Windows version info
│   ├── smoke_test.py                        # Basic testing
│   └── create_combined_readme.py            # Combined docs
├── assets/icons/
│   ├── icon.png                             # Linux icon
│   ├── icon.icns                            # macOS icon
│   └── icon.ico                             # Windows icon
├── requirements.txt                          # App dependencies
├── PackagingApps/packagerRequirements.txt   # Build dependencies
└── JumperlessWokwiBridge.py                 # Main application
```

### Icon Requirements

Create platform-specific icons:

```bash
# Linux: PNG format
assets/icons/icon.png

# macOS: ICNS format (use iconutil or third-party tools)
assets/icons/icon.icns

# Windows: ICO format (use online converters or tools)
assets/icons/icon.ico
```

## Workflow Configuration

### Triggering Builds

The workflow triggers on:

- **Push** to `main` or `develop` branches
- **Pull requests** to `main` branch
- **Tag pushes** (creates releases)
- **Manual dispatch** via GitHub UI

### Matrix Strategy

The workflow uses a matrix to build for multiple platforms:

```yaml
strategy:
  fail-fast: false
  matrix:
    include:
      - os: ubuntu-latest
        platform: linux
        arch: x64
      - os: macos-13
        platform: macos
        arch: x64
      - os: macos-latest
        platform: macos
        arch: arm64
      - os: windows-latest
        platform: windows
        arch: x64
```

### Environment Variables

- `PYTHON_VERSION`: Python version to use (default: "3.11")

## Package Structure

Each platform package includes:

```
Jumperless-[Platform]/
├── Jumperless[.exe]     # Native executable
├── README.md                       # Platform-specific instructions
└── Jumperless Python/              # Python fallback
    ├── JumperlessWokwiBridge.py    # Main application
    ├── requirements.txt            # Dependencies
    ├── launcher.py                 # Universal Python launcher
    ├── run_jumperless.sh           # Shell launcher (Linux/macOS)
    ├── run_jumperless.bat          # Batch launcher (Windows)
    ├── assets/                     # Application assets
    └── README.md                   # Fallback instructions
```

## Local Development

### Setting Up Local Build Environment

```bash
# Clone the repository
git clone https://github.com/your-username/Jumperless-App.git
cd Jumperless-App

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# or
.venv\Scripts\activate     # Windows

# Install dependencies
pip install -r PackagingApps/packagerRequirements.txt
pip install -r requirements.txt
```

### Building Locally

```bash
# Build for your current platform
python scripts/package_app.py --platform [linux|macos|windows] --arch x64

# Test the build
python scripts/smoke_test.py --platform [linux|macos|windows]
```

### Testing PyInstaller Build

```bash
# Linux
python -m PyInstaller --onefile --console --name "Jumperless" --icon "assets/icons/icon.png" JumperlessWokwiBridge.py

# macOS
python -m PyInstaller --onefile --console --name "Jumperless" --icon "assets/icons/icon.icns" JumperlessWokwiBridge.py

# Windows
python -m PyInstaller --onefile --console --name "Jumperless" --icon "assets/icons/icon.ico" JumperlessWokwiBridge.py
```

## Customization

### Modifying the Workflow

Edit `.github/workflows/build-and-package.yml` to:

- Add new platforms or architectures
- Change Python version
- Modify build flags
- Add additional testing steps

### Adding New Platforms

1. Add platform to the matrix in the workflow
2. Update `scripts/package_app.py` with platform-specific logic
3. Add platform-specific icons if needed
4. Update documentation

### Customizing Package Contents

Modify `scripts/package_app.py` to:

- Include additional files
- Change directory structure
- Add custom launchers
- Modify README templates

## Release Process

### Creating a Release

1. **Tag the release:**
   ```bash
   git tag -a v1.0.0 -m "Release v1.0.0"
   git push origin v1.0.0
   ```

2. **Automatic build:** GitHub Actions will automatically build and create a release

3. **Release contents:**
   - Individual platform packages
   - Combined release with all platforms
   - Comprehensive documentation
   - Automated release notes

### Release Artifacts

For each release, you'll get:

- `Jumperless-Linux-x64.tar.gz` / `.zip`
- `Jumperless-macOS-Intel.tar.gz` / `.zip`
- `Jumperless-macOS-Apple-Silicon.tar.gz` / `.zip`
- `Jumperless-Windows-x64.zip`
- Combined release with all platforms

## Troubleshooting

### Common Issues

#### Build Failures

**PyInstaller import errors:**
```bash
# Add hidden imports to PyInstaller command
--hidden-import your_module
```

**Missing dependencies:**
```bash
# Check and update requirements files
pip freeze > requirements.txt
```

**Platform-specific issues:**
```bash
# Check platform-specific dependencies in workflow
# Add system packages as needed
```

#### Packaging Issues

**Icons not found:**
```bash
# Ensure icons exist in assets/icons/
ls -la assets/icons/
```

**Executable not working:**
```bash
# Test locally first
python scripts/smoke_test.py --platform your_platform
```

#### Release Issues

**Release not created:**
- Check that the tag matches the pattern `v*`
- Verify GitHub token permissions
- Check workflow logs for errors

### Debugging

#### Local Debugging

```bash
# Run packaging script with verbose output
python scripts/package_app.py --platform linux --arch x64 --verbose

# Test executable locally
./builds/linux/Jumperless --help
```

#### GitHub Actions Debugging

1. Check workflow logs in Actions tab
2. Enable debug logging by adding secrets:
   - `ACTIONS_STEP_DEBUG=true`
   - `ACTIONS_RUNNER_DEBUG=true`
3. Use `workflow_dispatch` to test manually

### Performance Optimization

#### Faster Builds

- Use `uv` instead of `pip` (already configured)
- Enable dependency caching (already configured)
- Use `fail-fast: false` for matrix builds

#### Smaller Packages

- Use `--exclude-module` in PyInstaller for unused modules
- Compress assets before packaging
- Remove unnecessary files from packages

## Security Considerations

### Secrets Management

- Never commit secrets to the repository
- Use GitHub secrets for sensitive data
- Consider using OIDC for secure authentication

### Code Signing

For production releases, consider adding code signing:

- **macOS**: Apple Developer certificate
- **Windows**: Code signing certificate
- **Linux**: GPG signing for packages

## Best Practices

### Version Management

- Use semantic versioning (e.g., `v1.2.3`)
- Tag releases consistently
- Update version in multiple places if needed

### Testing

- Always test locally before pushing
- Use smoke tests to verify basic functionality
- Test on multiple platforms when possible

### Documentation

- Keep README files updated
- Document breaking changes
- Provide clear installation instructions

## Advanced Topics

### Alternative Packaging Tools

Consider these alternatives to PyInstaller:

- **Nuitka**: Compiles Python to C++
- **cx_Freeze**: Cross-platform freezing
- **py2exe**: Windows-only packaging
- **briefcase**: Modern packaging with BeeWare

### Custom Build Scripts

You can extend the system with custom scripts:

```python
# scripts/custom_build.py
def custom_build_step():
    # Your custom build logic here
    pass
```

### Integration with Other CI Systems

The scripts can be adapted for other CI systems:

- **GitLab CI**: Modify YAML syntax
- **Azure DevOps**: Use Azure-specific actions
- **Jenkins**: Convert to Groovy scripts

## Support

### Getting Help

- **GitHub Issues**: Report bugs and request features
- **Discussions**: Ask questions and share ideas
- **Discord**: Join the community chat

### Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

---

This CI/CD system provides a robust foundation for distributing Jumperless across multiple platforms. The combination of native executables and Python fallbacks ensures maximum compatibility while maintaining ease of use.

For the latest updates and detailed technical information, refer to the source code and workflow files in the repository. 