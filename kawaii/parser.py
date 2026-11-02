"""Transforme les lignes de jetons V3 en arbre d'instructions."""

from .errors import Baka
from .lexer import Tok

CAPACITIES = {
    "boss": "boss", "bossing": "boss",
    "reader": "reader", "reading": "reader",
    "writer": "writer", "writing": "writer",
    "counter": "counter", "counting": "counter",
    "judge": "judge", "comparing": "judge",
    "keeper": "keeper", "keeping": "keeper",
    "packer": "packer", "packing": "packer",
    "converter": "converter", "converting": "converter",
    "guesser": "guesser", "guessing": "guesser",
    "fetcher": "fetcher", "fetching": "fetcher",
}
PERSONALITIES = {"lazy", "shy", "tsundere", "kuudere", "dandere", "yandere",
                 "genki", "explosive", "clumsy", "ojou"}
TEST_OPS = {"==", "!=", ">", "<", ">=", "<="}
ASSIGN_OPS = {"+=", "-=", "*=", "/="}
DECORATIONS = {"✧": "sparkles", "nya": "nya", "(◕‿◕)": "kaomoji"}


class Node:
    def __init__(self, kind, line, **fields):
        self.kind = kind
        self.line = line.no
        self.text = line.text
        self.polite = line.polite
        self.__dict__.update(fields)

    def __repr__(self):
        return f"<{self.kind} l.{self.line}>"


def base_name(text):
    """« Sakura-chan » → (« Sakura », « chan »)."""
    for suffix in ("-sama", "-chan"):
        if text.endswith(suffix) and len(text) > len(suffix):
            return text[: -len(suffix)], suffix[1:]
    return text, None


def normalize(toks):
    """Remplace les alias kawaii par les mots-clés du pseudo-code."""
    low = [t.low for t in toks]

    def kw(*words):
        return [Tok("name", w) for w in words]

    if low[:2] == ["nani", "?"]:
        return kw("if") + toks[2:]
    if low[:2] == ["ehh", "?"]:
        return kw("else", "if") + toks[2:]
    if low[:2] == ["ara", "ara"]:
        return kw("else") + toks[2:]
    if low[0] == "ganbatte" and len(toks) > 1:
        if toks[1].kind == "num":
            return kw("repeat") + toks[1:]
        return toks[1:]
    if low == ["kami-sama", "onegai", ":"]:
        return kw("try") + toks[2:]
    if low[:2] == ["gomen", "if"]:
        return kw("catch") + toks[2:]
    if low[0] == "gomen":
        return kw("catch") + toks[1:]
    if low[0] == "daijoubu":
        return kw("finally") + toks[1:]
    if low[:2] == ["chotto", "matte"]:
        return kw("wait") + toks[2:]
    if len(toks) == 3 and toks[1].text == "," and low[2] == "hajime":
        return kw("start") + toks[:1]
    if low[:2] == ["kage", "bunshin"] and len(toks) >= 6 and low[3] == "wa":
        return kw("clone") + [toks[2], Tok("op", ":"), toks[4]]
    if len(toks) > 3 and low[1:3] == ["no", "jutsu"]:
        return toks[:1] + toks[3:]
    alias = {"bye_bye": "break", "next_desu": "next", "sayonara": "return", "end": "desu"}
    if low[0] in alias and len(toks) == 1:
        return kw(alias[low[0]])
    return toks


class Parser:
    def __init__(self, lines):
        self.lines = lines
        self.pos = 0

    # --- outils -----------------------------------------------------------
    def error(self, line, message):
        raise Baka("OwoBaka", message, line=line.no)

    def next_line(self):
        line = self.lines[self.pos]
        self.pos += 1
        line.toks = normalize(line.toks)
        return line

    def peek_low(self):
        if self.pos >= len(self.lines):
            return []
        toks = normalize(self.lines[self.pos].toks)
        self.lines[self.pos].toks = toks
        return [t.low for t in toks]

    def parse(self):
        body = self.block(stop=set())
        return body

    def block(self, stop, opener=None):
        """Lit des instructions jusqu'à une ligne dont le premier mot est dans stop."""
        body = []
        while self.pos < len(self.lines):
            low = self.peek_low()
            if low[0] in stop and not (low[0] == "until" and low[-1] == ":" and "until_end" in stop):
                return body
            body.append(self.statement(self.next_line()))
        if stop:
            where = opener.line if opener else None
            raise Baka("OwoBaka", "Un bloc n'est jamais fermé (il manque desu).", line=where)
        return body

    def expect_desu(self, node):
        line = self.next_line()
        if [t.low for t in line.toks] != ["desu"]:
            self.error(line, "J'attendais desu ici.")

    # --- valeurs et cibles --------------------------------------------------
    def value(self, toks, i, line):
        t = toks[i]
        if t.kind == "str":
            return ("lit", decode(t.text)), i + 1
        if t.kind == "num":
            return ("lit", number(t.text)), i + 1
        if t.text == "-" and i + 1 < len(toks) and toks[i + 1].kind == "num":
            return ("lit", -number(toks[i + 1].text)), i + 2
        if t.text == "[":
            items, i = [], i + 1
            while toks[i].text != "]":
                v, i = self.value(toks, i, line)
                if v[0] != "lit":
                    self.error(line, "Une liste ne contient que des valeurs écrites.")
                items.append(v[1])
                if toks[i].text == ",":
                    i += 1
            return ("lit", items), i + 1
        if t.low in ("hai", "iie", "muda"):
            return ("lit", {"hai": True, "iie": False, "muda": None}[t.low]), i + 1
        if t.kind == "name":
            return ("ref", base_name(t.text)[0]), i + 1
        self.error(line, f"J'attendais une valeur, pas « {t.text} ».")

    def operand(self, toks, i, line):
        if i >= len(toks):
            self.error(line, "Il manque quelque chose en fin de ligne.")
        return self.value(toks, i, line)

    def target(self, tok, line):
        if tok.kind != "name":
            self.error(line, f"J'attendais un nom de waifu, pas « {tok.text} ».")
        return base_name(tok.text)[0]

    def test(self, toks, line):
        """toks = jetons du test (sans le « : » final)."""
        judge = None
        if len(toks) >= 2 and toks[-2].low == "by":
            judge = self.target(toks[-1], line)
            toks = toks[:-2]
        left, i = self.operand(toks, 0, line)
        if i >= len(toks):
            self.error(line, "Il manque un opérateur de test (==, >, is empty…).")
        if toks[i].low == "is":
            rest = [t.low for t in toks[i + 1:]]
            if rest == ["empty"]:
                return {"left": left, "op": "empty", "right": None, "judge": judge}
            if rest == ["not", "empty"]:
                return {"left": left, "op": "not empty", "right": None, "judge": judge}
            self.error(line, "Après is, j'attendais empty ou not empty.")
        op = toks[i].text
        if op not in TEST_OPS:
            self.error(line, f"« {op} » n'est pas un opérateur de test.")
        right, j = self.operand(toks, i + 1, line)
        if j != len(toks):
            self.error(line, "Il reste des mots après le test.")
        return {"left": left, "op": op, "right": right, "judge": judge}

    def colon_test(self, line, start):
        toks = line.toks
        if toks[-1].text != ":":
            self.error(line, "Un bloc s'ouvre par « : » en fin de ligne.")
        return self.test(toks[start:-1], line)

    # --- instructions -------------------------------------------------------
    def statement(self, line):
        toks = line.toks
        low = [t.low for t in toks]
        head = low[0]
        n = len(toks)

        if head == "club" and low[1:] == [":"]:
            return self.club(line)
        if head == "gacha":
            if low[1:3] == ["club", "from"] and n == 4 and toks[3].kind == "str":
                return Node("gacha", line, path=decode(toks[3].text), club=True)
            if n == 2 and toks[1].kind == "str":
                return Node("gacha", line, path=decode(toks[1].text), club=False)
            self.error(line, 'Forme attendue : gacha "fichier.uwu".')
        if head in ("jutsu", "recipe") and n >= 5 and toks[2].text == "(" and low[-1] == ":":
            params = [base_name(t.text)[0] for t in toks[3:-2] if t.text != ","]
            node = Node("jutsu", line, name=toks[1].text, params=params)
            node.body = self.block({"desu"}, node)
            self.expect_desu(node)
            return node
        if head == "plan" and n == 3 and low[2] == ":":
            node = Node("plan", line, boss=self.target(toks[1], line))
            node.body = self.block({"desu"}, node)
            self.expect_desu(node)
            return node
        if head == "if":
            return self.if_chain(line)
        if head in ("while", "until") and low[-1] == ":":
            node = Node(head, line, test=self.colon_test(line, 1))
            node.body = self.block({"desu"}, node)
            self.expect_desu(node)
            return node
        if head == "repeat":
            if low[1:] == [":"]:
                node = Node("repeat_until", line)
                node.body = self.block({"until", "until_end"}, node)
                end = self.next_line()
                node.test = self.test(end.toks[1:], end)
                return node
            if n == 4 and toks[1].kind == "num" and low[2:] == ["times", ":"]:
                node = Node("times", line, count=int(number(toks[1].text)))
                node.body = self.block({"desu"}, node)
                self.expect_desu(node)
                return node
            self.error(line, "Forme attendue : repeat 5 times: ou repeat: … until test.")
        if head == "forever" and low[1:] == [":"]:
            node = Node("forever", line)
            node.body = self.block({"desu"}, node)
            self.expect_desu(node)
            return node
        if head in ("break", "next", "return") and n == 1:
            return Node(head, line)
        if head == "try" and low[1:] == [":"]:
            return self.try_block(line)
        if head == "clone" and n >= 4 and toks[2].text == ":":
            cap = CAPACITIES.get(low[3])
            if not cap:
                self.error(line, f"« {toks[3].text} » n'est pas une capacité.")
            growing = low[4:] == ["♡", "..."]
            return Node("clone", line, name=self.target(toks[1], line), cap=cap, growing=growing)
        if head == "poof" and n == 2:
            return Node("poof", line, name=self.target(toks[1], line))
        if head == "start" and n == 2:
            return Node("start", line, name=self.target(toks[1], line))
        if head == "wait" and n == 2:
            return Node("wait", line, name=self.target(toks[1], line))
        if head in ("ohayo", "oyasumi"):
            who = None
            if n == 2 and low[1] != "minna":
                who = self.target(toks[1], line)
            elif n > 2:
                self.error(line, f"Forme attendue : {head} ou {head} Sakura.")
            return Node(head, line, who=who)
        if low[:2] == ["tea", "time"] and n == 3:
            return Node("tea", line, who=self.target(toks[2], line))
        if head in ("arigatou", "sugoi", "headpat", "baka") and n == 2:
            who = None if low[1] == "minna" else self.target(toks[1], line)
            return Node("affection", line, word=head, who=who)
        if head == "gift" and n == 4 and toks[1].kind == "str" and low[2] == "to":
            return Node("gift", line, food=decode(toks[1].text), who=self.target(toks[3], line))
        if head == "drop" and n == 2:
            return Node("drop", line, target=self.target(toks[1], line))
        if head == "keep" and n == 4 and low[2] == "as":
            return Node("keep", line, target=self.target(toks[1], line), label=toks[3].text)
        if head == "forget" and n == 2:
            return Node("forget", line, label=toks[1].text)
        if head == "pack" and n == 4 and low[2] == "into":
            src, _ = self.value(toks, 1, line)
            return Node("pack", line, source=src, packer=self.target(toks[3], line))
        if head == "convert" and n == 4 and low[2] == "to" and low[3] in ("number", "text", "list"):
            return Node("convert", line, target=self.target(toks[1], line), to=low[3])
        if head == "send" and n == 4 and low[2] == "to" and toks[3].kind == "str":
            return Node("send", line, target=self.target(toks[1], line), url=decode(toks[3].text))
        if head == "write":
            return self.write(line, None, 1)
        if n >= 2 and toks[0].kind == "name" and low[1] == "write":
            return self.write(line, self.target(toks[0], line), 2)
        if toks[0].kind == "name" and n >= 2:
            first = self.target(toks[0], line)
            second = toks[1].text
            if second == ":" and n == 3 and toks[2].kind == "str":
                return Node("say", line, who=first, words=decode(toks[2].text))
            if second == "=":
                return self.row(line, first)
            if second == "←":
                return self.assign(line, first, toks[2:])
            if second in ("++", "--") and n == 2:
                return Node("inc" if second == "++" else "dec", line, target=first)
            if second in ASSIGN_OPS and n >= 3:
                src, j = self.value(toks, 2, line)
                if j != n:
                    self.error(line, "Il reste des mots après l'opération.")
                return Node("op", line, target=first, op=second, source=src)
            if second == "(" and low[-1] == ")":
                args = [self.target(t, line) for t in toks[2:-1] if t.text != ","]
                return Node("call", line, name=toks[0].text, args=args)
        self.error(line, f"Je ne comprends pas « {line.text} ».")

    def club(self, line):
        members = []
        while True:
            if self.pos >= len(self.lines):
                raise Baka("OwoBaka", "Le bloc club: n'est jamais fermé par desu.", line=line.no)
            m = self.next_line()
            low = [t.low for t in m.toks]
            if low == ["desu"]:
                break
            if len(m.toks) < 3 or m.toks[1].text != ":" or m.toks[0].kind != "name":
                self.error(m, "Une membre s'écrit : Nom-chan : capacité, personnalité")
            name, suffix = base_name(m.toks[0].text)
            words = [t.low for t in m.toks[2:] if t.text != ","]
            cap = CAPACITIES.get(words[0])
            if not cap:
                self.error(m, f"« {words[0]} » n'est pas une capacité "
                              f"(boss, reader, writer, counter, judge, keeper, packer, converter, guesser, fetcher).")
            for p in words[1:]:
                if p not in PERSONALITIES:
                    self.error(m, f"« {p} » n'est pas une personnalité ({', '.join(sorted(PERSONALITIES))}).")
            members.append({"name": name, "suffix": suffix, "cap": cap,
                            "pers": words[1:], "line": m.no})
        return Node("club", line, members=members)

    def row(self, line, name):
        toks = line.toks[2:]
        growing = False
        if len(toks) >= 2 and toks[-1].text == "..." and toks[-2].text == "♡":
            growing = True
            toks = toks[:-2]
        names = []
        for k, t in enumerate(toks):
            if k % 2 == 1:
                if t.text != "♡":
                    self.error(line, "Les membres d'une rangée se tiennent par ♡.")
                continue
            names.append(self.target(t, line))
        if not names:
            self.error(line, "Une rangée a besoin d'au moins une membre.")
        if len(names) == 1 and not growing:
            return Node("alias", line, name=name, member=names[0])
        return Node("row", line, name=name, members=names, growing=growing)

    def assign(self, line, target, toks):
        low = [t.low for t in toks]
        n = len(toks)
        if not toks:
            self.error(line, "Il manque ce qu'on met dans les mains après ←.")
        src = None
        if low[0] == "copy" and n == 2:
            src = ("copy", self.target(toks[1], line))
        elif low[0] == "read":
            if n == 1:
                src = ("read", None)
            elif n == 3 and low[1] == "from" and toks[2].kind == "str":
                src = ("read_file", decode(toks[2].text))
            elif n == 4 and low[1] in ("all", "everything") and low[2] == "from" and toks[3].kind == "str":
                src = ("read_all", decode(toks[3].text))
        elif low[0] == "guess" and n == 4 and toks[2].text == "..":
            lo, _ = self.value(toks, 1, line)
            hi, _ = self.value(toks, 3, line)
            src = ("guess", lo[1], hi[1])
        elif low[0] == "recall" and n == 2:
            src = ("recall", toks[1].text)
        elif low[0] in ("first", "last") and n == 3 and low[1] == "of":
            src = (low[0], self.target(toks[2], line))
        elif low[0] == "fetch" and n == 2 and toks[1].kind == "str":
            src = ("fetch", decode(toks[1].text))
        else:
            v, j = self.value(toks, 0, line)
            if j == n:
                src = ("move", v[1]) if v[0] == "ref" else v
        if src is None:
            self.error(line, f"Je ne comprends pas ce qui suit ← dans « {line.text} ».")
        return Node("assign", line, target=target, source=src)

    def write(self, line, actor, i):
        toks = line.toks
        if i >= len(toks):
            self.error(line, "Écrire quoi ?")
        what, i = self.value(toks, i, line)
        deco, newline, path = None, True, None
        rest = [t.low for t in toks[i:]]
        if rest[:1] and toks[i].text in DECORATIONS:
            deco = DECORATIONS[toks[i].text]
            rest = rest[1:]
        elif rest[:2] == ["with", "sparkles"]:
            deco, rest = "sparkles", rest[2:]
        elif rest[:2] == ["in", "kaomoji"]:
            deco, rest = "kaomoji", rest[2:]
        if rest == ["..."]:
            newline = False
        elif len(rest) == 2 and rest[0] == "to" and toks[-1].kind == "str":
            path = decode(toks[-1].text)
        elif rest:
            self.error(line, f"Je ne comprends pas la fin de « {line.text} ».")
        return Node("write", line, actor=actor, what=what, deco=deco, newline=newline, path=path)

    def if_chain(self, line):
        node = Node("if", line, branches=[], otherwise=None)
        test = self.colon_test(line, 1)
        while True:
            body = self.block({"else", "desu"}, node)
            node.branches.append((test, body))
            nxt = self.next_line()
            low = [t.low for t in nxt.toks]
            if low == ["desu"]:
                return node
            if low[:2] == ["else", "if"]:
                test = self.colon_test(nxt, 2)
                continue
            if low == ["else", ":"]:
                node.otherwise = self.block({"desu"}, node)
                self.expect_desu(node)
                return node
            self.error(nxt, "J'attendais else if, else: ou desu.")

    def try_block(self, line):
        node = Node("try", line, catches=[], final=None)
        node.body = self.block({"catch", "finally", "desu"}, node)
        while True:
            nxt = self.next_line()
            low = [t.low for t in nxt.toks]
            if low == ["desu"]:
                return node
            if low[0] == "catch" and low[-1] == ":" and len(low) in (2, 3):
                kind = nxt.toks[1].text if len(low) == 3 else None
                body = self.block({"catch", "finally", "desu"}, node)
                node.catches.append((kind, body))
                continue
            if low == ["finally", ":"]:
                node.final = self.block({"desu"}, node)
                self.expect_desu(node)
                return node
            self.error(nxt, "J'attendais catch, finally: ou desu.")


def decode(text):
    body = text[1:-1]
    return body.replace('\\"', '"').replace("\\n", "\n").replace("\\\\", "\\")


def number(text):
    return float(text) if "." in text else int(text)


def parse(lines):
    return Parser(lines).parse()
