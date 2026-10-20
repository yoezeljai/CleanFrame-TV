# TV and test status

## Handoff checkpoint — 20 October 2026

CleanFrame 0.6.1 was signed, installed in place and launched on 20 October. This update includes the grouped two-pane Settings and the integrated wallpaper picker. The TV reported `install completed`, retained the application in its installed list and returned `successfully launched`. This confirms installation and the launch command; physical rendering and remote feel need Nathan's observation. The application identity and author certificate are unchanged. No native Home/startup configuration commands were run. The original configuration snapshot and previous signed 0.6.0 package remain available locally.

## Device

- Samsung 55-inch The Frame, model QA55LS03DAWXXY (LS03D).
- Firmware shown in Nathan's photos: T-PTMDUABC-0090-2130.0.
- Live developer capability response: Tizen 9.0, ARMv7 / 32-bit ARM.
- Developer Mode enabled. The developer connection required a full mains power cycle after enabling it.

The network address and device identifier are local configuration, excluded from Git.

## Verified on 19 October 2026

1. Samsung SDB connects to the TV and reads its application list.
2. Netflix opens from a developer launch command, visually confirmed by Nathan.
3. The custom widget installs with Samsung-issued author and public distributor certificates and Samsung's official Tizen CLI signing.
4. The TV lists and opens the installed app, **Frame Home Test**.
5. Nathan confirmed the custom interface appears and launches both Netflix and YouTube using the normal remote.

## Existing identity

- Package: `nClrkHome1`
- Application: `nClrkHome1.FrameHome`
- Installed display name: `CleanFrame` (0.6.1; previously `Frame Home Test`)

Netflix uses `org.tizen.netflix-app`. YouTube first uses `9Ur5IzDKqV.TizenYouTube`, with `com.samsung.tv.cobalt-yt` as a fallback. These identifiers came from this TV's installed-app list.

## 0.2.0 installation — 19 October 2026

- Signed with the existing Samsung certificate; identity unchanged.
- The TV reported `install completed`, listed the same application ID, and reported a successful launch.
- The widget now contains Shore and List, bundled fonts/photos/icons, saved preferences, the app editor and real Tizen device actions.
- Browser checks passed for utility placement, focus restoration, persisted preferences and honest device-unavailable states. Device-adapter contract checks passed for app discovery, real call routing and failure handling.
- Nathan confirmed the 0.2.0 app and settings work, and Other apps opens. Nathan reported poor Shore responsiveness in both dock and settings and unwanted system apps in the catalogue. Art Mode and native Samsung screen destinations remain unconfirmed.

## Device actions awaiting visual confirmation

- All nine agreed streaming apps have IDs confirmed from this TV. The previous test visually confirmed Netflix and YouTube; this update uses the same public launch API.
- Native Art Mode uses an app-control launch with `mode=fullscreen`; its exact behaviour on this firmware remains to be checked.
- Samsung Home and TV settings use installed system-app IDs; the visible destinations need checking.
- Other apps reads the TV's visible app list. The returned list and return-focus behaviour need an on-device remote check.

Nathan explicitly resumed power-on startup work on 19 October 2026 after confirming the interface works well. Startup testing is now in scope. Nathan subsequently requested native Home-button routing and returning from streaming apps on exit/Back. See the native Home integration status below; physical remote and power-on checks are tracked separately from native setting readback.

## 0.3.0 — Shore performance and catalogue revision

- Both themes show a small 12-hour clock without AM/PM, refreshed on each minute and resume.
- Nine packaged wallpapers: eight from the requested Downloads set plus Golden Hour. Backgrounds are 1920px wide; picker thumbnails are 512px wide and only load when opened.
- Glass optics and settings blur are pre-rendered on the Mac. The TV no longer loads the optical module or uses live backdrop blur. Logo ink bounds are measured at build time, rather than reading canvases during TV startup.
- Dock movement uses matched 180ms transform animations and small compositor layers. The CPU-throttled browser benchmark measured about 214/216ms to settle in either direction, versus 348/348ms for 0.2.0. These are browser timings, not measurements from the TV.
- The catalogue filter was checked against 534 app entries read from this TV. It retains 23 consumer apps, with the nine agreed apps first and other streaming services next; EP packages, services, ad players and account utilities are excluded.
- Fourteen browser interaction checks passed, including gallery scrolling, photo selection/rotation, theme switching, clock format and absence of live glass/backdrop filters.
- The TV confirmed in-place installation and launch of 0.3.0. The signed package was checked against the current runtime source. Nathan confirmed that the updated app works extremely well. Default startup and Home routing were unchanged in 0.3.0.

## 0.4.0 — focus refinement and startup investigation

- Shore's selected app has a static light falloff, a soft edge and shadow, and a small logo lift. Movement keeps the same 180ms transform path; no live blur or optical filter was added.
- List's clock is now aligned to the top-right safe edge. Shore's utility icons retain their focus fill without the white inset outline.
- Five browser checks passed for focus styling, returning from utilities to the selected app, List clock position and browser errors. At 4x CPU slowdown, the dock settled in about 215ms right / 214ms left, with a maximum 17ms frame gap. These are browser timings.
- The TV confirmed in-place installation and launch of 0.4.0 using the same identity and certificate. Visual confirmation of these small refinements is pending.
- Samsung's current support guide describes Start with Smart Hub Home; disabling it resumes the last-used source. Older menus can also expose Autorun Last App. Neither description establishes a fixed custom launcher when a streaming app was last used. The actual menu and power-cycle result still need checking on this firmware.
- The local TV information endpoint reports the model and current power state. At the UI-only 0.4.0 installation, no startup helper or Home routing change had been applied. The later native Home integration is recorded below.

Startup sources:
- [Samsung start screen options](https://www.samsung.com/sg/support/tv-audio-video/enable-or-disable-the-start-screen-option-on-your-2025-samsung-smart-tv/)
- [Samsung web-app configuration](https://developer.samsung.com/smarttv/develop/guides/fundamentals/configuring-tv-applications.html)
- [Prelaunching is background loading, and is unsupported on 2019 and newer TVs](https://developer.samsung.com/smarttv/develop/guides/fundamentals/prelaunching-applications.html)

## Native Home integration — 19 October 2026

- Nathan's photo confirmed Start with Smart Hub Home on, Autorun Last App off, and Samsung TV Plus autorun off. Nathan switched the first off and the second on, then confirmed that a full off/on returned to CleanFrame when CleanFrame was the last-used app. That establishes last-app resume only.
- A bounded read-only probe ran as UID 901 (SDK), without root. It confirmed Tizen 9.0.0 ARMv7, firmware 2130.0, the required native libraries and .NET 6 runtime. The native API reports CleanFrame is eligible for app booting.
- The guarded native helper uses `app_operation_set_current_app` for the main Home operation, plus native `vconf_set_str` / `vconf_set_int` for the Home app ID and autostart. It uses no direct database writes, root acquisition, security-policy changes or resident service.
- Original typed settings and the native Home assignment were captured in ignored `.local/native-home/original.json`. Apply, exact-value restore/readback and reapply passed as the SDK user. Current readback names CleanFrame for Home, startup and boot-backup, with Home autostart enabled. The first-screen type still names Samsung Home.
- Nathan confirmed that the physical Home button from Netflix returns to CleanFrame. Netflix stays in its own app on repeated Back, so an exit destination was not observed. Nathan tentatively reported startup after Netflix returned to CleanFrame; treat that as provisional. Settings → Samsung Home did not visibly work with the earlier CoBA component target; the original CSFS target is now under test.
- The prepared local restore command is `python3 .local/native-home/run.py restore`. It re-stages the compiled helper and saved original values if temporary files were cleared. Restore Home/startup before uninstalling CleanFrame or changing its stable identity.
- Because Home now points to CleanFrame, the native Home autostart setting is intentionally on. This differs from the earlier last-app-resume trial. Do not apply the earlier toggle instructions again without checking the current assignment.

Implementation references: [S90D firmware 2130 native Home work](https://github.com/splitcipher/couchroot/blob/83906b468836869933012da03a4018fb339462b3/docs/devices/s90d/README.md) and its native API helper. That is a different TV model; the Frame's compatibility and settings above were checked directly. The exact Home and Back destinations still need the physical tests listed above.

## 0.5.0 — three layouts and Samsung Home escape correction

- Claude Opus 5.5 at extra-high effort created and revised Glass Grid after Nathan's margin/gutter feedback. The revised composition uses 112px side margins, 56px gutters, nine 528 x 232px tiles and 32px radii. Its standalone study reported 50 passing interaction checks and documented Taste exceptions for the requested glass, clock and TV stage.
- Integrated into the shared app, with the same curated app order/editor, real device actions, wallpaper picker and rotation. The names are List, Glass Dock and Glass Grid. A tick replaces Current in the chooser, and the stored `shore` preference remains compatible.
- Twenty-eight integrated browser checks passed for grid navigation/boundaries, single focus, utility return, three-way selection/tick, List clock placement, Dock navigation, persistence, all nine matching wallpaper material pairs, 1280 x 720 scaling and recovery from invalid preferences. No browser errors were reported. Dock timings remained about 216/214ms right/left at 4x browser CPU slowdown. The new Grid has not yet been timed on the TV.
- Samsung Home now explicitly launches `com.samsung.tv.csfs`, the original Home app verified by the native query. The CoBA subcomponent target did not visibly open Smart Hub. Physical confirmation of the updated escape action is pending.
- The TV reported successful in-place 0.5.0 installation and launch. Native readback after installation still names CleanFrame for Home/startup/boot-backup, with autostart 1. The original snapshot and tested rollback remain available. Power-on using Nathan's usual viewing/Art Mode routine is awaiting a definite result.
- Maintained native helper source is in `scripts/native-home/`; compiled SDK tools, original values and diagnostic results stay in ignored `.local/native-home/`.


## 0.6.0 — appearance builder, fonts and expanded gallery

- List and Dock share independent background, app display, font, Home-control display, focus and material choices. Home controls use the selected family, including Newsreader. Settings and editing panels retain Manrope.
- The dedicated editor applies membership changes and completed moves immediately, with Recently removed and session Undo. It preserves one to nine Home apps, real installed-app IDs and legacy preferences.
- Fifteen bundled images include the six new supplied wallpapers. Six font choices include three private Pangram families injected only into Nathan's local package. Public source includes Manrope, Geist and Newsreader.
- 124 browser acceptance checks, 40 CPU-throttled performance checks and 318 unsigned-package checks passed. New-image chrome and app-label contrast studies are recorded in the release report. These are browser/package evidence, not a TV benchmark or accessibility certification.
- Signed widget SHA-256: `0b8fa8510ff2a8f46d8c8290c44eac725d16b57a2b7bac2bdb9ce4b35b8b4952`; 16,155,563 bytes. All 148 applicable source files matched the signed archive byte for byte.
- The TV confirmed installation and launch. Physical rendering, the lightest fonts, the expanded catalogue and remote feel remain to be observed by Nathan. No startup helper was invoked, and the original native configuration snapshot remains intact.

Detailed local validation reports remain outside the public source.

## 0.6.1 — spacious Settings and integrated wallpaper selection

- Settings now opens a grouped overview and spacious two-pane choice screens. Arrows browse, OK applies, and adjacent checkmarks identify the applied choice. Back retains completed changes and restores category/choice focus.
- Wallpaper keeps the Settings frame, with six visible thumbnail rows and a stationary Home preview. Browsing waits 200ms for focus to settle, keeps the applied backdrop, and never saves. OK applies in place; Back restores the latest applied photo and cancels pending work.
- The final runtime passed 350 browser acceptance checks and 40 browser performance checks before packaging. Source validation passed after the version-only change. All 148 applicable runtime source files and eight font-overlay entries match the signed archive exactly. The six private font files are present.
- Signed widget SHA-256: `2e30923598ac3cda81d13802f80f5ea63d1306d50e1c437379589833a7146c6c`; 16,159,512 bytes. The author certificate matches the previously installed 0.6.0 package.
- The TV reported `install completed`, the installed-app list retained `nClrkHome1.FrameHome`, and the launch command returned `successfully launched`. These are device command confirmations, not visual or remote verification. The install script did not alter native Home/startup settings.

Local package evidence is retained privately in `.local/qa/`. These records describe the prior installation; the public-source cleanup did not contact the TV.
