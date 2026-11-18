#!/usr/bin/env python3
"""Render the Charybdis mini36 keymap (config/charybdis.keymap) as an HTML diagram.

Parses the ZMK keymap directly so the diagram cannot drift from what is compiled.
Layer keys show layer names instead of MO numbers; mouse/media/special keys use an
icon with a caption below. Trackball snipe/scroll facts are read from the shield
conf/overlay so the layer notes stay accurate.
"""
import json
import re
import sys
import html
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = Path(sys.argv[1] if len(sys.argv) > 1
           else ROOT / "config" / "charybdis.keymap")
OUT_HTML = Path(sys.argv[2] if len(sys.argv) > 2
                else ROOT / "docs" / "keymap-layers.html")
OUT_JSON = Path(sys.argv[3] if len(sys.argv) > 3
                else ROOT / "docs" / "keymap-layers.json")

KEYNAME = {
    "N0": "0", "N1": "1", "N2": "2", "N3": "3", "N4": "4",
    "N5": "5", "N6": "6", "N7": "7", "N8": "8", "N9": "9",
    "A": "A", "B": "B", "C": "C", "D": "D", "E": "E", "F": "F", "G": "G", "H": "H",
    "I": "I", "J": "J", "K": "K", "L": "L", "M": "M", "N": "N", "O": "O", "P": "P",
    "Q": "Q", "R": "R", "S": "S", "T": "T", "U": "U", "V": "V", "W": "W", "X": "X",
    "Y": "Y", "Z": "Z", "0": "0", "1": "1", "2": "2", "3": "3", "4": "4",
    "GRAVE": "`", "TILDE": "~", "MINUS": "-", "UNDER": "_", "EQUAL": "=", "PLUS": "+",
    "LBRC": "{", "RBRC": "}", "LBKT": "[", "RBKT": "]", "LPAR": "(", "RPAR": ")",
    "BSLH": "\\", "PIPE": "|", "SEMI": ";", "COLN": ":", "APOS": "'", "QUOT": "'",
    "COMMA": ",", "DOT": ".", "FSLH": "/", "QESL": "?", "EXCL": "!", "PRNT": "'",
    "STAR": "*", "HASH": "#", "DLLR": "$", "AMPS": "&", "PRCNT": "%", "CARET": "^",
    "AT": "@", "ATSN": "@",
    "BSL2": "|", "DEL": "Del", "BSpc": "Bksp", "BSPC": "Bksp", "RET": "Enter",
    "ENT": "Enter", "SPC": "Space", "TAB": "Tab", "ESC": "Esc", "CAPS": "Caps",
    "PSCRN": "PrtSc", "SLCK": "ScrLk", "PAUSE": "Pause", "UP": "\u2191", "DOWN": "\u2193",
    "LEFT": "\u2190", "RIGHT": "\u2192", "HOME": "Home", "END": "End",
    "PGUP": "PgUp", "PG_UP": "PgUp", "PG_DN": "PgDn", "PGDN": "PgDn",
    "F1": "F1", "F2": "F2", "F3": "F3", "F4": "F4", "F5": "F5", "F6": "F6",
    "F7": "F7", "F8": "F8", "F9": "F9", "F10": "F10", "F11": "F11", "F12": "F12",
    "LCTRL": "L-Ctrl", "RCTRL": "R-Ctrl", "LALT": "L-Alt", "RALT": "R-Alt",
    "LGUI": "L-GUI", "RGUI": "R-GUI", "LSHFT": "L-Sh", "RSFT": "R-Sh", "RSHFT": "R-Sh",
    "INS": "Ins", "LSPC": "Space",
    "C_MUTE": "Mute", "C_PP": "Play/Pause", "C_VOL_UP": "Vol +", "C_VOL_DN": "Vol \u2212",
    "C_NEXT": "Track \u23e9", "C_PREV": "Track \u23ea", "C_FF": "Fast \u23e9", "C_RW": "Rew \u23ea",
    "SCRL_UP": "Scroll \u2191", "SCRL_DOWN": "Scroll \u2193",
    "SCRL_LEFT": "Scroll \u2190", "SCRL_RIGHT": "Scroll \u2192",
}

SHIFTED = {
    "N1": "!", "N2": "@", "N3": "#", "N4": "$", "N5": "%",
    "N6": "^", "N7": "&", "N8": "*", "N9": "(", "N0": ")",
    "GRAVE": "~", "MINUS": "_", "EQUAL": "+", "SEMI": ":", "APOS": '"',
    "COMMA": "<", "DOT": ">", "FSLH": "?", "TILDE": "~",
}

MOD_PREFIX = {"LC": "Ctrl", "LS": "Shift", "LA": "Alt", "LG": "GUI"}
HOLD_MOD = {"LCTRL": "CTRL", "RCTRL": "CTRL", "LALT": "ALT", "RALT": "ALT",
            "LGUI": "GUI", "RGUI": "GUI", "LSHFT": "SHIFT", "RSHFT": "SHIFT",
            "RSFT": "SHIFT"}
MOUSE = {"LCLK": "Left", "RCLK": "Right", "MCLK": "Middle",
         "MB4": "Back", "MB5": "Forward", "SCRL_UP": "Scroll up",
         "SCRL_DOWN": "Scroll down"}
HOLDTAP = {"hml", "hmr", "lang_tab", "ctp", "cpps", "del_cad", "nav_hp"}
MORPH = {"p_slash", "eq_tilde"}

LAYER_SHORT = ["Base", "Nav/Sym", "FN/BT", "AutoMouse", "SlowMouse", "Scroll"]
MOUSE_VIS = {
    "LCLK": ("\u25a0\u00a6\u25a1\u00a6\u25a1", "Left Click"),
    "RCLK": ("\u25a1\u00a6\u25a1\u00a6\u25a0", "Right Click"),
    "MCLK": ("\u25a1\u00a6\u25a0\u00a6\u25a1", "Mid Click"),
    "MB4": ("\u21a9", "Back"),
    "MB5": ("\u21aa", "Forward"),
}
MEDIA_VIS = {
    "C_MUTE": ("\U0001f507", "Mute"),
    "C_PP": ("\u23ef", "Play/Pause"),
    "C_VOL_DN": ("\U0001f509", "Vol \u2212"),
    "C_VOL_UP": ("\U0001f50a", "Vol +"),
    "C_PREV": ("\u23ee", "Prev"),
    "C_RW": ("\u23ea", "Rewind"),
    "C_FF": ("\u23e9", "Fast Fwd"),
    "C_NEXT": ("\u23ed", "Next"),
}
ARROW_CAPTION = {"\u2190": "Left", "\u2192": "Right", "\u2191": "Up", "\u2193": "Down"}
MOUSE_SHORTCUTS = {
    "F2": (None, "F2", "Rename", None),
    "F5": (None, "F5", "Refresh", None),
    "LC(W)": ("\u2715", "", "Close Tab", "C+W"),
    "LC(LS(T))": ("\u21ba", "", "Reopen Tab", "C+S+T"),
    "LC(T)": ("\uff0b", "", "New Tab", "C+T"),
    "LC(LS(TAB))": ("\u21e4", "", "Prev Tab", "C+S+Tab"),
    "LC(TAB)": ("\u21e5", "", "Next Tab", "C+Tab"),
    "LC(LS(V))": ("\U0001f4cb", "", "Paste Plain", "C+S+V"),
    "LSHFT": ("\u21e7", "", "Shift", None),
}


def keyname(tok):
    tok = tok.strip()
    m = re.fullmatch(r"([A-Z]{2})\((.+)\)", tok)
    if m and m.group(1) in MOD_PREFIX:
        return "%s+%s" % (MOD_PREFIX[m.group(1)], keyname(m.group(2)))
    return KEYNAME.get(tok, tok)


def tokenize(rest):
    """Split a binding's argument text, keeping balanced-paren groups like LC(LS(T))."""
    toks, i, n = [], 0, len(rest)
    while i < n:
        while i < n and rest[i].isspace():
            i += 1
        if i >= n:
            break
        j = i
        while j < n and (rest[j].isalnum() or rest[j] in "_-"):
            j += 1
        if j < n and rest[j] == "(":
            depth, k = 0, j
            while k < n:
                if rest[k] == "(":
                    depth += 1
                elif rest[k] == ")":
                    depth -= 1
                    if depth == 0:
                        k += 1
                        break
                k += 1
            toks.append(rest[i:k])
            i = k
        else:
            toks.append(rest[i:j])
            i = j
    return toks


def parse(text):
    layers = []
    for idx, m in enumerate(re.finditer(r"layer_\d+\s*\{", text)):
        i, depth = m.end(), 1
        while depth:
            if text[i] == "{":
                depth += 1
            elif text[i] == "}":
                depth -= 1
            i += 1
        block = text[m.end():i - 1]
        label = re.search(r'label\s*=\s*"([^"]*)"', block)
        body = re.search(r"bindings\s*=\s*<(.*)>\s*;", block, re.S)
        if not body:
            continue
        clean = "\n".join(ln.split("//")[0] for ln in body.group(1).splitlines())
        raw = re.findall(r"&([A-Za-z0-9_]+)((?:[^&]|\n)*?)(?=&|$)", clean)
        keys = []
        for beh, rest in raw:
            keys.append(describe(beh, tokenize(rest), raw_text=rest.strip()))
        layers.append({"idx": idx, "label": label.group(1) if label else "",
                       "short": LAYER_SHORT[idx] if idx < len(LAYER_SHORT)
                       else (label.group(1) if label else str(idx)),
                       "note": "", "keys": keys})
    return layers


def describe(beh, args, raw_text=""):
    out = {"beh": beh, "main": "", "hold": "", "shift": "", "kind": "",
           "icon": "", "caption": "", "combo": "", "tok": "", "layer": None}
    up = beh.upper()

    if beh == "kp":
        tok = args[0] if args else ""
        out["tok"] = tok
        out["main"] = keyname(tok)
        out["shift"] = SHIFTED.get(tok, "")
        out["kind"] = "key"
    elif beh == "trans":
        out["main"], out["kind"] = "trans", "trans"
    elif beh == "none":
        out["main"], out["kind"] = "", "none"
    elif beh == "mo":
        out["kind"] = "layer"
        out["layer"] = int(args[0]) if args and args[0].isdigit() else None
        out["main"] = "MO " + (args[0] if args else "?")
    elif beh == "lt":
        out["kind"] = "layer"
        out["layer"] = int(args[0]) if args and args[0].isdigit() else None
        out["main"] = keyname(args[1]) if len(args) > 1 else ""
        out["hold"] = "MO " + (args[0] if args else "?")
    elif beh == "bt":
        what = args[0] if args else ""
        num = args[1] if len(args) > 1 else ""
        out["kind"] = "bt"
        out["tok"] = what
        out["main"] = {"BT_SEL": "BT " + num, "BT_CLR": "Clear BT",
                       "BT_CLR_ALL": "Clear all", "BT_NEXT": "BT next"}.get(what, what)
        if what == "BT_SEL":
            out["caption"] = "BT " + num
    elif beh == "out":
        out["kind"], out["main"] = "bt", "Out: BT/USB"
    elif beh == "bootloader":
        out["kind"], out["main"] = "bt", "Bootloader"
    elif beh == "caps_word":
        out["kind"], out["main"] = "util", "CapsWord"
    elif beh == "mkp":
        tok = args[0] if args else ""
        out["kind"], out["tok"] = "mouse", tok
        out["main"] = MOUSE.get(tok, tok)
    elif beh in MORPH:
        out["kind"] = "morph"
        if beh == "p_slash":
            out["main"], out["shift"] = "|", "\\"
        else:
            out["main"], out["shift"] = "=", "~"
    elif beh in HOLDTAP:
        out["kind"] = "hrm" if beh in ("hml", "hmr") else "holdtap"
        first = args[0] if args else ""
        second = args[1] if len(args) > 1 else ""
        if beh in ("hml", "hmr"):
            out["hold"] = HOLD_MOD.get(first, keyname(first))
            out["main"] = keyname(second)
        elif beh == "lang_tab":
            out["hold"], out["main"] = keyname(first), "\ud55c/\uc601"
        elif beh == "ctp":
            out["hold"], out["main"] = HOLD_MOD.get(first, keyname(first)), "Paste"
        elif beh == "cpps":
            out["hold"], out["main"] = keyname(first), "Copy"
        elif beh == "del_cad":
            out["hold"], out["main"] = "Ctrl+Alt+Del", keyname(second)
        elif beh == "nav_hp":
            out["hold"], out["main"] = keyname(first), keyname(second)
            out["tok"] = second
    else:
        out["kind"], out["main"] = "other", (up + " " + " ".join(args)).strip()
    out["src"] = ("&" + beh + " " + raw_text).strip()
    return out


def sensor_facts():
    facts = {"snipe_cpi": None, "snipe_layers": [], "scroll_layers": []}
    conf = ROOT / "config" / "boards" / "shields" / "charybdis" / "charybdis_right.conf"
    overlay = ROOT / "config" / "boards" / "shields" / "charybdis" / "charybdis_right.overlay"
    if conf.exists():
        m = re.search(r"^\s*CONFIG_PMW3610_SNIPE_CPI=(\d+)", conf.read_text(encoding="utf-8"), re.M)
        if m:
            facts["snipe_cpi"] = int(m.group(1))
    if overlay.exists():
        text = overlay.read_text(encoding="utf-8")
        for field, key in (("snipe_layers", "snipe-layers"), ("scroll_layers", "scroll-layers")):
            m = re.search(r"^\s*%s\s*=\s*<([^>]*)>" % re.escape(key), text, re.M)
            if m:
                facts[field] = [int(x) for x in m.group(1).split() if x.isdigit()]
    return facts


def layer_name(idx):
    return LAYER_SHORT[idx] if idx is not None and idx < len(LAYER_SHORT) else ("MO %s" % idx)


def enhance(layers):
    facts = sensor_facts()
    for lay in layers:
        idx = lay["idx"]
        for k in lay["keys"]:
            beh = k["beh"]
            if beh in ("mo", "lt") and k["layer"] is not None:
                name = layer_name(k["layer"])
                if beh == "mo":
                    k["main"], k["icon"], k["caption"] = "", "\u25a4", name
                else:
                    k["hold"] = name
            elif beh == "mkp":
                icon, cap = MOUSE_VIS.get(k["tok"], (None, k["main"]))
                if icon:
                    k["main"], k["icon"], k["caption"] = "", icon, cap
            elif beh == "kp" and k["tok"] in MEDIA_VIS:
                icon, cap = MEDIA_VIS[k["tok"]]
                k["kind"], k["main"], k["icon"], k["caption"] = "media", "", icon, cap
            elif beh == "bt":
                if k["tok"] == "BT_SEL":
                    k["main"], k["icon"], k["caption"] = "", "\U0001f535", k["caption"]
                elif k["tok"] == "BT_CLR":
                    k["main"], k["icon"], k["caption"] = "", "\U0001f535\u2715", "Clear BT"
                elif k["tok"] == "BT_CLR_ALL":
                    k["main"], k["icon"], k["caption"] = "", "\U0001f535\u2715\u2715", "Clear All"
            elif beh == "out":
                k["main"], k["icon"], k["caption"] = "", "\u21b9", "BT/USB"
            elif beh == "bootloader":
                k["main"], k["icon"], k["caption"] = "", "\u2699", "Bootloader"
            elif beh == "caps_word":
                k["main"], k["icon"], k["caption"] = "", "\u21ea", "CapsWord"
            elif beh == "lang_tab":
                k["main"], k["icon"], k["caption"] = "", "\U0001f310", "\ud55c/\uc601"
            elif beh == "ctp":
                k["main"], k["icon"], k["caption"] = "", "\U0001f4cb", "Paste"
            elif beh == "cpps":
                k["main"], k["icon"], k["caption"] = "", "\u29c9", "Copy"
            elif beh == "del_cad":
                k["main"], k["icon"], k["caption"] = "", "\u2326", "Del"
            elif beh == "nav_hp":
                cap = ARROW_CAPTION.get(k["main"], k["main"])
                k["icon"], k["main"], k["caption"] = k["main"], "", cap
            if idx in (3, 4) and beh == "kp" and k["tok"] in MOUSE_SHORTCUTS:
                icon, main, cap, combo = MOUSE_SHORTCUTS[k["tok"]]
                k["icon"], k["main"], k["caption"], k["combo"] = icon or "", main, cap, combo or ""
                if icon:
                    k["shift"] = ""
        notes = []
        if any(k["beh"] == "mkp" for k in lay["keys"]) and idx not in facts["snipe_layers"]:
            notes.append("마우스 클릭과 브라우저 단축키를 배치한 레이어입니다.")
        for other in layers:
            if other["idx"] < idx and \
                    [k["src"] for k in other["keys"]] == [k["src"] for k in lay["keys"]]:
                notes.append("%s와 키 배치가 완전히 동일합니다." % (other["label"] or other["short"]))
                break
        if idx in facts["snipe_layers"] and facts["snipe_cpi"] is not None:
            notes.append("차이는 트랙볼 Snipe CPI %d 적용뿐입니다." % facts["snipe_cpi"])
        if lay["keys"] and all(k["kind"] == "trans" for k in lay["keys"]):
            notes.append("모든 키가 trans입니다.")
            if idx in facts["scroll_layers"]:
                notes.append("트랙볼 스크롤 전용 레이어입니다.")
        lay["note"] = " ".join(notes)
    return layers


def cell(k, pos):
    cls = ["key", k["kind"]]
    if k["kind"] in ("hrm", "holdtap"):
        cls.append("ht")
    if pos >= 36:
        cls.append("thumb")
    if len(k["main"]) > 6:
        cls.append("long")
    if k["icon"] or k["caption"] or k["combo"]:
        cls.append("rich")
    body = ""
    if k["shift"]:
        body += '<span class="shift">%s</span>' % html.escape(k["shift"])
    if k["combo"]:
        body += '<span class="combo">%s</span>' % html.escape(k["combo"])
    if k["icon"]:
        sym = " sym" if not any(ord(c) > 0x2600 for c in k["icon"]) else ""
        body += '<span class="icon%s">%s</span>' % (sym, html.escape(k["icon"]))
    if k["main"]:
        main = html.escape(k["main"]).replace("+", "+<wbr>")
        body += '<span class="main">%s</span>' % main
    if k["caption"]:
        body += '<span class="caption">%s</span>' % html.escape(k["caption"])
    if k["hold"]:
        hold = html.escape(k["hold"]).replace("+", "+<wbr>")
        hcls = "hold long" if len(k["hold"]) > 10 else "hold"
        body += '<span class="%s">%s</span>' % (hcls, hold)
    title = html.escape(k.get("src", ""), quote=True)
    return '<div class="%s" title="%s"><i class="pos">%d</i>%s</div>' % (
        " ".join(cls), title, pos, body)


def page(layers):
    parts = ["""<!DOCTYPE html>
<html lang="ko"><head><meta charset="utf-8"><title>Charybdis mini36 keymap</title>
<style>
 body{margin:0;padding:28px;background:#16181d;color:#e6e6e6;
      font-family:'Segoe UI',Roboto,'Malgun Gothic',sans-serif}
 *{box-sizing:border-box}
 h1{font-size:20px;color:#7fd1c8;margin:0 0 4px}
 .sub{color:#8b93a1;font-size:12px;margin-bottom:10px}
 .note-top{color:#9aa3b1;font-size:11px;margin-bottom:18px}
 .layer-panel{background:#20242c;border:1px solid #2c313b;border-radius:14px;
              padding:20px 24px;margin-bottom:26px;width:max-content}
 .ttl{font-size:15px;font-weight:700;color:#7fd1c8;border-bottom:1px solid #313846;
      padding-bottom:8px;margin-bottom:6px}
 .layer-note{font-size:11px;color:#9aa3b1;margin:0 0 12px}
 .row{display:flex;gap:34px;justify-content:center;margin-bottom:7px}
 .grp{display:flex;gap:6px}
 .key{position:relative;width:60px;height:60px;flex:0 0 60px;border-radius:8px;background:#343a46;
      display:flex;flex-direction:column;align-items:center;justify-content:center;overflow:hidden;
      padding:3px 2px 6px;font-size:11px;
      box-shadow:inset 0 1px 0 rgba(255,255,255,.07),0 2px 3px rgba(0,0,0,.5)}
 .pos{position:absolute;top:2px;left:3px;font-size:7px;font-style:normal;color:#5c6472}
 .shift{position:absolute;top:2px;right:4px;font-size:9px;color:#ff9d7d;font-weight:700}
 .combo{font-size:8px;line-height:1;color:#9aa3b1;margin-top:5px;margin-bottom:1px;
        max-width:52px;text-align:center}
 .icon{font-size:15px;line-height:1;margin-bottom:2px}
 .icon.sym{font-size:13px}
 .main{max-width:54px;font-size:15px;font-weight:700;line-height:1.05;text-align:center}
 .key.long .main{font-size:10px}
 .caption{max-width:54px;font-size:9px;line-height:1.05;color:#cbd5e1;text-align:center;margin-top:1px}
 .hold{max-width:54px;font-size:9px;line-height:1.05;color:#f0c674;margin-top:2px;text-align:center}
 .hold.long{font-size:8px}
 .trans{opacity:.42;border:1px dashed #4a5260;background:#262b34}
 .trans .main{font-size:10px;font-weight:600}
 .none{opacity:.24;background:#20242c}
 .hrm{border:1px solid #f0c674}
 .key.layer{background:#3d3350;border:1px solid #6a5a86}
 .key.mouse{border:1px solid #3fae6f;color:#bff0d0}
 .key.bt{border:1px solid #2d9cdb;color:#bfe6f7}
 .key.util,.key.morph,.key.holdtap,.key.media{border:1px solid #b98ad9}
 .key.media{color:#e6d9f2}
 .key.key{color:#e9edf3}
 .key.thumb{background:#2f4a6d;border:1px solid #3d6ea3}
 .legend{display:flex;gap:16px;flex-wrap:wrap;font-size:11px;color:#9aa3b1;margin:0 0 10px}
 .sw{display:inline-block;width:12px;height:12px;border-radius:3px;margin-right:5px;vertical-align:-2px}
</style></head><body>
<h1>Charybdis mini36 (3x6+3x6, 42 keys) &mdash; ZMK keymap</h1>
<div class="sub">Generated from config/charybdis.keymap &middot; tap = large, hold = gold, Shift = orange corner</div>
<div class="note-top">아이콘 아래 글자 = 기능 설명 &middot; C=Ctrl, S=Shift &middot; 레이어 키는 MO 번호 대신 레이어 이름 표시</div>
<div class="legend">
 <span><i class="sw" style="background:#343a46"></i>key</span>
 <span><i class="sw" style="background:#f0c674"></i>home-row mod (hold)</span>
 <span><i class="sw" style="background:#2f4a6d"></i>thumb</span>
 <span><i class="sw" style="background:#3d3350"></i>layer</span>
 <span><i class="sw" style="background:#2d9cdb"></i>BT/output/boot</span>
 <span><i class="sw" style="background:#3fae6f"></i>mouse</span>
 <span><i class="sw" style="background:#b98ad9"></i>macro/morph/media</span>
</div>"""]
    for lay in layers:
        keys = lay["keys"]
        title = "LAYER %d : %s" % (lay["idx"], lay["label"] or "(unnamed)")
        parts.append('<div class="layer-panel"><div class="ttl">%s</div>' % html.escape(title))
        if lay["note"]:
            parts.append('<div class="layer-note">%s</div>' % html.escape(lay["note"]))
        for r in range(3):
            lo, hi = r * 12, r * 12 + 6
            left = "".join(cell(keys[i], i) for i in range(lo, hi))
            right = "".join(cell(keys[i], i) for i in range(hi, hi + 6))
            parts.append('<div class="row"><div class="grp">%s</div><div class="grp">%s</div></div>'
                         % (left, right))
        thumbs = keys[36:42]
        if len(thumbs) >= 6:
            l = "".join(cell(thumbs[i], 36 + i) for i in range(3))
            rr = "".join(cell(thumbs[i], 36 + i) for i in range(3, 6))
            parts.append('<div class="row" style="margin-top:12px"><div class="grp">%s</div>'
                         '<div class="grp">%s</div></div>' % (l, rr))
        parts.append("</div>")
    parts.append("</body></html>")
    return "\n".join(parts)


def main():
    text = SRC.read_text(encoding="utf-8")
    layers = enhance(parse(text))
    for lay in layers:
        print("LAYER %d %-14s %d keys  short=%s" % (lay["idx"], lay["label"], len(lay["keys"]), lay["short"]))
    OUT_JSON.write_text(json.dumps(layers, ensure_ascii=False, indent=1), encoding="utf-8")
    OUT_HTML.write_text(page(layers), encoding="utf-8")
    print("wrote", OUT_HTML, OUT_HTML.stat().st_size, "bytes")
    print("wrote", OUT_JSON)


main()