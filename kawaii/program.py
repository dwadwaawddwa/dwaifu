"""Charger un .uwu, suivre les gacha, et tout vérifier avant le départ."""

import os

from .errors import Baka
from .lexer import lex
from .parser import parse

STDLIB = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "stdlib")
ORDER_KINDS = {"assign", "inc", "dec", "op", "write", "drop", "keep", "forget", "pack", "convert", "send"}


class Program:
    def __init__(self, path):
        self.path = os.path.abspath(path)
        self.base_dir = os.path.dirname(self.path)
        self.members = []
        self.jutsu = {}
        self.plans = {}
        self.warnings = []
        with open(self.path, encoding="utf-8-sig") as f:
            self.source = f.read()
        lines, self.comments = lex(self.source)
        self.body = parse(lines)
        self.collect(self.body, self.base_dir, seen={self.path}, own=True)

    def collect(self, body, base_dir, seen, own, take_club=True):
        for node in body:
            if node.kind == "club" and take_club:
                self.members += node.members
            elif node.kind == "jutsu":
                self.jutsu[node.name] = node
            elif node.kind == "plan":
                self.plans[node.boss] = node
            elif node.kind == "gacha":
                self.gacha(node, base_dir, seen)

    def gacha(self, node, base_dir, seen):
        for folder in (base_dir, STDLIB):
            full = os.path.abspath(os.path.join(folder, node.path))
            if os.path.exists(full):
                break
        else:
            raise Baka("FileBaka", f"gacha : je ne trouve pas « {node.path} ».", line=node.line)
        if full in seen:
            return
        seen.add(full)
        with open(full, encoding="utf-8-sig") as f:
            try:
                lines, _ = lex(f.read())
                body = parse(lines)
            except Baka as e:
                e.message = f"{os.path.basename(full)} : {e.message}"
                raise
        self.collect(body, os.path.dirname(full), seen, own=False, take_club=node.club)


def walk(body):
    for node in body:
        yield node
        for attr in ("body", "otherwise", "final"):
            sub = getattr(node, attr, None)
            if sub:
                yield from walk(sub)
        for _, sub in getattr(node, "branches", []):
            yield from walk(sub)
        for _, sub in getattr(node, "catches", []):
            yield from walk(sub)


def all_nodes(program):
    yield from walk(program.body)
    for j in program.jutsu.values():
        if j not in program.body:
            yield from walk(j.body)


def refs(node):
    """Les noms de waifus qu'une instruction utilise."""
    names = []

    def val(v):
        if v and v[0] == "ref":
            names.append(v[1])

    def test(t):
        val(t["left"])
        val(t["right"])
        if t["judge"]:
            names.append(t["judge"])

    k = node.kind
    if k in ("assign", "inc", "dec", "op", "drop", "keep", "convert", "send"):
        names.append(node.target)
    if k == "assign" and node.source[0] in ("move", "copy", "first", "last"):
        names.append(node.source[1])
    if k == "op":
        val(node.source)
    if k == "write":
        val(node.what)
        if node.actor:
            names.append(node.actor)
    if k == "pack":
        val(node.source)
        names.append(node.packer)
    if k in ("say", "tea", "gift") or (k in ("ohayo", "oyasumi", "affection") and node.who):
        names.append(node.who)
    if k in ("poof", "start") or (k == "wait" and node.name.lower() != "minna"):
        names.append(node.name)
    if k == "row":
        names += node.members
    if k == "alias":
        names.append(node.member)
    if k == "call":
        names += node.args
    if k in ("while", "until", "repeat_until"):
        test(node.test)
    if k == "if":
        for t, _ in node.branches:
            test(t)
    return names


def check(program):
    """Les vérifications d'avant le départ. Rend la liste des avertissements."""
    if not program.members:
        raise Baka("NoBossBaka", "Il n'y a pas de bloc club: (et donc pas de présidente).")
    names = set()
    for m in program.members:
        full = f"{m['name']}-{m['suffix']}" if m["suffix"] else m["name"]
        if m["name"] in names:
            raise Baka("OwoBaka", f"Deux membres s'appellent {m['name']}.", line=m["line"])
        names.add(m["name"])
        if m["suffix"] is None:
            raise Baka("NoSuffixBaka", f"C'est qui, ça ? « {m['name']} » a besoin de -sama ou -chan.", line=m["line"])
        if (m["suffix"] == "sama") != (m["cap"] == "boss"):
            raise Baka("HonorificBaka", None, line=m["line"], waifu=full)
    if not any(m["cap"] == "boss" for m in program.members):
        raise Baka("NoBossBaka", None)

    known = set(names)
    nodes = list(all_nodes(program))
    for node in nodes:
        if node.kind in ("row", "alias", "clone"):
            known.add(node.name)
    for j in program.jutsu.values():
        known.update(j.params)
    for node in nodes:
        for name in refs(node):
            if name not in known:
                raise Baka("NobodyBaka", f"Personne ne s'appelle {name}.", line=node.line)
        if node.kind == "call" and node.name not in program.jutsu:
            raise Baka("NobodyBaka", f"Aucun jutsu ne s'appelle {node.name}.", line=node.line)
        if node.kind == "call" and len(node.args) != len(program.jutsu[node.name].params):
            raise Baka("OwoBaka", f"{node.name} attend {len(program.jutsu[node.name].params)} waifus.", line=node.line)
        if node.kind == "plan" and node.boss not in [m["name"] for m in program.members if m["cap"] == "boss"]:
            raise Baka("HonorificBaka", f"{node.boss} n'est pas une présidente du club.", line=node.line)

    orders = [n for n in walk(program.body) if n.kind in ORDER_KINDS]
    rude = [n for n in orders if not n.polite]
    if orders and len(rude) * 2 > len(orders):
        program.warnings.append(
            f"RudeBaka : {len(rude)} ordres sur {len(orders)} sans onegai. Le club boude un peu.")
    return program.warnings


RANKS = [(0.0, "C"), (0.25, "B"), (0.5, "A"), (0.75, "S")]


def rank(program, stats=None):
    """Le rang kawaii : la note de style du club (aucun effet sur le résultat)."""
    body = list(walk(program.body))
    orders = [n for n in body if n.kind in ORDER_KINDS]
    polite = sum(1 for n in orders if n.polite)
    rude = len(orders) - polite
    kind_words = sum(1 for n in body if n.kind == "affection" and n.word != "baka")
    baka = sum(1 for n in body if n.kind == "affection" and n.word == "baka")
    stats = stats or {"uncaught": 0, "left": 0}
    score = (polite - 2 * rude + 2 * kind_words + program.comments
             - 10 * baka - 5 * stats["uncaught"] - 20 * stats["left"])
    ratio = score / max(1, len(body))
    grade = "SS"
    for limit, name in RANKS:
        if ratio < limit:
            grade = name
            break
    detail = (f"onegai {polite}/{len(orders)} · gentillesses {kind_words} · "
              f"commentaires {program.comments} · baka {baka}")
    return grade, detail
