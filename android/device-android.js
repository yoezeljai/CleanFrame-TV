/* Fire TV (Android) device adapter: replaces app/device.js in the Android build. */
(function () {
  'use strict';
  window.CleanFramePlatform = 'Fire TV';
  window.CleanFrameExtraApps = [{ id: 'amazonmusic', name: 'Amazon Music', mark: true, appId: 'com.amazon.bueller.music' }];
  // CleanFrame's home row stores Tizen app IDs; each maps to candidate Fire TV packages, first installed wins.
  var PACKAGES = {
    'org.tizen.netflix-app': ['com.netflix.ninja'],
    'evKhCgZelL.AmazonIgnitionLauncher2': ['com.amazon.firebat', 'com.amazon.avod'],
    'fiZNCxMH9Y.Hotstar': ['in.startv.hotstar', 'in.startv.hotstar.dplus.tv'],
    'Y6A54cEa22.AppleTV': ['com.apple.atve.amazon.appletv'],
    // SmartTube (ad-free YouTube client) first; the official app if it is removed.
    '9Ur5IzDKqV.TizenYouTube': ['org.smarttube.stable', 'com.amazon.firetv.youtube', 'com.google.android.youtube.tv'],
    'OGLLvqej7u.CrunchyrollWebApp': ['com.crunchyroll.crunchyroid'],
    'rJeHak5zRg.Spotify': ['com.spotify.tv.android'],
    'com.amazon.bueller.music': ['com.amazon.bueller.music']
  };
  var EXTRA_BRANDS = { 'com.spotify.tv.android': 'spotify' };
  var HIDDEN = /^(com\.amazon\.(tv\.launcher|tv\.settings|device\.|kso|dcp|vizzini|ftv\.)|com\.android\.|android$)/;
  function bridge() { return window.CleanFrameAndroid; }
  function unavailable(done) {
    done({ message: 'Open CleanFrame on the Fire TV to use this control.', detail: 'The web preview cannot control the Fire TV.' });
  }
  var installed = null;
  function installedApps() {
    if (!installed) { try { installed = JSON.parse(bridge().apps()); } catch (e) { installed = []; } }
    return installed;
  }
  function isInstalled(pkg) { return installedApps().some(function (a) { return a.id === pkg; }); }
  function resolve(id) {
    var list = PACKAGES[id];
    if (!list) return [id];
    var have = list.filter(isInstalled);
    return have.length ? have : list;
  }
  function launchApp(id, done) {
    if (!bridge()) { unavailable(done); return; }
    var ok = resolve(id).some(function (pkg) { return bridge().launch(pkg); });
    done(ok ? null : { message: 'The Fire TV could not open this app.', detail: 'It may not be installed on this Fire TV.' });
  }
  function launch(brand, done) { done({ message: 'This app has no launch target.' }); }
  function art(done) { done({ message: 'Art Mode is not available on Fire TV.' }); }
  function home(done) {
    if (!bridge()) { unavailable(done); return; }
    done(bridge().fireHome() ? null : { message: 'The Fire TV could not open its home screen.' });
  }
  function settings(done) {
    if (!bridge()) { unavailable(done); return; }
    done(bridge().settings() ? null : { message: 'The Fire TV could not open Settings.' });
  }
  function apps(done) {
    if (!bridge()) { unavailable(done); return; }
    installed = null;
    var primary = {}, result = [];
    Object.keys(PACKAGES).forEach(function (id) { PACKAGES[id].forEach(function (pkg) { primary[pkg] = id; }); });
    installedApps().forEach(function (a) {
      if (primary[a.id] || HIDDEN.test(a.id)) return;
      result.push({ appId: a.id, name: a.name, brand: EXTRA_BRANDS[a.id] || '', icon: '', rank: 30 });
    });
    result.sort(function (a, b) { return a.name.toLowerCase().localeCompare(b.name.toLowerCase()); });
    done(null, result);
  }
  window.FrameDevice = { launch: launch, launchApp: launchApp, art: art, home: home, settings: settings, apps: apps };
}());
