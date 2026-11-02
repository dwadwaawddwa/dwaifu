"""Découpe un fichier .uwu en lignes de jetons et retire les commentaires kawaii."""

import re

from .errors import Baka

PAIRS = [("<3", "<3"), ("✿", "✿"), ("^_^", "^_^")]
KAOMOJI = "(◕‿◕)"
TODO = "(╯°□°)╯"

TOKEN_RE = re.compile(r"""
     (?P<ws>\s+)
    |(?P<str>"(?:\\.|[^"\\])*")
    |(?P<num>\d+(?:\.\d+)?)
    |(?P<name>[^\W\d]\w*(?:-(?:sama|chan))?)
    |(?P<op>\.\.\.|\.\.|←|<-|\+\+|--|\+=|-=|\*=|/=|==|!=|>=|<=|<>|~>|→|♡|✧|✦|\(◕‿◕\)|[><=:,()\[\]?!.\-*/+])
""", re.X)


class Tok:
    __slots__ = ("kind", "text")

    def __init__(self, kind, text):
        self.kind = kind
        self.text = text

    @property
    def low(self):
        return self.text.lower()

    def __repr__(self):
        return f"{self.kind}:{self.text}"


class Line:
    def __init__(self, no, toks, text, polite):
        self.no = no
        self.toks = toks
        self.text = text
        self.polite = polite


def strip_comments(source):
    """Rend [(numéro, code)] et le nombre de commentaires kawaii."""
    lines, comments = [], 0
    in_block, block_start = False, 0
    for no, raw in enumerate(source.splitlines(), 1):
        out, i, in_str = [], 0, False
        while i < len(raw):
            if in_block:
                j = raw.find("333>", i)
                if j < 0:
                    i = len(raw)
                    break
                in_block, i = False, j + 4
                continue
            c = raw[i]
            if in_str:
                out.append(c)
                if c == "\\" and i + 1 < len(raw):
                    out.append(raw[i + 1])
                    i += 2
                    continue
                if c == '"':
                    in_str = False
                i += 1
                continue
            if c == '"':
                in_str = True
                out.append(c)
                i += 1
                continue
            if raw.startswith("<333", i):
                in_block, block_start = True, no
                comments += 1
                i += 4
                continue
            if raw.startswith(TODO, i):
                comments += 1
                break
            if raw.startswith(KAOMOJI, i):
                rest = raw[i + len(KAOMOJI):].strip()
                if rest in ("", "onegai"):       # décoration de write, pas un commentaire
                    out.append(KAOMOJI)
                    i += len(KAOMOJI)
                    continue
                comments += 1
                break
            for open_, close in PAIRS:
                if raw.startswith(open_, i):
                    j = raw.find(close, i + len(open_))
                    comments += 1
                    i = len(raw) if j < 0 else j + len(close)
                    break
            else:
                out.append(c)
                i += 1
        if in_str:
            raise Baka("OwoBaka", "Un guillemet est resté ouvert.", line=no)
        lines.append((no, "".join(out)))
    if in_block:
        raise Baka("OwoBaka", "Le commentaire <333 n'est jamais fermé par 333>.", line=block_start)
    return lines, comments


def tokenize(code, no):
    toks, pos = [], 0
    while pos < len(code):
        m = TOKEN_RE.match(code, pos)
        if not m:
            raise Baka("OwoBaka", f"Je ne connais pas le symbole « {code[pos]} ».", line=no)
        pos = m.end()
        kind = m.lastgroup
        if kind == "ws":
            continue
        text = m.group()
        if kind == "op":
            text = {"<-": "←", "<>": "♡", "✦": "✧"}.get(text, text)
        toks.append(Tok(kind, text))
    return toks


def lex(source):
    """Rend (lignes, nombre de commentaires). Les lignes vides disparaissent."""
    raw_lines, comments = strip_comments(source)
    lines = []
    for no, code in raw_lines:
        toks = tokenize(code, no)
        if not toks:
            continue
        while toks and toks[-1].text == "!":
            toks.pop()
        polite = False
        if len(toks) > 1 and toks[-1].low == "onegai":
            toks.pop()
            polite = True
        lines.append(Line(no, toks, code.strip(), polite))
    return lines, comments
