# ArchBang Summer Theme — Design Spec

**Date:** 2026-04-28  
**Release name:** Summer  
**Wallpaper source:** `~/Backgrounds/beach.jpg` (anime-style beach illustration)

---

## Colour Palette

Extracted from beach.jpg.

| Name | Hex | Use |
|---|---|---|
| sky | `#87C8E8` | accents, mako border, wmenu selection bg |
| ocean | `#A8DFF0` | titlebar ARGB, secondary highlights |
| shallow | `#D8EEF8` | wmenu bg, surface areas |
| cloud | `#EDE8DF` | light text on dark surfaces |
| sand | `#D4C8A4` | titlebar button (iconify) |
| horizon | `#7AAEC0` | conky label colour |
| deep navy | `#1A3550` | primary text on light surfaces, wmenu fg |
| coral | `#E88A8A` | titlebar close button |
| dark base | `#1A2838` | mako background |

---

## Components

### labwc — Theme `AB_Summer`

New theme directory: `airootfs/etc/skel/.local/share/themes/AB_Summer/labwc/`

Files: `themerc`, `close.xbm`, `iconify.xbm`, `max.xbm` (reuse XBM shapes from Lightwave/Seafront-Storm).

**themerc key values:**

- `border.width: 0`
- `window.active.title.bg.color: #87C8E855` — translucent sky blue titlebar (ARGB)
- `window.inactive.title.bg.color: #D8EEF833` — pale inactive
- `window.active.label.text.color: #1A3550`
- `window.inactive.label.text.color: #7AAEC0`
- Active buttons: ocean (`#A8DFF0`), sand (`#D4C8A4`), coral (`#E88A8A`) for iconify/max/close
- Inactive buttons: `#7AAEC099`
- `window.active.shadow.size: 60`, color `#00000022`
- `window.inactive.shadow.size: 30`, color `#00000011`
- Menu bg: `#D8EEF8CC`, active: `#87C8E8CC`, text: `#1A3550`
- OSD: bg `#D8EEF8`, border `#87C8E8`, text `#1A3550`

Update `rc.xml`: `<name>AB_Summer</name>`, `cornerRadius` stays `6`.

---

### waybar — `style.css`

Update `style.css` to summer palette (waybar loads this by default — no `--style` flag in autostart). Also save a named copy as `waybar-summer-style.css`, matching the existing project pattern (`waybar-lightwave-style.css` precedent). No changes to `config` — existing modules (workspaces, taskbar, battery, tray, clock) unchanged.

**Palette variables:**

```css
@define-color bg      rgba(135, 200, 232, 0.28);
@define-color surface rgba(168, 223, 240, 0.40);
@define-color border  rgba(255, 255, 255, 0.38);
@define-color fg      #1A3550;
@define-color accent  #87C8E8;
@define-color subtext #7AAEC0;
```

**Key rules:**

- `window#waybar`: `background-color: @bg`, `border-top: 1px solid @border`
- `#workspaces button.active`: `background-color: @surface`, `color: @fg`, `font-weight: bold`
- `#clock`: `background-color: @surface`, `padding: 4px 10px`
- `#battery`, `#tray`, `#pulseaudio`: `color: @fg`
- Hover states: `opacity: 0.8`

---

### conky

Modify existing `conky.conf`. Content unchanged (keyboard shortcuts). Restyle colours only.

**Config changes:**

- `default_color = '#1A3550'` (was `#000000`)
- `own_window_argb_value = 0` (fully transparent, was `120`)

**Text section changes:**

- Section headers: `${color #7AAEC0}` (horizon blue, was `#1e1e2e`)
- `$hr` separator: inherits header colour
- Body text: `${color #1A3550}` (deep navy)
- `font` unchanged: `DejaVu Sans Mono:size=10`

---

### mako

Full replacement of `airootfs/etc/skel/.config/mako/config`.

```ini
background-color=#1A2838
text-color=#D8EEF8
border-color=#87C8E8
border-size=2
border-radius=3
default-timeout=5000
anchor=top-right
margin=8
padding=10,14
```

---

### wmenu — `AB_Scripts/wmenu-launcher`

Update colour variables only. Script structure unchanged.

```bash
BG_NORMAL="#D8EEF8"
FG_NORMAL="#1A3550"
BG_SELECTED="#87C8E8"
FG_SELECTED="#1A3550"
```

---

### Wallpaper & autostart

1. Copy `~/Backgrounds/beach.jpg` → `airootfs/etc/skel/Backgrounds/beach.jpg`
2. Update `airootfs/etc/skel/.config/labwc/autostart`: change `swaybg` line from `seafront.jpg` to `beach.jpg`

---

## Files Changed / Added

| Action | Path |
|---|---|
| ADD | `airootfs/etc/skel/Backgrounds/beach.jpg` |
| ADD | `airootfs/etc/skel/.local/share/themes/AB_Summer/labwc/themerc` |
| ADD | `airootfs/etc/skel/.local/share/themes/AB_Summer/labwc/close.xbm` |
| ADD | `airootfs/etc/skel/.local/share/themes/AB_Summer/labwc/iconify.xbm` |
| ADD | `airootfs/etc/skel/.local/share/themes/AB_Summer/labwc/max.xbm` |
| MOD | `airootfs/etc/skel/.config/waybar/style.css` |
| ADD | `airootfs/etc/skel/.config/waybar/waybar-summer-style.css` (reference copy) |
| MOD | `airootfs/etc/skel/.config/mako/config` |
| MOD | `airootfs/etc/skel/.config/conky/conky.conf` |
| MOD | `airootfs/etc/skel/.config/labwc/rc.xml` (theme name) |
| MOD | `airootfs/etc/skel/.config/labwc/autostart` (wallpaper path) |
| MOD | `airootfs/etc/skel/AB_Scripts/wmenu-launcher` (colours) |

Existing `Lightwave` and `Seafront-Storm` themes untouched.

---

## Out of Scope

- No new packages required — all components already in `packages.x86_64`
- No changes to `profiledef.sh` or build scripts
- No GTK theme changes
- No rofi (using wmenu)
