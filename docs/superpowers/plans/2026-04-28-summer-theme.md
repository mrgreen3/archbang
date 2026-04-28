# Summer Theme Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Apply the AB_Summer beach-palette theme to labwc, waybar, conky, mako, and wmenu for the ArchBang summer release.

**Architecture:** All config files live in `airootfs/etc/skel/` and are copied to new users' home dirs at first login. Theme is additive (new AB_Summer labwc theme dir) except old Lightwave/Seafront themes and seafront.jpg wallpaper which are deleted. No build script changes needed.

**Tech Stack:** labwc themerc, waybar CSS, conky Lua config, mako INI, bash (wmenu launcher)

---

## File Map

| Action | Path |
|---|---|
| COPY | `~/Backgrounds/beach.jpg` → `airootfs/etc/skel/Backgrounds/beach.jpg` |
| DEL | `airootfs/etc/skel/Backgrounds/seafront.jpg` |
| CREATE | `airootfs/etc/skel/.local/share/themes/AB_Summer/labwc/themerc` |
| COPY | `themes/Lightwave/labwc/*.xbm` → `themes/AB_Summer/labwc/` |
| DEL | `airootfs/etc/skel/.local/share/themes/Lightwave/` |
| DEL | `airootfs/etc/skel/.local/share/themes/Seafront/` |
| MOD | `airootfs/etc/skel/.config/labwc/rc.xml` — theme name |
| MOD | `airootfs/etc/skel/.config/labwc/autostart` — wallpaper path |
| MOD | `airootfs/etc/skel/.config/waybar/style.css` — full palette swap |
| CREATE | `airootfs/etc/skel/.config/waybar/waybar-summer-style.css` — reference copy |
| MOD | `airootfs/etc/skel/.config/mako/config` — full replacement |
| MOD | `airootfs/etc/skel/.config/conky/conky.conf` — colours only |
| MOD | `airootfs/etc/skel/AB_Scripts/wmenu-launcher` — colour vars |

---

## Task 1: Wallpaper

**Files:**
- Create: `airootfs/etc/skel/Backgrounds/beach.jpg`
- Delete: `airootfs/etc/skel/Backgrounds/seafront.jpg`
- Modify: `airootfs/etc/skel/.config/labwc/autostart`

- [ ] **Step 1: Verify current wallpaper line**

```bash
grep swaybg ~/archbang/airootfs/etc/skel/.config/labwc/autostart
```
Expected: `swaybg -i $HOME/Backgrounds/seafront.jpg -m fill &`

- [ ] **Step 2: Copy beach.jpg into skel**

```bash
cp ~/Backgrounds/beach.jpg ~/archbang/airootfs/etc/skel/Backgrounds/beach.jpg
```

- [ ] **Step 3: Delete seafront.jpg**

```bash
rm ~/archbang/airootfs/etc/skel/Backgrounds/seafront.jpg
```

- [ ] **Step 4: Update autostart wallpaper path**

In `airootfs/etc/skel/.config/labwc/autostart`, change line 7:

```bash
# Before
swaybg -i $HOME/Backgrounds/seafront.jpg -m fill &

# After
swaybg -i $HOME/Backgrounds/beach.jpg -m fill &
```

- [ ] **Step 5: Verify**

```bash
grep swaybg ~/archbang/airootfs/etc/skel/.config/labwc/autostart
ls ~/archbang/airootfs/etc/skel/Backgrounds/
```
Expected: `beach.jpg` only.

- [ ] **Step 6: Commit**

```bash
cd ~/archbang
git add airootfs/etc/skel/Backgrounds/beach.jpg \
        airootfs/etc/skel/.config/labwc/autostart
git rm airootfs/etc/skel/Backgrounds/seafront.jpg
git commit -m "theme: replace seafront wallpaper with beach.jpg"
```

---

## Task 2: AB_Summer labwc theme

**Files:**
- Create: `airootfs/etc/skel/.local/share/themes/AB_Summer/labwc/themerc`
- Create: `airootfs/etc/skel/.local/share/themes/AB_Summer/labwc/close.xbm`
- Create: `airootfs/etc/skel/.local/share/themes/AB_Summer/labwc/iconify.xbm`
- Create: `airootfs/etc/skel/.local/share/themes/AB_Summer/labwc/max.xbm`
- Delete: `airootfs/etc/skel/.local/share/themes/Lightwave/`
- Delete: `airootfs/etc/skel/.local/share/themes/Seafront/`
- Modify: `airootfs/etc/skel/.config/labwc/rc.xml`

- [ ] **Step 1: Create theme directory and copy XBM button bitmaps**

```bash
mkdir -p ~/archbang/airootfs/etc/skel/.local/share/themes/AB_Summer/labwc
cp ~/archbang/airootfs/etc/skel/.local/share/themes/Lightwave/labwc/*.xbm \
   ~/archbang/airootfs/etc/skel/.local/share/themes/AB_Summer/labwc/
```

- [ ] **Step 2: Write themerc**

Create `airootfs/etc/skel/.local/share/themes/AB_Summer/labwc/themerc` with this exact content:

```ini
# AB_Summer theme configuration for labwc
# Beach palette from ~/Backgrounds/beach.jpg

border.width: 0

window.active.border.color: #87C8E8
window.inactive.border.color: #D8EEF8

# ARGB: sky blue at ~33% opacity for frosted titlebar effect
window.active.title.bg.color: #87C8E855
window.inactive.title.bg.color: #D8EEF833
window.*.title.bg: Solid

window.active.label.text.color: #1A3550
window.inactive.label.text.color: #7AAEC0
window.label.text.justify: left

window.button.width: 26
window.button.height: 26
window.button.spacing: 0

# ocean blue iconify
window.active.button.iconify.unpressed.image.color: #A8DFF0
window.active.button.iconify.pressed.image.color: #A8DFF0
window.active.button.iconify.hover.image.color: #87C8E8

# sand max
window.active.button.max.unpressed.image.color: #D4C8A4
window.active.button.max.pressed.image.color: #D4C8A4
window.active.button.max.hover.image.color: #EDE8DF

# coral close
window.active.button.close.unpressed.image.color: #E88A8A
window.active.button.close.pressed.image.color: #E88A8A
window.active.button.close.hover.image.color: #FF6B6B

window.inactive.button.unpressed.image.color: #7AAEC099

window.active.shadow.size: 60
window.inactive.shadow.size: 30
window.active.shadow.color: #00000022
window.inactive.shadow.color: #00000011

menu.items.bg.color: #D8EEF8CC
menu.items.text.color: #1A3550
menu.items.active.bg.color: #87C8E8CC
menu.items.active.text.color: #1A3550
menu.border.color: #87C8E8
menu.border.width: 0

menu.overlap.x: -5
menu.overlap.y: 0

osd.bg.color: #D8EEF8
osd.border.color: #87C8E8
osd.border.width: 1
osd.label.text.color: #1A3550
```

- [ ] **Step 3: Update rc.xml theme name**

In `airootfs/etc/skel/.config/labwc/rc.xml`, change the theme block:

```xml
<!-- Before -->
<name>Lightwave</name>

<!-- After -->
<name>AB_Summer</name>
```

- [ ] **Step 4: Delete old theme directories**

```bash
cd ~/archbang
git rm -r airootfs/etc/skel/.local/share/themes/Lightwave/
git rm -r airootfs/etc/skel/.local/share/themes/Seafront/
```

- [ ] **Step 5: Verify**

```bash
grep '<name>' ~/archbang/airootfs/etc/skel/.config/labwc/rc.xml
ls ~/archbang/airootfs/etc/skel/.local/share/themes/
ls ~/archbang/airootfs/etc/skel/.local/share/themes/AB_Summer/labwc/
```
Expected: rc.xml shows `AB_Summer`, themes dir has `AB_Summer` only, labwc dir has `themerc close.xbm iconify.xbm max.xbm`.

- [ ] **Step 6: Commit**

```bash
cd ~/archbang
git add airootfs/etc/skel/.local/share/themes/AB_Summer/ \
        airootfs/etc/skel/.config/labwc/rc.xml
git commit -m "theme: add AB_Summer labwc theme, remove Lightwave and Seafront"
```

---

## Task 3: Waybar CSS

**Files:**
- Modify: `airootfs/etc/skel/.config/waybar/style.css`
- Create: `airootfs/etc/skel/.config/waybar/waybar-summer-style.css`

- [ ] **Step 1: Replace style.css with summer palette**

Write `airootfs/etc/skel/.config/waybar/style.css` with this exact content:

```css
/* ---------- Summer Palette (from beach.jpg) ---------- */
@define-color bg      rgba(135, 200, 232, 0.28);
@define-color surface rgba(168, 223, 240, 0.40);
@define-color border  rgba(255, 255, 255, 0.38);
@define-color fg      #1A3550;
@define-color accent  #87C8E8;
@define-color subtext #7AAEC0;
@define-color red     #E88A8A;
@define-color green   #27AE60;
@define-color yellow  #D4C8A4;

/* ---------- Base styling ---------- */
* {
    border-radius: 0;
}

window#waybar {
    background-color: @bg;
    color: @fg;
    border: none;
    border-top: 1px solid @border;
    padding: 5px 0;
}

/* ---------- Workspaces ---------- */
#workspaces {
    margin: 0;
}

#workspaces button {
    padding: 0 5px;
    margin: 0;
    color: @fg;
    background: transparent;
    border: none;
}

#workspaces button.active {
    color: @fg;
    background-color: @surface;
    padding: 0 5px;
    margin: 0;
    font-weight: bold;
}

#workspaces button.urgent {
    color: #FFFFFF;
    background-color: @red;
}

/* ---------- Window title ---------- */
#window {
    color: @fg;
    padding: 0 10px;
}

/* ---------- Clock ---------- */
#clock {
    color: @fg;
    background-color: @surface;
    font-weight: normal;
    padding: 4px 10px;
    margin: 0;
}

#clock:hover {
    opacity: 0.8;
}

/* ---------- Common section styling ---------- */
#tray, #pulseaudio, #battery {
    margin: 0;
    padding: 0 5px;
}

/* ---------- System tray ---------- */
#tray {
    color: @fg;
}

/* ---------- Pulseaudio ---------- */
#pulseaudio {
    color: @fg;
    font-size: 22px;
}

#pulseaudio.muted {
    color: @red;
}

/* ---------- Battery ---------- */
#battery {
    color: @fg;
    font-size: 22px;
}

#battery.warning {
    color: @yellow;
}

#battery.critical {
    color: @red;
}

#battery.charging {
    color: @green;
}

/* ---------- Taskbar ---------- */
#taskbar {
    margin: 0;
    padding: 0 5px;
}

#taskbar button {
    padding: 0 8px;
    margin: 0;
    color: @fg;
    background: transparent;
    border: none;
}

#taskbar button.active {
    color: @fg;
    background-color: @surface;
}

#taskbar button:hover {
    opacity: 0.8;
}

#taskbar button:not(.active) {
    color: @subtext;
}
```

- [ ] **Step 2: Copy as named reference**

```bash
cp ~/archbang/airootfs/etc/skel/.config/waybar/style.css \
   ~/archbang/airootfs/etc/skel/.config/waybar/waybar-summer-style.css
```

- [ ] **Step 3: Verify**

```bash
grep 'rgba(135' ~/archbang/airootfs/etc/skel/.config/waybar/style.css
grep 'rgba(135' ~/archbang/airootfs/etc/skel/.config/waybar/waybar-summer-style.css
```
Expected: both files show the `@define-color bg` line.

- [ ] **Step 4: Commit**

```bash
cd ~/archbang
git add airootfs/etc/skel/.config/waybar/style.css \
        airootfs/etc/skel/.config/waybar/waybar-summer-style.css
git commit -m "theme: update waybar CSS to summer beach palette"
```

---

## Task 4: Mako

**Files:**
- Modify: `airootfs/etc/skel/.config/mako/config`

- [ ] **Step 1: Verify current config**

```bash
cat ~/archbang/airootfs/etc/skel/.config/mako/config
```
Expected: shows `background-color=#1a1a2a` (Seafront-Storm).

- [ ] **Step 2: Replace mako config**

Write `airootfs/etc/skel/.config/mako/config` with this exact content:

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

- [ ] **Step 3: Verify**

```bash
grep 'border-color' ~/archbang/airootfs/etc/skel/.config/mako/config
```
Expected: `border-color=#87C8E8`

- [ ] **Step 4: Commit**

```bash
cd ~/archbang
git add airootfs/etc/skel/.config/mako/config
git commit -m "theme: update mako to summer palette"
```

---

## Task 5: Conky

**Files:**
- Modify: `airootfs/etc/skel/.config/conky/conky.conf`

- [ ] **Step 1: Verify current colours**

```bash
grep 'default_color\|argb_value\|1e1e2e' \
    ~/archbang/airootfs/etc/skel/.config/conky/conky.conf
```
Expected: `default_color = '#000000'`, `own_window_argb_value = 120`, two lines with `#1e1e2e`.

- [ ] **Step 2: Update default_color**

In `airootfs/etc/skel/.config/conky/conky.conf` line 6, change:

```lua
-- Before
default_color = '#000000',

-- After
default_color = '#1A3550',
```

- [ ] **Step 3: Update argb_value**

Line 30, change:

```lua
-- Before
own_window_argb_value = 120,

-- After
own_window_argb_value = 0,
```

- [ ] **Step 4: Update section header colours in conky.text**

Line 43, change:

```
-- Before
${font DejaVu Sans Mono:bold:size=10}${color #1e1e2e}Keyboard Shortcuts ${color #1e1e2e}$hr${color}${font DejaVu Sans Mono:size=10}

-- After
${font DejaVu Sans Mono:bold:size=10}${color #7AAEC0}Keyboard Shortcuts ${color #7AAEC0}$hr${color}${font DejaVu Sans Mono:size=10}
```

Line 56, change:

```
-- Before
${font DejaVu Sans Mono:bold:size=10}${color #1e1e2e}Window Controls ${color #1e1e2e}$hr${color}${font DejaVu Sans Mono:size=10}

-- After
${font DejaVu Sans Mono:bold:size=10}${color #7AAEC0}Window Controls ${color #7AAEC0}$hr${color}${font DejaVu Sans Mono:size=10}
```

- [ ] **Step 5: Verify**

```bash
grep 'default_color\|argb_value\|7AAEC0' \
    ~/archbang/airootfs/etc/skel/.config/conky/conky.conf
```
Expected: `default_color = '#1A3550'`, `own_window_argb_value = 0`, two lines with `#7AAEC0`.

- [ ] **Step 6: Commit**

```bash
cd ~/archbang
git add airootfs/etc/skel/.config/conky/conky.conf
git commit -m "theme: restyle conky with summer beach palette"
```

---

## Task 6: wmenu

**Files:**
- Modify: `airootfs/etc/skel/AB_Scripts/wmenu-launcher`

- [ ] **Step 1: Verify current colours**

```bash
grep 'BG_\|FG_' ~/archbang/airootfs/etc/skel/AB_Scripts/wmenu-launcher
```
Expected: `BG_NORMAL="#0F1419"`, `FG_NORMAL="#F0F0F0"`, `BG_SELECTED="#6BB3E5"`, `FG_SELECTED="#0A0A0A"`.

- [ ] **Step 2: Update colour variables**

In `airootfs/etc/skel/AB_Scripts/wmenu-launcher`, replace the four colour lines:

```bash
# Before
BG_NORMAL="#0F1419"
FG_NORMAL="#F0F0F0"
BG_SELECTED="#6BB3E5"
FG_SELECTED="#0A0A0A"

# After
BG_NORMAL="#D8EEF8"
FG_NORMAL="#1A3550"
BG_SELECTED="#87C8E8"
FG_SELECTED="#1A3550"
```

- [ ] **Step 3: Verify**

```bash
grep 'BG_\|FG_' ~/archbang/airootfs/etc/skel/AB_Scripts/wmenu-launcher
```
Expected: all four lines show summer values.

- [ ] **Step 4: Commit**

```bash
cd ~/archbang
git add airootfs/etc/skel/AB_Scripts/wmenu-launcher
git commit -m "theme: update wmenu colours to summer beach palette"
```
