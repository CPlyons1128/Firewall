#!/usr/bin/env python3
"""
sonicwall_exp_translate.py
- Decodes SonicWall .exp (base64) → key/value map
- Pretty-prints to .txt and writes JSON
- Optional: remove user/password-related fields so you can reimport safely
"""

import argparse
import base64
import json
import re
from pathlib import Path
from urllib.parse import unquote_plus

USER_PREFIXES = ("userObj",)
USER_EXACT = {"userIV", "passwordUniqueNum"}


def read_text(path: Path) -> str:
    raw = path.read_text(errors="ignore")
    try:
        data = base64.b64decode(raw, validate=False).decode("utf-8", errors="ignore")
        return data if "checksumVersion=" in data else raw
    except Exception:
        return raw


def tokenize(s: str) -> list[tuple[str, str]]:
    pairs = []
    for tok in s.split("&"):
        if "=" not in tok:
            continue
        k, v = tok.split("=", 1)
        pairs.append((k, unquote_plus(v)))
    return pairs


def drop_user_tokens(pairs: list[tuple[str, str]]) -> list[tuple[str, str]]:
    kept = []
    for k, v in pairs:
        if any(k.startswith(p) for p in USER_PREFIXES):
            continue
        if k in USER_EXACT:
            continue
        if re.fullmatch(r".*CryptPass.*", k):
            continue
        kept.append((k, v))
    return kept


def to_dict(pairs: list[tuple[str, str]]) -> dict:
    out: dict[str, object] = {}
    for k, v in pairs:
        if k in out:
            cur = out[k]
            if isinstance(cur, list):
                cur.append(v)
            else:
                out[k] = [cur, v]
        else:
            out[k] = v
    return out


def main():
    ap = argparse.ArgumentParser(prog="sonicwall_exp_translate")
    ap.add_argument("infile", type=Path, help=".exp file")
    ap.add_argument(
        "--clean-users",
        action="store_true",
        help="remove user/password-related entries",
    )
    ap.add_argument(
        "--out-prefix",
        type=Path,
        default=None,
        help="output prefix (default: infile stem)",
    )
    args = ap.parse_args()

    txt = read_text(args.infile)
    pairs = tokenize(txt)
    if args.clean_users:
        pairs = drop_user_tokens(pairs)

    out_prefix = args.out_prefix or args.infile.with_suffix("")
    txt_path = Path(f"{out_prefix}.translated.txt")
    json_path = Path(f"{out_prefix}.translated.json")

    with txt_path.open("w", encoding="utf-8") as f:
        for k, v in pairs:
            f.write(f"{k} = {v}\n")

    with json_path.open("w", encoding="utf-8") as f:
        json.dump(to_dict(pairs), f, indent=2, ensure_ascii=False)

    print(f"Wrote: {txt_path}")
    print(f"Wrote: {json_path}")


# run
main()
