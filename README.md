# EA app (Origin) Integration Plugin for GOG Galaxy 2.1+ (64-bit)

This repository contains the EA app (Origin) integration plugin for the 64-bit version of GOG Galaxy 2.1+.

The original community integration has been updated to work with the current 64-bit GOG Galaxy client and Python 3.13. In addition to compatibility improvements, this project includes dependency updates, bug fixes, stability improvements and ongoing maintenance.

---

## ✨ Features

* Compatible with GOG Galaxy 2.1+ (64-bit)
* Python 3.13 support
* Updated 64-bit dependencies
* Improved stability and compatibility
* Ongoing maintenance and bug fixes

---

## 📦 Installation

### Standard Installation (Recommended)

1. Close GOG Galaxy completely.
2. Download the latest release from this repository.
3. Open the following folder:

```text
%localappdata%\GOG.com\Galaxy\plugins\installed\
```

1. Extract the ZIP archive **directly into this folder**.

The resulting directory structure **must** look like this:

```text
%localappdata%\GOG.com\Galaxy\plugins\installed\
└── origin_7f53219b-4e2b-4591-9f4f-dfc5f4ba9eb0\
    ├── manifest.json
    ├── plugin.py
    ├── README.md
    └── ...
```

1. Start GOG Galaxy.

---

## 🔄 Resetting the Plugin Database (Recommended)

If the plugin behaves unexpectedly after an update, resetting the local plugin database is recommended.

1. Open `C:\ProgramData\GOG.com\Galaxy\storage\plugins\` and find the files starting with `origin_` and ending in `-storage.db`.
2. Rename each by appending `.old` (e.g. `origin_xxxxxxxxx-storage.db` -> `origin_xxxxxxxxx-storage.db.old`).
3. Start GOG Galaxy again and reconnect the EA app (Origin) integration if necessary.

### 🚀 First Start and Initial Sync (Important)

For a clean first run after installing or updating the plugin:

1. Close GOG Galaxy.
2. Open this folder:

```text
C:\ProgramData\GOG.com\Galaxy\storage\plugins\
```

1. If an `origin_...-storage.db` file exists there, delete it.
2. Start GOG Galaxy.
3. Start EA app and keep it open.
4. In GOG Galaxy, open the account menu (top-right) and click **Sync integrations**.
5. Wait until sync finishes.

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
