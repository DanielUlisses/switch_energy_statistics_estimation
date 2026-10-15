# HACS (Home Assistant Community Store) Installation

## Prerequisites

1. **HACS Installed**: Ensure you have HACS installed in your Home Assistant instance
   - If not installed, follow: https://hacs.xyz/docs/setup/download

## Installation Steps

### Step 1: Add Custom Repository

1. Open HACS in your Home Assistant
2. Go to **Integrations** tab
3. Click the **three dots menu (⋮)** in the top right
4. Select **Custom repositories**
5. Add the following details:
   - **Repository**: `https://github.com/DanielUlisses/switch_energy_statistics_estimation`
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
   - Pick the switch / light / fan / input_boolean entities, one per gang (1-8)
   - Set the watts per load and the number of loads for each gang

Or attach loads from a script with the `switch_energy_statistics.attach` service (see `README.md`).

## Benefits of HACS Installation

✅ **Automatic Updates**: Get notified of new versions
✅ **Easy Management**: Install/uninstall through UI
✅ **Version Control**: Track installed version and changelog
✅ **Backup Friendly**: HACS manages the installation location

## Troubleshooting HACS Installation

### Repository Not Found or No Releases
- **Check releases**: HACS installs from the GitHub releases of the repository (`hacs.json` sets `zip_release` with `release_filter: switch-stats-v*`)
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

1. **Remove manual installation**: Delete the `custom_components/switch_energy_statistics` folder
2. **Install via HACS** following the steps above (the folder name stays `switch_energy_statistics`)
3. **Restart Home Assistant**

Existing entries, entity IDs and history are kept: they live in Home Assistant's `.storage`, not in the integration folder.

## Integration Structure

```
custom_components/
└── switch_energy_statistics/
    ├── manifest.json
    ├── hacs.json
    ├── __init__.py
    ├── config_flow.py
    ├── const.py
    ├── sensor.py
    ├── services.py
    ├── services.yaml
    ├── tracker.py
    ├── translations/
    │   ├── en.json
    │   └── pt-BR.json
    ├── README.md (integration documentation)
    └── examples.md
```

## Support

- **Issues**: Report bugs at `https://github.com/DanielUlisses/switch_energy_statistics_estimation/issues`
- **Documentation**: Full docs in `README.md` and `examples.md`
