/* CleanFrame Tizen 3.0 compatibility runtime.
   Samsung's 2017 TV web engine (Chromium 47) has no CSS custom properties and no
   flexbox `gap`. scripts/build-tizen3.py splits style.css into plain chunks and
   "slots": rules that use var(), define --properties or set gap. This file
   resolves those slots against the live DOM and rewrites only the slots whose
   resolved text changed. ES5 only. */
(function () {
  'use strict';
  var D = window.CF_CSS, anchor = document.currentScript, nativeGCS = window.getComputedStyle.bind(window);
  var EMPTY = Object.create(null), pass = 0, dirty = true, running = false, ready = false, queued = false;
  var styleOf = {}, cssOf = {}, tokenEls = [], gapKids = [], gapMarked = [];

  D.chunks.forEach(function (c) {
    var st = document.createElement('style');
    if (typeof c === 'string') st.textContent = c;
    else styleOf[c] = st;
    anchor.parentNode.insertBefore(st, anchor);
  });
  var defSlots = [], varSlots = [], gapSlots = [];
  D.slots.forEach(function (s, i) {
    s.order = i;
    if (s.defs) defSlots.push(s);
    if (s.vars) varSlots.push(s);
    if (s.gap) gapSlots.push(s);
  });

  function cmp(a, b) {
    if (a.imp !== b.imp) return a.imp ? 1 : -1;
    for (var i = 0; i < 3; i++) if (a.spec[i] !== b.spec[i]) return a.spec[i] - b.spec[i];
    return a.order - b.order;
  }
  function all(sel) { try { return document.querySelectorAll(sel); } catch (e) { return []; } }
  var mediaCache = {};
  function mediaOk(m) {
    if (!m) return true;
    if (!(m in mediaCache)) mediaCache[m] = window.matchMedia(m).matches;
    return mediaCache[m];
  }

  function topComma(s) {
    for (var i = 0, d = 0; i < s.length; i++) {
      var ch = s.charAt(i);
      if (ch === '(') d++; else if (ch === ')') d--; else if (ch === ',' && !d) return i;
    }
    return -1;
  }
  /* Substitutes var() references; null means invalid at computed-value time. */
  function subst(v, get, depth) {
    var i = v.indexOf('var(');
    if (i < 0) return v;
    if (depth > 24) return null;
    var out = '', pos = 0;
    while (i >= 0) {
      out += v.slice(pos, i);
      var j = i + 4, d = 1;
      while (j < v.length && d) { var ch = v.charAt(j); if (ch === '(') d++; else if (ch === ')') d--; j++; }
      var inner = v.slice(i + 4, j - 1), c = topComma(inner);
      var val = get((c < 0 ? inner : inner.slice(0, c)).trim());
      if (val == null) {
        if (c < 0) return null;
        val = subst(inner.slice(c + 1).trim(), get, depth + 1);
        if (val == null) return null;
      }
      out += val; pos = j; i = v.indexOf('var(', pos);
    }
    return out + v.slice(pos);
  }

  /* Custom properties per element, inherited through the prototype chain. */
  function vars(el) {
    if (!el || el.nodeType !== 1) return EMPTY;
    if (el.__cfvp === pass) return el.__cfv;
    var parent = vars(el.parentNode), list = el.__cfp === pass ? el.__cfd : null, inline = el.__cfInline, out = parent;
    if (list || inline) {
      var raw = Object.create(null), seen = Object.create(null), busy = Object.create(null), k;
      if (list) list.sort(cmp);
      var apply = function (imp) {
        if (list) list.forEach(function (d) { if (d.imp === imp) d.slot.defs.forEach(function (p) { if (!!p[2] === imp) raw[p[0]] = p[1]; }); });
      };
      apply(false);
      if (inline) for (k in inline) raw[k] = inline[k];
      apply(true);
      var own = function (name) {
        if (name in seen) return seen[name];
        if (busy[name]) return null;
        busy[name] = true;
        var r = subst(raw[name], get, 0);
        busy[name] = false;
        return (seen[name] = r);
      };
      var get = function (name) { return name in raw ? own(name) : parent[name] == null ? null : parent[name]; };
      out = Object.create(parent);
      for (k in raw) out[k] = own(k);
    }
    el.__cfvp = pass; el.__cfv = out;
    return out;
  }
  function getter(m) { return function (n) { return m[n] == null ? null : m[n]; }; }

  function indexDefs() {
    defSlots.forEach(function (s) {
      if (!mediaOk(s.media)) return;
      s.sels.forEach(function (sel) {
        var els = all(sel.s);
        for (var i = 0; i < els.length; i++) {
          var el = els[i];
          if (el.__cfp !== pass) { el.__cfp = pass; el.__cfd = []; }
          el.__cfd.push({ slot: s, spec: sel.spec, imp: false, order: s.order });
          if (s.defs.some(function (p) { return p[2]; })) el.__cfd.push({ slot: s, spec: sel.spec, imp: true, order: s.order });
        }
      });
    });
  }

  function declText(s, m) {
    var g = getter(m), text = '';
    s.vars.forEach(function (d) {
      var v = subst(d[1], g, 0);
      text += d[0] + ':' + (v == null ? 'unset' : v) + (d[2] ? '!important' : '') + ';';
    });
    return text;
  }

  function writeVarSlots(touched) {
    varSlots.forEach(function (s) {
      var css = '';
      if (mediaOk(s.media)) s.sels.forEach(function (sel, si) {
        var els = all(sel.s), groups = {}, keys = [], i, el, text;
        for (i = 0; i < els.length; i++) {
          el = els[i]; text = declText(s, vars(el));
          if (!groups[text]) { groups[text] = []; keys.push(text); }
          groups[text].push(el);
        }
        if (keys.length === 1) css += sel.full + '{' + keys[0] + '}';
        else keys.forEach(function (text, gi) {
          var token = 'c' + s.order + '-' + si + '-' + gi;
          groups[text].forEach(function (el) {
            if (el.__cftp !== pass) { el.__cftp = pass; el.__cft = []; touched.push(el); }
            el.__cft.push(token);
          });
          css += sel.s + '[data-cf~="' + token + '"]' + sel.pe + '{' + text + '}';
        });
      });
      if (s.media && css) css = '@media ' + s.media + '{' + css + '}';
      if (cssOf[s.order] !== css) { cssOf[s.order] = css; styleOf[s.order].textContent = css; }
    });
  }

  function writeTokens(touched) {
    tokenEls.concat(touched).forEach(function (el) {
      var want = el.__cftp === pass ? el.__cft.join(' ') : '';
      if ((el.getAttribute('data-cf') || '') !== want) {
        if (want) el.setAttribute('data-cf', want); else el.removeAttribute('data-cf');
      }
    });
    tokenEls = touched;
  }

  var SIDE = { row: 'marginLeft', 'row-reverse': 'marginRight', column: 'marginTop', 'column-reverse': 'marginBottom' };
  function px(v, cs) {
    var n = parseFloat(v);
    if (isNaN(n)) return 0;
    if (/em$/.test(v) && !/rem$/.test(v)) return n * parseFloat(cs.fontSize);
    return n;
  }
  function autoMargin(el, side) {
    return D.autoMargins.some(function (r) {
      return r.sides.indexOf(side) >= 0 && mediaOk(r.media) && r.sels.some(function (sel) { try { return el.matches(sel); } catch (e) { return false; } });
    });
  }
  var END = { marginLeft: 'marginRight', marginRight: 'marginLeft', marginTop: 'marginBottom', marginBottom: 'marginTop' };
  function dashed(prop) { return prop.replace(/[A-Z]/g, function (c) { return '-' + c.toLowerCase(); }); }
  function inFlow(cs) { return cs.display !== 'none' && cs.position !== 'absolute' && cs.position !== 'fixed'; }
  function hasContent(cs) { return cs.content && cs.content !== 'none' && cs.content !== 'normal'; }
  /* Flex items in order: ::before, element children, non-blank text runs, ::after. */
  function flexItems(box) {
    var items = [], node, pcs;
    pcs = nativeGCS(box, '::before');
    if (hasContent(pcs) && inFlow(pcs)) items.push({ pe: '::before', cs: pcs });
    for (node = box.firstChild; node; node = node.nextSibling) {
      if (node.nodeType === 1) { var kcs = nativeGCS(node); if (inFlow(kcs)) items.push({ el: node, cs: kcs }); }
      else if (node.nodeType === 3 && /\S/.test(node.nodeValue)) {
        if (!items.length || !items[items.length - 1].text) items.push({ text: true });
      }
    }
    pcs = nativeGCS(box, '::after');
    if (hasContent(pcs) && inFlow(pcs)) items.push({ pe: '::after', cs: pcs });
    return items;
  }
  var gapStyle = document.createElement('style'), gapCss = '';
  anchor.parentNode.insertBefore(gapStyle, anchor);
  /* Emulates flex gap with a margin between each pair of adjacent flex items. Element
     items get inline margins; pseudo-elements get rules keyed by data-cfg; a text run
     can't take a margin, so its neighbour takes it on the facing side. */
  function applyGaps() {
    var boxes = [];
    gapSlots.forEach(function (s) {
      if (!mediaOk(s.media)) return;
      s.sels.forEach(function (sel) {
        var els = all(sel.s);
        for (var i = 0; i < els.length; i++) {
          var el = els[i], v = subst(s.gap[0], getter(vars(el)), 0), c = { imp: s.gap[1], spec: sel.spec, order: s.order, v: v };
          if (v == null) continue;
          if (el.__cfgp !== pass) { el.__cfgp = pass; el.__cfg = c; boxes.push(el); }
          else if (cmp(el.__cfg, c) <= 0) el.__cfg = c;
        }
      });
    });
    gapKids.forEach(function (k) { k.el.style[k.prop] = k.orig; });
    if (gapCss) gapStyle.textContent = '';
    var plan = [], rules = '', marked = [];
    boxes.forEach(function (box, bi) {
      var cs = nativeGCS(box), side = SIDE[cs.flexDirection];
      if ((cs.display !== 'flex' && cs.display !== 'inline-flex') || !side) return;
      var parts = box.__cfg.v.trim().split(/\s+/), gap = px(side === 'marginTop' || side === 'marginBottom' ? parts[0] : parts[1] || parts[0], cs);
      var items = flexItems(box), token = 'g' + bi;
      var give = function (item, prop) {
        if (item.text) return false;
        if (item.el && autoMargin(item.el, prop)) return true;
        var v = (parseFloat(item.cs[prop]) || 0) + gap + 'px';
        if (item.el) plan.push({ el: item.el, prop: prop, orig: item.el.style[prop], v: v });
        else {
          rules += '[data-cfg="' + token + '"]' + item.pe + '{' + dashed(prop) + ':' + v + '!important}';
          if (marked.indexOf(box) < 0) marked.push(box);
        }
        return true;
      };
      for (var i = 1; i < items.length; i++) give(items[i], side) || give(items[i - 1], END[side]);
      if (marked[marked.length - 1] === box) box.__cfgt = token;
    });
    plan.forEach(function (k) { k.el.style[k.prop] = k.v; });
    gapMarked.forEach(function (box) { if (marked.indexOf(box) < 0) box.removeAttribute('data-cfg'); });
    marked.forEach(function (box) { if (box.getAttribute('data-cfg') !== box.__cfgt) box.setAttribute('data-cfg', box.__cfgt); });
    gapMarked = marked;
    if (rules) gapStyle.textContent = rules;
    gapCss = rules;
    gapKids = plan;
  }

  function compute() {
    pass++; mediaCache = {};
    indexDefs();
    var touched = [];
    writeVarSlots(touched);
    writeTokens(touched);
    applyGaps();
  }
  function relevant(recs) {
    for (var i = 0; i < recs.length; i++) if (!document.head || !document.head.contains(recs[i].target)) return true;
    return false;
  }
  function run() {
    if (running) return;
    running = true;
    try { mo.takeRecords(); compute(); } finally { running = false; dirty = false; queued = false; }
  }
  function later() {
    dirty = true;
    if (!queued && ready) { queued = true; Promise.resolve().then(function () { if (dirty) run(); }); }
  }
  /* Layout reads made right after a DOM change must see resolved styles. */
  function flush() { if (!running && (dirty || relevant(mo.takeRecords()))) run(); }

  var mo = new MutationObserver(function (recs) { if (relevant(recs)) later(); });
  mo.observe(document.documentElement, { subtree: true, childList: true, attributes: true, attributeFilter: D.attrs });
  document.addEventListener('focus', later, true);
  document.addEventListener('blur', later, true);
  window.addEventListener('resize', function () { mediaCache = {}; later(); });

  function wrap(proto, name) {
    var f = proto[name];
    proto[name] = function () { flush(); return f.apply(this, arguments); };
  }
  wrap(Element.prototype, 'getBoundingClientRect');
  wrap(Element.prototype, 'getClientRects');
  window.getComputedStyle = function () { flush(); return nativeGCS.apply(window, arguments); };
  ['offsetWidth', 'offsetHeight', 'offsetLeft', 'offsetTop'].forEach(function (name) {
    var d = Object.getOwnPropertyDescriptor(HTMLElement.prototype, name);
    if (d && d.get && d.configurable) Object.defineProperty(HTMLElement.prototype, name, { configurable: true, get: function () { flush(); return d.get.call(this); } });
  });

  window.CFVars = {
    set: function (el, name, value) {
      if (name.indexOf('--') !== 0) { el.style.setProperty(name, value); return; }
      (el.__cfInline || (el.__cfInline = {}))[name] = String(value).trim();
      later();
    },
    remove: function (el, name) {
      if (name.indexOf('--') !== 0) { el.style.removeProperty(name); return; }
      if (el.__cfInline && name in el.__cfInline) { delete el.__cfInline[name]; later(); }
    },
    refresh: run
  };
  document.addEventListener('DOMContentLoaded', function () { ready = true; run(); });
})();
