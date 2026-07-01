## Version 2.1.2-64bit (experimental, untested)

### Fixed
- **`backend.py` - entitlements query, cross-platform linked games:** Removed the `ownershipMethod: [PURCHASE, REDEMPTION, ENTITLEMENT_GRANT]` filter from `_ENTITLEMENTS_QUERY`. This filter restricted the entitlements response to only those three ownership methods and could silently exclude games owned through a linked third-party storefront (for example, a Steam-purchased title such as Mass Effect Legendary Edition that shows up in the EA app despite not being purchased there). EA classifies linked-account entitlements under ownership methods outside that allowlist, so the filter risked dropping them from the query before they ever reached `get_offers` or the local install-check logic. This matches the unfiltered query used in the working reference fix for the FriendsOfGalaxy / BellezaEmporium EA app integration.

---

## Version 2.1.1-64bit (experimental, untested)

### Changed
- **`plugin.py` / `backend.py` - auth flow:** Replaced `client_id=JUNO_PC_CLIENT` with `client_id=EADOTCOM-WEB-SERVER`. The Juno PC Client ID is restricted to the physical EA Desktop client and strictly triggers an anti-fraud device verification (`pc_sign is missing` error). Since generating a fake `pc_sign` bypasses EA's security measures, this version switches to the web-based Client ID (`EADOTCOM-WEB-SERVER` with `display=junoWeb/login` and `redirect_uri=https://www.ea.com/login_check`). This relies on the standard OAuth2 authorization-code flow without device signatures.

---

## Version 2.1.0-64bit (experimental, untested)

### Overview
Origin as a service was sunset by EA in April 2025, breaking the old Origin SPA login flow (`client_id=ORIGIN_SPA_ID`) with a "Service limitations apply" error. This version switches the login flow to EA's current "EA Desktop" / Juno authentication endpoint. The downstream API calls in `OriginBackendClient` (entitlements, friends, subscriptions, etc.) still target the legacy Origin REST API and were **not** touched in this version - they may or may not still work and are expected to need a follow-up migration once login itself is confirmed working.

### Changed
- **`plugin.py` - auth flow:** Replaced the Origin SPA `web_session` parameters (`client_id=ORIGIN_SPA_ID`, `originXWeb/login`) with the EA Desktop / Juno equivalent (`client_id=JUNO_PC_CLIENT`, `display=junoClient/login`, `redirect_uri=qrc:///html/login_successful.html`). No device signature (`pc_sign`) is sent.
- **`plugin.py` - credential flow:** Switched from cookie-based re-authentication to OAuth2 authorization-code exchange, with refresh-token-based silent re-login on subsequent starts (`authenticate`, `pass_login_credentials`, `_do_authenticate`).
- **`backend.py` - `AuthenticatedHttpClient`:** Replaced the cookie-jar/token-via-cookies mechanism with `authenticate_with_code` (authorization_code grant) and `authenticate_with_refresh_token` (refresh_token grant) against `https://accounts.ea.com/connect/token`. Removed the now-unused custom `CookieJar`.

### Known unknowns
- The exact parameters and response shape of the `/connect/token` endpoint for the Juno client are not independently verified against a working reference implementation - the request needs a live test run to confirm it behaves as expected.
- Whether EA's Juno endpoint requires a `pc_sign` parameter unconditionally is unknown until tested; if so, this version will fail at the authorization-code step with an explicit `pc_sign is missing`-style error rather than the old generic "Service limitations apply".

---

## Version 2.0.0-64bit

### Overview
Initial 64-bit port of the Origin (EA app) integration for **GOG Galaxy 2.1+** running on **Python 3.13**. All third-party dependencies were moved out of the plugin ROOT into `/modules/` and resolved as 64-bit (`cp313-win_amd64`) packages via `melcom's Galaxy Plugin Scout`. Plugin manifest updated to display as **"Galaxy EA app plugin"** in the GOG Galaxy client.

### Added
- **`/modules/` dependency layout:** All third-party libraries relocated out of the plugin ROOT into `/modules/`, matching the layout used by the other 64-bit plugins in this toolkit.

### Changed
- **`plugin.py` – sys.path resolution:** Added a `sys.path` entry pointing at `/modules/` so vendored third-party dependencies (`aiohttp`, `galaxy`, `yarl`, etc.) can be imported correctly now that they no longer live in the plugin ROOT.
- **`manifest.json` – display name:** Renamed from "Galaxy Origin plugin" to **"Galaxy EA app plugin"** to match EA's current client branding. The internal `platform` identifier remains `origin`, as required by the GOG Galaxy SDK's `Platform.Origin` constant.
- **`manifest.json` – version scheme:** Adopted the `-64bit` version suffix convention used across the rest of the toolkit.

### Packages moved to `/modules/` (64-bit)
`aiohttp`, `async_timeout`, `attrs`, `certifi`, `chardet`, `galaxy_plugin_api`, `idna`, `multidict`, `typing_extensions`, `yarl`

---

## Version 0.40

- `get_local_size`: return `None` if map.crc not found instead of raising error
- fix detecting installed launcher & games when EA Desktop is installed

---

## Version 0.39

- update Galaxy API version to 0.68
- help with adding subscription games to user library when clicking Install
- add missing randomization to api[1-4].origin.com when fetching subscription games

---

## Version 0.38

- add ability to launch Origin games bought in external stores (#30 by @claushofmann + further changes)
- fix parsing games manifest files and handled files with invalid content
- refactor `get_subscription_games` and `get_game_library_settings`

---

## Version 0.37.1

- fix getting subscription with 'enable' status. Bug related with issue: (#18)

---

## Version 0.37

- rename Origin Access [Premium] to EA Play [Pro]
- fix crash if ProgramData is undefined in Environmental variables (#23 by @NathanaelA)

---

## Version 0.36

- better handle installation status of games
- fix error on retrieving achievements for some games
- added support for local sizes

---

## Version 0.35

- added support for subscriptions

---

## Version 0.34.1

- add extended logging to find session expiration time mechanism

---

## Version 0.34

- fix rare bug while parsing game times (#16)
- fix handling status 400 with "login_error": go to "Credentials Lost" instead of "Offline. Retry"