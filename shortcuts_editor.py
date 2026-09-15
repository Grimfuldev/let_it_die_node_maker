#!/usr/bin/env python3
"""Small Shortcuts.ini editor launched by Let It Die Node Maker."""
from __future__ import annotations

import os
import sys
import configparser

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

ACTIONS = [
    ("delete_sticker", "Despawn sticker"),
    ("cancel_connect", "Cancel port connect"),
    ("center_camera", "Center camera"),
    ("port_top_left", "Focus top-left port"),
    ("port_top_mid", "Focus top-mid port"),
    ("port_top_right", "Focus top-right port"),
    ("port_und_left", "Focus bottom-left port"),
    ("port_und_mid", "Focus bottom-mid port"),
    ("port_und_right", "Focus bottom-right port"),
    ("join_elevator", "Shift+click join elevator"),
    ("update_node", "Update focused node"),
    ("toggle_floor", "Toggle floor ruler"),
    ("toggle_hide", "Toggle hide stickers"),
    ("toggle_lock", "Toggle lock stickers"),
    ("toggle_sticker_big", "Toggle sticker Big"),
    ("add_sticker", "Add sticker"),
    ("cycle_port_color", "Cycle port color"),
    ("cycle_port_gate", "Cycle port lock"),
]

FIXED_COMMANDS = [
    ("CTRL + S", "Export JSON"),
    ("CTRL + R", "Render map PNG"),
    ("CTRL + F", "Open search"),
    ("DEL", "Delete selected node (or sticker)"),
    ("ESC", "Clear selection / blur field"),
    ("TAB", "Next text field"),
    ("+ / =", "Zoom in"),
    ("-", "Zoom out"),
    ("Mouse wheel", "Zoom grid (or catalog scroll)"),
    ("MMB / empty drag", "Pan camera"),
    ("RMB on grid sticker", "Despawn that sticker"),
    ("RMB empty grid", "Set sticker X/Y"),
    ("RMB 2s on path color", "Clear that path route"),
    ("Hold V + click neighbour dot", "Insert path dot between"),
    ("Double-click path dot", "Flip path arrow direction"),
]

VALID_LABELS = {
    "LSHIFT": "SHIFT", "RSHIFT": "SHIFT", "LCTRL": "CTRL", "RCTRL": "CTRL",
    "SPACE": "SPACE", "BACKSPACE": "BACKSPACE", "DELETE": "DEL",
    "RETURN": "ENTER", "KP_ENTER": "ENTER",
    "PERIOD": ".", "COMMA": ",", "KPERIOD": ".", "KCOMMA": ",",
}
for _c in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
    VALID_LABELS[_c] = _c
for _d in "0123456789":
    VALID_LABELS[_d] = _d
    VALID_LABELS["KP_" + _d] = _d

ALLOWED = set(VALID_LABELS.keys())

DEFAULT_BINDS = {
    "delete_sticker": "BACKSPACE",
    "cancel_connect": "X",
    "center_camera": "SPACE",
    "port_top_left": "Q",
    "port_top_mid": "W",
    "port_top_right": "E",
    "port_und_left": "A",
    "port_und_mid": "S",
    "port_und_right": "D",
    "join_elevator": "SHIFT",
    "update_node": "ENTER",
    "toggle_floor": "F",
    "toggle_hide": "H",
    "toggle_lock": "L",
    "toggle_sticker_big": "B",
    "add_sticker": "V",
    "cycle_port_color": "C",
    "cycle_port_gate": "Z",
}


def app_dir() -> str:
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def bundle_dir() -> str:
    if getattr(sys, "frozen", False):
        return getattr(sys, "_MEIPASS", app_dir())
    return app_dir()


SCRIPT_DIR = app_dir()
INI_PATH = os.path.join(SCRIPT_DIR, "Shortcuts.ini")
BUNDLED_INI = os.path.join(bundle_dir(), "Shortcuts.ini")


def key_label(raw: str) -> str:
    t = (raw or "").strip().upper().replace(" ", "")
    if t in ("ENTER", "RETURN"):
        return "ENTER"
    if t in ("DEL", "DELETE"):
        return "DEL"
    if t in (".", "PERIOD"):
        return "."
    if t in (",", "COMMA"):
        return ","
    return VALID_LABELS.get(t, t)


def default_bindings() -> dict:
    return {k: DEFAULT_BINDS.get(k, "") for k, _ in ACTIONS}


def ensure_ini(path: str = "") -> str:
    path = path or INI_PATH
    if os.path.isfile(path):
        return path
    if os.path.isfile(BUNDLED_INI):
        return BUNDLED_INI
    write_ini(path, default_bindings())
    return path


def load_bindings(path: str) -> dict:
    out = default_bindings()
    if not os.path.isfile(path):
        return out
    cfg = configparser.ConfigParser()
    cfg.read(path, encoding="utf-8")
    sec = cfg["shortcuts"] if cfg.has_section("shortcuts") else None
    if not sec:
        return out
    for action, _title in ACTIONS:
        if action in sec:
            out[action] = key_label(sec.get(action, ""))
    return out


def write_ini(path: str, binds: dict):
    lines = [
        "[shortcuts]",
        "; Keys use pygame names: A, B, SPACE, BACKSPACE, RETURN, F, LSHIFT, ...",
        "; Edited by shortcuts_editor.py",
        "",
    ]
    save_name = {
        "SHIFT": "LSHIFT", "CTRL": "LCTRL", "ENTER": "RETURN",
        "DEL": "DELETE", ".": "PERIOD", ",": "COMMA",
    }
    for action, _title in ACTIONS:
        raw = binds.get(action, "")
        lines.append(f"{action} = {save_name.get(raw, raw)}")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def conflicts(binds: dict) -> set:
    seen = {}
    bad = set()
    for act, key in binds.items():
        if not key:
            continue
        if key in seen:
            bad.add(act)
            bad.add(seen[key])
        else:
            seen[key] = act
    return bad


ASSET_BG = "UI background.png"
ASSET_CURSOR = "let it die cursor.png"
ASSET_ICON = "uncle glasses ready.png"


def find_ui_asset(*names: str) -> str:
    roots = [
        os.path.join(SCRIPT_DIR, "UI_assets"),
        SCRIPT_DIR,
    ]
    for root in roots:
        for name in names:
            path = os.path.join(root, name)
            if os.path.isfile(path):
                return path
    return ""


def color_titlebar_black() -> None:
    if sys.platform != "win32":
        return
    try:
        import ctypes
        import pygame
        wm = pygame.display.get_wm_info()
        hwnd = wm.get("window")
        if not hwnd:
            return
        color = ctypes.c_int(0)
        dark = ctypes.c_int(1)
        dwm = ctypes.windll.dwmapi
        dwm.DwmSetWindowAttribute(hwnd, 20, ctypes.byref(dark), 4)
        dwm.DwmSetWindowAttribute(hwnd, 35, ctypes.byref(color), 4)
        dwm.DwmSetWindowAttribute(hwnd, 34, ctypes.byref(color), 4)
    except Exception:
        pass


def apply_editor_chrome() -> None:
    import pygame
    icon_path = find_ui_asset(ASSET_ICON)
    if icon_path:
        try:
            icon = pygame.image.load(icon_path).convert_alpha()
            pygame.display.set_icon(icon)
        except Exception:
            pass
    color_titlebar_black()
    cur_path = find_ui_asset(ASSET_CURSOR)
    if cur_path:
        try:
            cur = pygame.image.load(cur_path).convert_alpha()
            cur = pygame.transform.smoothscale(cur, (32, 32))
            try:
                pygame.mouse.set_cursor((0, 0), cur)
            except Exception:
                pygame.mouse.set_cursor(pygame.cursors.Cursor((0, 0), cur))
        except Exception:
            pass


def find_bg() -> str:
    return find_ui_asset(ASSET_BG)


def pygame_key_to_label(ev) -> str:
    import pygame
    name = pygame.key.name(ev.key).upper().replace(" ", "")
    if name in ("LEFT SHIFT", "RIGHT SHIFT", "LSHIFT", "RSHIFT", "SHIFT"):
        return "SHIFT"
    if name in ("LEFT CTRL", "RIGHT CTRL", "LCTRL", "RCTRL", "CTRL", "LEFT CTRL"):
        return "CTRL"
    if name in ("RETURN", "ENTER", "KP ENTER"):
        return "ENTER"
    if name in ("DELETE", "DEL"):
        return "DEL"
    if name in (".", "PERIOD"):
        return "."
    if name in (",", "COMMA"):
        return ","
    if name == "SPACE":
        return "SPACE"
    if name == "BACKSPACE":
        return "BACKSPACE"
    if len(name) == 1 and name.isalnum():
        return name
    # pygame name for digits / letters
    canon = name.replace("KEYPAD", "KP_")
    return VALID_LABELS.get(canon, "")


def run():
    import pygame
    from pygame import Rect
    from PIL import Image

    pygame.init()
    W, H = 520, 760
    fixed_scroll = 0
    dragging_fixed = False
    screen = pygame.display.set_mode((W, H))
    pygame.display.set_caption("Shortcuts")
    apply_editor_chrome()
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("segoeui,arial", 15)
    font_b = pygame.font.SysFont("segoeui,arial", 16, bold=True)
    font_sm = pygame.font.SysFont("segoeui,arial", 13)

    bg_surf = None
    bg = find_bg()
    if bg:
        try:
            im = Image.open(bg).convert("RGBA").resize((W, H), Image.Resampling.LANCZOS)
            bg_surf = pygame.image.frombuffer(im.tobytes(), im.size, "RGBA")
        except Exception:
            bg_surf = None

    ensure_ini(INI_PATH)
    binds = load_bindings(INI_PATH)
    waiting = None
    waiting_old = ""
    status = "Click a key, then press a new key."
    running = True
    applied = False
    hwnd = None
    prev_btns = 7
    ignore_until = pygame.time.get_ticks() + 250
    if sys.platform == "win32":
        try:
            import ctypes
            hwnd = pygame.display.get_wm_info().get("window")
        except Exception:
            hwnd = None

    def clicked_outside() -> bool:
        if sys.platform != "win32" or not hwnd:
            return False
        import ctypes
        class POINT(ctypes.Structure):
            _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]
        user32 = ctypes.windll.user32
        down = 0
        if user32.GetAsyncKeyState(0x01) & 0x8000:
            down |= 1
        if user32.GetAsyncKeyState(0x02) & 0x8000:
            down |= 2
        if user32.GetAsyncKeyState(0x04) & 0x8000:
            down |= 4
        nonlocal prev_btns
        fresh = down & ~prev_btns
        prev_btns = down
        if not fresh or pygame.time.get_ticks() < ignore_until:
            return False
        pt = POINT()
        user32.GetCursorPos(ctypes.byref(pt))
        under = user32.WindowFromPoint(pt)
        return bool(under) and int(under) != int(hwnd)

    while running:
        click = False
        mouse = pygame.mouse.get_pos()
        if clicked_outside():
            running = False
            break
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                running = False
            elif ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                click = True
            elif ev.type == pygame.MOUSEBUTTONUP and ev.button == 1:
                dragging_fixed = False
            elif ev.type == pygame.MOUSEWHEEL:
                fixed_scroll = max(0, fixed_scroll - int(ev.y))
            elif ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 3:
                if waiting:
                    binds[waiting] = waiting_old
                    waiting = None
                    status = "Cancelled."
            elif ev.type == pygame.KEYDOWN and waiting:
                mods = pygame.key.get_mods()
                extra = mods & ~(pygame.KMOD_SHIFT | pygame.KMOD_CTRL | pygame.KMOD_CAPS | pygame.KMOD_NUM)
                # reject combo: ctrl/shift held unless the key itself is shift/ctrl
                label = pygame_key_to_label(ev)
                is_mod_key = label in ("SHIFT", "CTRL")
                if (mods & pygame.KMOD_CTRL) and not is_mod_key:
                    status = "No Ctrl+key combos. Press one key."
                elif (mods & pygame.KMOD_SHIFT) and not is_mod_key:
                    status = "No Shift+key combos. Press one key."
                elif not label:
                    status = "Invalid key."
                else:
                    binds[waiting] = label
                    waiting = None
                    status = f"Set to {label}."

        if bg_surf:
            screen.blit(bg_surf, (0, 0))
        else:
            screen.fill((22, 22, 26))

        title = font_b.render("Shortcuts", True, (180, 200, 255))
        screen.blit(title, (16, 12))

        bad = conflicts(binds)
        y = 40
        row_h = 28
        for action, title in ACTIONS:
            lab = font_sm.render(title, True, (210, 210, 214))
            screen.blit(lab, (16, y + 5))
            val = "press key..." if waiting == action else (binds.get(action) or "—")
            br = Rect(300, y, 200, 24)
            on = waiting == action
            conflict = action in bad and waiting != action
            fill = (70, 40, 40) if conflict else ((60, 70, 40) if on else (40, 40, 48))
            border = (220, 80, 80) if conflict else ((220, 220, 140) if on else (90, 90, 100))
            pygame.draw.rect(screen, fill, br, border_radius=3)
            pygame.draw.rect(screen, border, br, 1, border_radius=3)
            col = (255, 120, 120) if conflict else (240, 240, 240)
            ts = font.render(val, True, col)
            screen.blit(ts, (br.x + 8, br.y + 3))
            if click and br.collidepoint(mouse) and waiting is None:
                waiting_old = binds.get(action, "")
                waiting = action
                status = f"Press a key for: {title}"
            y += row_h

        fy0 = y + 8
        pygame.draw.line(screen, (70, 70, 80), (16, fy0), (W - 16, fy0), 1)
        head = font_sm.render("Fixed commands (not remappable)", True, (160, 170, 190))
        screen.blit(head, (16, fy0 + 6))
        box = Rect(16, fy0 + 24, W - 32, H - 56 - (fy0 + 24))
        pygame.draw.rect(screen, (24, 24, 28), box, border_radius=3)
        pygame.draw.rect(screen, (70, 70, 78), box, 1, border_radius=3)
        line_h = 20
        max_vis = max(1, box.h // line_h)
        max_s = max(0, len(FIXED_COMMANDS) - max_vis)
        if click and box.collidepoint(mouse) and mouse[0] >= box.right - 12:
            dragging_fixed = True
        if dragging_fixed and box.h > 0:
            t = (mouse[1] - box.y) / max(1, box.h)
            fixed_scroll = int(max(0, min(max_s, t * (max_s + 1))))
        fixed_scroll = max(0, min(max_s, fixed_scroll))
        screen.set_clip(box)
        yy = box.y + 4
        for i in range(fixed_scroll, len(FIXED_COMMANDS)):
            if yy + line_h > box.bottom:
                break
            key, desc = FIXED_COMMANDS[i]
            screen.blit(font_sm.render(key, True, (200, 200, 140)), (box.x + 8, yy))
            screen.blit(font_sm.render(desc, True, (190, 190, 196)), (box.x + 168, yy))
            yy += line_h
        screen.set_clip(None)
        bar = Rect(box.right - 10, box.y + 2, 8, box.h - 4)
        pygame.draw.rect(screen, (48, 48, 54), bar, border_radius=3)
        if max_s > 0:
            th = max(16, int(bar.h * max_vis / max(1, len(FIXED_COMMANDS))))
            ty = bar.y + int((bar.h - th) * fixed_scroll / max_s)
            pygame.draw.rect(screen, (140, 140, 150), Rect(bar.x, ty, bar.w, th), border_radius=3)

        apply_ok = not bad
        ar = Rect(16, H - 48, 100, 28)
        cr = Rect(124, H - 48, 100, 28)
        dr = Rect(232, H - 48, 100, 28)
        pygame.draw.rect(screen, (48, 70, 48) if apply_ok else (40, 40, 44), ar, border_radius=3)
        pygame.draw.rect(screen, (140, 200, 140) if apply_ok else (80, 80, 80), ar, 1, border_radius=3)
        at = font.render("Apply", True, (230, 230, 230) if apply_ok else (110, 110, 110))
        screen.blit(at, (ar.x + (ar.w - at.get_width()) // 2, ar.y + 4))
        pygame.draw.rect(screen, (48, 48, 54), cr, border_radius=3)
        pygame.draw.rect(screen, (140, 140, 145), cr, 1, border_radius=3)
        ct = font.render("Cancel", True, (230, 230, 230))
        screen.blit(ct, (cr.x + (cr.w - ct.get_width()) // 2, cr.y + 4))
        pygame.draw.rect(screen, (48, 48, 54), dr, border_radius=3)
        pygame.draw.rect(screen, (140, 140, 145), dr, 1, border_radius=3)
        dt = font.render("Default", True, (230, 230, 230))
        screen.blit(dt, (dr.x + (dr.w - dt.get_width()) // 2, dr.y + 4))

        st = font_sm.render(status, True, (200, 200, 160))
        screen.blit(st, (348, H - 42))

        if click and ar.collidepoint(mouse) and apply_ok:
            write_ini(INI_PATH, binds)
            applied = True
            running = False
        if click and cr.collidepoint(mouse):
            running = False
        if click and dr.collidepoint(mouse):
            binds = default_bindings()
            waiting = None
            status = "Restored defaults (Apply to save)."

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    return 0 if applied else 1


if __name__ == "__main__":
    sys.exit(run())