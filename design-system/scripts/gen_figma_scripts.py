#!/usr/bin/env python3
"""Generates use_figma Plugin-API scripts from figma-payload.json.

Outputs (design-system/scripts/figma/):
  01-variables.js  - collections + variables (idempotent: get-or-create by name)
  02-styles.js     - text styles (bound to font variables), effect styles (bound colors), grid styles

Run after build_tokens.py:  python3 -I design-system/scripts/gen_figma_scripts.py
"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "scripts", "figma")
os.makedirs(OUT, exist_ok=True)
P = json.load(open(os.path.join(ROOT, "figma-payload.json")))

VARS_DATA = {
    "ramps": P["ramps"], "base": P["base"], "alpha": P["alpha"], "semantic": P["semantic"],
    "spacing": P["spacing"], "radius": P["radius"], "size": P["size"],
    "typo": P["typo"], "typoModes": P["typoModes"], "motion": P["motion"],
}

VARS_JS = r"""
const D = __DATA__;
const hex = h => { h = h.replace('#',''); return { r: parseInt(h.slice(0,2),16)/255, g: parseInt(h.slice(2,4),16)/255, b: parseInt(h.slice(4,6),16)/255, a: h.length === 8 ? parseInt(h.slice(6,8),16)/255 : 1 }; };
const cols = await figma.variables.getLocalVariableCollectionsAsync();
const vars = await figma.variables.getLocalVariablesAsync();
const ids = {}; const report = {}; const notes = [];
function col(name, modes) {
  let c = cols.find(x => x.name === name);
  if (!c) { c = figma.variables.createVariableCollection(name); cols.push(c); }
  if (!modes.includes(c.modes[0].name)) c.renameMode(c.modes[0].modeId, modes[0]);
  const m = {};
  for (const mn of modes) { const f = c.modes.find(x => x.name === mn); m[mn] = f ? f.modeId : c.addMode(mn); }
  return { c, m };
}
function v(name, c, type) {
  let x = vars.find(y => y.name === name && y.variableCollectionId === c.id);
  if (!x) { x = figma.variables.createVariable(name, c, type); vars.push(x); }
  ids[name] = x.id; return x;
}
function web(x, s) { x.setVariableCodeSyntax('WEB', s); }

// Primitives (hidden from pickers + publishing; semantics alias them)
const pr = col('Primitives', ['Value']); pr.c.hiddenFromPublishing = true;
const primByName = {};
for (const [hue, ramp] of Object.entries(D.ramps)) for (const [step, h] of Object.entries(ramp)) {
  const x = v(`${hue}/${step}`, pr.c, 'COLOR'); x.setValueForMode(pr.m.Value, hex(h)); x.scopes = []; web(x, `var(--nk-${hue}-${step})`); primByName[`${hue}/${step}`] = x;
}
for (const [k, h] of Object.entries(D.base)) { const x = v(k, pr.c, 'COLOR'); x.setValueForMode(pr.m.Value, hex(h)); x.scopes = []; web(x, `var(--nk-${k})`); primByName[k] = x; }
for (const [k, h] of Object.entries(D.alpha)) { const x = v(`alpha/${k}`, pr.c, 'COLOR'); x.setValueForMode(pr.m.Value, hex(h)); x.scopes = []; web(x, `var(--nk-alpha-${k})`); primByName[`alpha/${k}`] = x; }
report.Primitives = pr.c.variableIds.length;

// Color (semantic, Light; Dark mode can be added later as a second mode)
const co = col('Color', ['Light']);
for (const [name, p, scopes, css] of D.semantic) {
  const target = primByName[p]; if (!target) throw new Error('missing primitive ' + p);
  const x = v(name, co.c, 'COLOR'); x.setValueForMode(co.m.Light, { type: 'VARIABLE_ALIAS', id: target.id }); x.scopes = scopes; web(x, css);
}
report.Color = co.c.variableIds.length;

// Spacing / Radius / Size
const sp = col('Spacing', ['Value']);
for (const [k, n] of Object.entries(D.spacing)) { const x = v(`spacing/${k}`, sp.c, 'FLOAT'); x.setValueForMode(sp.m.Value, n); x.scopes = ['GAP']; web(x, `var(--nk-spacing-${k})`); }
report.Spacing = sp.c.variableIds.length;
const ra = col('Radius', ['Value']);
for (const [k, n] of Object.entries(D.radius)) { const x = v(`radius/${k}`, ra.c, 'FLOAT'); x.setValueForMode(ra.m.Value, n); x.scopes = ['CORNER_RADIUS']; web(x, `var(--nk-radius-${k})`); }
report.Radius = ra.c.variableIds.length;
const sz = col('Size', ['Value']);
for (const [k, [n, scopes]] of Object.entries(D.size)) { const x = v(`size/${k}`, sz.c, 'FLOAT'); x.setValueForMode(sz.m.Value, n); x.scopes = scopes; web(x, `var(--nk-size-${k.replace(/\//g,'-')})`); }
report.Size = sz.c.variableIds.length;

// Typography (modes = script EN / RU·KZ; сейчас оба -> Onest)
const ty = col('Typography', D.typoModes);
// Archived variables (handwriting accent, 2026-11-06) are removed from the file
for (const x of vars.filter(y => y.variableCollectionId === ty.c.id && !(y.name in D.typo))) { notes.push('removed var ' + x.name); x.remove(); }
for (const [k, [type, vals, scopes]] of Object.entries(D.typo)) {
  const x = v(k, ty.c, type); for (const [mode, val] of Object.entries(vals)) x.setValueForMode(ty.m[mode], val); x.scopes = scopes; web(x, `var(--nk-${k.replace(/\//g,'-')})`);
}
report.Typography = ty.c.variableIds.length;

// Motion (TIMING/EASING types; skipped with a note if unsupported)
try {
  const mo = col('Motion', ['Value']);
  for (const [k, [type, val]] of Object.entries(D.motion)) {
    const x = v(`motion/${k}`, mo.c, type);
    if (type === 'TIMING') x.setValueForMode(mo.m.Value, val);
    else x.setValueForMode(mo.m.Value, { type: 'CUSTOM_CUBIC_BEZIER', easingFunctionCubicBezier: { x1: val[0], y1: val[1], x2: val[2], y2: val[3] } });
    web(x, `var(--nk-motion-${k.replace(/\//g,'-')})`);
  }
  report.Motion = mo.c.variableIds.length;
} catch (e) { notes.push('Motion skipped: ' + e.message); }

const all = await figma.variables.getLocalVariablesAsync();
const allScopes = all.filter(x => x.resolvedType !== 'BOOLEAN' && x.scopes.includes('ALL_SCOPES')).map(x => x.name);
const noSyntax = all.filter(x => !x.codeSyntax.WEB).map(x => x.name);
return { report, total: all.length, allScopesLeft: allScopes, missingWebSyntax: noSyntax, notes,
         collections: cols.map(c => ({ name: c.name, id: c.id, modes: c.modes.map(m => [m.name, m.modeId]) })), ids };
"""

STYLES_DATA = {"textStyles": P["textStyles"], "effects": P["effects"], "grids": P["grids"]}

STYLES_JS = r"""
const D = __DATA__;
const vars = await figma.variables.getLocalVariablesAsync();
const V = n => { const x = vars.find(y => y.name === n); if (!x) throw new Error('missing var ' + n); return x; };
// Load every font any mode can resolve to (FONT_FAMILY variables switch per mode)
const FAMILY = 'Onest';
const fonts = [...new Set(D.textStyles.map(t => t[2]))].map(st => [FAMILY, st]);
await Promise.all(fonts.map(([family, style]) => figma.loadFontAsync({ family, style })));
const existingT = await figma.getLocalTextStylesAsync();
const existingE = await figma.getLocalEffectStylesAsync();
const existingG = await figma.getLocalGridStylesAsync();
const out = { text: {}, effect: {}, grid: {}, removed: [] };


for (const [name, fam, style, size, lh, tr, tcase, desc] of D.textStyles) {
  let s = existingT.find(x => x.name === name) || figma.createTextStyle();
  s.name = name;
  s.fontName = { family: FAMILY, style };
  s.fontSize = size;
  s.lineHeight = { unit: 'PERCENT', value: lh };
  s.letterSpacing = { unit: 'PERCENT', value: tr };
  s.textCase = tcase || 'ORIGINAL';
  s.description = desc;
  s.setBoundVariable('fontFamily', V('font/body'));
  out.text[name] = s.id;
}

// Archived text styles (handwriting accent, 2026-11-06): consumers move to the replacement, then the style is removed
const ARCHIVED = { 'Accent/Note': 'Body/M' };
for (const s of existingT.filter(x => x.name in ARCHIVED)) {
  const repl = await figma.getStyleByIdAsync(out.text[ARCHIVED[s.name]]);
  for (const c of await s.getStyleConsumersAsync()) {
    if (c.node.type === 'TEXT') { for (const seg of c.node.getStyledTextSegments(['fontName'])) await figma.loadFontAsync(seg.fontName); await c.node.setTextStyleIdAsync(repl.id); out.removed.push('restyled ' + c.node.id); }
  }
  out.removed.push(s.name); s.remove();
}

for (const [name, spec] of Object.entries(D.effects)) {
  let s = existingE.find(x => x.name === name) || figma.createEffectStyle();
  s.name = name; s.description = spec.desc;
  s.effects = spec.shadows.map(([colorVar, x, y, blur, spread]) => {
    const base = { type: 'DROP_SHADOW', color: { r: 1, g: 1, b: 1, a: 1 }, offset: { x, y }, radius: blur, spread, visible: true, blendMode: 'NORMAL', showShadowBehindNode: false };
    return colorVar === 'white-raw' ? figma.variables.setBoundVariableForEffect(base, 'color', V('white')) : figma.variables.setBoundVariableForEffect(base, 'color', V(colorVar));
  });
  out.effect[name] = s.id;
}

for (const [name, g] of Object.entries(D.grids)) {
  let s = existingG.find(x => x.name === name) || figma.createGridStyle();
  s.name = name; s.description = g.desc;
  s.layoutGrids = [{ pattern: 'COLUMNS', alignment: 'STRETCH', count: g.count, gutterSize: g.gutter, offset: g.margin, visible: true, color: { r: 0, g: 0.38, b: 0.94, a: 0.08 } }];
  out.grid[name] = s.id;
}
return { removed: out.removed, counts: { text: Object.keys(out.text).length, effect: Object.keys(out.effect).length, grid: Object.keys(out.grid).length }, ids: out };
"""


def emit(fname, template, data):
    js = template.replace("__DATA__", json.dumps(data, ensure_ascii=False, separators=(",", ":"))).strip() + "\n"
    with open(os.path.join(OUT, fname), "w") as f:
        f.write(js)
    print(fname, len(js), "chars")


emit("01-variables.js", VARS_JS, VARS_DATA)
emit("02-styles.js", STYLES_JS, STYLES_DATA)
