# EA app (Origin) Integration Plugin for GOG Galaxy 2.1+ (64-bit)

This plugin imports your EA app library into GOG Galaxy 2.1+ 64-bit. Based on the original Origin community integration, it has been updated for the current GOG Galaxy client and Python 3.13.

---

## ✨ Features

* Imports your owned EA games into GOG Galaxy
* Syncs achievements and game time
* Detects locally installed EA games
* Launches games through the EA app

> [!NOTE]
> macOS compatibility may be technically possible, but it is currently untested because I do not have access to a Mac. If you use macOS and would like to help test the integration, feel free to contact me.

---

## 📦 Installation

### Automatic Installation with Plugin Updater (Recommended)

Use the [melcom GOG Galaxy Plugin Updater](https://github.com/melcom-creations/galaxy-integrations-64bit/tree/main/tools/melcom-galaxy_plugin_updater) to install or update the integration automatically.

1. Download and extract the Plugin Updater.
2. Double-click `update-plugins.bat`.
3. Select your preferred language.
4. Follow the displayed instructions.

### Manual Installation

1. Close GOG Galaxy completely, including the system tray application.
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

**Next step:** Continue with **First Start and Initial Sync** below.

> [!IMPORTANT]
> Do not place backup copies of this plugin inside the `plugins\installed` directory. GOG Galaxy scans every folder inside this directory during startup, so duplicate plugin folders can cause GUID conflicts or load an outdated version.

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

Reset the local plugin database if synchronization problems continue after restarting both applications.

1. Close GOG Galaxy completely.
2. Open `C:\ProgramData\GOG.com\Galaxy\storage\plugins\`.
3. Find every file starting with `origin_` and ending in `-storage.db`.
4. Rename each matching file by appending `.old`, for example:

   `origin_xxxxxxxxx-storage.db` -> `origin_xxxxxxxxx-storage.db.old`

5. Start the EA app and keep it open.
6. Start GOG Galaxy, reconnect the integration if necessary, select **Sync integrations** from the account menu, and wait for synchronization to finish.

---

## 🛠️ What to Do If the Plugin Has Problems

If the database reset above does not resolve the problem, create a clean session with fresh diagnostic files before contacting me. The reset procedure preserves the previous database as a `.old` file; the steps below remove the active database so the issue can be reproduced from a clean state.

1. Close GOG Galaxy completely, including the system tray application.
2. Open the following directory and delete the existing log files:

   ```text
   %ProgramData%\GOG.com\Galaxy\logs
   ```

3. Open the plugin storage directory:

   ```text
   C:\ProgramData\GOG.com\Galaxy\storage\plugins
   ```

   Delete only the active EA app database file starting with `origin_` and ending in `-storage.db`. Do not delete database files belonging to other integrations. If you are unsure which file is correct, do not delete anything from this directory.
4. Start the EA app and keep it open. Start GOG Galaxy, reproduce the problem, and then close GOG Galaxy completely so the new log is fully written.
5. Return to the logs directory and locate the newly created EA app plugin log:

   ```text
   plugin-origin-7f53219b-4e2b-4591-9f4f-dfc5f4ba9eb0.log
   ```

Send only this log file, not the entire logs folder. Include the exact steps taken, the expected and actual result, and whether the problem can be reproduced.

Without a fresh plugin log and a detailed description, I cannot reliably determine what is causing the problem. Once everything is ready, continue with [Support & Feedback](#-support--feedback) for contact options.

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

**GitHub Issues are intentionally disabled.** Health-related limitations prevent me from reliably managing separate issue trackers across all of my plugin repositories.

Before contacting me, follow **What to Do If the Plugin Has Problems** and prepare a fresh EA app plugin log with a detailed description.

* **GOG:** Send me a message or add me as a friend through my [GOG profile](https://www.gog.com/u/melcom).
* **Email:** `melcom @ gmx.net`
* **Discord:** `.melcom` - the leading dot is part of the username. You can send me a message or add me as a friend.

Logs can be attached directly or shared using an accessible cloud storage link, such as Dropbox, OneDrive, Google Drive, or a similar service. Response times may vary depending on my health and available development time. Thank you for your understanding.
