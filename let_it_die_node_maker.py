from __future__ import annotations

import json
import math
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

from PIL import Image, ImageDraw, ImageFont

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

GRID = 15
MAP_W = 2090
FLOOR_H = 175
NODE_W, NODE_H = 228, 90
CONNECT_W, CONNECT_H = 15, 22
CONNECT_OVERLAP = 8
STAR_DRAW = 36
STAR_NUM = 13
ELEV_S = 35
FLOOR_BOX = (60, 28)

VERSION = "v0.1"
WINDOW_TITLE = f"Let It Die Node Maker {VERSION}"

def app_dir() -> str:
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def bundle_dir() -> str:
    if getattr(sys, "frozen", False):
        return getattr(sys, "_MEIPASS", app_dir())
    return app_dir()


SCRIPT_DIR = app_dir()
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

def _dir(*parts: str) -> str:
    return os.path.join(*parts)


def resolve_data_dir(name: str) -> str:
    for root in (SCRIPT_DIR, bundle_dir()):
        p = _dir(root, name)
        if os.path.isdir(p):
            return p
    return _dir(SCRIPT_DIR, name)


def resolve_bundled_dir(name: str) -> str:
    for root in (bundle_dir(), SCRIPT_DIR):
        p = _dir(root, name)
        if os.path.isdir(p):
            return p
    return _dir(bundle_dir(), name)


GRID_ASSETS_DIR = resolve_data_dir("Grid_assets")
STICKER_ASSETS_DIR = resolve_data_dir("Sticker_assets")
THUMBS_DIR = _dir(STICKER_ASSETS_DIR, "catalog_thumbnails")
UI_ASSETS_DIR = resolve_data_dir("UI_assets")
UI_ASSETS_BUNDLE = _dir(bundle_dir(), "UI_assets")
FALLBACK_ASSETS_DIR = resolve_bundled_dir("Fallback_folder_assets")
FALLBACK_GRID_DIR = _dir(FALLBACK_ASSETS_DIR, "Grid_assets")
FALLBACK_STICKER_DIR = _dir(FALLBACK_ASSETS_DIR, "Sticker_assets")
DEFAULT_JSON = _dir(SCRIPT_DIR, "lid_map_images.json")


def placeholder_json_path() -> str:
    for p in (
        _dir(SCRIPT_DIR, "Placeholder.json"),
        _dir(FALLBACK_ASSETS_DIR, "Placeholder.json"),
        _dir(bundle_dir(), "Fallback_folder_assets", "Placeholder.json"),
    ):
        if p and os.path.isfile(p):
            return p
    return ""


ASSET_CURSOR = "let it die cursor.png"
ASSET_BG = "UI background.png"
ASSET_ICON = "uncle glasses ready.png"

def _first_existing(paths):
    for p in paths:
        if p and os.path.isfile(p):
            return p
    return None


def resolve_fonts():
    """Find TTF files on Windows/Linux/macOS, or next to this script."""
    windir = os.environ.get("WINDIR", r"C:\Windows")
    win_fonts = os.path.join(windir, "Fonts")
    candidates_reg = [
        os.path.join(SCRIPT_DIR, "DejaVuSans.ttf"),
        os.path.join(SCRIPT_DIR, "arial.ttf"),
        os.path.join(SCRIPT_DIR, "fonts", "DejaVuSans.ttf"),
        os.path.join(win_fonts, "arial.ttf"),
        os.path.join(win_fonts, "segoeui.ttf"),
        os.path.join(win_fonts, "tahoma.ttf"),
        os.path.join(win_fonts, "calibri.ttf"),
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/Library/Fonts/Arial.ttf",
    ]
    candidates_bold = [
        os.path.join(SCRIPT_DIR, "DejaVuSans-Bold.ttf"),
        os.path.join(SCRIPT_DIR, "arialbd.ttf"),
        os.path.join(SCRIPT_DIR, "fonts", "DejaVuSans-Bold.ttf"),
        os.path.join(win_fonts, "arialbd.ttf"),
        os.path.join(win_fonts, "segoeuib.ttf"),
        os.path.join(win_fonts, "tahomabd.ttf"),
        os.path.join(win_fonts, "calibrib.ttf"),
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "/Library/Fonts/Arial Bold.ttf",
    ]
    regular = _first_existing(candidates_reg)
    bold = _first_existing(candidates_bold) or regular
    return regular, bold


FONT_PATH, FONT_BOLD = resolve_fonts()

PORT_KEYS = [
    "top_left",
    "top_mid",
    "top_right",
    "und_left",
    "und_mid",
    "und_right",
]
EDGE_TARGET = "__EDGE__"

CONN_COLORS = {
    "orange": (0xE5, 0x78, 0x0E),
    "cyan": (0x02, 0xF2, 0xC4),
    "purple": (0x88, 0x65, 0xE8),
    "green": (0x68, 0xEF, 0x39),
    "blue": (0x00, 0x42, 0xFC),
    "magenta": (0xED, 0x23, 0x86),
    "pink": (0xDF, 0x9E, 0xF2),
}

ELEVATOR_KINDS = ["none", "blue", "green", "purple", "pink", "brown"]
ELEVATOR_HEX = {
    "blue": (0x50, 0x4E, 0x7D),
    "green": (0x43, 0x5F, 0x62),
    "purple": (0x60, 0x52, 0x88),
    "pink": (0x6C, 0x45, 0x66),
    "brown": (0x68, 0x67, 0x45),
}

MATERIALS = ["Iron", "Aluminum", "Copper", "Wood", "Oil", "Fabric", "None", "Empty", "ALL"]
MATERIAL_LABELS = {"ALL": "All", "Empty": "Empty"}
COLOR_ORDER = ["cyan", "blue", "purple", "orange", "green", "pink"]
GATES = ["open", "closed-gate", "gate-up", "gate-down"]
GATE_LABELS = {
    "none": "open",
    "open": "open",
    "open-gate": "open",
    "closed-gate": "closed",
    "gate-up": "gate-up",
    "gate-down": "gate-down",
}

FOOTER = "Make your own Let It Die maps: github.com/Grimfuldev/let_it_die_node_maker"

PATH_DOT_COLORS = ["Red_Path", "Orange_Path", "White_Path", "Cyan_Path", "Green_Path"]
PATH_DOT_RGB = {
    "Red_Path": (210, 48, 48),
    "Orange_Path": (230, 140, 36),
    "White_Path": (236, 236, 240),
    "Cyan_Path": (40, 210, 210),
    "Green_Path": (56, 190, 70),
}
PATH_ROUTE_DIR = "Path_route"
PORT_LINE_W = 3.5
PATH_LINE_W = 3
SCROLL_W = 14


def floor_label(idx: int) -> str:
    if idx <= 0:
        return "B1"
    return f"{idx}F"


def clamp(v, a, b):
    return max(a, min(b, v))


def snap(v: int, g: int = GRID) -> int:
    return int(round(v / g) * g)


def _tk_set_icon(root) -> None:
    try:
        import tkinter as tk
        ico = ""
        for root_dir in (UI_ASSETS_DIR, UI_ASSETS_BUNDLE, SCRIPT_DIR, bundle_dir()):
            for name in ("uncle glasses ready.png", "lidico.ico"):
                p = os.path.join(root_dir, name)
                if os.path.isfile(p):
                    ico = p
                    break
            if ico:
                break
        if not ico:
            return
        if ico.lower().endswith(".ico"):
            root.iconbitmap(ico)
        else:
            img = tk.PhotoImage(file=ico)
            root.iconphoto(True, img)
            root._lid_icon = img
    except Exception:
        pass


def native_file_dialog(mode="open", title="Open", filetypes=None, initialdir=None, initialfile=None):
    """Windows-friendly file/folder popup. mode: open | save | dir."""
    initialdir = initialdir or SCRIPT_DIR
    filetypes = filetypes or [("JSON", "*.json"), ("All files", "*.*")]
    try:
        import tkinter as tk
        from tkinter import filedialog
        root = tk.Tk()
        root.withdraw()
        try:
            root.wm_attributes("-topmost", 1)
        except Exception:
            pass
        _tk_set_icon(root)
        if mode == "dir":
            path = filedialog.askdirectory(title=title, initialdir=initialdir)
        elif mode == "save":
            path = filedialog.asksaveasfilename(
                title=title, initialdir=initialdir, initialfile=initialfile or "",
                defaultextension=".json", filetypes=filetypes,
            )
        else:
            path = filedialog.askopenfilename(
                title=title, initialdir=initialdir, filetypes=filetypes,
            )
        root.destroy()
        return path or ""
    except Exception:
        return ""


SHORTCUTS_PATH = _dir(SCRIPT_DIR, "Shortcuts.ini")

PORT_HOTKEY_ACTIONS = {
    "port_top_left": "top_left",
    "port_top_mid": "top_mid",
    "port_top_right": "top_right",
    "port_und_left": "und_left",
    "port_und_mid": "und_mid",
    "port_und_right": "und_right",
}


def load_shortcuts(path: str = "") -> Dict[str, int]:
    """Map action name -> pygame key constant. Empty if the ini is missing."""
    path = path or SHORTCUTS_PATH
    if not path or not os.path.isfile(path):
        bundled = os.path.join(bundle_dir(), "Shortcuts.ini")
        path = bundled if os.path.isfile(bundled) else path
    out: Dict[str, int] = {}
    if not path or not os.path.isfile(path):
        return out
    try:
        import pygame
        import configparser
        cfg = configparser.ConfigParser()
        cfg.read(path, encoding="utf-8")
        sec = cfg["shortcuts"] if cfg.has_section("shortcuts") else cfg[cfg.default_section]
        for action, raw in sec.items():
            name = str(raw).strip().upper().replace(" ", "")
            if not name:
                continue
            key = getattr(pygame, "K_" + name, None)
            if key is None:
                key = getattr(pygame, "K_" + name.lower(), None)
            if key is not None:
                out[action.lower()] = int(key)
    except Exception:
        return {}
    return out


def native_yes_no(title: str, message: str) -> bool:
    try:
        import tkinter as tk
        from tkinter import messagebox
        root = tk.Tk()
        root.withdraw()
        try:
            root.wm_attributes("-topmost", 1)
        except Exception:
            pass
        _tk_set_icon(root)
        ans = messagebox.askyesno(title, message)
        root.destroy()
        return bool(ans)
    except Exception:
        return False


def load_font(size: int, bold: bool = False):
    path = FONT_BOLD if bold else FONT_PATH
    if path:
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            pass
    try:
        return ImageFont.truetype("arial.ttf", size)
    except Exception:
        return ImageFont.load_default()


# ---------------------------------------------------------------------------
# Asset folders (recursive)
# ---------------------------------------------------------------------------

IGNORE_ASSET_DIRS = {"fallback", "catalog_thumbnails", "__pycache__"}

def walk_sticker_catalog(root: str, starred: Optional[set] = None) -> Tuple[List[tuple], List[str]]:
    """DFS: folder title, then PNGs in that folder, then child folders.
    Starred folders (rel path) sort first among siblings, then A–Z."""
    entries: List[tuple] = []
    names: List[str] = []
    starred = {str(s).replace("\\", "/").lower() for s in (starred or set())}

    def walk(folder: str, depth: int, rel: str):
        if not folder or not os.path.isdir(folder):
            return
        try:
            kids = os.listdir(folder)
        except OSError:
            return
        files, dirs = [], []
        for fn in kids:
            if fn.lower() in IGNORE_ASSET_DIRS:
                continue
            p = os.path.join(folder, fn)
            if os.path.isdir(p):
                dirs.append((fn, p))
            elif fn.lower().endswith(".png"):
                files.append((os.path.splitext(fn)[0], p))
        files.sort(key=lambda t: t[0].lower())
        dirs.sort(key=lambda t: (
            0 if ((rel + "/" + t[0] if rel else t[0]).replace("\\", "/").lower() in starred) else 1,
            t[0].lower(),
        ))
        if depth > 0:
            entries.append(("cat", os.path.basename(folder), depth, rel))
        for name, _p in files:
            entries.append(("item", name, depth, rel))
            names.append(name)
        for fn, p in dirs:
            child = fn if not rel else rel + "/" + fn
            walk(p, depth + 1, child.replace("\\", "/"))

    walk(root, 0, "")
    return entries, names


def catalog_rows(entries: List[Tuple[str, str]], cols: int = 5) -> List[Tuple[str, object]]:
    rows: List[Tuple[str, object]] = []
    bucket: List[str] = []

    def flush():
        if bucket:
            rows.append(("items", list(bucket)))
            bucket.clear()

    for ent in entries:
        kind = ent[0]
        val = ent[1]
        depth = ent[2] if len(ent) > 2 else 1
        if kind == "cat":
            flush()
            rel = ent[3] if len(ent) > 3 else val
            rows.append(("cat", (val, depth, rel)))
        else:
            bucket.append(val)
            if len(bucket) >= cols:
                flush()
    flush()
    return rows


def scan_png_tree(folder: str, skip_fallback: bool = True) -> Dict[str, str]:
    """Map basename -> path. Case-insensitive keys. Skips Fallback/thumbs."""
    out: Dict[str, str] = {}
    if not folder or not os.path.isdir(folder):
        return out
    for root, dirs, files in os.walk(folder):
        dirs[:] = [d for d in dirs if d.lower() not in IGNORE_ASSET_DIRS]
        if skip_fallback and "fallback" in os.path.normcase(root).split(os.sep):
            continue
        for fn in files:
            if not fn.lower().endswith(".png"):
                continue
            key = os.path.splitext(fn)[0]
            path = os.path.join(root, fn)
            out[key] = path
            out[key.lower()] = path
    return out


def lookup_png(index: Dict[str, str], *names: str) -> str:
    for n in names:
        if not n:
            continue
        p = index.get(n) or index.get(n.lower())
        if p and os.path.isfile(p):
            return p
    return ""


def star_count(stars: str) -> int:
    s = (stars or "").strip()
    if s.isdigit():
        return max(1, int(s))
    return 1


def material_file_names(kind: str, stars: str):
    k = kind or "None"
    s = (stars or "").strip()
    names = []
    if not s:
        names += [f"{k}_stack", f"{k.lower()}_stack", f"{k}_Stack"]
        names += [f"{k}_1", f"{k.lower()}_1"]
    else:
        n = star_count(s)
        names += [f"{k}_{n}", f"{k.lower()}_{n}", f"{k}_{n}".title()]
    names += [k, k.lower()]
    return tuple(names)


def elevator_file_names(kind: str):
    return (f"Elevator_{kind}", f"elevator_{kind}", kind, kind.capitalize())


def _copy_missing_tree(src: str, dest: str) -> None:
    """Copy files from src into dest. Never overwrite an existing dest file."""
    if not src or not os.path.isdir(src):
        return
    os.makedirs(dest, exist_ok=True)
    for root, dirs, files in os.walk(src):
        dirs[:] = [d for d in dirs if d.lower() not in IGNORE_ASSET_DIRS]
        rel = os.path.relpath(root, src)
        out_dir = dest if rel in (".", "") else os.path.join(dest, rel)
        os.makedirs(out_dir, exist_ok=True)
        for fn in files:
            dst = os.path.join(out_dir, fn)
            if os.path.isfile(dst):
                continue
            src_f = os.path.join(root, fn)
            try:
                shutil.copy2(src_f, dst)
            except Exception:
                pass


def ensure_user_asset_folders():
    os.makedirs(GRID_ASSETS_DIR, exist_ok=True)
    os.makedirs(STICKER_ASSETS_DIR, exist_ok=True)
    os.makedirs(THUMBS_DIR, exist_ok=True)
    _copy_missing_tree(FALLBACK_GRID_DIR, GRID_ASSETS_DIR)
    _copy_missing_tree(FALLBACK_STICKER_DIR, STICKER_ASSETS_DIR)


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

def blank_ports() -> Dict[str, dict]:
    return {
        k: {"target": "", "color": "cyan", "gate": "none"}
        for k in PORT_KEYS
    }


@dataclass
class Node:
    id: str
    title: str
    floor: int
    x: int  # world px, top-left, snapped
    material: str = "Empty"
    stars: str = ""
    elevator: str = "none"
    elevator_a: str = ""
    elevator_b: str = ""
    roof: bool = False
    elev_dx: int = 0
    mat_right: bool = False
    ports: Dict[str, dict] = field(default_factory=blank_ports)

    def rect(self) -> Tuple[int, int, int, int]:
        return (self.x, 0, NODE_W, NODE_H)  # y filled by renderer via floor

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "floor": self.floor,
            "x": self.x,
            "material": self.material,
            "stars": self.stars,
            "elevator": self.elevator,
            "elevator_a": self.elevator_a,
            "elevator_b": self.elevator_b,
            "roof": bool(self.roof),
            "elev_dx": int(self.elev_dx),
            "mat_right": bool(self.mat_right),
            "ports": self.ports,
        }

    @staticmethod
    def from_dict(d: dict) -> "Node":
        ports = blank_ports()
        src = d.get("ports") or {}
        for k in PORT_KEYS:
            if k in src:
                ports[k] = {
                    "target": str(src[k].get("target", "")),
                    "color": src[k].get("color", "cyan"),
                    "gate": src[k].get("gate", "none"),
                }
        return Node(
            id=d.get("id") or d.get("title") or "node",
            title=d.get("title", "NODE"),
            floor=int(d.get("floor", 0)),
            x=int(d.get("x", 0)),
            material=d.get("material", "Empty"),
            stars=str(d.get("stars", "")),
            elevator=d.get("elevator", "none"),
            elevator_a=d.get("elevator_a", ""),
            elevator_b=d.get("elevator_b", ""),
            roof=bool(d.get("roof", False)),
            elev_dx=int(d.get("elev_dx", 0)),
            mat_right=bool(d.get("mat_right", False)),
            ports=ports,
        )


@dataclass
class Sticker:
    id: str
    name: str
    tile_x: int
    tile_y: int
    big: bool = False

    def to_dict(self) -> dict:
        d = {
            "id": self.id,
            "name": self.name,
            "x": self.tile_x,
            "y": self.tile_y,
        }
        if self.big:
            d["big"] = True
        return d

    @staticmethod
    def from_dict(d: dict) -> "Sticker":
        return Sticker(
            id=d.get("id", d.get("name", "sticker")),
            name=d.get("name", ""),
            tile_x=int(d.get("x", 0)),
            tile_y=int(d.get("y", 0)),
            big=bool(d.get("big", False)),
        )


class MapState:
    def __init__(self):
        self.name = "Placeholder"
        self.nodes: List[Node] = []
        self.stickers: List[Sticker] = []
        self.path_routes: Dict[str, dict] = blank_path_routes()
        self.uid = 1

    def next_id(self, prefix="n") -> str:
        self.uid += 1
        return f"{prefix}{self.uid}"

    def max_floor(self) -> int:
        if not self.nodes:
            return 0
        return max(n.floor for n in self.nodes)

    def min_floor(self) -> int:
        if not self.nodes:
            return 0
        return min(n.floor for n in self.nodes)

    def floor_count(self) -> int:
        if not self.nodes:
            return 2
        return max(1, self.max_floor() - self.min_floor() + 1)

    def layout_floor(self, floor: int) -> int:
        return int(floor) - self.min_floor()

    def find_by_title(self, title: str) -> Optional[Node]:
        t = (title or "").strip().lower()
        if not t:
            return None
        for n in self.nodes:
            if n.title.strip().lower() == t:
                return n
        return None

    def find_by_id(self, nid: str) -> Optional[Node]:
        for n in self.nodes:
            if n.id == nid:
                return n
        return None

    def nodes_on_floor(self, fl: int) -> List[Node]:
        return [n for n in self.nodes if n.floor == fl]

    def elevator_group(self, kind: str) -> List[Node]:
        if kind in ("", "none"):
            return []
        return [n for n in self.nodes if n.elevator == kind]

    def elevator_segment(self, node: "Node") -> List[Node]:
        if not node or node.elevator in ("", "none"):
            return [node] if node else []
        for seg in self.elevator_segments(node.elevator):
            if any(n.id == node.id for n in seg):
                return seg
        return [node]

    def elevator_segments(self, kind: str) -> List[List[Node]]:
        ordered = sorted(self.elevator_group(kind), key=lambda z: z.floor)
        segs: List[List[Node]] = []
        cur: List[Node] = []
        for n in ordered:
            cur.append(n)
            if getattr(n, "roof", False):
                segs.append(cur)
                cur = []
        if cur:
            segs.append(cur)
        return segs

    def segment_touching_floor(self, kind: str, floor: int, exclude_id: Optional[str] = None) -> List[Node]:
        """Same-color cars that a new car on `floor` would join. Roof blocks past that floor."""
        if kind in ("", "none"):
            return []
        for seg in self.elevator_segments(kind):
            seg = [n for n in seg if n.id != exclude_id]
            if not seg:
                continue
            lo, hi = seg[0].floor, seg[-1].floor
            capped = getattr(seg[-1], "roof", False)
            if capped:
                if lo <= floor <= hi:
                    return seg
            elif floor >= lo:
                return seg
        return []

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "uid": self.uid,
            "nodes": [n.to_dict() for n in self.nodes],
            "stickers": [s.to_dict() for s in self.stickers],
            "path_routes": getattr(self, "path_routes", blank_path_routes()),
        }

    def load_dict(self, d: dict, assets: Optional["AssetStore"] = None):
        self.name = d.get("name", "Placeholder")
        self.uid = int(d.get("uid", 100))
        self.nodes = [Node.from_dict(x) for x in d.get("nodes", [])]
        raw_st = [Sticker.from_dict(x) for x in d.get("stickers", [])]
        if assets is not None:
            self.stickers = [s for s in raw_st if assets.has_sticker(s.name)]
        else:
            self.stickers = raw_st
        self.path_routes = blank_path_routes()
        raw_pr = d.get("path_routes") or {}
        if isinstance(raw_pr, dict):
            for color in PATH_DOT_COLORS:
                short = color.replace("_Path", "")
                src = (raw_pr.get(color) or raw_pr.get(color.lower())
                       or raw_pr.get(short) or raw_pr.get(short.lower()) or {})
                ids = list(src.get("ids") or [])
                direc = 1 if int(src.get("dir", 1) or 1) >= 0 else -1
                self.path_routes[color] = {"ids": ids, "dir": direc}
        live = {s.id for s in self.stickers}
        for color, bucket in self.path_routes.items():
            bucket["ids"] = [i for i in bucket.get("ids") or [] if i in live]
        for st in self.stickers:
            if path_dot_color(st.name):
                register_path_dot(self, st)
        resolve_imported_layout(self)
        ensure_reciprocal_ports(self)
        prune_edge_ports(self)

    def seed_default(self):
        self.nodes.clear()
        self.stickers.clear()
        self.path_routes = blank_path_routes()
        self.uid = 1
        self.name = "Placeholder"


def retarget_node_title(state: "MapState", old: str, new: str) -> None:
    o = (old or "").strip().lower()
    if not o or not (new or "").strip():
        return
    for n in state.nodes:
        for pdata in n.ports.values():
            tgt = (pdata.get("target") or "").strip()
            if tgt.lower() == o:
                pdata["target"] = new


# ---------------------------------------------------------------------------
# Asset store + thumbnails
# ---------------------------------------------------------------------------

class AssetStore:
    def __init__(self):
        self.images: Dict[str, Image.Image] = {}
        self.thumbs: Dict[str, Image.Image] = {}
        self.sticker_names: List[str] = []
        self.catalog_entries: List[tuple] = []
        self.starred_folders: set = set()
        self.thumb_folder = THUMBS_DIR
        self.grid_index: Dict[str, str] = {}
        self.sticker_index: Dict[str, str] = {}
        self.fallback_index: Dict[str, str] = {}

    def load_json(self, path: str = "") -> str:
        extra: Dict[str, str] = {}
        if path and os.path.isfile(path):
            with open(path, "r", encoding="utf-8") as f:
                meta = json.load(f)
            stickers = meta.get("stickers") if isinstance(meta, dict) else None
            if isinstance(stickers, dict):
                extra = {str(k): str(v) for k, v in stickers.items()}
            thumbs = meta.get("catalog_thumbnails") if isinstance(meta, dict) else None
            if thumbs:
                self.thumb_folder = thumbs
        return self.reload_images(extra)

    def reload_images(self, extra_stickers: Optional[Dict[str, str]] = None) -> str:
        self.images.clear()
        ensure_path_route_assets()
        self.grid_index = scan_png_tree(GRID_ASSETS_DIR, skip_fallback=True)
        self.sticker_index = scan_png_tree(STICKER_ASSETS_DIR, skip_fallback=True)
        self.fallback_index = {}
        self.fallback_index.update(scan_png_tree(FALLBACK_ASSETS_DIR, skip_fallback=False))
        self.fallback_index.update(scan_png_tree(FALLBACK_GRID_DIR, skip_fallback=False))
        self.fallback_index.update(scan_png_tree(FALLBACK_STICKER_DIR, skip_fallback=False))
        if extra_stickers:
            for k, p in extra_stickers.items():
                self.sticker_index[k] = p
                self.sticker_index[k.lower()] = p
        entries, names = walk_sticker_catalog(STICKER_ASSETS_DIR, getattr(self, "starred_folders", None))
        if extra_stickers:
            extra_names = []
            for k, p in extra_stickers.items():
                if not p or not os.path.isfile(p):
                    continue
                nm = os.path.splitext(os.path.basename(p))[0]
                if nm not in names:
                    extra_names.append(nm)
            if extra_names:
                entries.append(("cat", "Imported"))
                entries.extend(("item", n) for n in extra_names)
                names.extend(extra_names)
        self.catalog_entries = entries
        self.sticker_names = names
        os.makedirs(self.thumb_folder, exist_ok=True)
        self.sync_thumbnails()
        return "ok"

    def _open(self, name: str, p: str) -> Optional[Image.Image]:
        if not p or not os.path.isfile(p):
            return None
        img = Image.open(p).convert("RGBA")
        if img.width * img.height <= 65536:
            img = defringe_rgba(img)
        self.images[name] = img
        self.images[name.lower()] = img
        return img

    def _resolve(self, *names: str) -> str:
        p = lookup_png(self.grid_index, *names) or lookup_png(self.sticker_index, *names)
        if p:
            return p
        return lookup_png(getattr(self, "fallback_index", {}), *names)

    def has_sticker(self, name: str) -> bool:
        if not name:
            return False
        return bool(lookup_png(self.sticker_index, name)
                    or lookup_png(getattr(self, "fallback_index", {}), name))

    def get(self, name: str) -> Optional[Image.Image]:
        if not name:
            return None
        img = self.images.get(name) or self.images.get(name.lower())
        if img is not None:
            return img
        p = lookup_png(self.sticker_index, name)
        if p:
            return self._open(name, p)
        return self._open(name, self._resolve(name))

    def get_material(self, kind: str, stars: str = "") -> Optional[Image.Image]:
        if not kind or kind == "Empty":
            return None
        names = material_file_names(kind, stars)
        fb = getattr(self, "fallback_index", {})
        for key in names:
            img = self.images.get(key) or self.images.get(key.lower())
            if img is not None:
                return img
            p = lookup_png(self.grid_index, key) or lookup_png(fb, key)
            if p:
                return self._open(key, p)
        return None

    def get_elevator(self, kind: str) -> Optional[Image.Image]:
        names = elevator_file_names(kind)
        for n in names:
            img = self.images.get(n) or self.images.get(n.lower())
            if img is not None:
                return img
        return self._open(names[0], self._resolve(*names))

    def sync_thumbnails(self, force: bool = False):
        os.makedirs(self.thumb_folder, exist_ok=True)
        wanted = set(self.sticker_names)
        for name in self.sticker_names:
            thumb_path = os.path.join(self.thumb_folder, f"{name}.png")
            src = self.get(name)
            if src is None:
                continue
            if not force and os.path.isfile(thumb_path):
                try:
                    self.thumbs[name] = Image.open(thumb_path).convert("RGBA")
                    continue
                except Exception:
                    pass
            thumb = make_thumb(src, 64)
            thumb.save(thumb_path)
            self.thumbs[name] = thumb
        if os.path.isdir(self.thumb_folder):
            for fn in os.listdir(self.thumb_folder):
                if not fn.lower().endswith(".png"):
                    continue
                key = os.path.splitext(fn)[0]
                if key not in wanted:
                    try:
                        os.remove(os.path.join(self.thumb_folder, fn))
                    except OSError:
                        pass
                    self.thumbs.pop(key, None)


def defringe_rgba(img: Image.Image) -> Image.Image:
    """Drop hairline fringe. Do not recolor pixels (that causes color bloom)."""
    img = img.convert("RGBA")
    extrema = img.getextrema()
    if not extrema or extrema[3][0] == 255:
        return img
    cut = 28
    img.putdata([(0, 0, 0, 0) if p[3] < cut else p for p in img.getdata()])
    return img


def paste_rgba(base: Image.Image, sprite: Image.Image, xy: Tuple[int, int]) -> None:
    """Composite sprite with real alpha (no black-mask fringe)."""
    if sprite is None:
        return
    x, y = int(xy[0]), int(xy[1])
    sw, sh = sprite.size
    bw, bh = base.size
    sx0 = 0 if x >= 0 else -x
    sy0 = 0 if y >= 0 else -y
    dx0 = max(x, 0)
    dy0 = max(y, 0)
    dx1 = min(x + sw, bw)
    dy1 = min(y + sh, bh)
    if dx1 <= dx0 or dy1 <= dy0:
        return
    crop = sprite.crop((sx0, sy0, sx0 + (dx1 - dx0), sy0 + (dy1 - dy0)))
    dest = base.crop((dx0, dy0, dx1, dy1))
    base.paste(Image.alpha_composite(dest, crop), (dx0, dy0))


def make_thumb(img: Image.Image, size: int = 64) -> Image.Image:
    canvas = Image.new("RGBA", (size, size), (30, 30, 30, 255))
    src = img.copy()
    src.thumbnail((size - 6, size - 6), Image.Resampling.LANCZOS)
    ox = (size - src.width) // 2
    oy = (size - src.height) // 2
    paste_rgba(canvas, src, (ox, oy))
    return canvas


# ---------------------------------------------------------------------------
# Geometry helpers
# ---------------------------------------------------------------------------

def floor_top_y(floor_idx: int, floor_count: int) -> int:
    """World Y of the top of a floor panel. B1 is at the bottom."""
    # floors stacked: highest floor at y=0
    # floor_count panels: indices 0..floor_count-1 where 0=B1
    return (floor_count - 1 - floor_idx) * FLOOR_H


def node_y_on_floor(floor_idx: int, floor_count: int, min_floor: int = 0) -> int:
    top = floor_top_y(int(floor_idx) - int(min_floor), floor_count)
    return top + (FLOOR_H - NODE_H) // 2


def blue_elevator_x() -> int:
    """Preferred spawn: map center, then half a node left. Not a lock column."""
    return snap((MAP_W - NODE_W) // 2 - NODE_W // 2)


def port_position(node: Node, port: str, floor_count: int, min_floor: int = 0) -> Tuple[int, int]:
    """Top-left of node_connect for a port."""
    ny = node_y_on_floor(node.floor, floor_count, min_floor)
    nx = node.x
    cw, ch = CONNECT_W, CONNECT_H
    top = port.startswith("top")
    if top:
        cy = ny - ch + CONNECT_OVERLAP
    else:
        cy = ny + NODE_H - CONNECT_OVERLAP
    if port.endswith("mid"):
        cx = snap(nx + (NODE_W - cw) // 2)
    elif port.endswith("left"):
        cx = nx + GRID - cw // 2
    else:
        cx = nx + snap(NODE_W) - GRID - cw // 2
    return cx, cy


def port_exit(node: Node, port: str, floor_count: int, min_floor: int = 0) -> Tuple[float, float]:
    """Noodle origin: outer tip of node_connect, not the node box."""
    x, y = port_position(node, port, floor_count, min_floor)
    cx = x + CONNECT_W / 2
    if port.startswith("top"):
        return cx, y + 1
    return cx, y + CONNECT_H - 1


def node_center(node: Node, floor_count: int, min_floor: int = 0) -> Tuple[float, float]:
    return node.x + NODE_W / 2, node_y_on_floor(node.floor, floor_count, min_floor) + NODE_H / 2


def bezier_points(p0, p1, p2, p3, steps=32) -> List[Tuple[int, int]]:
    pts = []
    for i in range(steps + 1):
        t = i / steps
        u = 1 - t
        x = u**3 * p0[0] + 3 * u**2 * t * p1[0] + 3 * u * t**2 * p2[0] + t**3 * p3[0]
        y = u**3 * p0[1] + 3 * u**2 * t * p1[1] + 3 * u * t**2 * p2[1] + t**3 * p3[1]
        pts.append((int(x), int(y)))
    return pts


def connection_curve(a: Tuple[float, float], b: Tuple[float, float],
                     src_port: str = "und_mid", dest_port: str = "top_mid"):
    """Cubic always leaves away from the port (up from top, down from und)."""
    dist = math.hypot(b[0] - a[0], b[1] - a[1])
    reach = max(20, min(52, dist * 0.16 + 16))
    sdir = -1 if src_port.startswith("top") else 1
    ddir = -1 if dest_port.startswith("top") else 1
    dx = b[0] - a[0]
    c1 = (a[0] + dx * 0.12, a[1] + sdir * reach)
    c2 = (b[0] - dx * 0.12, b[1] + ddir * reach)
    return bezier_points(a, c1, c2, b, 24)


def aa_polyline(canvas: Image.Image, pts, color: Tuple[int, int, int], width: float = 3.5):
    """Draw an antialiased polyline via 2x supersample."""
    if not pts or len(pts) < 2 or canvas is None:
        return
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    pad = int(math.ceil(width)) + 3
    minx, miny = int(math.floor(min(xs))) - pad, int(math.floor(min(ys))) - pad
    maxx, maxy = int(math.ceil(max(xs))) + pad, int(math.ceil(max(ys))) + pad
    w, h = max(2, maxx - minx), max(2, maxy - miny)
    scale = 2
    ov = Image.new("RGBA", (w * scale, h * scale), (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    spts = [((p[0] - minx) * scale, (p[1] - miny) * scale) for p in pts]
    lw = max(1, int(round(width * scale)))
    d.line(spts, fill=color + (255,), width=lw, joint="curve")
    ov = ov.resize((w, h), Image.BILINEAR)
    if minx < canvas.width and miny < canvas.height and minx + w > 0 and miny + h > 0:
        paste_rgba(canvas, ov, (minx, miny))


def fold_search(s: str) -> str:
    return (s or "").lower().replace(" ", "_")


def resolved_port_targets(node: Node, state: MapState) -> List[Tuple[str, Node]]:
    found = []
    for pk, p in node.ports.items():
        t = (p.get("target") or "").strip()
        if not t or t == EDGE_TARGET:
            continue
        other = state.find_by_title(t)
        if other is not None and other.id != node.id:
            found.append((pk, other))
    return found


def node_has_drawn_line(node: Node, state: MapState) -> bool:
    if node.elevator and node.elevator != "none":
        if len(state.elevator_segment(node)) >= 2:
            return True
    if any((p.get("target") or "").strip() == EDGE_TARGET for p in node.ports.values()):
        return True
    return bool(resolved_port_targets(node, state))


def node_is_invalid(node: Node, state: MapState) -> bool:
    """Red border if no drawn lines, or illegal port geometry / duplicates."""
    targets = resolved_port_targets(node, state)
    names = [o.title.strip().lower() for _pk, o in targets]
    if any(names.count(t) > 2 for t in set(names)):
        return True
    for pk, other in targets:
        if not dest_floor_ok(node, pk, other):
            return True
    if not node_has_drawn_line(node, state):
        return True
    return False


def floor_move_blocked(node: Node, new_floor: int, state: MapState) -> Optional[str]:
    """Refuse a floor change that would make a port same-row or up/down mismatch."""
    if new_floor == node.floor:
        return None
    old = node.floor
    node.floor = new_floor
    try:
        if node_is_invalid(node, state) and resolved_port_targets(node, state):
            for pk, other in resolved_port_targets(node, state):
                if other.floor == new_floor:
                    return f"REFUSED: {node.title} would share floor {floor_label(new_floor)} with {other.title}"
                if pk.startswith("top") and other.floor < new_floor:
                    return f"REFUSED: top port of {node.title} cannot connect downward to {other.title}"
                if pk.startswith("und") and other.floor > new_floor:
                    return f"REFUSED: und port of {node.title} cannot connect upward to {other.title}"
            return f"REFUSED: moving {node.title} to {floor_label(new_floor)} breaks a port"
        title = node.title.strip().lower()
        for o in state.nodes:
            if o.id == node.id:
                continue
            for pk, pdata in o.ports.items():
                if (pdata.get("target") or "").strip().lower() != title:
                    continue
                if not dest_floor_ok(o, pk, node):
                    return f"REFUSED: {o.title}.{pk} would mismatch after moving {node.title}"
    finally:
        node.floor = old
    return None


def opposite_port_side(port: str) -> str:
    return "und" if port.startswith("top") else "top"


def port_side_ok(src_port: str, dest_port: str) -> bool:
    return dest_port.startswith(opposite_port_side(src_port))


def dest_floor_ok(src: Node, src_port: str, dest: Node) -> bool:
    if dest.id == src.id:
        return False
    if src_port.startswith("top"):
        return dest.floor > src.floor
    return dest.floor < src.floor


def clear_port_link(node: Node, port: str, state: MapState):
    tgt = (node.ports[port].get("target") or "").strip()
    node.ports[port]["target"] = ""
    if not tgt or tgt == EDGE_TARGET:
        return
    other = state.find_by_title(tgt)
    if other is None:
        return
    title = node.title.strip().lower()
    hits = [pk for pk, pdata in other.ports.items()
            if (pdata.get("target") or "").strip().lower() == title]
    dest = pick_matching_port(port, hits)
    if dest is None and hits:
        dest = hits[0]
    if dest:
        other.ports[dest]["target"] = ""


def make_port_link(src: Node, src_port: str, dest: Node, dest_port: str,
                   state: Optional["MapState"] = None):
    """Link ports. Up to two links between the same node pair."""
    st = src.title.strip().lower()
    dt = dest.title.strip().lower()
    src.ports[src_port]["target"] = dest.title
    dest.ports[dest_port]["target"] = src.title
    col = src.ports[src_port].get("color", "cyan")
    dest.ports[dest_port]["color"] = col
    src.ports[src_port]["color"] = col


def port_tail(port: str) -> str:
    if port.endswith("left"):
        return "left"
    if port.endswith("right"):
        return "right"
    return "mid"


def pick_matching_port(src_port: str, hits: List[str]) -> Optional[str]:
    if not hits:
        return None
    tail = port_tail(src_port)
    for pk in hits:
        if pk.endswith(tail) and port_side_ok(src_port, pk):
            return pk
    for pk in hits:
        if port_side_ok(src_port, pk):
            return pk
    return hits[0]


def paired_dest_port(node: Node, port: str, other: Node) -> Optional[str]:
    title = node.title.strip().lower()
    hits = [pk for pk, p in other.ports.items()
            if (p.get("target") or "").strip().lower() == title]
    return pick_matching_port(port, hits)


def sync_link_color(node: Node, port: str, color: str, state: MapState):
    node.ports[port]["color"] = color
    tgt = (node.ports[port].get("target") or "").strip()
    if not tgt:
        return
    other = state.find_by_title(tgt)
    if other is None:
        return
    dest = paired_dest_port(node, port, other)
    if dest:
        other.ports[dest]["color"] = color


def ensure_reciprocal_ports(state: MapState):
    """If A points at B but B has no port back, fill the matching side."""
    for n in list(state.nodes):
        for pk, pdata in n.ports.items():
            tgt = (pdata.get("target") or "").strip()
            if not tgt:
                continue
            other = state.find_by_title(tgt)
            if other is None:
                continue
            title = n.title.strip().lower()
            if any((p.get("target") or "").strip().lower() == title for p in other.ports.values()):
                continue
            if other.floor < n.floor:
                side = "top"
            elif other.floor > n.floor:
                side = "und"
            else:
                side = "und" if pk.startswith("top") else "top"
            dest_pk = f"{side}_mid"
            if (other.ports[dest_pk].get("target") or "").strip():
                for cand in PORT_KEYS:
                    if cand.startswith(side) and not (other.ports[cand].get("target") or "").strip():
                        dest_pk = cand
                        break
            other.ports[dest_pk]["target"] = n.title
            other.ports[dest_pk]["color"] = pdata.get("color", "cyan")


def prune_edge_ports(state: MapState):
    if not state.nodes:
        return
    lo, hi = state.min_floor(), state.max_floor()
    for n in state.nodes:
        for pk, pdata in n.ports.items():
            if (pdata.get("target") or "").strip() != EDGE_TARGET:
                continue
            if pk.startswith("top") and n.floor != hi:
                pdata["target"] = ""
            elif pk.startswith("und") and n.floor != lo:
                pdata["target"] = ""


def sticker_world(st: Sticker) -> Tuple[int, int]:
    return int(st.tile_x), int(st.tile_y)


def sticker_size(name: str, assets: "AssetStore", big: bool = False) -> Tuple[int, int]:
    img = assets.get(name)
    if img is None:
        w, h = GRID, GRID
    else:
        w, h = img.width, img.height
    if big:
        return int(w * 1.5), int(h * 1.5)
    return w, h


def clamp_sticker_xy(px: int, py: int, state: "MapState", assets: "AssetStore",
                     name: str, big: bool = False) -> Tuple[int, int]:
    w, h = sticker_size(name, assets, big)
    max_x = max(0, MAP_W - w)
    max_y = max(0, state.floor_count() * FLOOR_H - h)
    return clamp(int(px), 0, max_x), clamp(int(py), 0, max_y)


def path_dot_color(name: str) -> str:
    n = (name or "").strip()
    low = n.lower()
    for c in PATH_DOT_COLORS:
        if low == c.lower() or low + "_path" == c.lower() or low == c.lower().replace("_path", ""):
            return c
    return ""


def blank_path_routes() -> Dict[str, dict]:
    return {c: {"ids": [], "dir": 1} for c in PATH_DOT_COLORS}


def ensure_path_route_assets():
    dest_dir = os.path.join(STICKER_ASSETS_DIR, PATH_ROUTE_DIR)
    os.makedirs(dest_dir, exist_ok=True)
    copied = False
    for color in PATH_DOT_COLORS:
        dest = os.path.join(dest_dir, f"{color}.png")
        if os.path.isfile(dest):
            continue
        src = ""
        for root in (FALLBACK_STICKER_DIR, FALLBACK_ASSETS_DIR, FALLBACK_GRID_DIR):
            if not root or not os.path.isdir(root):
                continue
            for sub in (os.path.join(root, PATH_ROUTE_DIR), root):
                for fn in (f"{color}.png", f"{color.lower()}.png"):
                    p = os.path.join(sub, fn)
                    if os.path.isfile(p):
                        src = p
                        break
                if src:
                    break
            if src:
                break
        if src:
            try:
                shutil.copy2(src, dest)
                copied = True
            except Exception:
                pass
    return copied


def register_path_dot(state: "MapState", st: Sticker, selected_id: Optional[str] = None):
    color = path_dot_color(st.name)
    if not color:
        return
    if not getattr(state, "path_routes", None):
        state.path_routes = blank_path_routes()
    bucket = state.path_routes.setdefault(color, {"ids": [], "dir": 1})
    ids = bucket.setdefault("ids", [])
    if st.id in ids:
        return
    if selected_id and ids and selected_id == ids[0]:
        ids.insert(0, st.id)
    else:
        ids.append(st.id)


def insert_path_dot_between(state: "MapState", assets: "AssetStore",
                            a: Sticker, b: Sticker) -> Optional[Sticker]:
    color = path_dot_color(a.name)
    if not color or path_dot_color(b.name) != color or a.id == b.id:
        return None
    bucket = (getattr(state, "path_routes", None) or {}).get(color) or {}
    ids = list(bucket.get("ids") or [])
    if a.id not in ids or b.id not in ids:
        return None
    ia, ib = ids.index(a.id), ids.index(b.id)
    if abs(ia - ib) != 1:
        return None
    ax, ay = sticker_world(a)
    bx, by = sticker_world(b)
    tx, ty = clamp_sticker_xy(int(round((ax + bx) / 2)), int(round((ay + by) / 2)),
                              state, assets, a.name, False)
    st = Sticker(id=state.next_id("s"), name=a.name, tile_x=tx, tile_y=ty, big=False)
    state.stickers.append(st)
    ids.insert(min(ia, ib) + 1, st.id)
    bucket["ids"] = ids
    return st


def unregister_path_dot(state: "MapState", sid: str):
    routes = getattr(state, "path_routes", None) or {}
    for bucket in routes.values():
        ids = list(bucket.get("ids") or [])
        if sid in ids:
            ids.remove(sid)
            bucket["ids"] = ids


def drop_stickers(state: "MapState", drop_ids, selected_sticker: Optional[str] = None):
    drop = set(drop_ids or [])
    for sid in drop:
        unregister_path_dot(state, sid)
    state.stickers = [s for s in state.stickers if s.id not in drop]
    if selected_sticker in drop:
        return None
    return selected_sticker


def pop_last_path_dot(state: "MapState", color: str, selected_sticker: Optional[str] = None):
    bucket = (getattr(state, "path_routes", None) or {}).get(color) or {}
    ids = list(bucket.get("ids") or [])
    if not ids:
        return selected_sticker, False
    last = ids[-1]
    return drop_stickers(state, [last], selected_sticker), True


def clear_path_color(state: "MapState", color: str, selected_sticker: Optional[str] = None):
    bucket = (getattr(state, "path_routes", None) or {}).get(color) or {}
    ids = list(bucket.get("ids") or [])
    if not ids:
        return selected_sticker, False
    sel = drop_stickers(state, ids, selected_sticker)
    bucket["ids"] = []
    return sel, True


def path_dot_center(st: Sticker, assets: "AssetStore") -> Tuple[float, float]:
    x, y = sticker_world(st)
    w, h = sticker_size(st.name, assets, getattr(st, "big", False))
    return x + w / 2.0, y + h / 2.0


def _vsub(a, b):
    return (a[0] - b[0], a[1] - b[1])


def _vadd(a, b):
    return (a[0] + b[0], a[1] + b[1])


def _vmul(a, s):
    return (a[0] * s, a[1] * s)


def _vlen(a):
    return math.hypot(a[0], a[1]) or 1.0


def rounded_path(points: List[Tuple[float, float]], radius: float = 16.0) -> List[Tuple[int, int]]:
    """Catmull-Rom through every waypoint, blended toward the chord so corners stay mild."""
    if len(points) < 2:
        return [(int(p[0]), int(p[1])) for p in points]
    if len(points) == 2:
        a, b = points[0], points[1]
        return [(int(a[0]), int(a[1])), (int(b[0]), int(b[1]))]
    pts = [points[0]] + list(points) + [points[-1]]
    out: List[Tuple[int, int]] = [(int(points[0][0]), int(points[0][1]))]
    bend = 0.45
    for i in range(1, len(pts) - 2):
        p0, p1, p2, p3 = pts[i - 1], pts[i], pts[i + 1], pts[i + 2]
        steps = 8
        for k in range(1, steps + 1):
            t = k / steps
            t2, t3 = t * t, t * t * t
            sx = 0.5 * ((2 * p1[0]) + (-p0[0] + p2[0]) * t
                        + (2 * p0[0] - 5 * p1[0] + 4 * p2[0] - p3[0]) * t2
                        + (-p0[0] + 3 * p1[0] - 3 * p2[0] + p3[0]) * t3)
            sy = 0.5 * ((2 * p1[1]) + (-p0[1] + p2[1]) * t
                        + (2 * p0[1] - 5 * p1[1] + 4 * p2[1] - p3[1]) * t2
                        + (-p0[1] + 3 * p1[1] - 3 * p2[1] + p3[1]) * t3)
            lx = p1[0] + (p2[0] - p1[0]) * t
            ly = p1[1] + (p2[1] - p1[1]) * t
            x = lx * (1.0 - bend) + sx * bend
            y = ly * (1.0 - bend) + sy * bend
            out.append((int(x), int(y)))
    return out


def draw_path_arrows(draw: ImageDraw.ImageDraw, pts: List[Tuple[int, int]],
                     color: Tuple[int, int, int], forward: bool = True):
    if len(pts) < 2:
        return
    seq = pts if forward else list(reversed(pts))
    segs = []
    for i in range(1, len(seq)):
        x0, y0 = seq[i - 1]
        x1, y1 = seq[i]
        d = math.hypot(x1 - x0, y1 - y0)
        segs.append((x0, y0, x1, y1, d))
    spacing = 78.0
    acc = spacing * 0.6
    size = 12.0
    for x0, y0, x1, y1, d in segs:
        if d < 1:
            continue
        while acc <= d:
            u = acc / d
            px = x0 + (x1 - x0) * u
            py = y0 + (y1 - y0) * u
            ang = math.atan2(y1 - y0, x1 - x0)
            tip = (px + math.cos(ang) * size, py + math.sin(ang) * size)
            left = (px + math.cos(ang + 2.5) * size * 0.72,
                    py + math.sin(ang + 2.5) * size * 0.72)
            right = (px + math.cos(ang - 2.5) * size * 0.72,
                     py + math.sin(ang - 2.5) * size * 0.72)
            draw.polygon([tip, left, right], fill=color + (255,))
            acc += spacing
        acc -= d
        if acc < 0:
            acc = 0


def adjust_stickers_after_floor_change(state: "MapState", assets: "AssetStore", old_fc: int,
                                      skip_ids=None):
    """Shift stickers when the tower height changes; drop any that sit above the new top."""
    new_fc = state.floor_count()
    if new_fc == old_fc:
        return
    skip = set(skip_ids or [])
    dy = (old_fc - new_fc) * FLOOR_H
    keep = []
    for st in state.stickers:
        if st.id not in skip:
            st.tile_y -= dy
        w, h = sticker_size(st.name, assets, getattr(st, "big", False))
        if st.tile_y < 0:
            continue
        st.tile_x, st.tile_y = clamp_sticker_xy(st.tile_x, st.tile_y, state, assets, st.name, getattr(st, "big", False))
        if st.tile_y + h <= new_fc * FLOOR_H and st.tile_x + w <= MAP_W:
            keep.append(st)
    state.stickers = keep


def sticker_hits_node(st: Sticker, node: Node, assets: "AssetStore", fc: int, pad: int = 24,
                     min_floor: int = 0) -> bool:
    img = assets.get(st.name)
    if img is None:
        return False
    sx, sy = sticker_world(st)
    w, h = sticker_size(st.name, assets, getattr(st, "big", False))
    ny = node_y_on_floor(node.floor, fc, min_floor)
    return (sx + w >= node.x - pad and sx <= node.x + NODE_W + pad and
            sy + h >= ny - pad and sy <= ny + NODE_H + pad)


def sticker_locked_on_node(st: Sticker, state: MapState, assets: "AssetStore") -> bool:
    fc = state.floor_count()
    return any(sticker_hits_node(st, n, assets, fc, min_floor=state.min_floor()) for n in state.nodes)


def pil_to_surf(img: Image.Image):
    import pygame
    to_surf = getattr(pygame.image, "frombytes", pygame.image.fromstring)
    return to_surf(img.tobytes(), img.size, img.mode)


# ---------------------------------------------------------------------------
# PIL renderer (used both for editor blit source and final export)
# ---------------------------------------------------------------------------

class MapRenderer:
    def __init__(self, assets: AssetStore):
        self.assets = assets

    def render(self, state: MapState, crop: bool = False,
               selected_node: Optional[str] = None,
               selected_sticker: Optional[str] = None,
               view_box: Optional[Tuple[int, int, int, int]] = None,
               hide_stickers: bool = False,
               hide_paths: bool = False,
               live: bool = False,
               red_blink: bool = True) -> Image.Image:
        fc = state.floor_count()
        mf = state.min_floor()
        W, H = MAP_W, fc * FLOOR_H
        if view_box is None:
            ox, oy, vx1, vy1 = 0, 0, W, H
        else:
            ox = max(0, int(view_box[0]))
            oy = max(0, int(view_box[1]))
            vx1 = min(W, int(view_box[2]))
            vy1 = min(H, int(view_box[3]))
        cw, ch = max(1, vx1 - ox), max(1, vy1 - oy)
        canvas = Image.new("RGBA", (cw, ch), (20, 20, 20, 255))

        def vis(x0, y0, x1, y1) -> bool:
            return not (x1 < ox or y1 < oy or x0 > vx1 or y0 > vy1)

        # --- background panels (only visible band of the 10-floor strip) ---
        bg = self.assets.get("floor_bg")
        if bg is not None:
            y = (oy // bg.height) * bg.height
            while y < vy1:
                slice_h = min(bg.height, H - y)
                part = bg.crop((0, 0, MAP_W, slice_h))
                canvas.paste(part, (0 - ox, y - oy), part)
                y += slice_h

        # floor number boxes
        box = self.assets.get("floor_number_box")
        if box is None:
            box = Image.new("RGBA", FLOOR_BOX, (18, 18, 18, 230))
        bw, bh = box.size
        font = load_font(16, True)
        for fi in range(fc):
            top = floor_top_y(fi, fc)
            bx = int(bw * 0.05)
            by = top + int(bh * 2)
            if not vis(bx, by, bx + bw, by + bh):
                continue
            canvas.paste(box, (bx - ox, by - oy), box)
            label = floor_label(mf + fi)
            td = ImageDraw.Draw(canvas)
            bb = td.textbbox((0, 0), label, font=font)
            tw, th = bb[2] - bb[0], bb[3] - bb[1]
            tx = bx - ox + (bw - tw) / 2
            ty = by - oy + (bh - th) / 2 - 5
            td.text((tx, ty), label, font=font, fill=(255, 255, 255, 255))

        draw = ImageDraw.Draw(canvas)

        # --- connections (behind nodes) ---
        self._draw_elevators(draw, state, fc, ox, oy)
        self._draw_port_cables(canvas, draw, state, fc, ox, oy)

        # --- selection / alert plates (behind nodes) ---
        for n in state.nodes:
            ny = node_y_on_floor(n.floor, fc, mf)
            if not vis(n.x - 6, ny - 6, n.x + NODE_W + 6, ny + NODE_H + 6):
                continue
            box = [n.x - 3 - ox, ny - 3 - oy, n.x + NODE_W + 2 - ox, ny + NODE_H + 2 - oy]
            if node_is_invalid(n, state):
                fill = (150, 22, 22, 200) if (not live or red_blink) else (132, 20, 20, 190)
                try:
                    draw.rounded_rectangle(box, radius=8, fill=fill)
                except Exception:
                    draw.rectangle(box, fill=fill)
            if live and selected_node == n.id:
                plate = self.assets.get("Background_Node_Select")
                if plate is not None:
                    px = int(n.x + NODE_W / 2 - plate.width / 2 - ox)
                    py = int(ny + NODE_H / 2 - plate.height / 2 - oy)
                    paste_rgba(canvas, plate, (px, py))
                else:
                    try:
                        draw.rounded_rectangle(box, radius=8, fill=(210, 210, 214, 220))
                    except Exception:
                        draw.rectangle(box, fill=(210, 210, 214, 220))

        # --- nodes ---
        for n in state.nodes:
            ny = node_y_on_floor(n.floor, fc, mf)
            if not vis(n.x - 40, ny - 40, n.x + NODE_W + 40, ny + NODE_H + 40):
                continue
            self._draw_node(canvas, draw, n, fc, selected=False,
                            ox=ox, oy=oy, min_floor=mf)

        if not hide_paths:
            self._draw_path_routes(canvas, draw, state, ox, oy)

        # --- stickers ---
        if not hide_stickers:
            for st in state.stickers:
                if hide_paths and path_dot_color(st.name):
                    continue
                if not self.assets.has_sticker(st.name):
                    continue
                img = self.assets.get(st.name)
                if img is None:
                    continue
                if getattr(st, "big", False):
                    img = img.resize((int(img.width * 1.5), int(img.height * 1.5)), Image.NEAREST)
                x, y = sticker_world(st)
                if x + img.width < ox or y + img.height < oy or x > vx1 or y > vy1:
                    continue
                paste_rgba(canvas, img, (x - ox, y - oy))
                if selected_sticker == st.id:
                    d2 = ImageDraw.Draw(canvas)
                    d2.rectangle([x - 1 - ox, y - 1 - oy, x + img.width - ox, y + img.height - oy],
                                 outline=(255, 255, 255, 255), width=2)

        # --- port locks above stickers ---
        self._draw_port_locks(canvas, state, fc, mf, ox, oy)
        return canvas

    def _draw_port_locks(self, canvas: Image.Image, state: MapState, fc: int, mf: int,
                         ox: int = 0, oy: int = 0):
        locked = self.assets.get("locked_gate")
        upg = self.assets.get("open_gate_up")
        dng = self.assets.get("open_gate_down")
        for n in state.nodes:
            for pk, pdata in n.ports.items():
                if not (pdata.get("target") or "").strip():
                    continue
                gate = pdata.get("gate", "none")
                if gate in ("open-gate", "none", "", "open"):
                    continue
                gimg = None
                if gate == "closed-gate":
                    gimg = locked
                elif gate == "gate-up":
                    gimg = upg
                elif gate == "gate-down":
                    gimg = dng
                if gimg is None:
                    continue
                px, py = port_position(n, pk, fc, mf)
                cw = CONNECT_W
                gx = px + cw // 2 - gimg.width // 2 - ox
                gh = gimg.height
                ny0 = node_y_on_floor(n.floor, fc, mf) - oy
                top = pk.startswith("top")
                if top:
                    gy = (ny0 - (gh // 2) + 8) if gate == "gate-down" else (ny0 - gh + 8)
                else:
                    bot = ny0 + NODE_H
                    gy = (bot - (gh // 2) - 8) if gate == "gate-up" else (bot - 7)
                paste_rgba(canvas, gimg, (gx, gy))

    def _draw_elevators(self, draw: ImageDraw.ImageDraw, state: MapState, fc: int,
                       ox: int = 0, oy: int = 0):
        # group by color
        kinds = {}
        for n in state.nodes:
            if n.elevator and n.elevator != "none":
                kinds.setdefault(n.elevator, []).append(n)
        for kind, group in kinds.items():
            if len(group) < 1:
                continue
            color = ELEVATOR_HEX.get(kind, (80, 80, 160))
            pairs = []
            if len(group) >= 2:
                ordered = sorted(group, key=lambda z: z.floor)
                for a, b in zip(ordered, ordered[1:]):
                    pairs.append((a, b))
            drawn = set()
            for a, b in pairs:
                if getattr(a, "roof", False):
                    continue
                key = tuple(sorted((a.id, b.id)))
                if key in drawn:
                    continue
                drawn.add(key)
                cxa, _ = port_position(a, "top_mid", fc, state.min_floor())
                shaft_w = CONNECT_W + 2
                x0 = int(cxa - 1 - ox)
                ya = node_center(a, fc, state.min_floor())[1] - oy
                yb = node_center(b, fc, state.min_floor())[1] - oy
                if ya > yb:
                    ya, yb = yb, ya
                draw.rectangle([x0, ya, x0 + shaft_w - 1, yb], fill=color + (255,))

    def _draw_port_cables(self, canvas: Image.Image, draw: ImageDraw.ImageDraw, state: MapState, fc: int,
                         ox: int = 0, oy: int = 0):
        drawn = set()
        used = set()
        for n in state.nodes:
            for pk, pdata in n.ports.items():
                if (n.id, pk) in used:
                    continue
                tgt = (pdata.get("target") or "").strip()
                if not tgt:
                    continue
                if tgt == EDGE_TARGET:
                    a = port_exit(n, pk, fc, state.min_floor())
                    H = fc * FLOOR_H
                    if pk.startswith("top"):
                        b = (a[0], 0.0)
                    else:
                        b = (a[0], float(H))
                    locked = pdata.get("gate") == "closed-gate"
                    col_key = "magenta" if locked else pdata.get("color", "cyan")
                    col = CONN_COLORS.get(col_key, CONN_COLORS["cyan"])
                    aa_polyline(canvas, [(a[0] - ox, a[1] - oy), (b[0] - ox, b[1] - oy)],
                                col, PORT_LINE_W)
                    continue
                other = state.find_by_title(tgt)
                if other is None:
                    continue
                dest_port = self._best_dest_port(n, pk, other, used)
                if not dest_port:
                    continue
                key = tuple(sorted(((n.id, pk), (other.id, dest_port))))
                if key in drawn:
                    continue
                drawn.add(key)
                used.add((n.id, pk))
                used.add((other.id, dest_port))
                a = port_exit(n, pk, fc, state.min_floor())
                b = port_exit(other, dest_port, fc, state.min_floor())
                locked = (pdata.get("gate") == "closed-gate"
                          or other.ports.get(dest_port, {}).get("gate") == "closed-gate")
                col_key = "magenta" if locked else pdata.get("color", "cyan")
                col = CONN_COLORS.get(col_key, CONN_COLORS["cyan"])
                pts = [(p[0] - ox, p[1] - oy) for p in connection_curve(a, b, pk, dest_port)]
                if len(pts) >= 2:
                    aa_polyline(canvas, pts, col, PORT_LINE_W)

    def _draw_path_routes(self, canvas: Image.Image, draw: ImageDraw.ImageDraw,
                          state: MapState, ox: int, oy: int):
        by_id = {s.id: s for s in state.stickers}
        routes = getattr(state, "path_routes", None) or {}
        for color in PATH_DOT_COLORS:
            bucket = routes.get(color) or {}
            ids = [i for i in (bucket.get("ids") or []) if i in by_id]
            if len(ids) < 2:
                continue
            rgb = PATH_DOT_RGB.get(color, (200, 200, 200))
            forward = int(bucket.get("dir", 1) or 1) >= 0
            cents = [path_dot_center(by_id[i], self.assets) for i in ids]
            raw = rounded_path(cents, radius=32.0)
            pts = [(p[0] - ox, p[1] - oy) for p in raw]
            if len(pts) >= 2:
                aa_polyline(canvas, pts, rgb, PATH_LINE_W)
                draw_path_arrows(draw, pts, rgb, forward)

    def _best_dest_port(self, src: Node, src_port: str, dst: Node,
                        used: Optional[set] = None) -> Optional[str]:
        title = src.title.strip().lower()
        used = used or set()
        hits = [pk for pk, pdata in dst.ports.items()
                if (pdata.get("target") or "").strip().lower() == title
                and (dst.id, pk) not in used]
        return pick_matching_port(src_port, hits)

    def _draw_node(self, canvas: Image.Image, draw: ImageDraw.ImageDraw,
                   n: Node, fc: int, selected: bool = False, ox: int = 0, oy: int = 0,
                   min_floor: int = 0):
        ny = node_y_on_floor(n.floor, fc, min_floor) - oy
        nx = n.x - ox
        box = self.assets.get("node_box")
        if box is not None:
            paste_rgba(canvas, box, (nx, int(ny)))
        if selected:
            draw.rectangle([nx - 3, ny - 3, nx + NODE_W + 2, ny + NODE_H + 2],
                           outline=(255, 255, 255, 255), width=4)

        mat_img = self.assets.get_material(n.material, n.stars)
        if mat_img is not None:
            if getattr(n, "mat_right", False):
                mx = nx + NODE_W - mat_img.width // 2
            else:
                mx = nx - mat_img.width // 2
            my = ny + NODE_H // 2 - mat_img.height // 2
            paste_rgba(canvas, mat_img, (mx, my))
            stars_val = str(star_count(n.stars)) if n.material == "ALL" else (n.stars or "").strip()
            if n.material == "ALL":
                font = load_font(24, True)
                label = (n.stars or "").strip() or "1"
                bb = draw.textbbox((0, 0), label, font=font)
                tw, th = bb[2] - bb[0], bb[3] - bb[1]
                tx = mx + (mat_img.width - tw) / 2
                ty = my + (mat_img.height - th) / 2
                draw.text((tx, ty), label, font=font, fill=(0, 0, 0, 255))
            elif stars_val:
                star = self.assets.get("Star")
                if star is not None:
                    star_draw = star.resize((STAR_DRAW, STAR_DRAW), Image.Resampling.LANCZOS)
                    sx = mx + mat_img.width - star_draw.width - 1
                    sy = my + 1
                    paste_rgba(canvas, star_draw, (sx, sy))
                    font = load_font(STAR_NUM, True)
                    bb = draw.textbbox((0, 0), stars_val, font=font)
                    tw, th = bb[2] - bb[0], bb[3] - bb[1]
                    draw.text((sx + (star_draw.width - tw) / 2, sy + (star_draw.height - th) / 2 - 1),
                              stars_val, font=font, fill=(20, 20, 20, 255))

        # title centered, moved up 10px
        font = load_font(14, True)
        title = n.title
        bb = draw.textbbox((0, 0), title, font=font)
        tw, th = bb[2] - bb[0], bb[3] - bb[1]
        tx = nx + (NODE_W - tw) / 2
        ty = ny + (NODE_H - th) / 2 - 10
        draw.text((tx, ty), title, font=font, fill=(25, 25, 25, 255))

        # elevator glyph in middle of node
        if n.elevator and n.elevator != "none":
            ev = self.assets.get_elevator(n.elevator)
            if ev is not None:
                half = ev.width / 2
                dx = clamp(int(getattr(n, "elev_dx", 0)),
                           int(-NODE_W / 2 + half), int(NODE_W / 2 - half))
                ex = int(nx + NODE_W / 2 - half + dx)
                ey = int(ny + NODE_H / 2 - ev.height / 2 + 22)
                paste_rgba(canvas, ev, (ex, ey))

        conn = self.assets.get("node_connect")
        for pk, pdata in n.ports.items():
            tgt = (pdata.get("target") or "").strip()
            if not tgt:
                continue
            px, py = port_position(n, pk, fc, min_floor)
            px, py = px - ox, py - oy
            ch = conn.height if conn is not None else CONNECT_H
            cw = conn.width if conn is not None else CONNECT_W
            paste_rgba(canvas, conn, (px, py))

    def export_png(self, state: MapState, path: str,
                   hide_stickers: bool = False, hide_paths: bool = False):
        img = self.render(state, crop=True, hide_stickers=hide_stickers, hide_paths=hide_paths)
        # footer
        footer_h = 28
        out = Image.new("RGBA", (img.width, img.height + footer_h), (18, 18, 18, 255))
        out.paste(img, (0, 0), img)
        d = ImageDraw.Draw(out)
        font = load_font(14)
        d.text((8, img.height + 6), FOOTER, font=font, fill=(220, 220, 220, 255))
        # flatten
        bg = Image.new("RGB", out.size, (20, 20, 20))
        bg.paste(out, mask=out.split()[-1])
        bg.save(path)


def enrich_groups(state: MapState, assets: AssetStore) -> dict:
    """Attach sticker/asset names whose bbox sits inside a node perimeter."""
    fc = state.floor_count()
    mf = state.min_floor()
    data = state.to_dict()
    for nd in data["nodes"]:
        node = state.find_by_id(nd["id"])
        ny = node_y_on_floor(node.floor, fc, mf)
        nx1, ny1 = node.x, ny
        nx2, ny2 = node.x + NODE_W, ny + NODE_H
        group = []
        # material / elevator count as grouped images
        if node.material and node.material not in ("Empty", "none"):
            group.append(node.material)
        if node.elevator and node.elevator != "none":
            group.append(f"Elevator_{node.elevator}")
        for st in state.stickers:
            img = assets.get(st.name)
            if img is None:
                continue
            x, y = sticker_world(st)
            w, h = sticker_size(st.name, assets, getattr(st, "big", False))
            cx, cy = x + w / 2, y + h / 2
            if nx1 <= cx <= nx2 and ny1 <= cy <= ny2:
                group.append(st.name)
        nd["group"] = group
    return data


# ---------------------------------------------------------------------------
# Collision / drag helpers
# ---------------------------------------------------------------------------

def elevator_on_floor(state: MapState, kind: str, floor: int,
                     ignore_id: Optional[str] = None) -> bool:
    if not kind or kind == "none":
        return False
    return any(o.elevator == kind and o.floor == floor and o.id != ignore_id
               for o in state.nodes)


def rig_members(node: Node, state: MapState) -> List[Node]:
    if node.elevator and node.elevator != "none":
        return state.elevator_segment(node)
    return [node]


def merge_intervals(ivals: List[Tuple[int, int]]) -> List[Tuple[int, int]]:
    if not ivals:
        return []
    ivals = sorted(ivals)
    out = [[ivals[0][0], ivals[0][1]]]
    for a, b in ivals[1:]:
        if a <= out[-1][1] + GRID:
            out[-1][1] = max(out[-1][1], b)
        else:
            out.append([a, b])
    return [(a, b) for a, b in out]


def occupied_intervals(node: Node, state: MapState,
                       floors: Optional[List[int]] = None,
                       ignore_ids: Optional[set] = None) -> List[Tuple[int, int]]:
    members = rig_members(node, state)
    skip = set(ignore_ids or []) | {m.id for m in members}
    fls = set(floors if floors is not None else [m.floor for m in members])
    ivals = []
    for fl in fls:
        for o in state.nodes_on_floor(fl):
            if o.id in skip:
                continue
            ivals.append((o.x, o.x + NODE_W))
    return merge_intervals(ivals)


def slot_fits(x: int, intervals: List[Tuple[int, int]]) -> bool:
    if x < 0 or x + NODE_W > MAP_W:
        return False
    for a, b in intervals:
        if not (x + NODE_W + GRID <= a or b + GRID <= x):
            return False
    return True



def search_left_then_right(desired_x: int, intervals: List[Tuple[int, int]]) -> Optional[int]:
    """Prefer desired X. If blocked, walk left one tile at a time, then right."""
    x0 = snap(clamp(desired_x, 0, MAP_W - NODE_W))
    if slot_fits(x0, intervals):
        return x0
    x = x0 - GRID
    while x >= 0:
        if slot_fits(x, intervals):
            return x
        x -= GRID
    x = x0 + GRID
    while x + NODE_W <= MAP_W:
        if slot_fits(x, intervals):
            return x
        x += GRID
    return None


def proposed_x_legal(node: Node, new_x: int, state: MapState, direction: int,
                     floor: Optional[int] = None) -> Tuple[int, bool, Optional[str]]:
    """Stop at the 15px gap. Jump only into a gap that fully fits the box
    on every floor of the elevator rig. Never jumps the opposite way."""
    new_x = snap(clamp(new_x, 0, MAP_W - NODE_W))
    extra = [floor] if floor is not None else None
    ivals = occupied_intervals(node, state, floors=extra)

    if direction == 0:
        return (new_x if slot_fits(new_x, ivals) else node.x), False, None
    if slot_fits(new_x, ivals):
        return new_x, False, None

    hits = [iv for iv in ivals if not (new_x + NODE_W + GRID <= iv[0] or iv[1] + GRID <= new_x)]
    if direction > 0:
        hits = [iv for iv in hits if iv[1] > node.x]
        hits.sort(key=lambda t: t[0])
        if not hits:
            return new_x, False, None
        first = hits[0]
        rest_at = snap(first[0] - NODE_W - GRID)
        if rest_at < 0 or not slot_fits(rest_at, [iv for iv in ivals if iv != first]):
            rest_at = node.x
        if new_x < first[0] + NODE_W // 2:
            return max(node.x, rest_at), False, None
        ahead = [iv for iv in ivals if iv[0] >= first[0]]
        for i, (a, b) in enumerate(ahead):
            dest = snap(b + GRID)
            nxt = ahead[i + 1][0] if i + 1 < len(ahead) else MAP_W
            if dest + NODE_W + GRID <= nxt and slot_fits(dest, ivals):
                return dest, True, None
        return rest_at, False, "REFUSED: no gap to the right that fits"

    hits = [iv for iv in hits if iv[0] < node.x + NODE_W]
    hits.sort(key=lambda t: t[0])
    if not hits:
        return new_x, False, None
    last = hits[-1]
    rest_at = snap(last[1] + GRID)
    if rest_at + NODE_W > MAP_W or not slot_fits(rest_at, [iv for iv in ivals if iv != last]):
        rest_at = node.x
    if new_x + NODE_W > last[0] + NODE_W // 2:
        return min(node.x, rest_at), False, None
    behind = [iv for iv in ivals if iv[1] <= last[1]]
    for i, (a, b) in enumerate(reversed(behind)):
        dest = snap(a - NODE_W - GRID)
        prev = behind[len(behind) - 2 - i][1] if i + 1 < len(behind) else 0
        if dest >= prev + GRID and slot_fits(dest, ivals):
            return dest, True, None
    return rest_at, False, "REFUSED: no gap to the left that fits"


def fit_x_on_floor(node: Node, desired_x: int, floor: int, state: MapState) -> Optional[int]:
    """Fit on `floor` at desired X, else left, else right. None = floor full.
    Existing elevator shafts stay on their column or refuse."""
    ivals = occupied_intervals(node, state, floors=[floor], ignore_ids={node.id})
    if node.elevator != "none":
        grp = state.segment_touching_floor(node.elevator, floor, node.id)
        if grp:
            x = grp[0].x
            return x if slot_fits(x, ivals) else None
    return search_left_then_right(desired_x, ivals)


def collect_node_stickers(node: Node, state: MapState, assets: "AssetStore", fc: int):
    mf = state.min_floor()
    ny = node_y_on_floor(node.floor, fc, mf)
    out = []
    for st in state.stickers:
        if sticker_hits_node(st, node, assets, fc, min_floor=mf):
            out.append((st.id, st.tile_x - node.x, st.tile_y - ny))
    return out


def apply_node_stickers(node: Node, offsets, state: MapState, fc: int):
    ny = node_y_on_floor(node.floor, fc, state.min_floor())
    by_id = {s.id: s for s in state.stickers}
    for sid, dxt, dyt in offsets:
        st = by_id.get(sid)
        if st:
            st.tile_x = node.x + dxt
            st.tile_y = ny + dyt


def move_node_to_floor(node: Node, new_floor: int, state: MapState, assets: "AssetStore") -> Optional[str]:
    new_floor = max(0, new_floor)
    blocked = floor_move_blocked(node, new_floor, state)
    if blocked:
        return blocked
    if elevator_on_floor(state, node.elevator, new_floor, node.id):
        return f"REFUSED: {node.elevator} elevator already on {floor_label(new_floor)}"
    dest = fit_x_on_floor(node, node.x, new_floor, state)
    if dest is None:
        return f"REFUSED: floor full"
    if new_floor == node.floor:
        fc = state.floor_count()
        carried = collect_node_stickers(node, state, assets, fc)
        node.x = dest
        apply_node_stickers(node, carried, state, fc)
        return None
    old_fc = state.floor_count()
    offsets = collect_node_stickers(node, state, assets, old_fc)
    node.x = dest
    node.floor = new_floor
    adjust_stickers_after_floor_change(state, assets, old_fc, skip_ids=[o[0] for o in offsets])
    apply_node_stickers(node, offsets, state, state.floor_count())
    if node.elevator != "none":
        apply_elevator_x(state, node.elevator, node.x, assets, anchor=node)
    return None


def resolve_imported_layout(state: MapState) -> None:
    """On JSON import: nudge any overlapping node left, then right."""
    for n in list(state.nodes):
        ivals = occupied_intervals(n, state, floors=[n.floor], ignore_ids={n.id})
        if slot_fits(n.x, ivals):
            continue
        dest = search_left_then_right(n.x, ivals)
        if dest is not None:
            n.x = dest


def spawn_x_for_floor(state: MapState, floor: int, elevator: str = "none") -> Optional[int]:
    dummy = Node(id="__spawn__", title="", floor=floor, x=0, elevator=elevator)
    prefer = blue_elevator_x() if elevator == "blue" else snap((MAP_W - NODE_W) // 2)
    return fit_x_on_floor(dummy, prefer, floor, state)


def apply_elevator_x(state: MapState, kind: str, x: int, assets: Optional["AssetStore"] = None,
                     anchor: Optional[Node] = None):
    if not kind or kind == "none":
        return
    fc = state.floor_count()
    members = state.elevator_segment(anchor) if anchor is not None else state.elevator_group(kind)
    for n in members:
        carried = collect_node_stickers(n, state, assets, fc) if assets is not None else []
        n.x = x
        if assets is not None:
            apply_node_stickers(n, carried, state, fc)


def find_ui_asset(*names: str) -> str:
    roots = []
    for root in (UI_ASSETS_DIR, UI_ASSETS_BUNDLE, SCRIPT_DIR, bundle_dir()):
        if root and root not in roots:
            roots.append(root)
    for root in roots:
        for name in names:
            path = os.path.join(root, name)
            if os.path.isfile(path):
                return path
    return ""


def color_titlebar_black() -> None:
    """Windows: black caption bar, light title text via immersive dark mode."""
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


def apply_editor_chrome(screen) -> None:
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
            pygame.mouse.set_cursor((0, 0), cur)
        except Exception:
            try:
                pygame.mouse.set_cursor(pygame.cursors.Cursor((0, 0), cur))
            except Exception:
                pass


def load_panel_background(width: int, height: int):
    import pygame
    path = find_ui_asset(ASSET_BG)
    if not path or width < 8 or height < 8:
        return None
    try:
        img = pygame.image.load(path).convert()
        return pygame.transform.smoothscale(img, (width, height))
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Minimal pygame UI toolkit
# ---------------------------------------------------------------------------

def run_editor():
    import pygame
    from pygame import Rect

    pygame.init()
    pygame.key.set_repeat(350, 35)
    shortcuts = load_shortcuts()
    hotkey_held = set()
    pygame.display.set_caption(WINDOW_TITLE)
    screen = pygame.display.set_mode((1600, 900), pygame.RESIZABLE)
    apply_editor_chrome(screen)
    clock = pygame.time.Clock()
    def pg_font(path, size, bold=False):
        if path:
            try:
                return pygame.font.Font(path, size)
            except Exception:
                pass
        f = pygame.font.SysFont("arial,segoeui,tahoma,calibri,sans", size, bold=bold)
        return f

    ui_font = pg_font(FONT_PATH, 13)
    ui_font_sm = pg_font(FONT_PATH, 11)
    ui_font_b = pg_font(FONT_BOLD, 13, bold=True)

    ensure_user_asset_folders()
    assets = AssetStore()
    assets.load_json(DEFAULT_JSON)
    renderer = MapRenderer(assets)
    state = MapState()
    boot = placeholder_json_path()
    if boot:
        try:
            with open(boot, "r", encoding="utf-8") as f:
                state.load_dict(json.load(f), assets)
        except Exception:
            state.seed_default()
    else:
        state.seed_default()
    def saved_map_fingerprint() -> str:
        return json.dumps(enrich_groups(state, assets), sort_keys=True, separators=(",", ":"))

    last_saved_sig = saved_map_fingerprint()

    # camera
    cam_x, cam_y = 0, 0
    zoom = 0.55
    dragging_map = False
    dragging_scroll = False
    search_open = False
    connect_press = None
    last_mouse = (0, 0)

    selected_node: Optional[str] = None
    selected_sticker: Optional[str] = None
    dragging_node = None
    dragging_sticker = None
    dragging_elev = None
    drag_grab_off = 0  # px from node left where click started
    drag_sticker_off = (0, 0)
    awaiting_resume_off = None  # after teleport, wait for mouse local x
    last_dir = 0
    stickers_dragged_with: List[Tuple[str, int, int]] = []  # id, dx_tiles, dy_tiles

    status = "Ready."
    status_at = 0
    collapsed_cats = set()
    status_color = (200, 200, 160)
    lock_stickers = False
    hide_stickers = False
    hide_paths = False
    hide_mode = 0
    last_dot_click = {"id": "", "t": 0}
    path_v_used = False
    catalog_rmb = None
    show_floor_ruler = False
    floor_box_surf = None
    catalog_sel = 0
    pg_thumbs: Dict[str, Any] = {}
    thumb_cd_until = 0
    view_cache = {"sig": None, "surf": None, "box": (0, 0, 1, 1)}
    panel_bg_cache = {"key": None, "surf": None}
    catalog_scroll = 0
    catalog_dragging = False
    catalog_bar = {"rect": None, "max": 0}
    focused_port: Optional[str] = None
    port_focus_at = 0

    def set_focused_port(pk: Optional[str]):
        nonlocal focused_port, port_focus_at
        if pk != focused_port:
            port_focus_at = pygame.time.get_ticks()
        focused_port = pk

    def do_export_json():
        nonlocal last_saved_sig
        state.name = fields["export_name"] or "Placeholder"
        path = native_file_dialog("save", "Export map JSON",
                                 [("JSON", "*.json"), ("All files", "*.*")],
                                 SCRIPT_DIR, f"{state.name}.json")
        if path:
            data = enrich_groups(state, assets)
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            last_saved_sig = saved_map_fingerprint()
            set_status(f"Exported {path}")

    def do_render_png():
        broken = [n.title for n in state.nodes if node_is_invalid(n, state)]
        state.name = fields["export_name"] or "Placeholder"
        folder = native_file_dialog("dir", "Choose folder for rendered PNG", initialdir=SCRIPT_DIR)
        if folder:
            png = os.path.join(folder, f"{state.name}.png")
            renderer.export_png(state, png, hide_stickers=hide_stickers, hide_paths=hide_paths)
            if broken:
                set_status("Some nodes are not connected")
            else:
                set_status(f"Rendered {png}")

    connect_mode: Optional[str] = None  # None | pick_node | pick_port
    connect_src_id: Optional[str] = None
    connect_src_port: Optional[str] = None
    connect_dest_id: Optional[str] = None

    # text fields
    fields = {
        "export_name": state.name,
        "title": "",
        "floor": "",
        "stars": "",
        "sticker_x": str(blue_elevator_x()),
        "sticker_y": "390",
        "base": "0",
        "search": "",
    }
    active_field = None
    field_backup = {}
    field_sel = {}  # key -> (start, end) inclusive-exclusive
    field_view = {}  # key -> first visible char
    selecting_field = None
    caret_blink = 0

    port_color = {k: "cyan" for k in PORT_KEYS}
    port_gate = {k: "none" for k in PORT_KEYS}
    mat_sel = "Empty"
    elev_sel = "none"
    roof_sel = False
    mat_right_sel = False

    def set_status(msg: str):
        nonlocal status, status_color, status_at
        status = msg
        status_at = pygame.time.get_ticks()
        low = (msg or "").lower()
        if low.startswith("refused") or low.startswith("refuse"):
            status_color = (255, 150, 150)
        else:
            status_color = (200, 200, 160)

    def despawn_selected_node():
        nonlocal selected_node, selected_sticker
        if not selected_node:
            return
        nd = state.find_by_id(selected_node)
        old_fc = state.floor_count()
        drop = set()
        if nd:
            title = nd.title.strip().lower()
            for pk in list(nd.ports.keys()):
                clear_port_link(nd, pk, state)
            for o in state.nodes:
                if o.id == nd.id:
                    continue
                for pk, pdata in o.ports.items():
                    if (pdata.get("target") or "").strip().lower() == title:
                        pdata["target"] = ""
            fc = state.floor_count()
            for st in state.stickers:
                if sticker_hits_node(st, nd, assets, fc, min_floor=state.min_floor()):
                    drop.add(st.id)
        state.nodes = [n for n in state.nodes if n.id != selected_node]
        if drop:
            for sid in drop:
                unregister_path_dot(state, sid)
            state.stickers = [s for s in state.stickers if s.id not in drop]
        selected_node = None
        selected_sticker = None
        adjust_stickers_after_floor_change(state, assets, old_fc)
        prune_edge_ports(state)
        set_status("Node deleted.")

    def fill_form_from_node(n: Optional[Node]):
        nonlocal mat_sel, elev_sel, roof_sel, mat_right_sel, focused_port, active_field, selecting_field
        if active_field:
            commit_field(active_field)
            active_field = None
            selecting_field = None
        if n is None:
            fields["title"] = ""
            fields["floor"] = ""
            fields["stars"] = ""
            for k in PORT_KEYS:
                port_color[k] = "cyan"
                port_gate[k] = "none"
            mat_sel = "Empty"
            elev_sel = "none"
            roof_sel = False
            mat_right_sel = False
            set_focused_port(None)
            return
        fields["title"] = n.title
        fields["floor"] = str(n.floor)
        fields["stars"] = n.stars
        ny = node_y_on_floor(n.floor, state.floor_count(), state.min_floor())
        fields["sticker_x"] = str(int(round(n.x + NODE_W / 2)))
        fields["sticker_y"] = str(int(round(ny + NODE_H / 2)))
        mat_sel = n.material
        elev_sel = n.elevator
        roof_sel = bool(getattr(n, "roof", False))
        mat_right_sel = bool(getattr(n, "mat_right", False))
        for k in PORT_KEYS:
            port_color[k] = n.ports[k].get("color", "cyan")
            port_gate[k] = n.ports[k].get("gate", "none")
        set_focused_port(None)

    fill_form_from_node(None)

    def read_form_into(n: Node):
        # Snapshot decorations on this node BEFORE any x/floor/elevator snap.
        carried = collect_node_stickers(n, state, assets, state.floor_count())
        new_title = fields["title"].strip() or n.title
        other = state.find_by_title(new_title)
        if other is not None and other.id != n.id:
            set_status("REFUSED: that node name already exists")
            return False
        old_title = n.title
        n.title = new_title
        if old_title.strip().lower() != new_title.strip().lower() or old_title != new_title:
            retarget_node_title(state, old_title, new_title)
        n.stars = fields["stars"].strip()
        n.material = mat_sel
        n.mat_right = bool(mat_right_sel)
        try:
            new_fl = max(0, int(fields["floor"]))
        except ValueError:
            new_fl = n.floor
        new_elev = elev_sel
        old_elev = n.elevator
        old_grp = list(state.elevator_segment(n)) if old_elev not in ("", "none") else [n]
        dest_rig = []
        if new_elev not in ("", "none"):
            others = [g for g in state.elevator_group(new_elev) if g.id != n.id]
            if others:
                near = min(others, key=lambda g: abs(g.floor - new_fl))
                dest_rig = [g for g in state.elevator_segment(near) if g.id != n.id]

        if new_elev in ("", "none"):
            targets = [n]
            new_elev = "none"
        elif dest_rig:
            targets = [n]
        else:
            targets = list(old_grp) if old_elev not in ("", "none") else [n]

        for g in targets:
            fl = new_fl if g.id == n.id else g.floor
            if new_elev not in ("", "none") and elevator_on_floor(state, new_elev, fl, g.id):
                set_status(f"REFUSED: {new_elev} elevator already on {floor_label(fl)}")
                return False
        if new_elev not in ("", "none"):
            probe = Node(id=n.id, title=n.title, floor=new_fl, x=n.x, elevator=new_elev)
            if fit_x_on_floor(probe, n.x, new_fl, state) is None:
                set_status(f"REFUSED: no space for {new_elev} elevator on {floor_label(new_fl)}")
                return False
        for g in targets:
            g.elevator = new_elev
            g.elevator_a = ""
            g.elevator_b = ""
        n.roof = bool(roof_sel)
        for k in PORT_KEYS:
            n.ports[k]["color"] = port_color[k]
            n.ports[k]["gate"] = port_gate[k]
        blocked = move_node_to_floor(n, new_fl, state, assets)
        if blocked:
            fields["floor"] = str(n.floor)
            set_status(blocked)
            return False
        if n.elevator != "none":
            apply_elevator_x(state, n.elevator, n.x, assets, anchor=n)
        # Re-attach the original snapshot at the final x/floor.
        apply_node_stickers(n, carried, state, state.floor_count())
        prune_edge_ports(state)
        return True

    def add_sticker_from_ui():
        nonlocal selected_sticker, selected_node
        names = assets.sticker_names
        if not names:
            set_status("No stickers in Sticker_assets")
            return
        name = names[catalog_sel % len(names)]
        try:
            tx = int(fields["sticker_x"] or "0")
            ty = int(fields["sticker_y"] or "0")
        except ValueError:
            tx, ty = 0, 0
        if assets.get(name) is None:
            set_status(f"Missing image for sticker '{name}'")
            return
        tx, ty = clamp_sticker_xy(tx, ty, state, assets, name, False)
        if any(s.name == name and s.tile_x == tx and s.tile_y == ty for s in state.stickers):
            set_status("REFUSED: same sticker already at that position")
            return
        st = Sticker(id=state.next_id("s"), name=name, tile_x=tx, tile_y=ty, big=False)
        state.stickers.append(st)
        register_path_dot(state, st, selected_sticker)
        selected_sticker = st.id
        selected_node = None
        set_status(f"Added sticker {name} @ ({tx},{ty})")

    def despawn_selected_sticker():
        nonlocal selected_sticker, selected_node
        if not selected_sticker:
            set_status("No sticker selected.")
            return
        st = next((s for s in state.stickers if s.id == selected_sticker), None)
        nxt_id = None
        color = path_dot_color(st.name) if st else ""
        if color:
            ids = list(((state.path_routes or {}).get(color) or {}).get("ids") or [])
            if selected_sticker in ids:
                i = ids.index(selected_sticker)
                if i + 1 < len(ids):
                    nxt_id = ids[i + 1]
                elif i > 0:
                    nxt_id = ids[i - 1]
        unregister_path_dot(state, selected_sticker)
        state.stickers = [s for s in state.stickers if s.id != selected_sticker]
        selected_sticker = nxt_id
        selected_node = None
        if selected_sticker:
            nxt = next((s for s in state.stickers if s.id == selected_sticker), None)
            if nxt:
                fields["sticker_x"] = str(int(nxt.tile_x))
                fields["sticker_y"] = str(int(nxt.tile_y))
        set_status("Sticker despawned.")

    def cancel_connect(msg="Connection cancelled."):
        nonlocal connect_mode, connect_src_id, connect_src_port, connect_dest_id, connect_press
        connect_mode = None
        connect_src_id = None
        connect_src_port = None
        connect_dest_id = None
        connect_press = None
        set_status(msg)

    def finish_connect_click(sx, sy):
        nonlocal focused_port, selected_node, selected_sticker, connect_dest_id
        wx, wy = world_from_screen(sx, sy, sw, sh)
        src = state.find_by_id(connect_src_id) if connect_src_id else None
        dest = hit_node(wx, wy)
        if dest is None or src is None:
            return
        if dest.id == src.id:
            cancel_connect("Connection cancelled.")
            return
        if not dest_floor_ok(src, connect_src_port, dest):
            cancel_connect("REFUSED: same-floor or up/down mismatch — connection aborted.")
            return
        connect_dest_id = dest.id
        selected_node = dest.id
        selected_sticker = None
        fill_form_from_node(dest)
        set_status("doing port connection — click a valid port (or another node)")

    def canvas_rect(sw, sh):
        return Rect(0, 0, max(8, sw - 420 - SCROLL_W), sh - 28)

    def scroll_rect(sw, sh):
        return Rect(sw - 420 - SCROLL_W, 0, SCROLL_W, sh - 28)

    def scroll_cam_from_y(my, sw, sh):
        nonlocal cam_y
        sr = scroll_rect(sw, sh)
        cr = canvas_rect(sw, sh)
        world_h = state.floor_count() * FLOOR_H
        view_h = cr.h / max(0.05, zoom)
        max_cam = max(0.0, world_h - view_h)
        steps = max(1, int(math.ceil(max_cam / FLOOR_H)))
        t = (my - sr.y) / max(1, sr.h)
        step = int(clamp(round(t * steps), 0, steps))
        cam_y = min(max_cam, step * FLOOR_H)

    def world_from_screen(mx, my, sw, sh):
        r = canvas_rect(sw, sh)
        wx = (mx - r.x) / zoom + cam_x
        wy = (my - r.y) / zoom + cam_y
        return wx, wy

    def hit_node(wx, wy) -> Optional[Node]:
        fc = state.floor_count()
        mf = state.min_floor()
        # topmost first
        for n in reversed(state.nodes):
            ny = node_y_on_floor(n.floor, fc, mf)
            if n.x <= wx <= n.x + NODE_W and ny <= wy <= ny + NODE_H:
                return n
        return None

    def hit_elevator_icon(wx, wy) -> Optional[Node]:
        fc = state.floor_count()
        mf = state.min_floor()
        for n in reversed(state.nodes):
            if not n.elevator or n.elevator == "none":
                continue
            ev = assets.get_elevator(n.elevator)
            w = ev.width if ev is not None else ELEV_S
            h = ev.height if ev is not None else ELEV_S
            ny = node_y_on_floor(n.floor, fc, mf)
            half = w / 2
            dx = clamp(int(getattr(n, "elev_dx", 0)), int(-NODE_W / 2 + half), int(NODE_W / 2 - half))
            ex = n.x + NODE_W / 2 - half + dx
            ey = ny + NODE_H / 2 - h / 2 + 22
            if ex <= wx <= ex + w and ey <= wy <= ey + h:
                return n
        return None

    def hit_sticker(wx, wy) -> Optional[Sticker]:
        for st in reversed(state.stickers):
            img = assets.get(st.name)
            if img is None:
                continue
            x, y = sticker_world(st)
            w, h = sticker_size(st.name, assets, getattr(st, "big", False))
            if x <= wx <= x + w and y <= wy <= y + h:
                if hide_stickers or (hide_paths and path_dot_color(st.name)) or (
                        lock_stickers and sticker_locked_on_node(st, state, assets)):
                    continue
                return st
        return None

    # widget layout helpers
    buttons = {}  # name -> Rect computed each frame

    def draw_text(surf, text, pos, font=None, color=(230, 230, 230)):
        font = font or ui_font
        surf.blit(font.render(text, True, color), pos)

    def button(surf, name, rect, label, mouse, click):
        hover = rect.collidepoint(mouse)
        col = (70, 70, 80) if not hover else (95, 95, 110)
        pygame.draw.rect(surf, col, rect, border_radius=3)
        pygame.draw.rect(surf, (140, 140, 150), rect, 1, border_radius=3)
        ts = ui_font.render(label, True, (240, 240, 240))
        surf.blit(ts, (rect.x + (rect.w - ts.get_width()) // 2, rect.y + (rect.h - ts.get_height()) // 2))
        buttons[name] = rect
        return click and hover

    def _field_slice(key, rect):
        txt = fields.get(key, "")
        max_w = max(8, rect.w - 8)
        sel = field_sel.get(key) or (len(txt), len(txt))
        caret = max(0, min(len(txt), sel[1]))
        off = max(0, min(len(txt), field_view.get(key, 0)))
        if caret < off:
            off = caret
        while off < caret and ui_font.size(txt[off:caret])[0] > max_w:
            off += 1
        end = off
        while end < len(txt) and ui_font.size(txt[off:end + 1])[0] <= max_w:
            end += 1
        field_view[key] = off
        return off, txt[off:end]

    def _field_index_at(key, rect, mx):
        txt = fields.get(key, "")
        off, shown = _field_slice(key, rect)
        x = mx - rect.x - 4
        if x <= 0:
            return off
        for i in range(len(shown) + 1):
            if ui_font.size(shown[:i])[0] >= x:
                return off + i
        return off + len(shown)

    def commit_field(key: str) -> bool:
        nonlocal active_field
        if not key or key not in fields:
            return True
        raw = fields.get(key, "")
        prev = field_backup.get(key, raw)
        ok = True
        if key == "stars":
            fields[key] = "".join(c for c in raw if c.isdigit())
            n = state.find_by_id(selected_node) if selected_node else None
            if n is not None:
                n.stars = fields[key]
        elif key == "floor":
            try:
                v = int(str(raw).strip())
                if v < 0:
                    raise ValueError
                fields[key] = str(v)
            except ValueError:
                fields[key] = prev
                ok = False
                set_status("REFUSED: floor must be 0 or higher")
            else:
                n = state.find_by_id(selected_node) if selected_node else None
                if n is not None and not read_form_into(n):
                    fields[key] = prev
                    ok = False
        elif key == "title":
            t = raw.strip()
            n = state.find_by_id(selected_node) if selected_node else None
            if not t:
                if n is not None:
                    fields[key] = prev or n.title
                    ok = False
                else:
                    fields[key] = t
            else:
                other = state.find_by_title(t)
                if other is not None and (n is None or other.id != n.id):
                    fields[key] = prev
                    ok = False
                    set_status("REFUSED: that node name already exists")
                else:
                    fields[key] = t
                    if n is not None and n.title != t:
                        retarget_node_title(state, n.title, t)
                        n.title = t
        elif key in ("sticker_x", "sticker_y"):
            try:
                v = int(str(raw).strip())
                fields[key] = str(v)
            except ValueError:
                fields[key] = prev
                ok = False
                set_status("REFUSED: sticker coordinate must be a number")
            else:
                st = next((s for s in state.stickers if s.id == selected_sticker), None)
                if st is not None:
                    try:
                        tx = int(fields["sticker_x"] or "0")
                        ty = int(fields["sticker_y"] or "0")
                    except ValueError:
                        tx, ty = int(st.tile_x), int(st.tile_y)
                    st.tile_x, st.tile_y = clamp_sticker_xy(tx, ty, state, assets, st.name, st.big)
                    fields["sticker_x"] = str(int(st.tile_x))
                    fields["sticker_y"] = str(int(st.tile_y))
        elif key == "base":
            rawu = (raw or "").strip().upper()
            new_base = None
            if rawu in ("B1", "0"):
                new_base = 0
            else:
                try:
                    new_base = int(rawu)
                except ValueError:
                    new_base = None
            if new_base is None or new_base < 0:
                fields[key] = prev
                ok = False
                set_status("REFUSED: base must be 0 / B1 or a positive floor number")
            else:
                fields[key] = "0" if new_base == 0 else str(new_base)
        elif key == "export_name":
            t = raw.strip()
            if not t:
                fields[key] = prev or "Placeholder"
            else:
                fields[key] = t
                state.name = t
        field_backup[key] = fields.get(key, prev)
        return ok

    def field_box(surf, key, rect, mouse, click, label=None):
        nonlocal active_field, selecting_field
        if label:
            draw_text(surf, label, (rect.x, rect.y - 14), ui_font_sm, (180, 180, 180))
        hover = rect.collidepoint(mouse)
        if click and hover:
            if active_field and active_field != key:
                commit_field(active_field)
                active_field = None
            if active_field != key:
                field_backup[key] = fields.get(key, "")
            active_field = key
            selecting_field = key
            idx = _field_index_at(key, rect, mouse[0])
            field_sel[key] = (idx, idx)
        focus = active_field == key
        pygame.draw.rect(surf, (25, 25, 30), rect, border_radius=2)
        pygame.draw.rect(surf, (220, 220, 220) if focus else (90, 90, 100), rect, 1, border_radius=2)
        txt = fields.get(key, "")
        off, shown = _field_slice(key, rect)
        ts = ui_font.render(shown, True, (240, 240, 240))
        sel = field_sel.get(key)
        if focus and sel and sel[0] != sel[1]:
            a, b = sorted(sel)
            a, b = max(0, a - off), max(0, b - off)
            x0s = rect.x + 4 + ui_font.size(shown[:a])[0]
            x1s = rect.x + 4 + ui_font.size(shown[:b])[0]
            pygame.draw.rect(surf, (70, 110, 180), Rect(x0s, rect.y + 3, max(2, x1s - x0s), rect.h - 6))
        prev_clip = surf.get_clip()
        surf.set_clip(rect)
        surf.blit(ts, (rect.x + 4, rect.y + (rect.h - ts.get_height()) // 2))
        surf.set_clip(prev_clip)
        if focus and (caret_blink // 30) % 2 == 0:
            caret_i = sel[1] if sel else len(txt)
            caret_i = max(0, caret_i - off)
            cx = rect.x + 4 + ui_font.size(shown[:caret_i])[0]
            pygame.draw.line(surf, (240, 240, 240), (cx, rect.y + 4), (cx, rect.bottom - 4))
        buttons[f"field_{key}"] = rect

    def radio_row(surf, x, y, options, current, mouse, click, prefix):
        chosen = current
        xx = x
        for opt in options:
            r = Rect(xx, y, 8 + ui_font_sm.size(opt)[0] + 16, 18)
            on = current == opt
            pygame.draw.rect(surf, (50, 90, 50) if on else (40, 40, 48), r, border_radius=3)
            pygame.draw.rect(surf, (180, 220, 180) if on else (80, 80, 90), r, 1, border_radius=3)
            surf.blit(ui_font_sm.render(opt, True, (230, 230, 230)), (r.x + 6, r.y + 2))
            if click and r.collidepoint(mouse):
                chosen = opt
            xx = r.right + 4
        return chosen, xx, y + 22

    def checkbox(surf, rect, on, label, mouse, click):
        pygame.draw.rect(surf, (60, 140, 60) if on else (40, 40, 48), rect, border_radius=2)
        pygame.draw.rect(surf, (200, 200, 200), rect, 1, border_radius=2)
        if on:
            pygame.draw.line(surf, (240, 240, 240), (rect.x + 3, rect.y + 8), (rect.x + 7, rect.y + 13), 2)
            pygame.draw.line(surf, (240, 240, 240), (rect.x + 7, rect.y + 13), (rect.x + 14, rect.y + 3), 2)
        surf.blit(ui_font_sm.render(label, True, (220, 220, 220)), (rect.right + 6, rect.y + 1))
        return on if not (click and rect.collidepoint(mouse)) else (not on)

    def draw_gate_lock(surf, x, y, kind: str):
        """Tiny lock so we don't depend on emoji fonts."""
        if kind == "open":
            return
        body = Rect(x + 3, y + 8, 12, 10)
        if kind == "closed-gate":
            col, shackle = (110, 35, 35), (90, 25, 25)
        else:
            col, shackle = (45, 100, 55), (35, 80, 45)
        pygame.draw.arc(surf, shackle, Rect(x + 4, y + 1, 10, 10), 0.0, 3.15, 2)
        pygame.draw.rect(surf, col, body, border_radius=2)

    running = True
    click = False
    while running:
        sw, sh = screen.get_size()
        mouse = pygame.mouse.get_pos()
        click = False
        events = pygame.event.get()
        for ev in events:
            if ev.type == pygame.QUIT:
                if saved_map_fingerprint() != last_saved_sig:
                    if native_yes_no("Let It Die Node Maker",
                                    "Save changes before leaving?"):
                        state.name = fields["export_name"] or "Placeholder"
                        path = native_file_dialog(
                            "save", "Export map JSON",
                            [("JSON", "*.json"), ("All files", "*.*")],
                            SCRIPT_DIR, f"{state.name}.json",
                        )
                        if not path:
                            continue
                        with open(path, "w", encoding="utf-8") as f:
                            json.dump(enrich_groups(state, assets), f, indent=2)
                running = False
            elif ev.type == pygame.VIDEORESIZE:
                screen = pygame.display.set_mode(ev.size, pygame.RESIZABLE)
                pygame.display.set_caption(WINDOW_TITLE)
                apply_editor_chrome(screen)
            elif ev.type == pygame.MOUSEBUTTONDOWN:
                if ev.button == 1:
                    click = True
                    last_mouse = ev.pos
                    cr = canvas_rect(sw, sh)
                    sr = scroll_rect(sw, sh)
                    if sr.collidepoint(ev.pos):
                        dragging_scroll = True
                        scroll_cam_from_y(ev.pos[1], sw, sh)
                    elif search_open and Rect(cr.right - 228, cr.y + 6, 226, 22).collidepoint(ev.pos):
                        sbox = Rect(cr.right - 228, cr.y + 6, 200, 22)
                        xbtn = Rect(sbox.right + 4, sbox.y, 22, 22)
                        if xbtn.collidepoint(ev.pos):
                            search_open = False
                            fields["search"] = ""
                            if active_field == "search":
                                active_field = None
                    elif cr.collidepoint(ev.pos) and ev.pos[0] < sw - 420:
                        wx, wy = world_from_screen(*ev.pos, sw, sh)
                        if connect_mode:
                            connect_press = ev.pos
                            last_mouse = ev.pos
                        else:
                            st = hit_sticker(wx, wy)
                            nd = hit_node(wx, wy)
                            if st is not None:
                                add_key = shortcuts.get("add_sticker")
                                prev_st = next((s for s in state.stickers if s.id == selected_sticker), None) if selected_sticker else None
                                if (add_key and add_key in hotkey_held
                                        and prev_st is not None
                                        and path_dot_color(prev_st.name)
                                        and path_dot_color(st.name)):
                                    mid = insert_path_dot_between(state, assets, prev_st, st)
                                    if mid is not None:
                                        path_v_used = True
                                        selected_sticker = mid.id
                                        selected_node = None
                                        fields["sticker_x"] = str(int(mid.tile_x))
                                        fields["sticker_y"] = str(int(mid.tile_y))
                                        set_status(f"Inserted {mid.name} path dot")
                                        fill_form_from_node(None)
                                        continue
                                selected_sticker = st.id
                                selected_node = None
                                sx, sy = sticker_world(st)
                                fields["sticker_x"] = str(int(sx))
                                fields["sticker_y"] = str(int(sy))
                                if st.name in assets.sticker_names:
                                    catalog_sel = assets.sticker_names.index(st.name)
                                rows = catalog_rows(
                                    getattr(assets, "catalog_entries", None)
                                    or [("item", n) for n in assets.sticker_names], 5)
                                for i, (kind, payload) in enumerate(rows):
                                    if kind == "items" and st.name in payload:
                                        catalog_scroll = i
                                        break
                                nowc = pygame.time.get_ticks()
                                color = path_dot_color(st.name)
                                if (color and last_dot_click["id"] == st.id
                                        and nowc - last_dot_click["t"] < 400):
                                    bucket = state.path_routes.setdefault(color, {"ids": [], "dir": 1})
                                    bucket["dir"] = -1 if int(bucket.get("dir", 1) or 1) >= 0 else 1
                                    last_dot_click = {"id": "", "t": 0}
                                    set_status(f"{color} path arrows flipped")
                                else:
                                    last_dot_click = {"id": st.id, "t": nowc}
                                    dragging_sticker = st.id
                                    drag_sticker_off = (wx - sx, wy - sy)
                                fill_form_from_node(None)
                            else:
                                evn = hit_elevator_icon(wx, wy)
                                if evn is not None:
                                    selected_node = evn.id
                                    selected_sticker = None
                                    fill_form_from_node(evn)
                                    if not (lock_stickers or hide_stickers):
                                        dragging_elev = evn.id
                                elif nd is not None:
                                    join_key = shortcuts.get("join_elevator")
                                    shift_on = bool(pygame.key.get_mods() & pygame.KMOD_SHIFT)
                                    prev = state.find_by_id(selected_node) if selected_node else None
                                    if (shortcuts and join_key and shift_on and prev is not None
                                            and prev.elevator not in ("", "none")
                                            and nd.id != prev.id):
                                        selected_node = nd.id
                                        selected_sticker = None
                                        fill_form_from_node(nd)
                                        elev_sel = prev.elevator
                                        if read_form_into(nd):
                                            set_status(f"{nd.title} set to {nd.elevator} elevator")
                                        else:
                                            fill_form_from_node(nd)
                                    else:
                                        selected_node = nd.id
                                        selected_sticker = None
                                        fill_form_from_node(nd)
                                        dragging_node = nd.id
                                        drag_grab_off = wx - nd.x
                                        awaiting_resume_off = None
                                        last_dir = 0
                                        stickers_dragged_with = collect_node_stickers(nd, state, assets, state.floor_count())
                                else:
                                    had = selected_node
                                    selected_node = None
                                    selected_sticker = None
                                    dragging_map = True
                                    if had:
                                        fill_form_from_node(None)
                    else:
                        # clicking panel: if not on a field, clear focus later via field_box
                        pass
                elif ev.button == 2:
                    dragging_map = True
                    last_mouse = ev.pos
                elif ev.button == 3:
                    cr = canvas_rect(sw, sh)
                    if cr.collidepoint(ev.pos) and ev.pos[0] < sw - 420:
                        wx, wy = world_from_screen(*ev.pos, sw, sh)
                        st = hit_sticker(wx, wy)
                        if st is not None:
                            unregister_path_dot(state, st.id)
                            state.stickers = [s for s in state.stickers if s.id != st.id]
                            if selected_sticker == st.id:
                                selected_sticker = None
                            set_status("Sticker despawned.")
                        else:
                            fields["sticker_x"] = str(int(wx))
                            fields["sticker_y"] = str(int(wy))
                            if not selected_node:
                                fc = state.floor_count()
                                mf = state.min_floor()
                                idx = int(wy // FLOOR_H)
                                fi = (fc - 1) - idx
                                if 0 <= fi < fc:
                                    fields["floor"] = str(mf + fi)
                            set_status(f"Sticker pos ({int(wx)}, {int(wy)})")
                    elif ev.pos[0] >= sw - 420:
                        catalog_rmb = {"t": pygame.time.get_ticks(), "cleared": False}
                    else:
                        dragging_map = True
                        last_mouse = ev.pos
                elif ev.button == 4:
                    if mouse[0] >= sw - 420:
                        catalog_scroll = max(0, catalog_scroll - 1)
                    else:
                        zoom = clamp(zoom * 1.1, 0.2, 2.0)
                elif ev.button == 5:
                    if mouse[0] >= sw - 420:
                        catalog_scroll += 1
                    else:
                        zoom = clamp(zoom / 1.1, 0.2, 2.0)
            elif ev.type == pygame.MOUSEBUTTONUP:
                if connect_mode and connect_press and not dragging_map and ev.button == 1:
                    finish_connect_click(*connect_press)
                connect_press = None
                dragging_map = False
                dragging_scroll = False
                dragging_node = None
                dragging_sticker = None
                dragging_elev = None
                awaiting_resume_off = None
                stickers_dragged_with = []
                selecting_field = None
                catalog_dragging = False
                catalog_rmb = None
            elif ev.type == pygame.MOUSEMOTION:
                mx, my = ev.pos
                if catalog_dragging and catalog_bar.get("rect"):
                    r = catalog_bar["rect"]
                    max_s = catalog_bar.get("max", 0)
                    t = (my - r.y) / max(1, r.h)
                    catalog_scroll = int(clamp(t * (max_s + 1), 0, max_s))
                elif selecting_field and selecting_field in fields:
                    rsel = buttons.get(f"field_{selecting_field}")
                    if rsel:
                        idx = _field_index_at(selecting_field, rsel, mx)
                        a = field_sel.get(selecting_field, (idx, idx))[0]
                        field_sel[selecting_field] = (a, idx)
                elif connect_mode and connect_press and ev.buttons[0]:
                    if abs(mx - connect_press[0]) + abs(my - connect_press[1]) > 8:
                        dragging_map = True
                    if dragging_map:
                        dx = (last_mouse[0] - mx) / zoom
                        dy = (last_mouse[1] - my) / zoom
                        cam_x += dx
                        cam_y += dy
                        last_mouse = ev.pos
                elif dragging_scroll:
                    scroll_cam_from_y(my, sw, sh)
                    last_mouse = ev.pos
                elif dragging_map:
                    dx = (last_mouse[0] - mx) / zoom
                    dy = (last_mouse[1] - my) / zoom
                    cam_x += dx
                    cam_y += dy
                    last_mouse = ev.pos
                elif dragging_elev:
                    wx, wy = world_from_screen(mx, my, sw, sh)
                    n = state.find_by_id(dragging_elev)
                    if n:
                        ev = assets.get_elevator(n.elevator)
                        w = ev.width if ev is not None else ELEV_S
                        half = w / 2
                        dx = wx - (n.x + NODE_W / 2)
                        n.elev_dx = int(clamp(dx, -NODE_W / 2 + half, NODE_W / 2 - half))
                elif dragging_sticker:
                    wx, wy = world_from_screen(mx, my, sw, sh)
                    for st in state.stickers:
                        if st.id == dragging_sticker:
                            st.tile_x, st.tile_y = clamp_sticker_xy(
                                int(wx - drag_sticker_off[0]),
                                int(wy - drag_sticker_off[1]),
                                state, assets, st.name, getattr(st, "big", False))
                            fields["sticker_x"] = str(st.tile_x)
                            fields["sticker_y"] = str(st.tile_y)
                            break
                elif dragging_node:
                    wx, wy = world_from_screen(mx, my, sw, sh)
                    n = state.find_by_id(dragging_node)
                    if n:
                        desired = snap(wx - drag_grab_off)
                        direction = 1 if desired > n.x else (-1 if desired < n.x else 0)
                        last_dir = direction or last_dir
                        if awaiting_resume_off is not None:
                            local = wx - n.x
                            if abs(local - awaiting_resume_off) < 8:
                                awaiting_resume_off = None
                        else:
                            nx, jumped, refuse = proposed_x_legal(n, desired, state, direction)
                            if refuse:
                                set_status(refuse)
                            if jumped and nx != desired and direction != 0:
                                awaiting_resume_off = drag_grab_off
                            n.x = nx
                        if n.elevator != "none":
                            apply_elevator_x(state, n.elevator, n.x, assets, anchor=n)
                        apply_node_stickers(n, stickers_dragged_with, state, state.floor_count())
            elif ev.type == pygame.KEYUP:
                add_key = shortcuts.get("add_sticker") if shortcuts else None
                if add_key and ev.key == add_key and not (hide_stickers or lock_stickers):
                    cur = next((s for s in state.stickers if s.id == selected_sticker), None) if selected_sticker else None
                    if cur is not None and path_dot_color(cur.name) and not path_v_used:
                        add_sticker_from_ui()
                    path_v_used = False
                hotkey_held.discard(ev.key)
            elif ev.type == pygame.KEYDOWN:
                mods = pygame.key.get_mods()
                if (mods & pygame.KMOD_CTRL) and ev.key == pygame.K_s:
                    do_export_json()
                    continue
                if (mods & pygame.KMOD_CTRL) and ev.key == pygame.K_r:
                    do_render_png()
                    continue
                if (mods & pygame.KMOD_CTRL) and ev.key == pygame.K_f:
                    search_open = True
                    active_field = "search"
                    field_sel["search"] = (0, len(fields.get("search") or ""))
                    continue
                if active_field:
                    txt = fields[active_field]
                    sel = field_sel.get(active_field)
                    if ev.key == pygame.K_a and (mods & pygame.KMOD_CTRL):
                        field_sel[active_field] = (0, len(txt))
                    elif ev.key == pygame.K_LEFT:
                        i = sel[1] if sel else len(txt)
                        i = max(0, i - 1)
                        if mods & pygame.KMOD_SHIFT:
                            a = sel[0] if sel else i + 1
                            field_sel[active_field] = (a, i)
                        else:
                            field_sel[active_field] = (i, i)
                    elif ev.key == pygame.K_RIGHT:
                        i = sel[1] if sel else len(txt)
                        i = min(len(txt), i + 1)
                        if mods & pygame.KMOD_SHIFT:
                            a = sel[0] if sel else i - 1
                            field_sel[active_field] = (a, i)
                        else:
                            field_sel[active_field] = (i, i)
                    elif ev.key == pygame.K_HOME:
                        field_sel[active_field] = (0, 0)
                    elif ev.key == pygame.K_END:
                        field_sel[active_field] = (len(txt), len(txt))
                    elif ev.key in (pygame.K_BACKSPACE, pygame.K_DELETE) and sel and sel[0] != sel[1]:
                        a, b = sorted(sel)
                        fields[active_field] = txt[:a] + txt[b:]
                        field_sel[active_field] = (a, a)
                    elif ev.key == pygame.K_BACKSPACE:
                        i = sel[1] if sel else len(txt)
                        i = max(0, min(len(txt), i))
                        if i > 0:
                            fields[active_field] = txt[:i - 1] + txt[i:]
                            field_sel[active_field] = (i - 1, i - 1)
                    elif ev.key == pygame.K_DELETE:
                        i = sel[1] if sel else len(txt)
                        i = max(0, min(len(txt), i))
                        if i < len(txt):
                            fields[active_field] = txt[:i] + txt[i + 1:]
                            field_sel[active_field] = (i, i)
                    elif ev.key == pygame.K_RETURN:
                        commit_field(active_field)
                        active_field = None
                        selecting_field = None
                    elif ev.key == pygame.K_ESCAPE:
                        if active_field in field_backup:
                            fields[active_field] = field_backup[active_field]
                        active_field = None
                        selecting_field = None
                    elif ev.key == pygame.K_TAB:
                        commit_field(active_field)
                        keys = list(fields.keys())
                        i = keys.index(active_field) if active_field in keys else -1
                        nxt = keys[(i + 1) % len(keys)]
                        field_backup[nxt] = fields.get(nxt, "")
                        active_field = nxt
                        field_sel[active_field] = (0, len(fields[active_field]))
                    else:
                        ch = ev.unicode
                        if ch and ch.isprintable():
                            if active_field == "stars" and not ch.isdigit():
                                ch = ""
                            if ch:
                                if sel and sel[0] != sel[1]:
                                    a, b = sorted(sel)
                                    fields[active_field] = txt[:a] + ch + txt[b:]
                                    field_sel[active_field] = (a + 1, a + 1)
                                else:
                                    i = sel[1] if sel else len(txt)
                                    i = max(0, min(len(txt), i))
                                    fields[active_field] = txt[:i] + ch + txt[i:]
                                    field_sel[active_field] = (i + 1, i + 1)
                elif shortcuts:
                    names = [k for k, v in shortcuts.items() if v == ev.key]
                    name = names[0] if names else None
                    if ev.key in hotkey_held and name not in ("delete_sticker",):
                        pass
                    else:
                        hotkey_held.add(ev.key)
                        if connect_mode and (
                                ev.key == shortcuts.get("cancel_connect")
                                or ev.key == shortcuts.get("delete_port")):
                            cancel_connect("Connection cancelled.")
                        elif name == "delete_sticker" and selected_sticker:
                            despawn_selected_sticker()
                        elif name == "center_camera" and not connect_mode:
                            H = state.floor_count() * FLOOR_H
                            cr2 = canvas_rect(sw, sh)
                            cam_x = MAP_W / 2 - (cr2.w / zoom) / 2
                            cam_y = H / 2 - (cr2.h / zoom) / 2
                            set_status("Camera centered.")
                        elif name == "update_node" and selected_node:
                            n = state.find_by_id(selected_node)
                            if n and read_form_into(n):
                                if n.elevator != "none":
                                    apply_elevator_x(state, n.elevator, n.x, assets, anchor=n)
                                set_status(f"Updated {n.title}")
                        elif name == "toggle_floor":
                            show_floor_ruler = not show_floor_ruler
                        elif name == "toggle_hide":
                            hide_mode = (hide_mode + 1) % 3
                            hide_paths = hide_mode >= 1
                            hide_stickers = hide_mode >= 2
                            if hide_stickers:
                                selected_sticker = None
                                dragging_sticker = None
                        elif name == "toggle_lock":
                            lock_stickers = not lock_stickers
                        elif name == "add_sticker" and not (hide_stickers or lock_stickers):
                            cur = next((s for s in state.stickers if s.id == selected_sticker), None) if selected_sticker else None
                            if cur is not None and path_dot_color(cur.name):
                                path_v_used = False
                            else:
                                add_sticker_from_ui()
                        elif name == "toggle_sticker_big" and selected_sticker:
                            st = next((s for s in state.stickers if s.id == selected_sticker), None)
                            if st:
                                st.big = not st.big
                                st.tile_x, st.tile_y = clamp_sticker_xy(
                                    st.tile_x, st.tile_y, state, assets, st.name, st.big)
                        elif name == "cycle_port_color" and selected_node and focused_port:
                            n = state.find_by_id(selected_node)
                            if n and (n.ports[focused_port].get("gate") or "") != "closed-gate":
                                cur = port_color.get(focused_port, n.ports[focused_port].get("color", "cyan"))
                                try:
                                    i = COLOR_ORDER.index(cur)
                                except ValueError:
                                    i = 0
                                nxt = COLOR_ORDER[(i + 1) % len(COLOR_ORDER)]
                                port_color[focused_port] = nxt
                                sync_link_color(n, focused_port, nxt, state)
                        elif name == "cycle_port_gate" and selected_node and focused_port:
                            n = state.find_by_id(selected_node)
                            if n:
                                gcur = port_gate.get(focused_port, n.ports[focused_port].get("gate", "open"))
                                if gcur in ("open-gate", "none", ""):
                                    gcur = "open"
                                try:
                                    gi = GATES.index(gcur)
                                except ValueError:
                                    gi = 0
                                nxt = GATES[(gi + 1) % len(GATES)]
                                port_gate[focused_port] = nxt
                                n.ports[focused_port]["gate"] = nxt
                        elif name in PORT_HOTKEY_ACTIONS and selected_node:
                            pk = PORT_HOTKEY_ACTIONS[name]
                            n = state.find_by_id(selected_node)
                            if n:
                                if connect_mode and connect_src_id:
                                    src = state.find_by_id(connect_src_id)
                                    if src and n.id == src.id and pk == connect_src_port:
                                        cancel_connect("Connection cancelled.")
                                        continue
                                    used = bool((n.ports[pk].get("target") or "").strip())
                                    if src and n.id == src.id:
                                        srcp = src.ports.get(connect_src_port, {})
                                        src_tgt = (srcp.get("target") or "").strip()
                                        same_kind = connect_src_port and (
                                            pk.startswith("top") == connect_src_port.startswith("top"))
                                        if pk != connect_src_port and not used and same_kind and src_tgt:
                                            src.ports[pk]["color"] = srcp.get("color", "cyan")
                                            src.ports[pk]["gate"] = srcp.get("gate", "open")
                                            src.ports[pk]["target"] = src_tgt
                                            srcp["target"] = ""
                                            set_focused_port(pk)
                                            cancel_connect(f"Port moved to {pk}")
                                    elif src and n.id != src.id and port_side_ok(connect_src_port, pk) and dest_floor_ok(src, connect_src_port, n):
                                        clear_port_link(src, connect_src_port, state)
                                        clear_port_link(n, pk, state)
                                        make_port_link(src, connect_src_port, n, pk, state)
                                        set_focused_port(pk)
                                        fill_form_from_node(n)
                                        set_focused_port(pk)
                                        cancel_connect(f"Linked {src.title} ↔ {n.title}")
                                else:
                                    port_color[pk] = n.ports[pk].get("color", "cyan")
                                    port_gate[pk] = n.ports[pk].get("gate", "none")
                                    if focused_port != pk:
                                        set_focused_port(pk)
                                    else:
                                        set_focused_port(pk)
                                        lo, hi = state.min_floor(), state.max_floor()
                                        if pk.startswith("und") and n.floor == lo:
                                            clear_port_link(n, pk, state)
                                            n.ports[pk]["target"] = EDGE_TARGET
                                            set_status(f"Edge line down from {n.title}")
                                        elif pk.startswith("top") and n.floor == hi:
                                            clear_port_link(n, pk, state)
                                            n.ports[pk]["target"] = EDGE_TARGET
                                            set_status(f"Edge line up from {n.title}")
                                        else:
                                            connect_mode = "pick_node"
                                            connect_src_id = n.id
                                            connect_src_port = pk
                                            connect_dest_id = None
                                            set_status("doing port connection")
                    if ev.key == pygame.K_DELETE and selected_node:
                        despawn_selected_node()
                    elif ev.key == pygame.K_DELETE and selected_sticker:
                        despawn_selected_sticker()
                    elif ev.key == pygame.K_ESCAPE:
                        selected_node = None
                        selected_sticker = None
                    elif ev.key in (pygame.K_EQUALS, pygame.K_PLUS, pygame.K_KP_PLUS):
                        zoom = clamp(zoom * 1.1, 0.2, 2.0)
                    elif ev.key in (pygame.K_MINUS, pygame.K_KP_MINUS):
                        zoom = clamp(zoom / 1.1, 0.2, 2.0)
                else:
                    if ev.key == pygame.K_DELETE and selected_node:
                        despawn_selected_node()
                    elif ev.key == pygame.K_DELETE and selected_sticker:
                        despawn_selected_sticker()
                    elif ev.key == pygame.K_ESCAPE:
                        selected_node = None
                        selected_sticker = None
                    elif ev.key in (pygame.K_EQUALS, pygame.K_PLUS, pygame.K_KP_PLUS):
                        zoom = clamp(zoom * 1.1, 0.2, 2.0)
                    elif ev.key in (pygame.K_MINUS, pygame.K_KP_MINUS):
                        zoom = clamp(zoom / 1.1, 0.2, 2.0)

        caret_blink += 1

        # ---- draw map (visible band only + cache) ----
        screen.fill((22, 22, 26))
        cr = canvas_rect(sw, sh)
        world_h = state.floor_count() * FLOOR_H
        vis_w = max(1, int(math.ceil(cr.w / zoom)) + 2)
        vis_h = max(1, int(math.ceil(cr.h / zoom)) + 2)
        left_c = int(max(0, min(MAP_W - 1, math.floor(cam_x))))
        top_c = int(max(0, min(world_h - 1, math.floor(cam_y))))
        right_c = int(min(MAP_W, max(left_c + 1, math.ceil(cam_x + vis_w))))
        bottom_c = int(min(world_h, max(top_c + 1, math.ceil(cam_y + vis_h))))
        view_box = (left_c, top_c, right_c, bottom_c)
        now = pygame.time.get_ticks()
        red_blink = (now // 4000) % 2 == 0
        view_sig = (
            hide_stickers, hide_paths, hide_mode, selected_node, selected_sticker, red_blink, round(zoom, 3), view_box,
            tuple((c, tuple((state.path_routes.get(c) or {}).get("ids") or []),
                   (state.path_routes.get(c) or {}).get("dir", 1)) for c in PATH_DOT_COLORS),
            tuple((n.id, n.floor, n.x, n.elevator, getattr(n, "roof", False), getattr(n, "elev_dx", 0), n.title, n.material, n.stars, getattr(n, "mat_right", False),
                   tuple((k, n.ports[k].get("target"), n.ports[k].get("color"), n.ports[k].get("gate"))
                         for k in PORT_KEYS))
                  for n in state.nodes),
            tuple((s.id, s.name, s.tile_x, s.tile_y, getattr(s, "big", False)) for s in state.stickers),
        )
        if view_cache["sig"] != view_sig:
            band = renderer.render(
                state,
                crop=False,
                selected_node=selected_node,
                selected_sticker=None,
                view_box=view_box,
                hide_stickers=hide_stickers,
                hide_paths=hide_paths,
                live=True,
                red_blink=red_blink,
            )
            surf = pil_to_surf(band.convert("RGBA"))
            tw = max(1, int(round(band.width * zoom)))
            th = max(1, int(round(band.height * zoom)))
            view_cache["surf"] = pygame.transform.scale(surf, (tw, th))
            view_cache["box"] = view_box
            view_cache["sig"] = view_sig
        cached = view_cache["surf"]
        if cached is not None:
            bx0, by0 = view_cache["box"][0], view_cache["box"][1]
            blit_x = cr.x + int(round((bx0 - cam_x) * zoom))
            blit_y = cr.y + int(round((by0 - cam_y) * zoom))
            screen.set_clip(cr)
            screen.blit(cached, (blit_x, blit_y))
            if selected_sticker and not hide_stickers:
                st = next((s for s in state.stickers if s.id == selected_sticker), None)
                if st is not None:
                    w, h = sticker_size(st.name, assets, getattr(st, "big", False))
                    sx = cr.x + int(round((st.tile_x - cam_x) * zoom))
                    sy = cr.y + int(round((st.tile_y - cam_y) * zoom))
                    pygame.draw.rect(screen, (255, 255, 255),
                                     Rect(sx, sy, int(round(w * zoom)), int(round(h * zoom))), 2)
            if show_floor_ruler:
                if floor_box_surf is None:
                    pbox = assets.get("floor_number_box")
                    if pbox is None:
                        pbox = Image.new("RGBA", FLOOR_BOX, (18, 18, 18, 230))
                    floor_box_surf = pil_to_surf(pbox.convert("RGBA"))
                fc = state.floor_count()
                bw, bh = floor_box_surf.get_width(), floor_box_surf.get_height()
                for fi in range(fc):
                    top = floor_top_y(fi, fc)
                    by = top + int(bh * 2)
                    sy = cr.y + int(round((by - cam_y) * zoom))
                    if sy + bh < cr.y or sy > cr.bottom:
                        continue
                    sx = cr.x + 4
                    screen.blit(floor_box_surf, (sx, sy))
                    lab = floor_label(state.min_floor() + fi)
                    ts = ui_font.render(lab, True, (255, 255, 255))
                    screen.blit(ts, (sx + (bw - ts.get_width()) // 2,
                                     sy + (bh - ts.get_height()) // 2 - 1))
            screen.set_clip(None)

        # floor scrollbar
        sr = scroll_rect(sw, sh)
        pygame.draw.rect(screen, (28, 28, 32), sr)
        pygame.draw.rect(screen, (70, 70, 78), sr, 1)
        world_h = state.floor_count() * FLOOR_H
        view_h = cr.h / max(0.05, zoom)
        max_cam = max(0.0, world_h - view_h)
        steps = max(1, int(math.ceil(max_cam / FLOOR_H))) if max_cam > 0 else 1
        thumb_h = max(22, int(sr.h / (steps + 1)))
        step = int(clamp(round(cam_y / FLOOR_H), 0, steps))
        ty = sr.y + int((sr.h - thumb_h) * (step / steps if steps else 0))
        pygame.draw.rect(screen, (130, 130, 140), Rect(sr.x + 2, ty, sr.w - 4, thumb_h), border_radius=3)

        q = fold_search(fields.get("search") or "") if search_open else ""
        if search_open and q:
            def _scr(wx, wy):
                return (cr.x + int(round((wx - cam_x) * zoom)),
                        cr.y + int(round((wy - cam_y) * zoom)))
            fc = state.floor_count()
            mf = state.min_floor()
            for n in state.nodes:
                hit_n = q in fold_search(n.title)
                hit_m = q in fold_search(n.material or "")
                if hit_n or hit_m:
                    ny = node_y_on_floor(n.floor, fc, mf)
                    sx, sy = _scr(n.x, ny)
                    rr = Rect(sx - 2, sy - 2, int(NODE_W * zoom) + 4, int(NODE_H * zoom) + 4)
                    pygame.draw.rect(screen, (240, 210, 40), rr, 2, border_radius=6)
            if not hide_stickers:
                for st in state.stickers:
                    if hide_paths and path_dot_color(st.name):
                        continue
                    if q not in fold_search(st.name):
                        continue
                    x, y = sticker_world(st)
                    w, h = sticker_size(st.name, assets, getattr(st, "big", False))
                    sx, sy = _scr(x, y)
                    rr = Rect(sx - 2, sy - 2, int(w * zoom) + 4, int(h * zoom) + 4)
                    pygame.draw.rect(screen, (240, 210, 40), rr, 2, border_radius=5)

        if search_open:
            sbox = Rect(cr.right - 228, cr.y + 6, 200, 22)
            field_box(screen, "search", sbox, mouse, click)
            xbtn = Rect(sbox.right + 4, sbox.y, 22, 22)
            pygame.draw.rect(screen, (70, 40, 40), xbtn, border_radius=3)
            pygame.draw.rect(screen, (200, 80, 80), xbtn, 1, border_radius=3)
            xt = ui_font_b.render("X", True, (240, 240, 240))
            screen.blit(xt, (xbtn.x + (xbtn.w - xt.get_width()) // 2,
                             xbtn.y + (xbtn.h - xt.get_height()) // 2))

        pygame.draw.rect(screen, (10, 10, 12), cr, 1)
        if connect_mode:
            msg = "doing port connection"
            ts = ui_font_b.render(msg, True, (80, 220, 110))
            msg_x = cr.right - ts.get_width() - 12
            msg_y = cr.bottom - ts.get_height() - 8
            cancel_r = Rect(msg_x + ts.get_width() - 88, msg_y - 30, 88, 24)
            if cancel_r.right > cr.right - 8:
                cancel_r.x = cr.right - 96
            pygame.draw.rect(screen, (180, 40, 40), cancel_r, border_radius=3)
            pygame.draw.rect(screen, (255, 255, 255), cancel_r, 2, border_radius=3)
            cl = ui_font_b.render("CANCEL", True, (255, 255, 255))
            screen.blit(cl, (cancel_r.x + (cancel_r.w - cl.get_width()) // 2,
                             cancel_r.y + (cancel_r.h - cl.get_height()) // 2))
            screen.blit(ts, (msg_x, msg_y))
            if click and cancel_r.collidepoint(mouse):
                cancel_connect()

        # ---- side panel ----
        panel = Rect(sw - 420, 0, 420, sh - 28)
        pygame.draw.rect(screen, (32, 32, 38), panel)
        bg_key = (panel.w, panel.h)
        if panel_bg_cache.get("key") != bg_key:
            panel_bg_cache["key"] = bg_key
            panel_bg_cache["surf"] = load_panel_background(panel.w, panel.h)
        if panel_bg_cache.get("surf") is not None:
            screen.blit(panel_bg_cache["surf"], panel.topleft)
        pygame.draw.line(screen, (80, 80, 90), (panel.x, 0), (panel.x, sh), 2)

        x0 = panel.x + 10
        y = 8

        # file row
        field_box(screen, "export_name", Rect(x0, y + 14, 136, 22), mouse, click, "Export name")
        if button(screen, "import", Rect(x0 + 144, y + 14, 64, 22), "Import", mouse, click):
            path = native_file_dialog("open", "Import map JSON",
                                     [("JSON", "*.json"), ("All files", "*.*")], SCRIPT_DIR)
            if path and os.path.isfile(path):
                with open(path, "r", encoding="utf-8") as f:
                    state.load_dict(json.load(f), assets)
                base = os.path.splitext(os.path.basename(path))[0]
                fields["export_name"] = base
                state.name = base
                last_saved_sig = saved_map_fingerprint()
                set_status(f"Imported {path}")
            elif path:
                set_status(f"No file {path}")
        if button(screen, "exportj", Rect(x0 + 212, y + 14, 88, 22), "Export JSON", mouse, click):
            do_export_json()
        if button(screen, "render", Rect(x0 + 304, y + 14, 56, 22), "Render", mouse, click):
            do_render_png()
        y += 44
        if button(screen, "center", Rect(x0, y, 54, 22), "Center", mouse, click):
            H = state.floor_count() * FLOOR_H
            cr2 = canvas_rect(sw, sh)
            cam_x = MAP_W / 2 - (cr2.w / zoom) / 2
            cam_y = H / 2 - (cr2.h / zoom) / 2
            set_status("Camera centered.")
        lock_stickers = checkbox(screen, Rect(x0 + 62, y + 3, 16, 16), lock_stickers,
                                 "Lock ☻", mouse, click)
        hide_box = Rect(x0 + 158, y + 3, 16, 16)
        hide_fill = (40, 40, 48) if hide_mode == 0 else ((70, 70, 40) if hide_mode == 1 else (60, 140, 60))
        pygame.draw.rect(screen, hide_fill, hide_box, border_radius=2)
        pygame.draw.rect(screen, (200, 200, 200), hide_box, 1, border_radius=2)
        if hide_mode == 1:
            pygame.draw.line(screen, (240, 240, 140), (hide_box.x + 3, hide_box.centery),
                             (hide_box.right - 3, hide_box.centery), 2)
        elif hide_mode >= 2:
            pygame.draw.line(screen, (240, 240, 240), (hide_box.x + 3, hide_box.y + 8),
                             (hide_box.x + 7, hide_box.y + 13), 2)
            pygame.draw.line(screen, (240, 240, 240), (hide_box.x + 7, hide_box.y + 13),
                             (hide_box.x + 14, hide_box.y + 3), 2)
        screen.blit(ui_font_sm.render("Hide ☻", True, (220, 220, 220)), (hide_box.right + 6, hide_box.y + 1))
        if click and hide_box.collidepoint(mouse):
            hide_mode = (hide_mode + 1) % 3
            hide_paths = hide_mode >= 1
            hide_stickers = hide_mode >= 2
            if hide_stickers:
                selected_sticker = None
                dragging_sticker = None
        show_floor_ruler = checkbox(screen, Rect(x0 + 230, y + 3, 16, 16), show_floor_ruler,
                                    "Floor", mouse, click)
        if button(screen, "basego", Rect(x0 + 292, y, 40, 22), "Base", mouse, click):
            raw = (fields["base"] or "").strip().upper()
            if raw in ("B1", "B-1", "B01"):
                new_base = 0
            else:
                try:
                    new_base = int(raw)
                except ValueError:
                    new_base = None
            if new_base is None or new_base < 0:
                set_status("REFUSED: base must be 0 / B1 or a positive floor number")
            elif not state.nodes:
                set_status("No nodes to rebase.")
            else:
                old_min = state.min_floor()
                delta = new_base - old_min
                if delta != 0:
                    for n in state.nodes:
                        n.floor += delta
                    prune_edge_ports(state)
                    if selected_node:
                        sn = state.find_by_id(selected_node)
                        if sn:
                            fields["floor"] = str(sn.floor)
                set_status(f"Base is now {floor_label(state.min_floor())}")
        field_box(screen, "base", Rect(x0 + 336, y, 40, 22), mouse, click)
        y += 34
        pygame.draw.line(screen, (70, 70, 80), (x0, y), (panel.right - 10, y))
        y += 8
        draw_text(screen, "NODE", (x0, y), ui_font_b, (180, 200, 255))
        y += 20
        field_box(screen, "title", Rect(x0, y + 14, 280, 22), mouse, click, "Title")
        field_box(screen, "floor", Rect(x0 + 290, y + 14, 110, 22), mouse, click, "Floor # (0=B1)")
        y += 44

        draw_text(screen, "Ports", (x0, y), ui_font_sm, (160, 160, 160))
        draw_text(screen, "color / gate", (x0 + 210, y), ui_font_sm, (160, 160, 160))
        y += 16
        viz = Rect(x0, y, 196, 118)
        pygame.draw.rect(screen, (28, 28, 34), viz, border_radius=4)
        pygame.draw.rect(screen, (90, 90, 100), viz, 1, border_radius=4)
        # wire frame
        pygame.draw.line(screen, (160, 160, 170), (viz.x + 22, viz.y + 22), (viz.x + 22, viz.y + 96), 1)
        pygame.draw.line(screen, (160, 160, 170), (viz.x + 22, viz.y + 96), (viz.x + 174, viz.y + 96), 1)
        pygame.draw.line(screen, (160, 160, 170), (viz.x + 174, viz.y + 96), (viz.x + 174, viz.y + 22), 1)
        pygame.draw.line(screen, (160, 160, 170), (viz.x + 174, viz.y + 22), (viz.x + 22, viz.y + 22), 1)
        port_ui = {
            "top_left": (viz.x + 10, viz.y + 8),
            "top_mid": (viz.x + 86, viz.y + 8),
            "top_right": (viz.x + 162, viz.y + 8),
            "und_left": (viz.x + 10, viz.y + 90),
            "und_mid": (viz.x + 86, viz.y + 90),
            "und_right": (viz.x + 162, viz.y + 90),
        }
        cur_node = state.find_by_id(selected_node) if selected_node else None
        src_conn = state.find_by_id(connect_src_id) if connect_mode and connect_src_id else None
        for pk, (px, py) in port_ui.items():
            pr = Rect(px, py, 22, 22)
            used = bool(cur_node and (cur_node.ports[pk].get("target") or "").strip())
            eligible = True
            if connect_mode and src_conn and connect_src_port and cur_node:
                empty = not used
                same = cur_node.id == src_conn.id
                if same:
                    src_tgt = str((src_conn.ports.get(connect_src_port) or {}).get("target") or "").strip()
                    src_has = bool(src_tgt)
                    same_kind = pk.startswith("top") == connect_src_port.startswith("top")
                    eligible = bool(src_has) and pk != connect_src_port and empty and same_kind
                else:
                    eligible = port_side_ok(connect_src_port, pk) and dest_floor_ok(src_conn, connect_src_port, cur_node)
            if focused_port == pk and used:
                fill = (50, 190, 70) if ((pygame.time.get_ticks() - port_focus_at) // 1000) % 2 == 0 else (130, 130, 135)
            elif focused_port == pk:
                fill = (50, 190, 70)
            elif connect_mode and not eligible:
                fill = (28, 28, 32)
            elif used:
                fill = (130, 130, 135)
            else:
                fill = (18, 18, 22)
            pygame.draw.rect(screen, fill, pr, border_radius=2)
            pygame.draw.rect(screen, (70, 70, 75) if (connect_mode and not eligible) else (200, 200, 200), pr, 1, border_radius=2)
            if click and pr.collidepoint(mouse):
                if connect_mode and cur_node and connect_src_id == cur_node.id and pk == connect_src_port:
                    cancel_connect("Connection cancelled.")
                elif connect_mode and cur_node and not eligible:
                    pass
                elif connect_mode and cur_node:
                    src = state.find_by_id(connect_src_id) if connect_src_id else None
                    empty = not (cur_node.ports[pk].get("target") or "").strip()
                    same_kind = connect_src_port and (
                        pk.startswith("top") == connect_src_port.startswith("top"))
                    srcp = src.ports.get(connect_src_port, {}) if src else {}
                    src_tgt = (srcp.get("target") or "").strip()
                    if (src and cur_node.id == src.id and pk != connect_src_port
                            and empty and same_kind and src_tgt):
                        src.ports[pk]["color"] = srcp.get("color", "cyan")
                        src.ports[pk]["gate"] = srcp.get("gate", "open")
                        src.ports[pk]["target"] = src_tgt
                        srcp["target"] = ""
                        set_focused_port(pk)
                        port_color[pk] = src.ports[pk].get("color", "cyan")
                        port_gate[pk] = src.ports[pk].get("gate", "open")
                        fill_form_from_node(src)
                        set_focused_port(pk)
                        cancel_connect(f"Port moved to {pk}")
                    elif src and cur_node.id != src.id and port_side_ok(connect_src_port, pk) and dest_floor_ok(src, connect_src_port, cur_node):
                        clear_port_link(src, connect_src_port, state)
                        clear_port_link(cur_node, pk, state)
                        make_port_link(src, connect_src_port, cur_node, pk, state)
                        set_focused_port(pk)
                        fill_form_from_node(cur_node)
                        cancel_connect(f"Linked {src.title} ↔ {cur_node.title}")
                else:
                    set_focused_port(pk)
                    if cur_node:
                        port_color[pk] = cur_node.ports[pk].get("color", "cyan")
                        port_gate[pk] = cur_node.ports[pk].get("gate", "none")
        # connected-to + color/gate/start only while a port square is focused
        cx0 = x0 + 206
        cy0 = y
        start_r = None
        if focused_port:
            draw_text(screen, "connected to:", (viz.x + 48, viz.y + 40), ui_font_sm, (180, 180, 180))
            link_name = ""
            if cur_node:
                link_name = (cur_node.ports[focused_port].get("target") or "").strip()
            pygame.draw.rect(screen, (12, 12, 14), Rect(viz.x + 36, viz.y + 56, 124, 20))
            pygame.draw.rect(screen, (70, 70, 80), Rect(viz.x + 36, viz.y + 56, 124, 20), 1)
            if link_name == EDGE_TARGET:
                link_name = "edge"
            if link_name:
                draw_text(screen, link_name[:16], (viz.x + 40, viz.y + 58), ui_font_sm, (230, 230, 230))

            for i, ck in enumerate(COLOR_ORDER):
                swatch = Rect(cx0 + i * 28, cy0, 24, 24)
                pygame.draw.rect(screen, CONN_COLORS[ck], swatch, border_radius=3)
                if port_color.get(focused_port) == ck:
                    pygame.draw.rect(screen, (255, 255, 255), swatch, 2, border_radius=3)
                if click and swatch.collidepoint(mouse):
                    port_color[focused_port] = ck
                    if cur_node:
                        sync_link_color(cur_node, focused_port, ck, state)
            gy = cy0 + 32
            gcur = port_gate[focused_port]
            if gcur in ("open-gate", "none", ""):
                gcur = "open"
            draw_gate_lock(screen, cx0, gy + 2, gcur)
            glabel = GATE_LABELS.get(gcur, gcur)
            if button(screen, "gatef", Rect(cx0 + 22, gy, 88, 24), glabel, mouse, click):
                try:
                    gi = GATES.index(gcur)
                except ValueError:
                    gi = 0
                port_gate[focused_port] = GATES[(gi + 1) % len(GATES)]
                if cur_node:
                    cur_node.ports[focused_port]["gate"] = port_gate[focused_port]
            draw_text(screen, port_color.get(focused_port, "cyan"),
                      (cx0 + 114, gy + 4), ui_font, CONN_COLORS[port_color.get(focused_port, "cyan")])
            start_r = Rect(cx0, gy + 32, 88, 26)
            start_on = connect_mode is not None
            pygame.draw.rect(screen, (90, 40, 40) if start_on else (48, 48, 54), start_r, border_radius=4)
            pygame.draw.rect(screen, (220, 80, 80) if start_on else (140, 140, 145), start_r, 2, border_radius=4)
            sl = ui_font.render("Cancel" if start_on else "Start", True, (240, 240, 240))
            screen.blit(sl, (start_r.x + (start_r.w - sl.get_width()) // 2,
                             start_r.y + (start_r.h - sl.get_height()) // 2))
            if click and start_r.collidepoint(mouse) and cur_node:
                if connect_mode:
                    cancel_connect("Connection cancelled.")
                else:
                    lo, hi = state.min_floor(), state.max_floor()
                    fp = focused_port or ""
                    if fp.startswith("und") and cur_node.floor == lo:
                        clear_port_link(cur_node, fp, state)
                        cur_node.ports[fp]["target"] = EDGE_TARGET
                        cancel_connect(f"Edge line down from {cur_node.title}")
                    elif fp.startswith("top") and cur_node.floor == hi:
                        clear_port_link(cur_node, fp, state)
                        cur_node.ports[fp]["target"] = EDGE_TARGET
                        cancel_connect(f"Edge line up from {cur_node.title}")
                    else:
                        connect_mode = "pick_node"
                        connect_src_id = cur_node.id
                        connect_src_port = focused_port
                        connect_dest_id = None
                        set_status("doing port connection")
            if button(screen, "rmport", Rect(cx0 + 96, gy + 32, 88, 26), "Remove", mouse, click):
                if cur_node:
                    clear_port_link(cur_node, focused_port, state)
                    set_status("Connection removed.")
        y += 126

        draw_text(screen, "Elevator:", (x0, y), ui_font_sm, (160, 160, 160))
        y += 16
        elev_sel, exx, _ = radio_row(screen, x0, y, ELEVATOR_KINDS, elev_sel, mouse, click, "el")
        roof_sel = checkbox(screen, Rect(exx + 6, y + 1, 16, 16), roof_sel, "Roof", mouse, click)
        if selected_node:
            rn = state.find_by_id(selected_node)
            if rn is not None and bool(getattr(rn, "roof", False)) != bool(roof_sel):
                if roof_sel:
                    rn.roof = True
                else:
                    upper = None
                    if rn.elevator not in ("", "none"):
                        uppers = [o for o in state.elevator_group(rn.elevator)
                                  if o.id != rn.id and o.floor > rn.floor]
                        if uppers:
                            upper = min(uppers, key=lambda o: o.floor)
                    if upper is None:
                        rn.roof = False
                    else:
                        members = list(state.elevator_segment(rn))
                        skip = {m.id for m in members}
                        ok = True
                        for m in members:
                            ivals = []
                            for o in state.nodes_on_floor(m.floor):
                                if o.id in skip:
                                    continue
                                ivals.append((o.x, o.x + NODE_W))
                            if not slot_fits(upper.x, merge_intervals(ivals)):
                                ok = False
                                break
                        if ok:
                            rn.roof = False
                            apply_elevator_x(state, rn.elevator, upper.x, assets, anchor=rn)
                        else:
                            roof_sel = True
                            set_status("REFUSED: no space to join elevator rig above")
        y += 24

        draw_text(screen, "Material:", (x0, y), ui_font_sm, (160, 160, 160))
        y += 16
        # wrap materials
        xx, yy = x0, y
        for m in MATERIALS:
            label = MATERIAL_LABELS.get(m, m)
            r = Rect(xx, yy, 8 + ui_font_sm.size(label)[0] + 14, 18)
            on = mat_sel == m
            pygame.draw.rect(screen, (70, 70, 40) if on else (40, 40, 48), r, border_radius=3)
            pygame.draw.rect(screen, (220, 200, 120) if on else (80, 80, 90), r, 1, border_radius=3)
            screen.blit(ui_font_sm.render(label, True, (230, 230, 230)), (r.x + 6, r.y + 2))
            if click and r.collidepoint(mouse):
                mat_sel = m
            xx = r.right + 4
            if m == "Fabric" or xx > panel.right - 80:
                xx = x0
                yy += 20
        y = yy + 24
        field_box(screen, "stars", Rect(x0, y + 14, 80, 22), mouse, click, "Stars")
        mat_right_sel = checkbox(screen, Rect(x0 + 100, y + 16, 16, 16), mat_right_sel, "Right", mouse, click)
        if selected_node:
            rn = state.find_by_id(selected_node)
            if rn is not None:
                rn.mat_right = bool(mat_right_sel)
        y += 44

        floor_valid = (fields["floor"] or "").strip().lstrip("-").isdigit() and int(fields["floor"]) >= 0
        add_rect = Rect(x0, y, 130, 26)
        if floor_valid:
            add_clicked = button(screen, "addn", add_rect, "Add node", mouse, click)
        else:
            pygame.draw.rect(screen, (40, 40, 44), add_rect, border_radius=3)
            pygame.draw.rect(screen, (80, 80, 80), add_rect, 1, border_radius=3)
            ts = ui_font.render("Add node", True, (110, 110, 110))
            screen.blit(ts, (add_rect.x + (add_rect.w - ts.get_width()) // 2,
                             add_rect.y + (add_rect.h - ts.get_height()) // 2))
            add_clicked = False
        if add_clicked:
            fl = int(fields["floor"])
            title = fields["title"].strip() or "NEW"
            existing = state.find_by_title(title)
            if existing:
                set_status("REFUSED: that node name already exists")
            elif elevator_on_floor(state, elev_sel, fl):
                set_status(f"REFUSED: {elev_sel} elevator already on {floor_label(fl)}")
            else:
                sx = spawn_x_for_floor(state, fl, elev_sel)
                if sx is None:
                    set_status("REFUSED: floor full")
                else:
                    n = Node(
                        id=state.next_id(),
                        title=title,
                        floor=fl,
                        x=sx,
                    )
                    if read_form_into(n):
                        old_fc = state.floor_count()
                        state.nodes.append(n)
                        adjust_stickers_after_floor_change(state, assets, old_fc)
                        selected_node = n.id
                        if n.elevator != "none":
                            apply_elevator_x(state, n.elevator, n.x, assets, anchor=n)
                        prune_edge_ports(state)
                        set_status(f"Added {n.title} on {floor_label(n.floor)}")
        if button(screen, "updn", Rect(x0 + 140, y, 130, 26), "Update node", mouse, click):
            n = state.find_by_id(selected_node) if selected_node else None
            if not n:
                set_status("No node selected.")
            else:
                if read_form_into(n):
                    if n.elevator != "none":
                        apply_elevator_x(state, n.elevator, n.x, assets, anchor=n)
                    set_status(f"Updated {n.title}")
        if button(screen, "deln", Rect(x0 + 280, y, 120, 26), "Delete node", mouse, click):
            despawn_selected_node()
        y += 36

        pygame.draw.line(screen, (70, 70, 80), (x0, y), (panel.right - 10, y))
        y += 8
        sticker_sec_y = y
        stickers_frozen = hide_stickers or lock_stickers
        sclick = click and not stickers_frozen
        st_col = (180, 200, 255) if not stickers_frozen else (90, 90, 100)
        draw_text(screen, "STICKERS", (x0, y), ui_font_b, st_col)
        _sn = assets.sticker_names
        if _sn:
            pick = _sn[catalog_sel % len(_sn)]
            tw = ui_font_b.size("STICKERS")[0]
            draw_text(screen, " - " + pick, (x0 + tw, y + 2), ui_font_sm, st_col)
        y += 18
        field_box(screen, "sticker_x", Rect(x0, y + 14, 70, 22), mouse, sclick, "X")
        field_box(screen, "sticker_y", Rect(x0 + 80, y + 14, 70, 22), mouse, sclick, "Y")
        sel_st = next((s for s in state.stickers if s.id == selected_sticker), None)
        big_r = Rect(x0 + 234, y + 14, 70, 22)
        if sel_st:
            if button(screen, "bigst", big_r, "Big" if not sel_st.big else "Norm", mouse, sclick):
                sel_st.big = not sel_st.big
                sel_st.tile_x, sel_st.tile_y = clamp_sticker_xy(
                    sel_st.tile_x, sel_st.tile_y, state, assets, sel_st.name, sel_st.big)
                set_status("Sticker enlarged." if sel_st.big else "Sticker normal size.")
        else:
            pygame.draw.rect(screen, (40, 40, 44), big_r, border_radius=3)
            pygame.draw.rect(screen, (80, 80, 80), big_r, 1, border_radius=3)
            ts = ui_font.render("Big", True, (110, 110, 110))
            screen.blit(ts, (big_r.x + (big_r.w - ts.get_width()) // 2,
                             big_r.y + (big_r.h - ts.get_height()) // 2))
        if button(screen, "addst", Rect(x0 + 160, y + 14, 70, 22), "Add", mouse, sclick):
            add_sticker_from_ui()
        if button(screen, "despawn", Rect(x0 + 310, y + 14, 96, 22), "Despawn", mouse, sclick):
            despawn_selected_sticker()
        y += 44

        # catalog
        cat_h = max(80, panel.bottom - y - 8)
        cat_rect = Rect(x0, y, 400, cat_h)
        pygame.draw.rect(screen, (24, 24, 28), cat_rect)
        pygame.draw.rect(screen, (80, 80, 90), cat_rect, 1)
        names = assets.sticker_names
        cell = 72
        cols = 5
        header_h = 18
        raw_ent = getattr(assets, "catalog_entries", None) or [("item", n, 0) for n in names]
        vis_ent = []
        hide_below = None
        for ent in raw_ent:
            kind = ent[0]
            depth = ent[2] if len(ent) > 2 else 1
            if kind == "cat":
                if hide_below is not None and depth > hide_below:
                    continue
                hide_below = None
                vis_ent.append(ent)
                key = (ent[3] if len(ent) > 3 else ent[1], depth)
                if key in collapsed_cats:
                    hide_below = depth
            else:
                if hide_below is not None:
                    continue
                vis_ent.append(ent)
        rows = catalog_rows(vis_ent, cols)
        if rows:
            catalog_scroll = clamp(catalog_scroll, 0, max(0, len(rows) - 1))
            ycur = cat_rect.y + 4
            for ri in range(catalog_scroll, len(rows)):
                kind, payload = rows[ri]
                if kind == "cat":
                    if ycur + header_h > cat_rect.bottom:
                        break
                    if isinstance(payload, tuple) and len(payload) >= 3:
                        cname, cdepth, rel = payload[0], payload[1], payload[2]
                    elif isinstance(payload, tuple):
                        cname, cdepth, rel = payload[0], payload[1], payload[0]
                    else:
                        cname, cdepth, rel = payload, 1, str(payload)
                    rel = str(rel).replace("\\", "/")
                    ckey = (rel or cname, cdepth)
                    on = ckey in collapsed_cats
                    cb = Rect(cat_rect.x + 6, ycur + 2, 12, 12)
                    pygame.draw.rect(screen, (70, 70, 40) if on else (36, 36, 42), cb, border_radius=2)
                    pygame.draw.rect(screen, (200, 200, 120) if on else (90, 90, 100), cb, 1, border_radius=2)
                    if on:
                        pygame.draw.line(screen, (220, 220, 140), (cb.x + 3, cb.centery), (cb.right - 3, cb.centery), 2)
                    if sclick and cb.collidepoint(mouse):
                        if on:
                            collapsed_cats.discard(ckey)
                        else:
                            collapsed_cats.add(ckey)
                    draw_text(screen, str(cname), (cat_rect.x + 22, ycur), ui_font_sm, (150, 150, 158))
                    starred = getattr(assets, "starred_folders", set())
                    lit = rel.lower() in {str(s).replace("\\", "/").lower() for s in starred}
                    star_sz = 14
                    star_r = Rect(cat_rect.right - 30, ycur + 1, star_sz, star_sz)
                    cache = catalog_bar.setdefault("star_surfs", {})
                    if "on" not in cache or "off" not in cache:
                        for key, fname in (("on", "Catalog_star_yellow"), ("off", "Catalog_star_gray")):
                            simg = assets.get(fname)
                            if simg is not None:
                                tiny = simg if simg.size == (star_sz, star_sz) else simg.resize(
                                    (star_sz, star_sz), Image.Resampling.LANCZOS)
                                cache[key] = pil_to_surf(tiny)
                    surf = cache.get("on" if lit else "off")
                    if surf is not None:
                        screen.blit(surf, star_r.topleft)
                    else:
                        pygame.draw.rect(screen, (230, 200, 50) if lit else (70, 70, 76), star_r)
                    if click and star_r.collidepoint(mouse):
                        cur = set(getattr(assets, "starred_folders", set()))
                        key = rel.lower()
                        if key in {str(s).lower() for s in cur}:
                            cur = {s for s in cur if str(s).replace("\\", "/").lower() != key}
                        else:
                            cur.add(rel)
                        assets.starred_folders = cur
                        assets.reload_images()
                    pygame.draw.line(screen, (70, 70, 78),
                                     (cat_rect.x + 8, ycur + header_h - 3),
                                     (cat_rect.right - 32, ycur + header_h - 3), 1)
                    ycur += header_h
                    continue
                if ycur + 64 > cat_rect.bottom:
                    break
                for col, name in enumerate(payload):
                    rx = cat_rect.x + 6 + col * cell
                    ry = ycur
                    r = Rect(rx, ry, 64, 64)
                    idx = names.index(name) if name in names else 0
                    on = idx == catalog_sel
                    pygame.draw.rect(screen, (50, 50, 58), r)
                    th = assets.thumbs.get(name)
                    if th is not None:
                        if name not in pg_thumbs:
                            pg_thumbs[name] = pil_to_surf(th.convert("RGBA"))
                        screen.blit(pg_thumbs[name], r)
                    else:
                        draw_text(screen, name[:6], (rx + 4, ry + 24), ui_font_sm)
                    pygame.draw.rect(screen, (255, 255, 255) if on else (90, 90, 100), r, 3 if on else 1)
                    if sclick and r.collidepoint(mouse):
                        catalog_sel = idx
                    color = path_dot_color(name)
                    if color and r.collidepoint(mouse) and catalog_rmb is not None:
                        catalog_rmb["name"] = name
                        held = pygame.time.get_ticks() - catalog_rmb["t"]
                        if held >= 2000 and not catalog_rmb.get("cleared"):
                            selected_sticker, ok = clear_path_color(state, color, selected_sticker)
                            catalog_rmb["cleared"] = True
                            set_status(f"Cleared {color} path" if ok else f"No {color} path dots")
                        elif held >= 400:
                            pygame.draw.rect(screen, (180, 50, 50), r, 3)
                ycur += cell
            vis = max(1, (cat_rect.h - 8) // cell)
            max_s = max(0, len(rows) - vis)
            catalog_scroll = clamp(catalog_scroll, 0, max_s)
            bar = Rect(cat_rect.right - 10, cat_rect.y + 2, 8, cat_rect.h - 4)
            catalog_bar["rect"] = bar
            catalog_bar["max"] = max_s
            pygame.draw.rect(screen, (48, 48, 54), bar, border_radius=3)
            if max_s > 0:
                th = max(18, int(bar.h * vis / max(1, len(rows))))
                ty = bar.y + int((bar.h - th) * catalog_scroll / max_s)
                thumb = Rect(bar.x, ty, bar.w, th)
                pygame.draw.rect(screen, (140, 140, 150), thumb, border_radius=3)
                if sclick and bar.collidepoint(mouse):
                    catalog_dragging = True
                    t = (mouse[1] - bar.y) / max(1, bar.h)
                    catalog_scroll = int(clamp(t * (max_s + 1), 0, max_s))

        if stickers_frozen:
            ov = pygame.Surface((panel.w, max(1, panel.bottom - sticker_sec_y)), pygame.SRCALPHA)
            ov.fill((16, 16, 20, 160))
            screen.blit(ov, (panel.x, sticker_sec_y))

        if status_at and pygame.time.get_ticks() - status_at > 10000:
            status = "Ready."
            status_color = (200, 200, 160)
            status_at = 0
        # status bar
        pygame.draw.rect(screen, (16, 16, 18), Rect(0, sh - 28, sw, 28))
        draw_text(screen, status, (8, sh - 22), ui_font_sm, status_color)
        now_ui = pygame.time.get_ticks()
        thumb_r = Rect(sw - 150, sh - 24, 88, 20)
        keys_r = Rect(sw - 58, sh - 24, 50, 20)
        on_cd = now_ui < thumb_cd_until
        if on_cd:
            pygame.draw.rect(screen, (40, 40, 44), thumb_r, border_radius=3)
            pygame.draw.rect(screen, (80, 80, 80), thumb_r, 1, border_radius=3)
            ts = ui_font_sm.render("Thumbnail", True, (110, 110, 110))
            screen.blit(ts, (thumb_r.x + (thumb_r.w - ts.get_width()) // 2,
                             thumb_r.y + (thumb_r.h - ts.get_height()) // 2))
        elif button(screen, "thumbs", thumb_r, "Thumbnail", mouse, click):
            ensure_user_asset_folders()
            assets.reload_images()
            assets.sync_thumbnails(force=True)
            pg_thumbs.clear()
            catalog_bar.pop("star_surfs", None)
            thumb_cd_until = pygame.time.get_ticks() + 5000
            set_status("Catalog thumbnails updated.")
        if button(screen, "keys", keys_r, "Keys", mouse, click):
            helper = os.path.join(bundle_dir(), "shortcuts_editor.py")
            if not os.path.isfile(helper):
                helper = os.path.join(SCRIPT_DIR, "shortcuts_editor.py")
            try:
                if getattr(sys, "frozen", False):
                    proc = subprocess.Popen([sys.executable, "--shortcuts"], cwd=SCRIPT_DIR)
                elif os.path.isfile(helper):
                    proc = subprocess.Popen([sys.executable, helper], cwd=SCRIPT_DIR)
                else:
                    set_status("REFUSED: shortcuts_editor.py not found")
                    proc = None
                if proc is not None:
                    while proc.poll() is None:
                        pygame.event.clear()
                        pygame.event.pump()
                        clock.tick(30)
                    shortcuts = load_shortcuts()
                    set_status("Shortcuts reloaded.")
            except Exception as e:
                set_status(f"Shortcuts editor failed: {e}")

        if click and active_field:
            fr = buttons.get(f"field_{active_field}")
            on_it = bool(fr and hasattr(fr, "collidepoint") and fr.collidepoint(mouse))
            if not on_it:
                commit_field(active_field)
                active_field = None
                selecting_field = None

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()


def render_headless(out_png: str, out_json: str = ""):
    ensure_user_asset_folders()
    assets = AssetStore()
    assets.load_json(DEFAULT_JSON)
    renderer = MapRenderer(assets)
    state = MapState()
    boot = placeholder_json_path()
    if boot:
        try:
            with open(boot, "r", encoding="utf-8") as f:
                state.load_dict(json.load(f), assets)
        except Exception:
            state.seed_default()
    else:
        state.seed_default()
    renderer.export_png(state, out_png)
    print("wrote", out_png)


def main():
    if "--shortcuts" in sys.argv:
        import shortcuts_editor
        raise SystemExit(shortcuts_editor.run())
    ensure_user_asset_folders()
    if "--render-test" in sys.argv:
        os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
        out = os.path.join(SCRIPT_DIR, "Placeholder.png")
        js = os.path.join(SCRIPT_DIR, "Placeholder.json")
        render_headless(out, js)
        return
    try:
        run_editor()
    except Exception as e:
        import traceback
        print("Editor failed to open a window:", e)
        traceback.print_exc()
        print("Generating default map instead.")
        render_headless(os.path.join(SCRIPT_DIR, "Placeholder.png"),
                        os.path.join(SCRIPT_DIR, "Placeholder.json"))


if __name__ == "__main__":
    main()