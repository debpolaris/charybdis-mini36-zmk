#!/usr/bin/env python3
"""Render the Charybdis mini36 keymap (config/charybdis.keymap) as an HTML diagram.

Parses the ZMK keymap directly so the diagram cannot drift from what is compiled.
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
    for m in re.finditer(r"layer_\d+\s*\{", text):
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
        layers.append({"label": label.group(1) if label else "", "keys": keys})
    return layers


def describe(beh, args, raw_text=""):
    out = {"beh": beh, "main": "", "hold": "", "shift": "", "kind": ""}
    up = beh.upper()

    if beh == "kp":
        tok = args[0] if args else ""
        out["main"] = keyname(tok)
        out["shift"] = SHIFTED.get(tok, "")
        out["kind"] = "key"
    elif beh == "trans":
        out["main"], out["kind"] = "trans", "trans"
    elif beh == "none":
        out["main"], out["kind"] = "", "none"
    elif beh == "mo":
        out["main"], out["kind"] = "MO " + (args[0] if args else "?"), "layer"
    elif beh == "lt":
        out["kind"] = "layer"
        out["main"] = keyname(args[1]) if len(args) > 1 else ""
        out["hold"] = "MO " + (args[0] if args else "?")
    elif beh == "bt":
        what = args[0] if args else ""
        num = args[1] if len(args) > 1 else ""
        out["kind"] = "bt"
        out["main"] = {"BT_SEL": "BT " + num, "BT_CLR": "Clear BT",
                       "BT_CLR_ALL": "Clear all", "BT_NEXT": "BT next"}.get(what, what)
    elif beh == "out":
        out["kind"], out["main"] = "bt", "Out: BT/USB"
    elif beh == "bootloader":
        out["kind"], out["main"] = "bt", "Bootloader"
    elif beh == "caps_word":
        out["kind"], out["main"] = "util", "CapsWord"
    elif beh == "mkp":
        tok = args[0] if args else ""
        out["kind"], out["main"] = "mouse", MOUSE.get(tok, tok)
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
            out["hold"], out["main"] = keyname(first), "\ud55c&\uc601"
        elif beh == "ctp":
            out["hold"], out["main"] = HOLD_MOD.get(first, keyname(first)), "Paste"
        elif beh == "cpps":
            out["hold"], out["main"] = keyname(first), "Copy"
        elif beh == "del_cad":
            out["hold"], out["main"] = "Ctrl+Alt+Del", keyname(second)
        elif beh == "nav_hp":
            out["hold"], out["main"] = keyname(first), keyname(second)
    else:
        out["kind"], out["main"] = "other", (up + " " + " ".join(args)).strip()
    out["src"] = ("&" + beh + " " + raw_text).strip()
    return out


def cell(k, pos):
    cls = ["key", k["kind"]]
    if k["kind"] == "hrm" or k["kind"] in ("holdtap",):
        cls.append("ht")
    if pos >= 36:
        cls.append("thumb")
    if len(k["main"]) > 6:
        cls.append("long")
    body = ""
    if k["shift"]:
        body += '<span class="shift">%s</span>' % html.escape(k["shift"])
    main = html.escape(k["main"]).replace("+", "+<wbr>") or "&nbsp;"
    body += '<span class="main">%s</span>' % main
    if k["hold"]:
        body += '<span class="hold">%s</span>' % html.escape(k["hold"])
    return '<div class="%s"><i class="pos">%d</i>%s</div>' % (" ".join(cls), pos, body)


def page(layers):
    parts = ["""<!DOCTYPE html>
<html lang="ko"><head><meta charset="utf-8"><title>Charybdis mini36 keymap</title>
<style>
 body{margin:0;padding:28px;background:#16181d;color:#e6e6e6;
      font-family:'Segoe UI',Roboto,'Malgun Gothic',sans-serif}
 *{box-sizing:border-box}
 h1{font-size:20px;color:#7fd1c8;margin:0 0 4px}
 .sub{color:#8b93a1;font-size:12px;margin-bottom:22px}
 .layer-panel{background:#20242c;border:1px solid #2c313b;border-radius:14px;
              padding:20px 24px;margin-bottom:26px;width:max-content}
 .ttl{font-size:15px;font-weight:700;color:#7fd1c8;border-bottom:1px solid #313846;
      padding-bottom:8px;margin-bottom:14px}
 .row{display:flex;gap:34px;justify-content:center;margin-bottom:7px}
 .grp{display:flex;gap:6px}
 .key{position:relative;width:60px;height:60px;flex:0 0 60px;border-radius:8px;background:#343a46;
      display:flex;flex-direction:column;align-items:center;justify-content:center;overflow:hidden;
      font-size:11px;box-shadow:inset 0 1px 0 rgba(255,255,255,.07),0 2px 3px rgba(0,0,0,.5)}
 .main{max-width:54px;font-size:14px;font-weight:700;line-height:1.1;text-align:center}
 .key.long .main{font-size:10px}
 .hold{max-width:54px;font-size:10px;line-height:1.1;color:#f0c674;margin-top:2px;text-align:center}
 .shift{position:absolute;top:3px;right:5px;font-size:10px;color:#ff9d7d;font-weight:700}
 .pos{position:absolute;bottom:2px;left:4px;font-size:8px;font-style:normal;color:#5c6472}
 .trans{opacity:.42;border:1px dashed #4a5260;background:#262b34}
 .none{opacity:.24;background:#20242c}
 .hrm{border:1px solid #f0c674}
 .key.layer{background:#3d3350;border:1px solid #6a5a86}
 .key.mouse{border:1px solid #3fae6f;color:#bff0d0}
 .key.bt{border:1px solid #2d9cdb;color:#bfe6f7}
 .key.util,.key.morph,.key.holdtap{border:1px solid #b98ad9}
 .key.key{color:#e9edf3}
 .key.thumb{background:#2f4a6d;border:1px solid #3d6ea3}
 .legend{display:flex;gap:16px;flex-wrap:wrap;font-size:11px;color:#9aa3b1;margin:0 0 22px}
 .sw{display:inline-block;width:12px;height:12px;border-radius:3px;margin-right:5px;
     vertical-align:-2px}
</style></head><body>
<h1>Charybdis mini36 (3x6+3x6, 42 keys) &mdash; ZMK keymap</h1>
<div class="sub">Generated from config/charybdis.keymap &middot; tap = large, hold = gold, Shift = orange corner</div>
<div class="legend">
 <span><i class="sw" style="background:#343a46"></i>key</span>
 <span><i class="sw" style="background:#f0c674"></i>home-row mod (hold)</span>
 <span><i class="sw" style="background:#2f4a6d"></i>thumb</span>
 <span><i class="sw" style="background:#3d3350"></i>layer</span>
 <span><i class="sw" style="background:#2d9cdb"></i>BT/output/boot</span>
 <span><i class="sw" style="background:#3fae6f"></i>mouse</span>
 <span><i class="sw" style="background:#b98ad9"></i>macro/morph</span>
</div>"""]
    for lay in layers:
        keys = lay["keys"]
        parts.append('<div class="layer-panel"><div class="ttl">%s</div>' %
                     html.escape(lay["label"] or "(unnamed)"))
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
    layers = parse(text)
    for lay in layers:
        print("%-14s %d keys" % (lay["label"], len(lay["keys"])))
    OUT_JSON.write_text(json.dumps(layers, ensure_ascii=False, indent=1), encoding="utf-8")
    OUT_HTML.write_text(page(layers), encoding="utf-8")
    print("wrote", OUT_HTML, OUT_HTML.stat().st_size, "bytes")
    print("wrote", OUT_JSON)


main()
