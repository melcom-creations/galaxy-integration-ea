# Changelog

All notable changes to this plugin will be documented in this file.

---

## Version 2.0.5-64bit

### Fixed in Version 2.0.5-64bit

- **`plugin.py` – game time cache:** Fixed a crash in `handshake_complete()` where `GameTime` (a dataclass) was passed directly to `json.dumps()` when persisting the game-time cache, raising `TypeError: Object of type GameTime is not JSON serializable` on every startup. Cache entries are now converted with `dataclasses.asdict()` before serialization.

---

## Version 2.0.4-64bit

### Overview for Version 2.0.4-64bit

Maintenance release focused on startup dependency bootstrap reliability. The module loader now resolves bundled dependency paths more robustly across folder-name casing and path normalization edge cases.

### Fixed in Version 2.0.4-64bit

- Fixed module loader to locate the bundled modules directory regardless of folder name casing (modules, Modules, etc.).
- Hardened startup dependency bootstrap with normalized absolute path handling and duplicate `sys.path` protection, improving reliability of `from galaxy.api...` imports in edge-case runtime setups.

### Technical Breakdown for Version 2.0.4-64bit

#### 1. Module folder casing tolerance

The loader now resolves common casing variants of the dependency folder, preventing startup import failures caused by packaging differences.

#### 2. Normalized path insertion

Dependency paths are normalized and de-duplicated before insertion into `sys.path`, reducing import-order and duplicate-entry issues.

---

## Version 2.0.3-64bit

### Fixed in Version 2.0.3-64bit

- **`backend.py` – cross-platform entitlements:** Removed the `ownershipMethod: [PURCHASE, REDEMPTION, ENTITLEMENT_GRANT]` filter from `_ENTITLEMENTS_QUERY`. This filter silently excluded games linked from third-party storefronts (e.g. Mass Effect: Legendary Edition purchased via Steam and linked to an EA account), because EA classifies such linked-account entitlements under ownership methods outside that allowlist.

### Changed in Version 2.0.3-64bit

- **`ea_device_sign.py`** replaces `pcsign_hash.py`. Inspired by BellezaEmporium's `galaxy-integration-ead`. Renamed, restructured, and modernized: the hardware fallback now uses PowerShell `Get-CimInstance` instead of the deprecated `wmic` command-line tool.

---

## Version 2.0.2-64bit

### Changed in Version 2.0.2-64bit

- **`plugin.py` / `backend.py` – auth flow:** Switched `client_id` from `JUNO_PC_CLIENT` to `EADOTCOM-WEB-SERVER`. The Juno PC Client ID is restricted to the EA Desktop client and requires a device signature. The web-based client ID uses the standard OAuth2 authorization-code flow (`display=junoWeb/login`, `redirect_uri=https://www.ea.com/login_check`) without device signatures.

---

## Version 2.0.1-64bit

### Overview for Version 2.0.1-64bit

The Origin SPA login flow (`client_id=ORIGIN_SPA_ID`) was broken by EA's April 2025 Origin sunset, showing a "Service limitations apply" error. This version migrates the login flow to EA's current Juno authentication endpoint.

### Changed in Version 2.0.1-64bit

- **`plugin.py` – auth flow:** Replaced Origin SPA parameters with the EA Desktop / Juno equivalent (`client_id=JUNO_PC_CLIENT`, `display=junoClient/login`, `redirect_uri=qrc:///html/login_successful.html`).
- **`plugin.py` – credential flow:** Switched from cookie-based re-authentication to OAuth2 authorization-code exchange with refresh-token-based silent re-login on subsequent starts.
- **`backend.py` – `AuthenticatedHttpClient`:** Replaced cookie-jar/token-via-cookies with `authenticate_with_code` (authorization_code grant) and `authenticate_with_refresh_token` (refresh_token grant) against `https://accounts.ea.com/connect/token`.

---

## Version 2.0.0-64bit

### Overview for Version 2.0.0-64bit

Initial 64-bit port of the Origin (EA app) integration for **GOG Galaxy 2.1+** running on **Python 3.13**. All third-party dependencies moved to `/modules/` and resolved as 64-bit (`cp313-win_amd64`) packages via melcom's Galaxy Plugin Scout. Plugin manifest updated to display as **"Galaxy EA app plugin"** in the GOG Galaxy client.

### Added in Version 2.0.0-64bit

- **`/modules/` dependency layout:** All third-party libraries relocated from the plugin ROOT into `/modules/`.

### Changed in Version 2.0.0-64bit

- **`plugin.py` – sys.path resolution:** Added a `sys.path` entry pointing at `/modules/` for vendored dependency imports.
- **`manifest.json` – display name:** Renamed from "Galaxy Origin plugin" to **"Galaxy EA app plugin"** to match EA's current client branding. The internal `platform` identifier remains `origin`, as required by the GOG Galaxy SDK.
- **`manifest.json` – version scheme:** Adopted the `-64bit` version suffix convention.

### Packages moved to `/modules/` (64-bit) in Version 2.0.0-64bit

`aiohttp`, `async_timeout`, `attrs`, `certifi`, `chardet`, `galaxy_plugin_api`, `idna`, `multidict`, `typing_extensions`, `yarl`

---

## Version 0.40

- `get_local_size`: return `None` if map.crc not found instead of raising error
- Fix detecting installed launcher & games when EA Desktop is installed

---

## Version 0.39

- Update Galaxy API version to 0.68
- Help with adding subscription games to user library when clicking Install
- Add missing randomization to api[1-4].origin.com when fetching subscription games

---

## Version 0.38

- Add ability to launch Origin games bought in external stores (#30 by @claushofmann)
- Fix parsing games manifest files; handle files with invalid content
- Refactor `get_subscription_games` and `get_game_library_settings`

---

## Version 0.37.1

- Fix getting subscription with 'enable' status (#18)

---

## Version 0.37

- Rename Origin Access [Premium] to EA Play [Pro]
- Fix crash if ProgramData is undefined in environment variables (#23 by @NathanaelA)

---

## Version 0.36

- Better handle installation status of games
- Fix error on retrieving achievements for some games
- Added support for local sizes

---

## Version 0.35

- Added support for subscriptions

---

## Version 0.34.1

- Add extended logging to find session expiration time mechanism

---

## Version 0.34

- Fix rare bug while parsing game times (#16)
- Fix handling status 400 with "login_error": go to "Credentials Lost" instead of "Offline. Retry"
