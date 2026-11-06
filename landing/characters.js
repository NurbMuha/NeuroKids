/* NeuroKids — illustration cast.
 *
 * Style: flat colour-block bodies (no outline), thin ink line limbs,
 * minimal faces. Every colour is a DS primitive: var(--nk-<ramp>-<step>).
 *
 * Usage in HTML:
 *   <div class="nk-char" data-ch="spark-wave"></div>      // a preset from PRESETS
 *   <div class="nk-orb"  data-shape="cloud" data-color="aqua-400" data-eyes="closed"></div>
 *
 * Character frame: viewBox -30 0 260 (ground+10), body centred on x=100,
 * soles on the per-body ground line (square 236, star 212). Arms and props are drawn from shoulder/hand
 * coordinates, so one pose library serves every body shape.
 */
(() => {
  'use strict';

  const v = (t) => `var(--nk-${t})`;
  const fill = (t) => `style="fill:${v(t)}"`;
  const n = (x) => +x.toFixed(1);

  /* ---------- shared shapes ---------- */

  // four-pointed sparkle
  function spark(x, y, s) {
    const k = s * 0.18;
    return `M${x} ${y - s}C${x + k} ${y - k} ${x + k} ${y - k} ${x + s} ${y}` +
      `C${x + k} ${y + k} ${x + k} ${y + k} ${x} ${y + s}` +
      `C${x - k} ${y + k} ${x - k} ${y + k} ${x - s} ${y}` +
      `C${x - k} ${y - k} ${x - k} ${y - k} ${x} ${y - s}Z`;
  }

  function heart(x, y, s) {
    return `M${x} ${y + s * 0.9}C${x - s * 1.3} ${y} ${x - s * 0.9} ${y - s * 1.1} ${x} ${y - s * 0.35}` +
      `C${x + s * 0.9} ${y - s * 1.1} ${x + s * 1.3} ${y} ${x} ${y + s * 0.9}Z`;
  }

  // puffy five-lobed star with soft notches
  function starPath(cx, cy, R, r, lobes = 5) {
    const step = (Math.PI * 2) / lobes;
    const rot = -Math.PI / 2;
    const eps = 0.09;
    const p = (rad, a) => `${n(cx + rad * Math.cos(a))} ${n(cy + rad * Math.sin(a))}`;
    let d = `M${p(r, rot - step / 2 + eps)}`;
    for (let i = 0; i < lobes; i++) {
      const a = rot + i * step;
      d += `C${p(R * 1.2, a - step * 0.3)} ${p(R * 1.2, a + step * 0.3)} ${p(r, a + step / 2 - eps)}`;
      d += `Q${p(r * 0.94, a + step / 2)} ${p(r, a + step / 2 + eps)}`;
    }
    return d + 'Z';
  }

  /* ---------- bodies ---------- */

  const BODY = {
    square: {
      d: 'M100 42C146 41 162 50 162 100C163 148 150 162 100 162C52 163 38 150 38 102C37 54 52 43 100 42Z',
      face: [100, 90], sh: [154, 114], hip: 150, legX: 19, ground: 236,
    },
    star: {
      d: starPath(100, 100, 70, 42),
      face: [100, 94], sh: [138, 116], hip: 138, legX: 16, ground: 212,
    },
    round: {
      d: 'M100 40C137 40 162 66 162 102C162 138 137 162 100 162C63 162 38 138 38 102C38 66 63 40 100 40Z',
      face: [100, 92], sh: [156, 112], hip: 150, legX: 19, ground: 236,
    },
  };

  /* ---------- arms ---------- */

  // right-arm control points as offsets from the shoulder: [c1, c2, hand]
  const POSE = {
    down:  [[12, 14], [18, 34], [14, 58]],
    hip:   [[24, 2], [32, 26], [8, 36]],
    wave:  [[18, -8], [28, -26], [28, -52]],
    raise: [[18, -10], [30, -30], [30, -58]],
    reach: [[16, -2], [30, -6], [46, -16]],
    thumb: [[20, 4], [30, -12], [26, -34]],
    type:  [[10, 12], [6, 28], [-16, 34]],
    cam:   [[12, -2], [6, -14], [-8, -22]],
    camL:  [[-6, 16], [-34, 8], [-46, -16]],
    mega:  [[12, 2], [8, -10], [-4, -14]],
    mug:   [[8, 22], [-4, 30], [-20, 26]],
    sign:  [[14, 8], [16, 22], [4, 28]],
  };

  function arm(b, side, pose) {
    const s = side === 'r' ? 1 : -1;
    const sx = side === 'r' ? b.sh[0] : 200 - b.sh[0];
    const sy = b.sh[1];
    const [c1, c2, end] = POSE[pose];
    const P = ([dx, dy]) => [sx + s * dx, sy + dy];
    const [x1, y1] = P(c1), [x2, y2] = P(c2), [hx, hy] = P(end);
    // stop the line at the edge of the fist
    const len = Math.hypot(hx - x2, hy - y2) || 1;
    const lx = hx - ((hx - x2) / len) * 6.5, ly = hy - ((hy - y2) / len) * 6.5;
    const thumb = pose === 'thumb' ? `<path d="M${n(hx - 3)} ${n(hy - 6)}L${n(hx - 3)} ${n(hy - 17)}"/>` : '';
    const svg =
      `<g class="arm arm-${side} pose-${pose}" style="transform-origin:${n(sx)}px ${n(sy)}px;--dir:${s}">` +
      `<path d="M${n(sx)} ${n(sy)}C${n(x1)} ${n(y1)} ${n(x2)} ${n(y2)} ${n(lx)} ${n(ly)}"/>` +
      `<circle cx="${n(hx)}" cy="${n(hy)}" r="6.5"/>${thumb}</g>`;
    return { svg, hand: [n(hx), n(hy)] };
  }

  /* ---------- legs ---------- */

  function legs(b, mode) {
    if (mode === 'none') return '';
    const g = b.ground;
    const leg = (x, cls, out) =>
      `<g class="leg ${cls}" style="transform-origin:${x}px ${b.hip}px">` +
      `<path d="M${x - 5} ${b.hip}L${x - 5} ${g}M${x + 5} ${b.hip}L${x + 5} ${g}M${x - 5 * out} ${g}L${x + 13 * out} ${g}"/></g>`;
    return `<g class="ch-legs">${leg(100 - b.legX, 'leg-l', -1)}${leg(100 + b.legX, 'leg-r', 1)}</g>`;
  }

  /* ---------- face ---------- */

  function face(b, o) {
    const fx = b.face[0] + (o.look || 0) * 12;
    const fy = b.face[1] + (o.lookY || 0);
    const open = (x) => `<ellipse cx="${n(x)}" cy="${n(fy)}" rx="2.9" ry="3.9"/>`;
    const closed = (x) => `<path d="M${n(x - 5)} ${n(fy - 1)}Q${n(x)} ${n(fy + 5)} ${n(x + 5)} ${n(fy - 1)}"/>`;
    const happy = (x) => `<path d="M${n(x - 5)} ${n(fy + 2)}Q${n(x)} ${n(fy - 5)} ${n(x + 5)} ${n(fy + 2)}"/>`;
    const [l, r] = [fx - 11, fx + 11];
    const eyes = o.eyes === 'closed'
      ? `<g class="eyes-open ch-line">${closed(l)}${closed(r)}</g>`
      : `<g class="eyes-open ch-ink">${open(l)}${open(r)}</g>`;
    return (
      `<g class="ch-face">` +
      `<g class="ch-eyes"><g class="ch-look">${eyes}</g>` +
      `<g class="eyes-happy ch-line">${happy(l)}${happy(r)}</g></g>` +
      `<path class="ch-line ch-mouth" d="M${n(fx - 7)} ${n(fy + 11)}Q${n(fx)} ${n(fy + 18)} ${n(fx + 7)} ${n(fy + 11)}"/>` +
      `</g>`
    );
  }

  /* ---------- props ---------- */

  const PROPS = {
    laptop: {
      over: true,
      draw: () =>
        `<g class="prop prop-laptop">` +
        `<g class="prop-fx">` +
        `<circle class="fx fx-1" cx="58" cy="114" r="5" ${fill('saffron-200')}/>` +
        `<rect class="fx fx-2" x="136" y="108" width="10" height="10" rx="2.5" ${fill('white')}/>` +
        `<path class="fx fx-3" d="${spark(150, 120, 8)}" ${fill('aqua-200')}/></g>` +
        `<rect x="56" y="116" width="88" height="46" rx="7" ${fill('neutral-800')}/>` +
        `<path class="prop-glow" d="${spark(100, 139, 10)}" ${fill('saffron-400')}/>` +
        `<rect x="42" y="160" width="116" height="9" rx="4.5" ${fill('neutral-300')}/></g>`,
    },
    flag: {
      draw: ([hx, hy]) => {
        const x0 = hx + 2, y0 = hy - 52, cw = 9.5, chh = 9.4;
        let cells = '';
        for (let r = 0; r < 3; r++)
          for (let c = 0; c < 4; c++)
            if ((r + c) % 2 === 0)
              cells += `<rect x="${n(x0 + c * cw)}" y="${n(y0 + r * chh)}" width="${cw}" height="${chh}" ${fill('neutral-800')}/>`;
        return (
          `<g class="prop prop-flag">` +
          `<path class="ch-line" d="M${hx} ${hy + 22}L${hx} ${y0 - 4}"/>` +
          `<g class="flag-cloth" style="transform-origin:${hx}px ${y0}px">` +
          `<rect x="${x0}" y="${y0}" width="${cw * 4}" height="${chh * 3}" ${fill('white')}/>${cells}</g></g>`
        );
      },
    },
    doc: {
      draw: ([hx, hy]) =>
        `<g class="prop prop-doc"><g transform="rotate(-8 ${hx + 10} ${hy - 22})">` +
        `<rect x="${hx - 8}" y="${hy - 48}" width="36" height="44" rx="4" ${fill('neutral-50')}/>` +
        `<path class="ch-line thin" d="M${hx - 1} ${hy - 38}L${hx + 20} ${hy - 38}M${hx - 1} ${hy - 31}L${hx + 20} ${hy - 31}M${hx - 1} ${hy - 24}L${hx + 12} ${hy - 24}"/>` +
        `<circle class="doc-seal" cx="${hx + 18}" cy="${hy - 13}" r="6" ${fill('blue-500')}/></g></g>`,
    },
    camera: {
      draw: (_, b, o) => {
        const cx = b.face[0] + 22, cy = b.face[1] - 2;
        return (
          `<g class="prop prop-camera">` +
          `<rect x="${cx - 14}" y="${cy - 22}" width="16" height="8" rx="3" ${fill('aqua-500')}/>` +
          `<rect x="${cx - 24}" y="${cy - 16}" width="48" height="32" rx="8" ${fill('aqua-400')}/>` +
          `<circle cx="${cx}" cy="${cy}" r="11" ${fill('neutral-800')}/>` +
          `<circle cx="${cx}" cy="${cy}" r="4.5" ${fill('aqua-200')}/>` +
          `<path class="prop-flash" d="${spark(cx + 26, cy - 30, 12)}" ${fill('white')}/></g>`
        );
      },
    },
    megaphone: {
      draw: ([hx, hy], b, o) =>
        `<g class="prop prop-mega">` +
        `<g class="mega-cone" style="transform-origin:${hx - 30}px ${hy}px">` +
        `<path d="M${hx - 30} ${hy - 6}L${hx + 36} ${hy - 32}Q${hx + 46} ${hy + 2} ${hx + 36} ${hy + 36}L${hx - 30} ${hy + 8}Z" ${fill(o.propColor || 'orange-400')}/>` +
        `<ellipse cx="${hx + 38}" cy="${hy + 2}" rx="7" ry="33" ${fill(o.propColor2 || 'orange-300')}/></g>` +
        `<g class="mega-sound ch-line">` +
        `<path d="M${hx + 56} ${hy - 12}Q${hx + 62} ${hy + 2} ${hx + 56} ${hy + 16}"/>` +
        `<path d="M${hx + 66} ${hy - 22}Q${hx + 76} ${hy + 2} ${hx + 66} ${hy + 26}"/></g></g>`,
    },
    mug: {
      draw: ([hx, hy], b, o) =>
        `<g class="prop prop-mug">` +
        `<g class="mug-steam ch-line thin">` +
        `<path d="M${hx + 10} ${hy - 18}Q${hx + 6} ${hy - 26} ${hx + 10} ${hy - 34}Q${hx + 14} ${hy - 42} ${hx + 10} ${hy - 50}"/>` +
        `<path d="M${hx + 22} ${hy - 18}Q${hx + 18} ${hy - 26} ${hx + 22} ${hy - 34}"/></g>` +
        `<path d="M${hx + 28} ${hy - 6}Q${hx + 38} ${hy - 6} ${hx + 38} ${hy + 2}Q${hx + 38} ${hy + 10} ${hx + 28} ${hy + 10}" ` +
        `fill="none" style="stroke:${v(o.propColor || 'saffron-400')}" stroke-width="5" stroke-linecap="round"/>` +
        `<rect x="${hx + 2}" y="${hy - 14}" width="28" height="32" rx="7" ${fill(o.propColor || 'saffron-400')}/></g>`,
    },
    sign: {
      draw: () =>
        `<g class="prop prop-sign">` +
        `<rect x="44" y="112" width="112" height="62" rx="10" ${fill('neutral-50')}/>` +
        `<circle cx="56" cy="122" r="3.2" ${fill('red-400')}/><circle cx="66" cy="122" r="3.2" ${fill('saffron-400')}/>` +
        `<circle cx="76" cy="122" r="3.2" ${fill('grass-500')}/>` +
        `<rect class="sign-title" x="56" y="134" width="46" height="10" rx="5" ${fill('blue-500')}/>` +
        `<rect x="56" y="150" width="62" height="6" rx="3" ${fill('neutral-300')}/>` +
        `<rect x="56" y="160" width="44" height="6" rx="3" ${fill('neutral-300')}/>` +
        `<circle class="sign-pic" cx="136" cy="152" r="12" ${fill('saffron-400')}/></g>`,
    },
  };

  /* ---------- presets (the cast) ---------- */

  const PRESETS = {
    'bit-laptop': { shape: 'square', color: 'blue-500', arms: ['type', 'type'], prop: 'laptop', look: 0.1, lookY: -4 },
    'spark-wave': { shape: 'star', color: 'saffron-400', arms: ['wave', 'hip'], look: -0.15 },
    'spark-flag': { shape: 'star', color: 'saffron-400', arms: ['raise', 'down'], prop: 'flag', look: 0.25 },
    'pix-camera': { shape: 'square', color: 'red-400', arms: ['cam', 'camL'], prop: 'camera', look: -0.75 },
    'mira-doc': { shape: 'square', color: 'saffron-400', arms: ['reach', 'down'], prop: 'doc', legs: 'walk', look: 0.45 },
    'leaf-sign': { shape: 'square', color: 'grass-500', arms: ['sign', 'sign'], prop: 'sign', lookY: -10 },
    'leaf-thumb': { shape: 'square', color: 'grass-500', arms: ['thumb', 'down'], look: 0.3 },
    'aqua-mega': { shape: 'round', color: 'aqua-400', arms: ['mega', 'hip'], prop: 'megaphone', look: 0.55 },
    'bit-walk': { shape: 'square', color: 'blue-500', arms: ['mug', 'down'], prop: 'mug', legs: 'walk', look: 0.45, propColor: 'orange-400' },
  };

  function character(o) {
    const b = BODY[o.shape];
    const [poseR, poseL] = o.arms || ['down', 'down'];
    const aR = arm(b, 'r', poseR), aL = arm(b, 'l', poseL);
    const prop = o.prop ? PROPS[o.prop] : null;
    const propSvg = prop ? prop.draw(aR.hand, b, o) : '';
    const arms = `<g class="ch-arms">${aL.svg}${aR.svg}</g>`;
    const upper =
      `<path class="ch-body" d="${b.d}" ${fill(o.color)}/>` +
      face(b, o) +
      // the laptop lid hides the typing hands; every other prop sits under the fists
      (prop && prop.over ? arms + propSvg : propSvg + arms);
    const walk = o.legs === 'walk';
    return (
      `<svg class="ch${walk ? ' is-walk' : ''}" viewBox="-30 0 260 ${b.ground + 10}" aria-hidden="true" focusable="false">` +
      legs(b, o.legs) +
      `<g class="ch-upper" style="transform-origin:100px ${b.hip + 10}px">${upper}</g></svg>`
    );
  }

  /* ---------- limbless primitives (ambient orbs) ---------- */

  const ORB = {
    circle: 'M60 14C86 14 106 34 106 60C106 86 86 106 60 106C34 106 14 86 14 60C14 34 34 14 60 14Z',
    cloud: 'M30 92C14 92 6 80 10 68C4 56 14 42 28 46C30 30 48 22 60 32C70 18 94 22 96 40C112 40 118 58 110 68C118 80 108 94 94 92Z',
    drop: 'M60 8C60 8 102 52 102 76C102 99 84 112 60 112C36 112 18 99 18 76C18 52 60 8 60 8Z',
    blob: 'M60 14C88 12 108 30 106 58C104 86 90 108 60 106C30 104 12 88 14 58C16 30 34 16 60 14Z',
    star: starPath(60, 62, 46, 28),
  };

  function orb(o) {
    const fx = 60 + (+o.look || 0) * 8;
    const fy = o.shape === 'drop' ? 74 : o.shape === 'cloud' ? 66 : 60;
    const closed = (x) => `<path d="M${x - 4.5} ${fy - 1}Q${x} ${fy + 4} ${x + 4.5} ${fy - 1}"/>`;
    const open = (x) => `<ellipse cx="${x}" cy="${fy}" rx="2.6" ry="3.4"/>`;
    const happy = (x) => `<path d="M${x - 4.5} ${fy + 2}Q${x} ${fy - 4} ${x + 4.5} ${fy + 2}"/>`;
    const [l, r] = [fx - 9, fx + 9];
    const eyes = o.eyes === 'closed'
      ? `<g class="eyes-open ch-line">${closed(l)}${closed(r)}</g>`
      : `<g class="eyes-open ch-ink">${open(l)}${open(r)}</g>`;
    return (
      `<svg class="ch ch-orb" viewBox="0 0 120 120" aria-hidden="true" focusable="false">` +
      `<g class="ch-upper" style="transform-origin:60px 106px">` +
      `<path class="ch-body" d="${ORB[o.shape] || ORB.circle}" ${fill(o.color || 'saffron-400')}/>` +
      `<g class="ch-face"><g class="ch-eyes"><g class="ch-look">${eyes}</g>` +
      `<g class="eyes-happy ch-line">${happy(l)}${happy(r)}</g></g>` +
      `<path class="ch-line ch-mouth" d="M${fx - 6} ${fy + 9}Q${fx} ${fy + 14} ${fx + 6} ${fy + 9}"/></g>` +
      `</g></svg>`
    );
  }

  /* ---------- mount ---------- */

  function mount(root = document) {
    root.querySelectorAll('[data-ch]').forEach((el) => {
      const preset = PRESETS[el.dataset.ch];
      if (!preset) return;
      const o = { ...preset };
      if (el.dataset.color) o.color = el.dataset.color;
      const say = el.dataset.say ? `<span class="bubble">${el.dataset.say}</span>` : '';
      el.innerHTML = `<div class="ch-motion">${character(o)}${say}</div>`;
    });
    root.querySelectorAll('.nk-orb[data-shape]').forEach((el) => {
      el.innerHTML = `<div class="ch-motion">${orb(el.dataset)}</div>`;
    });
    // de-synchronise idle loops so the cast never blinks in unison
    root.querySelectorAll('.ch').forEach((svg, i) => {
      svg.style.setProperty('--d', `${(-(i * 0.73) % 5).toFixed(2)}s`);
    });
  }

  window.NKCast = { mount, spark, heart, starPath };
})();
