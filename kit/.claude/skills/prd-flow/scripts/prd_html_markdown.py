"""The markdown subset of the PRD anatomy, parsed into blocks and rendered to HTML (stdlib only)."""

import html
import re
from collections.abc import Callable

RULE_ID = r"[A-Z][A-Z0-9]*(?:-[A-Z0-9]+)*-\d+[a-z]?"
LOOSE_ID = r"[A-Z][A-Z0-9]*(?:-[A-Z0-9]+)*(?:-\d+[a-z]?|\d+[a-z]?)"
RULE_CELL = re.compile(rf"^({RULE_ID})(?:\s*·\s*(\w+))?$")
LOOSE_CELL = re.compile(rf"^({LOOSE_ID})(?:\s*·\s*(\w+))?$")
LEAD_ID = re.compile(rf"^({LOOSE_ID})\s+(\S.*)$")
SEVERITIES = ("high", "medium", "low")
CALLOUTS = {"CAUTION": "risk", "WARNING": "warn", "IMPORTANT": "info", "NOTE": "note", "TIP": "note"}
FENCE = re.compile(r"^(`{3,}|~{3,})\s*([\w-]*)")
HEADING = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")
LIST_ITEM = re.compile(r"^(\s*)([-*+]|\d+[.)])\s+(.*)$")
SEPARATOR = re.compile(r"^\|?[\s|:-]+$")
PIPE = re.compile(r"(?<!\\)\|")
ESCAPABLE = re.compile(r"\\([\\`*_{}\[\]()#+\-.!|<>~])")
CODE_SPAN = re.compile(r"(`+)(.+?)\1", re.S)
MARKER = re.compile(r"\*(\([^*]+?\))\*")
LINK = re.compile(r"\[([^\]]+)\]\(([^)\s]+)\)")
BOLD = re.compile(r"\*\*(?=\S)(.+?)(?<=\S)\*\*|__(?=\S)(.+?)(?<=\S)__")
ITALIC = re.compile(r"(?<![\w*])\*(?=[^\s*])(.+?)(?<=[^\s*])\*(?![\w*])|(?<![\w])_(?=\S)(.+?)(?<=\S)_(?!\w)")
SLOT = re.compile("\x00(\\d+)\x00")
TAG = re.compile(r"(<[^>]+>)")
HYPHEN_ID = re.compile(rf"(?<![\w-])({RULE_ID})(?![\w-])")
CHECKED = "checked in code"

Resolver = Callable[[str], tuple[str, str]]


def esc(text: str) -> str:
    return html.escape(text, quote=False)


def attr(text: str) -> str:
    return html.escape(text, quote=True)


def marker_class(text: str) -> str:
    low = text.lower()
    for word, cls in (("superseded", "old"), ("proposed", "prop"), ("pending", "pending"),
                      ("approved", "pending"), (CHECKED, "checked"), ("planned", "pending")):
        if word in low:
            return f"mk mk-{cls}"
    return "mk"


SAFE_SCHEMES = {"http", "https", "mailto"}


class Inline:
    """Inline markdown (code, links, bold, italics, markers) to escaped HTML."""

    def __init__(self, resolve: Resolver) -> None:
        self.resolve = resolve

    def __call__(self, text: str) -> str:
        slots: list[str] = []

        def keep(fragment: str) -> str:
            slots.append(fragment)
            return f"\x00{len(slots) - 1}\x00"

        text = CODE_SPAN.sub(lambda m: keep(f"<code>{esc(m.group(2).strip())}</code>"), text)
        text = ESCAPABLE.sub(lambda m: keep(esc(m.group(1))), text)
        text = esc(text)
        text = MARKER.sub(lambda m: keep(f'<i class="{marker_class(m.group(1))}">{m.group(1)}</i>'), text)
        text = LINK.sub(lambda m: self.link(m.group(1), html.unescape(m.group(2)), keep), text)
        text = BOLD.sub(lambda m: f"<b>{m.group(1) or m.group(2)}</b>", text)
        text = ITALIC.sub(lambda m: f"<em>{m.group(1) or m.group(2)}</em>", text)
        while SLOT.search(text):
            text = SLOT.sub(lambda m: slots[int(m.group(1))], text)
        return on_text(text, lambda t: HYPHEN_ID.sub(r'<span class="nw">\1</span>', t))

    def link(self, label: str, url: str, keep: Callable[[str], str]) -> str:
        href, go = self.resolve(url)
        scheme = re.match(r"^([a-zA-Z][a-zA-Z0-9+.-]*):", href)
        if scheme and scheme.group(1).lower() not in SAFE_SCHEMES:
            return label
        extra = f' data-go="{attr(go)}"' if go else ""
        if scheme:
            extra += ' target="_blank" rel="noopener"'
        return keep(f'<a href="{attr(href)}"{extra}>') + label + keep("</a>")


def split_row(line: str) -> list[str]:
    line = line.strip()
    if line.startswith("|"):
        line = line[1:]
    if line.endswith("|") and not line.endswith("\\|"):
        line = line[:-1]
    return [c.strip().replace("\\|", "|") for c in PIPE.split(line)]


def parse(text: str) -> list[tuple]:
    """Block list: ("h", level, text), ("p", text), ("list", ordered, start, items), ("table", header, rows),
    ("callout", kind, blocks), ("mermaid", src), ("code", lang, src). List items are (text, children)."""
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    blocks: list[tuple] = []
    para: list[str] = []
    i = 0

    def flush() -> None:
        if para:
            blocks.append(("p", " ".join(s.strip() for s in para)))
            para.clear()

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        fence = FENCE.match(stripped)
        if fence:
            flush()
            mark, lang, body = fence.group(1), fence.group(2).lower(), []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith(mark):
                body.append(lines[i])
                i += 1
            src = "\n".join(body).strip("\n")
            blocks.append(("mermaid", src) if lang == "mermaid" else ("code", lang, src))
        elif not stripped:
            flush()
        elif HEADING.match(stripped) and not line.startswith("    "):
            flush()
            m = HEADING.match(stripped)
            blocks.append(("h", len(m.group(1)), m.group(2)))
        elif stripped.startswith(">"):
            flush()
            inner = []
            while i < len(lines) and lines[i].strip().startswith(">"):
                inner.append(re.sub(r"^\s*>\s?", "", lines[i]))
                i += 1
            blocks.append(callout(inner))
            continue
        elif stripped.startswith("|") and i + 1 < len(lines) and SEPARATOR.match(lines[i + 1].strip()) and "-" in lines[i + 1]:
            flush()
            header = split_row(stripped)
            rows = []
            i += 2
            while i < len(lines) and lines[i].strip().startswith("|"):
                rows.append(split_row(lines[i]))
                i += 1
            blocks.append(("table", header, rows))
            continue
        elif LIST_ITEM.match(line):
            flush()
            i = parse_list(lines, i, blocks)
            continue
        elif re.fullmatch(r"(-{3,}|\*{3,}|_{3,})", stripped):
            flush()
        else:
            para.append(line)
        i += 1
    flush()
    return blocks


def callout(inner: list[str]) -> tuple:
    kind = "plain"
    if inner:
        m = re.match(r"^\[!(\w+)\]\s*(.*)$", inner[0].strip())
        if m:
            kind = CALLOUTS.get(m.group(1).upper(), "note")
            inner = ([m.group(2)] if m.group(2) else []) + inner[1:]
    return ("callout", kind, parse("\n".join(inner)))


def parse_list(lines: list[str], i: int, blocks: list[tuple]) -> int:
    first = LIST_ITEM.match(lines[i])
    base = len(first.group(1))
    ordered = first.group(2)[0].isdigit()
    start = int(first.group(2)[:-1]) if ordered else 1
    items: list[list] = []
    child_lines: list[str] = []

    def close_item() -> None:
        if items and child_lines:
            items[-1][1] = parse_children(child_lines)
        child_lines.clear()

    while i < len(lines):
        line = lines[i]
        m = LIST_ITEM.match(line)
        if m and len(m.group(1)) == base:
            close_item()
            items.append([m.group(3).strip(), []])
        elif line.strip() and (len(line) - len(line.lstrip())) > base and items:
            if child_lines or LIST_ITEM.match(line):
                child_lines.append(line)
            else:
                items[-1][0] += " " + line.strip()
        else:
            break
        i += 1
    close_item()
    blocks.append(("list", ordered, start, [(t, c) for t, c in items]))
    return i


def parse_children(lines: list[str]) -> list[tuple]:
    indent = min(len(s) - len(s.lstrip()) for s in lines if s.strip())
    return parse("\n".join(s[indent:] for s in lines))


def severity(cell: str) -> tuple[str, str]:
    m = LOOSE_CELL.match(cell.strip())
    if not m:
        return "", ""
    sev = (m.group(2) or "").lower()
    return m.group(1), sev if sev in SEVERITIES else ""


def via_cell(value: str, label: str = "") -> str:
    v = value.strip().lower()
    if not v:
        return '<td class="via"></td>'
    return f'<td class="via"{label}><span class="via-tag v-{attr(re.sub(r"[^a-z0-9-]", "-", v))}">{esc(v)}</span></td>'


def strip_tags(fragment: str) -> str:
    return html.unescape(re.sub(r"<[^>]+>", "", fragment))


def on_text(fragment: str, fn: Callable[[str], str]) -> str:
    parts = TAG.split(fragment)
    return "".join(p if n % 2 else fn(p) for n, p in enumerate(parts))


def wbr(fragment: str) -> str:
    return on_text(fragment, lambda t: re.sub(r"(/|::|;)(?=\S)", r"\1<wbr>", t))


def column_classes(header: list[str]) -> list[str]:
    names = {"source": "src", "evidence": "src", "example": "ex", "change via": "via"}
    return [names.get(h.strip().lower(), "") for h in header]


def table(header: list[str], rows: list[list[str]], inline: Inline, mode: str = "auto",
          sev_of: Callable[[list[str]], str] | None = None) -> str:
    """mode `auto`: a rule table (bare `<td>ID</td>`, the row the gate reads) when a row starts with a rule ID,
    otherwise `mx`; `mx`: never a rule table; `decision`: a rule table whose ID cell is not a gate row."""
    rules = mode == "decision" or (mode == "auto" and any(r and RULE_CELL.match(r[0].strip()) for r in rows))
    bare_ids = mode == "auto"
    classes = column_classes(header)
    out = [f'<div class="tw"><table class="{"rules" if rules else "mx"}"><thead><tr>']
    out += [f"<th>{inline(h)}</th>" for h in header]
    out.append("</tr></thead><tbody>")
    for row in rows:
        row = (row + [""] * len(header))[: len(header)]
        rid, sev = severity(row[0])
        if sev_of and not sev:
            sev = sev_of(row)
        cells = []
        for n, cell in enumerate(row):
            cls = classes[n]
            label = f' data-label="{attr(strip_tags(inline(header[n])))}"' if n >= (2 if rules else 1) and header[n] else ""
            if cls == "via":
                cells.append(via_cell(cell, label))
            elif n == 0 and rules:
                cells.append(f"<td>{esc(rid or cell)}</td>" if bare_ids else f'<td class="qid">{esc(rid or cell)}</td>')
            elif n == 0 and rid:
                cells.append(f'<td class="idc"><span class="pid">{esc(rid)}</span></td>')
            elif n == 1 and rules:
                cells.append(f'<td class="rule">{inline(cell)}</td>')
            else:
                body = wbr(inline(cell)) if cls == "src" else inline(cell)
                cells.append(f'<td class="{cls}"{label}>{body}</td>' if cls else f"<td{label}>{body}</td>")
        via = next((row[n] for n, c in enumerate(classes) if c == "via"), "").strip().lower()
        attrs = (f' data-via="{attr(via)}"' if via and rules else "") + (f' data-sev="{sev}"' if sev and rules else "")
        out.append(f"<tr{attrs}>{''.join(cells)}</tr>")
    out.append("</tbody></table></div>")
    return "".join(out)


def render_list(block: tuple, inline: Inline) -> str:
    _, ordered, start, items = block
    if ordered:
        reset = f' style="counter-reset:st {start - 1}"' if start != 1 else ""
        head = f'<ol class="story"{reset}>'
    else:
        head = "<ul>"
    body = "".join(f"<li>{inline(text)}{render_inner(children, inline)}</li>" for text, children in items)
    return head + body + ("</ol>" if ordered else "</ul>")


def render_inner(blocks: list[tuple], inline: Inline) -> str:
    out = []
    for b in blocks:
        if b[0] == "list":
            out.append(render_list(b, inline))
        elif b[0] == "p":
            out.append(f"<p>{inline(b[1])}</p>")
        else:
            out.append(render_blocks([b], inline))
    return "".join(out)


def render_callout(block: tuple, inline: Inline) -> str:
    _, kind, inner = block
    title, verified = "", False
    if inner and inner[0][0] == "p":
        text = inner[0][1].strip()
        m = re.fullmatch(r"\*\*(.+)\*\*", text)
        if m and "**" not in m.group(1).replace(f"*({CHECKED})*", ""):
            body = m.group(1)
            verified = f"*({CHECKED})*" in body
            title = inline(body.replace(f"*({CHECKED})*", "").strip())
            inner = inner[1:]
    if not title and inner and inner[-1][0] == "p" and f"*({CHECKED})*" in inner[-1][1]:
        verified = True
        inner = inner[:-1] + [("p", inner[-1][1].replace(f"*({CHECKED})*", "").strip())]
    badge = f'<span class="verified">{CHECKED}</span>' if verified else ""
    head = f'<b class="t">{title}{badge}</b>' if title else ""
    body = render_inner(inner, inline)
    if badge and not title:
        body += f"<p>{badge}</p>"
    cls = "callout" if kind == "plain" else f"callout {kind}"
    return f'<div class="{cls}">{head}{body}</div>'


def render_blocks(blocks: list[tuple], inline: Inline, table_fn: Callable | None = None, lede: bool = True) -> str:
    """Prose blocks (paragraphs, lists, h3 and deeper) are grouped in `div.explain`; the first paragraph is the lede."""
    out: list[str] = []
    prose: list[str] = []
    lede_done = not lede

    def flush() -> None:
        if prose:
            out.append('<div class="explain">' + "".join(prose) + "</div>")
            prose.clear()

    for b in blocks:
        kind = b[0]
        if kind == "p":
            cls = "" if lede_done else ' class="lede"'
            lede_done = True
            prose.append(f"<p{cls}>{inline(b[1])}</p>")
        elif kind == "h":
            level = max(3, min(b[1], 4))
            prose.append(f"<h{level}>{inline(b[2])}</h{level}>")
        elif kind == "list":
            prose.append(render_list(b, inline))
        else:
            flush()
            if kind == "table":
                out.append((table_fn or table)(b[1], b[2], inline))
            elif kind == "callout":
                out.append(render_callout(b, inline))
            elif kind == "mermaid":
                out.append(f'<div class="diag"><pre class="mermaid">{esc(b[1])}</pre></div>')
            elif kind == "code":
                out.append(f'<pre class="code"><code>{esc(b[2])}</code></pre>')
    flush()
    return "\n".join(out)
