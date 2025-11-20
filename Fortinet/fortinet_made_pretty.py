# Run this with:
# python3 fortinet_made_pretty.py <.conf file> >> <whatever you want to name this>.txt

import sys

INDENT = "    "  # 4 spaces
indent_level = 0
last_nonempty = None
seen_first_config = False


def shorten_base64(line: str) -> str:
    """Shorten very long set image-base64 lines to keep the file readable."""
    key = 'set image-base64 "'
    idx = line.find(key)
    if idx == -1:
        return line

    start = line.find('"', idx)
    end = line.rfind('"')
    if start == -1 or end == -1 or end <= start + 1:
        return line

    data = line[start + 1 : end]
    if len(data) <= 80:
        return line

    preview = data[:32] + " ... " + data[-32:]
    return f'{line[:start+1]}{preview}"'


def maybe_blank_line(token_type: str, current_indent: int) -> None:
    global last_nonempty, seen_first_config

    if last_nonempty is None:
        return

    # Extra space before each new top-level config (after the first)
    if token_type == "config" and current_indent == 0:
        if seen_first_config:
            print()
        seen_first_config = True
        return

    # Space between top-level edit blocks (objects) for readability
    if token_type == "edit" and current_indent == 1:
        if last_nonempty not in ("config", "edit"):
            print()


def line_out(line: str) -> None:
    global indent_level, last_nonempty

    stripped = line.strip()
    if not stripped:
        return

    token_type = "other"
    if stripped in ("next", "end"):
        token_type = "end"
    elif stripped.startswith("config "):
        token_type = "config"
    elif stripped.startswith("edit "):
        token_type = "edit"

    # decrease indent on 'next' and 'end'
    if token_type == "end":
        indent_level = max(indent_level - 1, 0)

    maybe_blank_line(token_type, indent_level)

    pretty = shorten_base64(stripped)
    print(f"{INDENT * indent_level}{pretty}")

    # increase indent after 'config' or 'edit'
    if token_type in ("config", "edit"):
        indent_level += 1

    if token_type in ("config", "edit"):
        last_nonempty = token_type
    else:
        last_nonempty = stripped


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: python3 fortinet_made_pretty.py <config.conf>")
        sys.exit(1)

    with open(sys.argv[1], "r", errors="ignore") as f:
        for raw_line in f:
            line_out(raw_line)


main()
