# HACS (Home Assistant Community Store) Installation

## Prerequisites

1. **HACS Installed**: Ensure you have HACS installed in your Home Assistant instance
   - If not installed, follow: https://hacs.xyz/docs/setup/download

## First Time Setup (Repository Owner)

If you're setting up this repository for the first time:

1. **Push to GitHub** (if not already done):
   ```bash
   git add .
   git commit -m "Add Switch Energy Statistics integration"
   git push origin main
   ```

2. **Create the first release**:
   ```bash
   git tag v1.0.0
   git push origin v1.0.0
   ```

3. **Wait for GitHub Actions**: The release workflow will automatically create a ZIP file and GitHub release

## Installation Steps

### Step 1: Add Custom Repository

1. Open HACS in your Home Assistant
2. Go to **Integrations** tab
3. Click the **three dots menu (⋮)** in the top right
4. Select **Custom repositories**
5. Add the following details:
   - **Repository**: `https://github.com/danielulisses/zigbee-devices`
   - **Category**: `Integration`
   - Click **Add**

### Step 2: Install the Integration

1. In HACS → Integrations, search for **"Switch Energy Statistics"**
2. Click on the integration
3. Click **Install**
4. **Restart Home Assistant**

### Step 3: Configure the Integration

1. Go to **Settings** → **Devices & Services** → **Integrations**
2. Click **Add Integration**
3. Search for **"Switch Energy Statistics Estimation"**
4. Follow the configuration wizard:
   - Select your switch entity
   - Set number of gangs (1-8)
   - Configure power consumption for each gang

## Benefits of HACS Installation

✅ **Automatic Updates**: Get notified of new versions
✅ **Easy Management**: Install/uninstall through UI
✅ **Version Control**: Track installed version and changelog
✅ **Backup Friendly**: HACS manages the installation location

## Troubleshooting HACS Installation

### Repository Not Found or No Releases
- **Create a release**: The repository needs at least one GitHub release
  ```bash
  git tag v1.0.0
  git push origin v1.0.0
  ```
- **Wait for Actions**: GitHub Actions will create the release (may take 1-2 minutes)
- **Check repository is public**: Ensure the GitHub repository is publicly accessible
- **Verify URL**: Double-check the repository URL is correct

### Integration Not Appearing
- Make sure you added it as **Integration** category (not Plugin)
- Refresh HACS cache: Settings → Clear cache
- Restart Home Assistant

### Installation Fails
- Check Home Assistant logs for errors
- Ensure you have sufficient disk space
- Try manual installation as fallback

## Migration from Manual Installation

If you previously installed manually:

1. **Remove manual installation**: Delete the `custom_components/switch_energy_statistics_estimation` folder
2. **Restart Home Assistant**
3. **Install via HACS** following the steps above
4. **Re-add integration** through the UI
5. **Your configuration will be preserved**

## Repository Structure

```
zigbee-devices/
├── README.md (main repository readme)
├── custom_components/
│   └── switch_energy_statistics_estimation/
│       ├── manifest.json
│       ├── hacs.json
│       ├── __init__.py
│       ├── config_flow.py
│       ├── sensor.py
│       ├── const.py
│       ├── services.py
│       ├── services.yaml
│       ├── translations/
│       │   └── en.json
│       ├── README.md (integration documentation)
│       └── examples.md
└── relay-2-types/ (other components)
```

## Support

- **Issues**: Report bugs at `https://github.com/danielulisses/zigbee-devices/issues`
- **Discussions**: Ask questions in repository discussions
- **Documentation**: Full docs in `README.md` and `examples.md`
