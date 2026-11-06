const D = {"textStyles":[["Display/XL","body","ExtraBold",64,100,-3.0,null,"Приветствие, праздничные экраны. Строчные или sentence case, акцентное слово — цветом."],["Display/L","body","ExtraBold",52,110,-3.0,null,"Крупный экспрессивный заголовок."],["Display/M","body","ExtraBold",40,115,-3.0,null,"Экспрессивный заголовок."],["Display/S","body","ExtraBold",32,120,-3.0,null,"Малый экспрессивный заголовок, пустые состояния."],["Heading/H1","body","Bold",40,115,-3.0,null,"Заголовок страницы (md display-md)."],["Heading/H2","body","Bold",32,120,-3.0,null,"Заголовок секции (md display-sm)."],["Heading/H3","body","Bold",24,133,-2.5,null,"Заголовок карточки или блока (md heading-sm)."],["Heading/H4","body","Bold",18,144,-1.0,null,"Малый заголовок (кит: Headline Bold 18)."],["Body/L","body","Regular",24,133,-2.5,null,"Лид-абзац (md body-lg; интерлиньяж увеличен для многострочного текста)."],["Body/M","body","Regular",20,150,-1.0,null,"Крупный основной текст (md body-md)."],["Body/S","body","Regular",18,156,-1.0,null,"Текст уроков для чтения."],["Body/XS","body","Regular",16,150,0.0,null,"Основной текст интерфейса (md body-xs)."],["Body/XXS","body","Regular",14,143,0.0,null,"Плотный интерфейс, вторичный текст."],["Label/Button-L","body","Bold",16,125,0.0,null,"Подпись кнопки размера L (56px)."],["Label/Button","body","Bold",14,115,0.0,null,"Подпись кнопок S/M (md button-md)."],["Label/Small","body","Bold",12,133,0.0,null,"Бейджи, чипы, мелкие подписи."],["Label/Overline","body","Bold",12,133,6,"UPPER","Надзаголовок секции, ВСЕ ПРОПИСНЫЕ."],["Caption/Default","body","Medium",12,133,0.0,null,"Подписи, мета, мелкий текст (md caption)."],["Data/KPI","body","Bold",40,110,-3.0,null,"Числа KPI. В коде: font-variant-numeric: tabular-nums."],["Data/Table","body","Regular",14,143,0.0,null,"Ячейки таблиц. В коде: font-variant-numeric: tabular-nums."],["Data/Axis","body","Medium",12,133,0.0,null,"Оси и легенды графиков. В коде: tabular-nums."]],"effects":{"Elevation/Overlay-1":{"desc":"Меню, поповеры, тултипы. Карточки остаются плоскими (правило Headspace).","shadows":[["color/shadow/soft",0,2,4,0],["color/shadow/medium",0,8,24,0]]},"Elevation/Overlay-2":{"desc":"Модалки, тосты, боковые панели.","shadows":[["color/shadow/soft",0,4,8,0],["color/shadow/strong",0,16,48,0]]},"Elevation/Lift":{"desc":"Жёсткий «лифт» 2px под тёмной пилюлей (md: единственная тень #141313).","shadows":[["color/shadow/lift",0,2,0,0]]},"Focus/Ring":{"desc":"Фокус с клавиатуры: зазор 2px белым + кольцо 2px брендовым (тени со spread; белый слой последним, поверх). У фрейма должен быть включён Clip content.","shadows":[["color/border/focus",0,0,0,4],["white-raw",0,0,0,2]]}},"grids":{"Grid/Desktop-12":{"count":12,"gutter":24,"margin":80,"desc":"Фрейм 1440: поля 80px, контейнер 1280. Для полноширинных страниц."},"Grid/Tablet-8":{"count":8,"gutter":24,"margin":32,"desc":"Фреймы 768–1024."},"Grid/Mobile-4":{"count":4,"gutter":16,"margin":16,"desc":"Фреймы 360–375."},"Grid/App-content-12":{"count":12,"gutter":24,"margin":32,"desc":"Контентная область кабинета (справа от сайдбара): поля 32px."}}};
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
