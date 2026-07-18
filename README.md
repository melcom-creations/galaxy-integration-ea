# EA app (Origin) Integration Plugin for GOG Galaxy 2.1+ (64-bit)

This repository contains the EA app (Origin) integration plugin for the native 64-bit version of GOG Galaxy 2.1+. It is based on the original community integration and has been updated for the current GOG Galaxy client and Python 3.13. The project includes updated dependencies, compatibility fixes, stability improvements, and ongoing maintenance.

---

## ✨ Features

* Imports your owned EA games into GOG Galaxy
* Syncs achievements and game time
* Detects locally installed EA games
* Launches games through the EA app
* Supports GOG Galaxy 2.1+ 64-bit and Python 3.13
* Includes updated dependencies, compatibility fixes, and stability improvements

---

## 📦 Installation

### Automatic Installation with Plugin Updater (Recommended)

The easiest way to install the EA app integration is with the [melcom GOG Galaxy Plugin Updater](https://github.com/melcom-creations/galaxy-integrations-64bit/tree/main/tools/melcom-galaxy_plugin_updater). The updater detects existing integrations and can install any supported melcom plugins that are still missing.

1. Download and extract the Plugin Updater.
2. Double-click `update-plugins.bat`.
3. Select your preferred language.
4. Follow the displayed instructions.

### Manual Installation

1. Close GOG Galaxy completely and make sure it is no longer running in the system tray.
2. Download the latest release package from this repository.
3. Extract the ZIP archive directly into:

```text
%localappdata%\GOG.com\Galaxy\plugins\installed\
```

The resulting directory structure must look like this:

```text
%localappdata%\GOG.com\Galaxy\plugins\installed\
└── origin_7f53219b-4e2b-4591-9f4f-dfc5f4ba9eb0\
    ├── manifest.json
    ├── plugin.py
    ├── README.md
    └── ...
```

4. Start GOG Galaxy.

---

## 🚀 First Start and Initial Sync

For the first synchronization after installing or updating the plugin:

1. Start the EA app and keep it open.
2. Start GOG Galaxy.
3. Connect the EA app integration through **Settings -> Integrations** if necessary.
4. Open the account menu in the top-right corner and select **Sync integrations**.
5. Wait until the synchronization has finished.

---

## 🔄 Resetting the Plugin Database (Troubleshooting)

Reset the local plugin database only if the integration behaves unexpectedly or synchronization problems continue after restarting both applications.

1. Close GOG Galaxy completely.
2. Open `C:\ProgramData\GOG.com\Galaxy\storage\plugins\`.
3. Find every file starting with `origin_` and ending in `-storage.db`.
4. Rename each matching file by appending `.old`, for example:

   `origin_xxxxxxxxx-storage.db` -> `origin_xxxxxxxxx-storage.db.old`

5. Start GOG Galaxy and reconnect the EA app integration if necessary.

---

## ⚠️ Important

Do **not** place backup copies of this plugin inside the `plugins\installed` directory.

GOG Galaxy scans every folder inside this directory during startup. Duplicate plugin folders can lead to GUID conflicts or cause Galaxy to load an outdated version of the plugin.

---

## 🙏 Credits

**Original Community Integration**
Friends of Galaxy
[Friends of Galaxy Origin integration](https://github.com/FriendsOfGalaxy/galaxy-integration-origin)

**EA Device Signing**
Inspired by BellezaEmporium's galaxy-integration-ead
[BellezaEmporium EA device-signing integration](https://github.com/BellezaEmporium/galaxy-integration-ead)

**64-bit Port, Maintenance and Improvements**
melcom

---

## 🤝 Support & Feedback

This project is developed and maintained by one person. Response times may vary, especially during periods when health-related limitations reduce available development time.

**GitHub Issues are intentionally disabled.**

If you would like to report a bug or suggest an improvement, please use the contact form on my website:

📩 [Contact form](https://melcom-creations.github.io/melcom-music/contact.html)

Thank you for your patience and support!
