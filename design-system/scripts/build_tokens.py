#!/usr/bin/env python3
"""NeuroKids design tokens generator.

Builds OKLCH-interpolated color ramps around exact anchor colors
(Headspace palette + accessibility-derived values), defines semantic
aliases, spacing/radius/size/typography/motion/effect tokens, validates
WCAG contrast for every semantic pairing, and writes:

  design-system/tokens.json            (W3C DTCG format + Figma extensions)
  design-system/contrast-report.md     (every checked pair with ratio + pass/fail)
  design-system/figma-payload.json     (compact payload embedded into use_figma scripts)

Run:  python3 -I design-system/scripts/build_tokens.py
Stdlib only.
"""
import json
import math
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STEPS = [50, 100, 200, 300, 400, 500, 600, 700, 800, 900]
# Default lightness targets (OKLCH L) used only where no anchor constrains a step.
END_L = {50: 0.972, 900: 0.27}


# ---------------------------------------------------------------- color math
def hex2rgb(h):
    h = h.lstrip("#")
    return [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]


def lin(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def delin(c):
    return 12.92 * c if c <= 0.0031308 else 1.055 * (c ** (1 / 2.4)) - 0.055


def rgb2oklab(rgb):
    r, g, b = [lin(c) for c in rgb]
    l = 0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b
    m = 0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b
    s = 0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b
    l_, m_, s_ = [x ** (1 / 3) for x in (l, m, s)]
    return (0.2104542553 * l_ + 0.7936177850 * m_ - 0.0040720468 * s_,
            1.9779984951 * l_ - 2.4285922050 * m_ + 0.4505937099 * s_,
            0.0259040371 * l_ + 0.7827717662 * m_ - 0.8086757660 * s_)


def oklab2linrgb(L, a, b):
    l_ = L + 0.3963377774 * a + 0.2158037573 * b
    m_ = L - 0.1055613458 * a - 0.0638541728 * b
    s_ = L - 0.0894841775 * a - 1.2914855480 * b
    l, m, s = l_ ** 3, m_ ** 3, s_ ** 3
    return (4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s,
            -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s,
            -0.0041960863 * l - 0.7034186147 * m + 1.7076147010 * s)


def to_lch(h):
    L, a, b = rgb2oklab(hex2rgb(h))
    return L, math.hypot(a, b), math.atan2(b, a)


def lch_to_hex(L, C, H):
    """OKLCH -> hex with gamut mapping by chroma reduction (hue + lightness preserved)."""
    def in_gamut(c):
        r = oklab2linrgb(L, c * math.cos(H), c * math.sin(H))
        return all(-1e-6 <= x <= 1 + 1e-6 for x in r), r
    ok, r = in_gamut(C)
    if not ok:
        lo, hi = 0.0, C
        for _ in range(40):
            mid = (lo + hi) / 2
            if in_gamut(mid)[0]:
                lo = mid
            else:
                hi = mid
        _, r = in_gamut(lo)
    return "#" + "".join(f"{round(min(1, max(0, delin(min(1, max(0, x))))) * 255):02X}" for x in r)


def rel_lum(h):
    r, g, b = [lin(c) for c in hex2rgb(h)]
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a, b):
    la, lb = rel_lum(a), rel_lum(b)
    return (max(la, lb) + 0.05) / (min(la, lb) + 0.05)


def lerp(a, b, t):
    return a + (b - a) * t


def lerp_hue(h1, h2, t):
    d = (h2 - h1 + math.pi) % (2 * math.pi) - math.pi
    return h1 + d * t


# ---------------------------------------------------------------- ramps
# Exact anchors. Every value here is kept verbatim in the output ramp.
#   source: md = headspace.design.md, kit = Headspace Figma kit, a11y = derived for WCAG
RAMP_ANCHORS = {
    "neutral": {50: "#F9F4F2",   # md canvas
                200: "#E2DED9",  # md hairline (decorative dividers only)
                500: "#908C88",  # a11y: input border >= 3:1 on white & canvas
                600: "#63605D",  # md ink-meta
                700: "#44423F",  # md ink-soft
                800: "#2D2C2B",  # md ink (all headings/body)
                900: "#141313"}, # md ink-strong
    "blue": {500: "#0061EF",     # md primary (CTA)
             600: "#004DDA",     # a11y: hover (md primary-deep #0000EE was a browser link artifact)
             700: "#003FCC"},    # a11y: pressed
    "saffron": {400: "#FFCE00",  # md orb-saffron
                600: "#B58600",  # a11y: chart mark >= 3:1
                700: "#966700"}, # a11y: warning text >= 4.5:1
    "pink": {300: "#FFA1CC",     # md orb-pink
             500: "#CA719B"},    # a11y: chart mark >= 3:1
    "aqua": {400: "#00A4FF",     # md orb-aqua
             500: "#0092EC"},    # a11y: chart mark >= 3:1
    "grass": {600: "#02873E"},   # md orb-grass
    "violet": {800: "#3B197F"},  # md orb-ultraviolet
    "red": {500: "#DC4C44",      # kit error
            600: "#CA3B35"},     # a11y: error text >= 4.5:1
    "orange": {400: "#FF7E1D",   # kit primary orange (streak / data accent only, never CTA)
               500: "#E66700"},  # a11y: chart mark >= 3:1
}


def build_ramp(anchors):
    idx = {s: i for i, s in enumerate(STEPS)}
    pts = sorted((idx[s], to_lch(h)) for s, h in anchors.items())
    first_i, (fL, fC, fH) = pts[0]
    last_i, (lL, lC, lH) = pts[-1]
    maxC = max(p[1][1] for p in pts)
    # virtual ends (only if not anchored)
    if first_i != 0:
        pts.insert(0, (0, (END_L[50], min(0.035, maxC * 0.18), fH)))
    if last_i != len(STEPS) - 1:
        n = len(STEPS) - 1 - last_i
        endL = min(END_L[900], lL - 0.045 * n)
        pts.append((len(STEPS) - 1, (endL, lC * 0.75, lH)))
    out = {}
    for s in STEPS:
        i = idx[s]
        if s in anchors:
            out[s] = anchors[s].upper()
            continue
        for (i0, p0), (i1, p1) in zip(pts, pts[1:]):
            if i0 <= i <= i1:
                t = (i - i0) / (i1 - i0)
                # light end: ease so tints stay close together (50/100/200 usable as surfaces)
                tl = t ** 1.5 if (i0 == 0 and 50 not in anchors) else t
                L = lerp(p0[0], p1[0], tl)
                C = lerp(p0[1], p1[1], t)
                H = lerp_hue(p0[2], p1[2], t)
                out[s] = lch_to_hex(L, C, H)
                break
    # monotonic lightness check
    Ls = [to_lch(out[s])[0] for s in STEPS]
    bad = [STEPS[i] for i in range(1, len(Ls)) if not Ls[i] < Ls[i - 1]]
    if bad:
        raise SystemExit(f"non-monotonic lightness at steps {bad}: {dict(zip(STEPS, [round(x, 3) for x in Ls]))}")
    return out


def darken_until(hex_, bgs, target):
    """Lightest color along hex_'s OKLCH hue/chroma line that reaches `target` contrast on every bg."""
    L, C, H = to_lch(hex_)
    while L > 0.05:
        c = lch_to_hex(L, C, H)
        if all(contrast(c, b) >= target for b in bgs):
            return c
        L -= 0.002
    raise SystemExit(f"cannot reach {target} for {hex_}")


# Neutral first: the darkest neutral surface (neutral/100 = surface-sunken) sets the bar
# for every status text color, so status text passes 4.5:1 on ALL neutral surfaces.
_neutral = build_ramp(RAMP_ANCHORS["neutral"])
_text_bgs = ["#FFFFFF", _neutral[50], _neutral[100]]
RAMP_ANCHORS["saffron"][700] = darken_until("#966700", _text_bgs, 4.5)  # warning text
RAMP_ANCHORS["red"][600] = darken_until("#CA3B35", _text_bgs, 4.5)      # error text/fill/border
RAMPS = {name: build_ramp(a) for name, a in RAMP_ANCHORS.items()}
BASE = {"white": "#FFFFFF", "black": "#000000"}
# Alpha primitives (8-digit hex) for shadows and scrim, from neutral/900 #141313
ALPHA = {"neutral-900-a06": "#1413130F", "neutral-900-a12": "#1413131F",
         "neutral-900-a16": "#14131329", "neutral-900-a48": "#1413137A"}


def prim(path):
    """Resolve 'blue/500' | 'white' | 'alpha/neutral-900-a48' to hex."""
    if path in BASE:
        return BASE[path]
    if path.startswith("alpha/"):
        return ALPHA[path.split("/", 1)[1]]
    hue, step = path.split("/")
    return RAMPS[hue][int(step)]


# ---------------------------------------------------------------- semantics (Light)
SEM = {
    # backgrounds  -> FRAME_FILL, SHAPE_FILL
    "color/bg/canvas": "neutral/50",
    "color/bg/surface": "white",
    "color/bg/surface-sunken": "neutral/100",
    "color/bg/inverse": "neutral/800",
    "color/bg/brand": "blue/500",
    "color/bg/brand-hover": "blue/600",
    "color/bg/brand-pressed": "blue/700",
    "color/bg/brand-subtle": "blue/50",
    "color/bg/dark": "neutral/800",
    "color/bg/dark-hover": "neutral/700",
    "color/bg/dark-pressed": "neutral/900",
    "color/bg/neutral-hover": "neutral/100",
    "color/bg/neutral-pressed": "neutral/200",
    "color/bg/disabled": "neutral/200",
    "color/bg/scrim": "alpha/neutral-900-a48",
    "color/bg/accent/saffron": "saffron/400",
    "color/bg/accent/pink": "pink/300",
    "color/bg/accent/aqua": "aqua/400",
    "color/bg/accent/grass": "grass/600",
    "color/bg/accent/violet": "violet/800",
    "color/bg/accent/orange": "orange/400",
    "color/bg/accent/saffron-subtle": "saffron/50",
    "color/bg/accent/pink-subtle": "pink/50",
    "color/bg/accent/aqua-subtle": "aqua/50",
    "color/bg/accent/grass-subtle": "grass/50",
    "color/bg/accent/violet-subtle": "violet/50",
    "color/bg/accent/orange-subtle": "orange/50",
    "color/bg/status/success": "grass/600",
    "color/bg/status/success-subtle": "grass/50",
    "color/bg/status/warning": "saffron/400",
    "color/bg/status/warning-subtle": "saffron/50",
    "color/bg/status/error": "red/600",
    "color/bg/danger-hover": "red/700",
    "color/bg/danger-pressed": "red/800",
    "color/bg/status/error-subtle": "red/50",
    "color/bg/status/info": "blue/500",
    "color/bg/status/info-subtle": "blue/50",
    # text -> TEXT_FILL
    "color/text/primary": "neutral/800",
    "color/text/secondary": "neutral/700",
    "color/text/tertiary": "neutral/600",
    "color/text/disabled": "neutral/400",
    "color/text/inverse": "white",
    "color/text/on-brand": "white",
    "color/text/on-accent": "neutral/800",
    "color/text/brand": "blue/600",
    "color/text/link": "blue/600",
    "color/text/link-hover": "blue/700",
    "color/text/success": "grass/700",
    "color/text/warning": "saffron/700",
    "color/text/error": "red/600",
    "color/text/info": "blue/600",
    # borders -> STROKE_COLOR
    "color/border/subtle": "neutral/200",
    "color/border/default": "neutral/500",
    "color/border/strong": "neutral/800",
    "color/border/disabled": "neutral/300",
    "color/border/focus": "blue/500",
    "color/border/brand": "blue/500",
    "color/border/inverse": "white",
    "color/border/success": "grass/600",
    "color/border/warning": "saffron/600",
    "color/border/error": "red/600",
    # icons -> SHAPE_FILL, STROKE_COLOR
    "color/icon/primary": "neutral/800",
    "color/icon/secondary": "neutral/600",
    "color/icon/disabled": "neutral/400",
    "color/icon/inverse": "white",
    "color/icon/brand": "blue/500",
    "color/icon/on-accent": "neutral/800",
    "color/icon/success": "grass/600",
    "color/icon/warning": "saffron/600",
    "color/icon/error": "red/600",
    # shadows -> EFFECT_COLOR
    "color/shadow/soft": "alpha/neutral-900-a06",
    "color/shadow/medium": "alpha/neutral-900-a12",
    "color/shadow/strong": "alpha/neutral-900-a16",
    "color/shadow/lift": "neutral/900",
}
SCOPES = {
    "color/bg/": ["FRAME_FILL", "SHAPE_FILL"],
    "color/text/": ["TEXT_FILL"],
    "color/border/": ["STROKE_COLOR"],
    "color/icon/": ["SHAPE_FILL", "STROKE_COLOR"],
    "color/shadow/": ["EFFECT_COLOR"],
}


def scope_for(name):
    for k, v in SCOPES.items():
        if name.startswith(k):
            return v
    raise KeyError(name)


def css(name):
    return "var(--nk-" + name.replace("/", "-") + ")"


# ---------------------------------------------------------------- numbers
SPACING = {"none": 0, "3xs": 2, "xxs": 4, "xs": 6, "sm": 8, "md": 12, "base": 16,
           "lg": 24, "xl": 32, "2xl": 48, "3xl": 64, "4xl": 80}
RADIUS = {"none": 0, "sm": 8, "md": 16, "lg": 24, "xl": 32, "full": 999}
SIZE = {  # name: (value, scopes)
    "control/sm": (40, ["WIDTH_HEIGHT"]), "control/md": (48, ["WIDTH_HEIGHT"]), "control/lg": (56, ["WIDTH_HEIGHT"]),
    "icon/xs": (16, ["WIDTH_HEIGHT"]), "icon/sm": (20, ["WIDTH_HEIGHT"]), "icon/md": (24, ["WIDTH_HEIGHT"]),
    "icon/lg": (32, ["WIDTH_HEIGHT"]), "icon/xl": (48, ["WIDTH_HEIGHT"]), "icon/2xl": (64, ["WIDTH_HEIGHT"]),
    "icon/3xl": (96, ["WIDTH_HEIGHT"]),
    "layout/header": (64, ["WIDTH_HEIGHT"]), "layout/sidebar": (264, ["WIDTH_HEIGHT"]),
    "layout/sidebar-collapsed": (80, ["WIDTH_HEIGHT"]), "layout/tabbar": (64, ["WIDTH_HEIGHT"]),
    "layout/container-max": (1280, ["WIDTH_HEIGHT"]),
    "stroke/default": (1, ["STROKE_FLOAT"]), "stroke/strong": (2, ["STROKE_FLOAT"]), "stroke/focus": (2, ["STROKE_FLOAT"]),
}
TYPO_MODES = ["EN", "RU·KZ"]
TYPO = {  # name: (type, {mode: value}, scopes)
    # Onest: геометрический гротеск, ближайший бесплатный аналог Headspace Apercu
    # с полной кириллицей (RU + KZ: Ә Ғ Қ Ң Ө Ұ Ү Һ І проверены по cmap), wght 100-900, tnum.
    # Режимы EN / RU·KZ оставлены, чтобы позже можно было развести шрифты по скриптам.
    "font/body": ("STRING", {"EN": "Onest", "RU·KZ": "Onest"}, ["FONT_FAMILY"]),
}
# ARCHIVED 2026-11-06 (по решению пользователя «убрать в ящик»): рукописный акцент.
# Не попадает в Figma и tokens.json. Чтобы вернуть: перенести в TYPO и вернуть
# стиль Accent/Note из ARCHIVED_TEXT_STYLES, family 'accent' в gen_figma_scripts.py.
ARCHIVED_TYPO = {
    "font/accent": ("STRING", {"EN": "Gochi Hand", "RU·KZ": "Pangolin"}, ["FONT_FAMILY"]),
    "font/accent-style": ("STRING", {"EN": "Regular", "RU·KZ": "Regular"}, ["FONT_STYLE"]),
}
# Motion: CSS-friendly durations/easings (Apple guidance: critically damped default,
# press feedback instant; reduced-motion -> cross-fade)
MOTION = {
    "duration/instant": ("TIMING", 0.1), "duration/fast": ("TIMING", 0.2),
    "duration/base": ("TIMING", 0.3), "duration/slow": ("TIMING", 0.4),
    "easing/standard": ("EASING", [0.2, 0.0, 0.0, 1.0]),
    "easing/enter": ("EASING", [0.0, 0.0, 0.2, 1.0]),
    "easing/exit": ("EASING", [0.4, 0.0, 1.0, 1.0]),
}

# ---------------------------------------------------------------- text styles
# Трекинг по спецификации Headspace (headspace.design.md): -3% от 32px, -2.5% на 24px,
# -1% на 18-20px, 0 на 16px и мельче (на мелком кириллическом тексте не сжимаем).
def tracking_pct(size):
    if size >= 32:
        return -3.0
    if size >= 24:
        return -2.5
    if size >= 18:
        return -1.0
    return 0.0


TEXT_STYLES = [
    # name, family, style, size, line-height %, tracking %, case, description
    ("Display/XL", "body", "ExtraBold", 64, 100, None, None, "Приветствие, праздничные экраны. Строчные или sentence case, акцентное слово — цветом."),
    ("Display/L", "body", "ExtraBold", 52, 110, None, None, "Крупный экспрессивный заголовок."),
    ("Display/M", "body", "ExtraBold", 40, 115, None, None, "Экспрессивный заголовок."),
    ("Display/S", "body", "ExtraBold", 32, 120, None, None, "Малый экспрессивный заголовок, пустые состояния."),
    ("Heading/H1", "body", "Bold", 40, 115, None, None, "Заголовок страницы (md display-md)."),
    ("Heading/H2", "body", "Bold", 32, 120, None, None, "Заголовок секции (md display-sm)."),
    ("Heading/H3", "body", "Bold", 24, 133, None, None, "Заголовок карточки или блока (md heading-sm)."),
    ("Heading/H4", "body", "Bold", 18, 144, None, None, "Малый заголовок (кит: Headline Bold 18)."),
    ("Body/L", "body", "Regular", 24, 133, None, None, "Лид-абзац (md body-lg; интерлиньяж увеличен для многострочного текста)."),
    ("Body/M", "body", "Regular", 20, 150, None, None, "Крупный основной текст (md body-md)."),
    ("Body/S", "body", "Regular", 18, 156, None, None, "Текст уроков для чтения."),
    ("Body/XS", "body", "Regular", 16, 150, None, None, "Основной текст интерфейса (md body-xs)."),
    ("Body/XXS", "body", "Regular", 14, 143, None, None, "Плотный интерфейс, вторичный текст."),
    ("Label/Button-L", "body", "Bold", 16, 125, None, None, "Подпись кнопки размера L (56px)."),
    ("Label/Button", "body", "Bold", 14, 115, None, None, "Подпись кнопок S/M (md button-md)."),
    ("Label/Small", "body", "Bold", 12, 133, None, None, "Бейджи, чипы, мелкие подписи."),
    ("Label/Overline", "body", "Bold", 12, 133, 6, "UPPER", "Надзаголовок секции, ВСЕ ПРОПИСНЫЕ."),
    ("Caption/Default", "body", "Medium", 12, 133, None, None, "Подписи, мета, мелкий текст (md caption)."),
    ("Data/KPI", "body", "Bold", 40, 110, None, None, "Числа KPI. В коде: font-variant-numeric: tabular-nums."),
    ("Data/Table", "body", "Regular", 14, 143, None, None, "Ячейки таблиц. В коде: font-variant-numeric: tabular-nums."),
    ("Data/Axis", "body", "Medium", 12, 133, None, None, "Оси и легенды графиков. В коде: tabular-nums."),
]

ARCHIVED_TEXT_STYLES = [
    ("Accent/Note", "accent", None, 20, 140, 0, None, "Поощрения: «Так держать!» / «Жарайсың!» / «Keep up the great work!». Не меньше 20px."),
]

EFFECTS = {
    "Elevation/Overlay-1": {"desc": "Меню, поповеры, тултипы. Карточки остаются плоскими (правило Headspace).",
                            "shadows": [("color/shadow/soft", 0, 2, 4, 0), ("color/shadow/medium", 0, 8, 24, 0)]},
    "Elevation/Overlay-2": {"desc": "Модалки, тосты, боковые панели.",
                            "shadows": [("color/shadow/soft", 0, 4, 8, 0), ("color/shadow/strong", 0, 16, 48, 0)]},
    "Elevation/Lift": {"desc": "Жёсткий «лифт» 2px под тёмной пилюлей (md: единственная тень #141313).",
                       "shadows": [("color/shadow/lift", 0, 2, 0, 0)]},
    "Focus/Ring": {"desc": "Фокус с клавиатуры: зазор 2px белым + кольцо 2px брендовым (тени со spread; белый слой последним, поверх). У фрейма должен быть включён Clip content.",
                   "shadows": [("color/border/focus", 0, 0, 0, 4), ("white-raw", 0, 0, 0, 2)]}  # later effect paints on top,
}
GRIDS = {
    "Grid/Desktop-12": {"count": 12, "gutter": 24, "margin": 80, "desc": "Фрейм 1440: поля 80px, контейнер 1280. Для полноширинных страниц."},
    "Grid/Tablet-8": {"count": 8, "gutter": 24, "margin": 32, "desc": "Фреймы 768–1024."},
    "Grid/Mobile-4": {"count": 4, "gutter": 16, "margin": 16, "desc": "Фреймы 360–375."},
    "Grid/App-content-12": {"count": 12, "gutter": 24, "margin": 32, "desc": "Контентная область кабинета (справа от сайдбара): поля 32px."},
}

# ---------------------------------------------------------------- contrast checks
CHECKS = [  # (fg, bg, min, label)
]
for fg in ["color/text/primary", "color/text/secondary", "color/text/tertiary", "color/text/link",
           "color/text/brand", "color/text/success", "color/text/warning", "color/text/error", "color/text/info"]:
    for bg in ["color/bg/canvas", "color/bg/surface", "color/bg/surface-sunken"]:
        CHECKS.append((fg, bg, 4.5, "text"))
for bg in ["color/bg/danger-hover", "color/bg/danger-pressed", "color/bg/brand", "color/bg/brand-hover", "color/bg/brand-pressed", "color/bg/accent/grass",
           "color/bg/accent/violet", "color/bg/status/success", "color/bg/status/error", "color/bg/status/info",
           "color/bg/dark", "color/bg/dark-hover", "color/bg/dark-pressed", "color/bg/inverse"]:
    CHECKS.append(("color/text/on-brand", bg, 4.5, "text on fill"))
for bg in ["color/bg/accent/saffron", "color/bg/accent/pink", "color/bg/accent/aqua", "color/bg/accent/orange",
           "color/bg/status/warning", "color/bg/brand-subtle"] + \
          [f"color/bg/accent/{h}-subtle" for h in ["saffron", "pink", "aqua", "grass", "violet", "orange"]] + \
          [f"color/bg/status/{s}-subtle" for s in ["success", "warning", "error", "info"]]:
    CHECKS.append(("color/text/on-accent", bg, 4.5, "text on fill"))
for s in ["success", "warning", "error", "info"]:
    CHECKS.append((f"color/text/{s}", f"color/bg/status/{s}-subtle", 4.5, "status text on its tint"))
for fg in ["color/border/default", "color/border/focus", "color/border/strong", "color/border/error",
           "color/border/success", "color/border/warning",
           "color/icon/primary", "color/icon/secondary", "color/icon/brand", "color/icon/success",
           "color/icon/warning", "color/icon/error"]:
    for bg in ["color/bg/canvas", "color/bg/surface"]:
        CHECKS.append((fg, bg, 3.0, "non-text (WCAG 1.4.11)"))
INFO_PAIRS = [("color/border/subtle", "color/bg/surface", "decorative divider only (not a control boundary)"),
              ("color/text/disabled", "color/bg/surface", "disabled text is exempt (WCAG 1.4.3)")]


def main():
    sem_hex = {k: prim(v) for k, v in SEM.items()}
    rows, fails = [], []
    for fg, bg, mn, kind in CHECKS:
        r = contrast(sem_hex[fg][:7], sem_hex[bg][:7])
        ok = r >= mn
        rows.append((fg, bg, sem_hex[fg][:7], sem_hex[bg][:7], r, mn, kind, ok))
        if not ok:
            fails.append((fg, bg, round(r, 2), mn))

    # ---- tokens.json (DTCG)
    def ext(collection, scopes, code):
        return {"com.figma": {"collection": collection, "scopes": scopes, "codeSyntax": {"WEB": code}}}

    prim_tree = {}
    for hue, ramp in RAMPS.items():
        prim_tree[hue] = {str(s): {"$type": "color", "$value": v,
                                   "$extensions": ext("Primitives", [], f"var(--nk-{hue}-{s})")}
                          for s, v in ramp.items()}
    for k, v in BASE.items():
        prim_tree[k] = {"$type": "color", "$value": v, "$extensions": ext("Primitives", [], f"var(--nk-{k})")}
    prim_tree["alpha"] = {k: {"$type": "color", "$value": v, "$extensions": ext("Primitives", [], f"var(--nk-alpha-{k})")}
                          for k, v in ALPHA.items()}

    def ref(p):
        if p in BASE:
            return "{primitives." + p + "}"
        if p.startswith("alpha/"):
            return "{primitives.alpha." + p.split("/", 1)[1] + "}"
        h, s = p.split("/")
        return "{primitives." + h + "." + s + "}"

    sem_tree = {}
    for name, p in SEM.items():
        node = sem_tree
        parts = name.split("/")[1:]
        for part in parts[:-1]:
            node = node.setdefault(part, {})
        node[parts[-1]] = {"$type": "color", "$value": ref(p), "$extensions": ext("Color", scope_for(name), css(name))}

    tokens = {
        "$description": "NeuroKids design tokens (Headspace-based). Generated by scripts/build_tokens.py — do not edit by hand.",
        "primitives": prim_tree,
        "color": sem_tree,
        "spacing": {k: {"$type": "dimension", "$value": f"{v}px", "$extensions": ext("Spacing", ["GAP"], f"var(--nk-spacing-{k})")} for k, v in SPACING.items()},
        "radius": {k: {"$type": "dimension", "$value": f"{v}px", "$extensions": ext("Radius", ["CORNER_RADIUS"], f"var(--nk-radius-{k})")} for k, v in RADIUS.items()},
        "size": {k: {"$type": "dimension", "$value": f"{v}px", "$extensions": ext("Size", sc, "var(--nk-size-" + k.replace('/', '-') + ")")} for k, (v, sc) in SIZE.items()},
        "font": {k.split("/", 1)[1]: {"$type": "fontFamily" if "style" not in k else "string", "$value": vals,
                                      "$extensions": ext("Typography", sc, "var(--nk-" + k.replace('/', '-') + ")")}
                 for k, (t, vals, sc) in TYPO.items()},
        "motion": {k: {"$type": "duration" if t == "TIMING" else "cubicBezier",
                       "$value": f"{int(v * 1000)}ms" if t == "TIMING" else v,
                       "$extensions": ext("Motion", [], "var(--nk-motion-" + k.replace('/', '-') + ")")}
                   for k, (t, v) in MOTION.items()},
        "typography": {n: {"$type": "typography", "$value": {
            "fontFamily": "{font." + fam + "}", "fontWeight": {"Regular": 400, "Medium": 500, "Bold": 700, "ExtraBold": 800}.get(st, 400),
            "fontSize": f"{sz}px", "lineHeight": lh / 100,
            "letterSpacing": f"{(tracking_pct(sz) if tr is None else tr)}%"}, "$description": d}
            for n, fam, st, sz, lh, tr, case, d in TEXT_STYLES},
    }
    with open(os.path.join(ROOT, "tokens.json"), "w") as f:
        json.dump(tokens, f, ensure_ascii=False, indent=2)

    # ---- compact payload for Figma scripts
    payload = {
        "ramps": RAMPS, "base": BASE, "alpha": ALPHA,
        "semantic": [[n, p, scope_for(n), css(n)] for n, p in SEM.items()],
        "spacing": SPACING, "radius": RADIUS, "size": {k: v for k, v in SIZE.items()},
        "typo": {k: [t, vals, sc] for k, (t, vals, sc) in TYPO.items()}, "typoModes": TYPO_MODES,
        "motion": MOTION,
        "textStyles": [[n, fam, st, sz, lh, (tracking_pct(sz) if tr is None else tr), case, d]
                       for n, fam, st, sz, lh, tr, case, d in TEXT_STYLES],
        "effects": EFFECTS, "grids": GRIDS,
    }
    with open(os.path.join(ROOT, "figma-payload.json"), "w") as f:
        json.dump(payload, f, ensure_ascii=False, separators=(",", ":"))

    # ---- contrast report
    lines = ["# NeuroKids — отчёт по контрасту (тема Light)", "",
             "Сгенерировано `scripts/build_tokens.py`. Порог: текст 4.5:1, неразрешённые элементы интерфейса 3:1 (WCAG 2.2 AA).", "",
             f"Проверено пар: {len(rows)}, не прошло: {len(fails)}.", "",
             "| Передний план | Фон | Цвета | Контраст | Порог | Тип | Итог |", "|---|---|---|---|---|---|---|"]
    for fg, bg, fh, bh, r, mn, kind, ok in rows:
        lines.append(f"| `{fg}` | `{bg}` | {fh} / {bh} | {r:.2f} | {mn} | {kind} | {'✅' if ok else '❌'} |")
    lines += ["", "## Пары только для справки", ""]
    for fg, bg, note in INFO_PAIRS:
        lines.append(f"- `{fg}` на `{bg}`: {contrast(sem_hex[fg][:7], sem_hex[bg][:7]):.2f} — {note}")
    lines += ["", "## Шкалы", "", "| Шкала | " + " | ".join(str(s) for s in STEPS) + " |",
              "|---|" + "---|" * len(STEPS)]
    for hue, ramp in RAMPS.items():
        lines.append(f"| {hue} | " + " | ".join(ramp[s] for s in STEPS) + " |")
    with open(os.path.join(ROOT, "contrast-report.md"), "w") as f:
        f.write("\n".join(lines) + "\n")

    # ---- console summary
    print("RAMPS")
    for hue, ramp in RAMPS.items():
        print(f"  {hue:8s} " + " ".join(f"{s}:{ramp[s]}" for s in STEPS))
    print(f"checks: {len(rows)}  fails: {len(fails)}")
    for f_ in fails:
        print("  FAIL", f_)
    print("text styles:", len(TEXT_STYLES), " semantic:", len(SEM), " primitives:",
          sum(len(r) for r in RAMPS.values()) + len(BASE) + len(ALPHA))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
