"""Le club en action : waifus, rangées, doigts, et l'exécution des instructions."""

import os
import urllib.request

from .errors import Baka
from . import chat as lines

FOODS = ["dango", "mochi", "onigiri", "taiyaki", "ramen", "melon pan", "matcha"]
NEW_NAMES = ["Aoi", "Mei", "Yui", "Koharu", "Hana", "Momo", "Rika", "Emi", "Nao", "Saya"]


class Waifu:
    def __init__(self, name, suffix, cap, pers=(), clone=False):
        self.name = name
        self.suffix = suffix or "chan"
        self.cap = cap
        self.pers = list(pers)
        self.clone = clone
        self.hands = 0 if cap == "counter" else None
        self.awake = clone
        self.affection = 50
        self.shelf = {}
        self.verdict = "nothing"
        self.gone = False
        self.likes = self.hates = None
        self.last_sugoi = -100
        self.grumbled = False

    @property
    def full(self):
        return f"{self.name}-{self.suffix}"

    def has(self, trait):
        return trait in self.pers


class Row:
    """Des compteuses qui forment un nombre : la plus à gauche compte les plus gros paquets."""

    def __init__(self, name, members, growing):
        self.name = name
        self.members = members
        self.growing = growing

    @property
    def full(self):
        return self.name

    @property
    def value(self):
        total = 0
        for m in self.members:
            total = total * 10 + (m.hands or 0)
        return total


class Signal(Exception):
    pass


class Break(Signal):
    pass


class Next(Signal):
    pass


class Return(Signal):
    pass


def is_number(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def fmt(v, inner=False):
    if v is None:
        return "muda"
    if v is True:
        return "hai"
    if v is False:
        return "iie"
    if isinstance(v, float):
        return ("%f" % v).rstrip("0").rstrip(".")
    if isinstance(v, list):
        return "[" + ", ".join(fmt(x, True) for x in v) + "]"
    if isinstance(v, str) and inner:
        return '"' + v + '"'
    return str(v)


def looks_number(text):
    try:
        return int(text)
    except ValueError:
        try:
            return float(text)
        except ValueError:
            return text


class Interpreter:
    def __init__(self, program, chat, rng, read_line, base_dir, max_steps=2_000_000):
        self.program = program
        self.chat = chat
        self.rng = rng
        self.read_line = read_line
        self.base_dir = base_dir
        self.max_steps = max_steps
        self.steps = 0
        self.members = {}
        self.globals = {}
        self.frames = []
        self.files = {}
        self.boss = None
        self.stats = {"uncaught": 0, "left": 0}
        self.line = None
        for m in program.members:
            w = Waifu(m["name"], m["suffix"], m["cap"], m["pers"])
            w.likes, w.hates = rng.sample(FOODS, 2)
            self.members[w.name] = w
            self.globals[w.name] = w
            if self.boss is None and w.cap == "boss":
                self.boss = w

    # --- trouver les waifus ------------------------------------------------
    def err(self, kind, message=None, who=None):
        return Baka(kind, message, line=self.line, waifu=who.full if who else None)

    def lookup(self, name):
        if self.frames and name in self.frames[-1]["names"]:
            return self.frames[-1]["names"][name]
        if name in self.globals:
            return self.globals[name]
        raise self.err("NobodyBaka", f"Personne ne s'appelle {name} dans le club.")

    def waifus(self):
        seen = list(self.members.values())
        for frame in self.frames:
            seen += [t for t in frame["names"].values() if isinstance(t, Waifu) and t.clone]
        return [w for w in seen if not w.gone]

    def resolve(self, cap, explicit=None):
        if explicit:
            w = self.lookup(explicit)
            if not isinstance(w, Waifu) or w.cap != cap:
                raise self.err("JobBaka", f"{explicit} n'est pas {cap}.", w if isinstance(w, Waifu) else None)
            return w
        found = []
        for w in self.waifus():
            if w.cap == cap and w not in found:
                found.append(w)
        if not found:
            raise self.err("JobBaka", f"Personne n'est {cap} dans le club !")
        if len(found) > 1:
            names = ", ".join(w.name for w in found)
            raise self.err("WhoBaka", f"Qui doit le faire ? ({names}) Nomme-la avec « by » ou devant le verbe.")
        return found[0]

    def holder(self, name):
        t = self.lookup(name)
        if isinstance(t, Waifu) and t.cap == "boss":
            raise self.err("JobBaka", "Une présidente n'a pas de mains.", t)
        return t

    # --- les ordres --------------------------------------------------------
    def order(self, w, polite):
        if isinstance(w, Row):
            for m in w.members:
                self.order(m, True)
            w = w.members[-1]
        if w.gone:
            raise self.err("HeartbreakBaka", "Elle a quitté le club.", w)
        if not w.awake:
            raise self.err("SleepyBaka", None, w)
        if not polite:
            self.change_affection(w, -1)
            if not w.grumbled or w.affection < 20:
                self.chat.line(w.full, lines.rude(w))
                w.grumbled = True

    def change_affection(self, w, delta):
        w.affection = max(0, min(100, w.affection + delta))
        if w.affection == 0 and not w.gone:
            w.gone = True
            self.stats["left"] += 1
            raise self.err("HeartbreakBaka", None, w)

    # --- les mains ---------------------------------------------------------
    def get(self, t):
        if isinstance(t, Row):
            return t.value
        if t.hands is None:
            raise self.err("EmptyHandsBaka", None, t)
        return t.hands

    def peek(self, t):
        return t.value if isinstance(t, Row) else t.hands

    def put(self, t, v):
        if isinstance(t, Row):
            self.row_set(t, v)
            return
        if t.cap == "counter" and is_number(v):
            if isinstance(v, float) and not v.is_integer():
                raise self.err("FingersBaka", "Je ne lève pas de demi-doigt !", t)
            if v < 0 or v > 10:
                raise self.err("FingersBaka", f"Je n'ai que dix doigts ! ({fmt(v)})", t)
            v = int(v)
        t.hands = v

    def clear(self, t):
        if isinstance(t, Row):
            for m in t.members:
                m.hands = 0
        else:
            t.hands = None

    def row_set(self, row, v):
        if not is_number(v) or (isinstance(v, float) and not v.is_integer()):
            raise self.err("TypeBaka", f"Une rangée ne tient que des nombres entiers, pas {fmt(v, True)}.")
        v = int(v)
        if v < 0:
            raise self.err("FingersBaka", "Pas de doigts négatifs !")
        n = len(row.members)
        lead_max = 9 if row.growing else 10
        while v // 10 ** (n - 1) > lead_max:
            if not row.growing:
                raise self.err("FingersBaka", f"Il manque une waifu dans la rangée {row.name} pour tenir {v} !")
            self.grow(row)
            n += 1
        for k, m in enumerate(row.members):
            if k == 0:
                m.hands = v // 10 ** (n - 1)
            else:
                m.hands = (v // 10 ** (n - 1 - k)) % 10

    def grow(self, row):
        taken = {w.name for w in self.waifus()}
        name = next((x for x in NEW_NAMES if x not in taken), f"Kumi{len(taken)}")
        w = Waifu(name, "chan", "counter", clone=True)
        w.hands = 0
        self.globals.setdefault(name, w)
        row.members.insert(0, w)
        self.chat.line(w.full, "Une nouvelle waifu rejoint la rangée !")

    def count(self, t, up):
        if isinstance(t, Row):
            return self.row_count(t, up)
        if t.cap != "counter":
            raise self.err("JobBaka", "Je ne sais pas compter sur mes doigts !", t)
        v = self.get(t)
        if not is_number(v):
            raise self.err("TypeBaka", f"On ne compte pas sur {fmt(v, True)} !", t)
        if up and v >= 10:
            raise self.err("OverflowBaka", None, t)
        if not up and v <= 0:
            raise self.err("UnderflowBaka", None, t)
        t.hands = v + (1 if up else -1)
        self.chat.line(t.full, lines.fingers(t), detail=True)

    def row_count(self, row, up):
        ms = row.members
        i = len(ms) - 1
        if up:
            while True:
                m = ms[i]
                limit = 9 if (i > 0 or row.growing) else 10
                if m.hands < limit:
                    m.hands += 1
                    break
                if i == 0 and not row.growing:
                    raise self.err("OverflowBaka", f"La rangée {row.name} n'a plus de doigts !", m)
                m.hands = 0
                if i == 0:
                    self.grow(row)
                    i = 1
                left = ms[i - 1]
                self.chat.line(m.full, lines.carry(m, left))
                i -= 1
        else:
            if row.value == 0:
                raise self.err("UnderflowBaka", f"La rangée {row.name} est déjà à zéro !", ms[-1])
            while True:
                m = ms[i]
                if m.hands > 0:
                    m.hands -= 1
                    break
                m.hands = 9
                self.chat.line(m.full, f"{ms[i - 1].name}-{ms[i - 1].suffix}, je t'emprunte un paquet.", detail=True)
                i -= 1
        self.chat.line(ms[-1].full, f"{row.name} = {row.value}", detail=True)

    # --- la juge -----------------------------------------------------------
    def operand(self, v):
        if v[0] == "lit":
            return v[1]
        return self.peek(self.lookup(v[1]))

    def judge(self, test):
        j = self.resolve("judge", test["judge"])
        self.order(j, True)
        left = self.operand(test["left"])
        op = test["op"]
        if op in ("empty", "not empty"):
            empty = left is None or left == [] or left == ""
            j.verdict = "empty" if empty else "different"
            self.chat.line(j.full, f"{fmt(left, True)} : {j.verdict}", detail=True)
            return empty if op == "empty" else not empty
        right = self.operand(test["right"])
        verdict = self.compare(left, right, op, j)
        j.verdict = verdict
        self.chat.line(j.full, lines.verdict(fmt(left, True), fmt(right, True), verdict), detail=True)
        return {
            "==": verdict == "same", "!=": verdict != "same",
            ">": verdict == "bigger", "<": verdict == "smaller",
            ">=": verdict in ("bigger", "same"), "<=": verdict in ("smaller", "same"),
        }[op]

    def compare(self, a, b, op, j):
        if (is_number(a) and isinstance(b, str)) or (isinstance(a, str) and is_number(b)):
            raise self.err("TypeBaka", f"Je ne compare pas un texte et un nombre ({fmt(a, True)}, {fmt(b, True)}).", j)
        same_kind = (is_number(a) and is_number(b)) or (isinstance(a, str) and isinstance(b, str))
        if same_kind:
            return "same" if a == b else ("bigger" if a > b else "smaller")
        if op in ("==", "!="):
            return "same" if a == b else "different"
        raise self.err("TypeBaka", f"Je ne range pas {fmt(a, True)} et {fmt(b, True)} par taille.", j)

    # --- exécution ---------------------------------------------------------
    def run(self):
        if self.boss:
            self.boss.awake = True
        self.block(self.program.body)

    def tick(self, node):
        self.line = node.line
        self.steps += 1
        if self.steps > self.max_steps:
            raise self.err("TiredBaka", f"Le club est épuisé après {self.max_steps} instructions (boucle sans fin ?).")

    def block(self, body):
        for node in body:
            self.tick(node)
            getattr(self, "do_" + node.kind)(node)

    def do_club(self, node):
        pass

    def do_gacha(self, node):
        pass

    def do_jutsu(self, node):
        pass

    def do_plan(self, node):
        pass

    def do_alias(self, node):
        self.globals[node.name] = self.lookup(node.member)

    def do_row(self, node):
        ms = []
        for name in node.members:
            w = self.lookup(name)
            if not isinstance(w, Waifu) or w.cap != "counter":
                raise self.err("JobBaka", f"{name} n'est pas une compteuse : elle ne peut pas entrer dans une rangée.")
            ms.append(w)
        row = Row(node.name, ms, node.growing)
        start = sum((m.hands or 0) * 10 ** (len(ms) - 1 - k) for k, m in enumerate(ms))
        self.row_set(row, start)
        self.globals[node.name] = row

    def do_assign(self, node):
        t = self.holder(node.target)
        src = node.source
        kind = src[0]
        if kind == "lit":
            self.order(t, node.polite)
            self.clear(t)
            self.put(t, src[1])
            return
        if kind == "move":
            giver = self.lookup(src[1])
            if giver is t:
                return
            self.order(giver, node.polite)
            v = self.get(giver)
            self.clear(t)
            self.put(t, v)
            self.clear(giver)
            return
        if kind == "copy":
            k = self.resolve("keeper")
            self.order(k, node.polite)
            v = self.get(self.lookup(src[1]))
            self.chat.line(k.full, f"Je garde une copie de {src[1]} ({fmt(v, True)}).", detail=True)
            self.clear(t)
            self.put(t, v)
            return
        if kind in ("read", "read_file", "read_all"):
            r = t if isinstance(t, Waifu) and t.cap == "reader" else self.resolve("reader")
            self.order(r, node.polite)
            v = self.read(r, kind, src[1])
        elif kind == "guess":
            r = t if isinstance(t, Waifu) and t.cap == "guesser" else self.resolve("guesser")
            self.order(r, node.polite)
            lo, hi = src[1], src[2]
            if not (is_number(lo) and is_number(hi)) or lo > hi:
                raise self.err("TypeBaka", "guess a besoin de deux nombres, le petit d'abord.", r)
            v = self.rng.randint(int(lo), int(hi))
            self.chat.line(r.full, "J'ai choisi un nombre... c'est un secret ♡", detail=True)
        elif kind == "recall":
            r = self.resolve("keeper")
            self.order(r, node.polite)
            if src[1] not in r.shelf:
                raise self.err("ShelfBaka", f"« {src[1]} » n'est pas sur mon étagère.", r)
            v = r.shelf[src[1]]
        elif kind in ("first", "last"):
            r = self.lookup(src[1])
            if not isinstance(r, Waifu) or r.cap != "packer":
                raise self.err("JobBaka", f"{src[1]} n'est pas une packer.")
            self.order(r, node.polite)
            box = self.get(r)
            if not isinstance(box, (list, str)):
                raise self.err("TypeBaka", "Je ne tiens pas une liste ni un texte.", r)
            if not box:
                raise self.err("EmptyHandsBaka", "Ma liste est vide !", r)
            if kind == "first":
                v, rest = box[0], box[1:]
            else:
                v, rest = box[-1], box[:-1]
            r.hands = rest
        else:  # fetch
            r = self.resolve("fetcher")
            self.order(r, node.polite)
            try:
                with urllib.request.urlopen(src[1], timeout=10) as resp:
                    v = resp.read().decode("utf-8", "replace")
            except Exception as e:
                raise self.err("FileBaka", f"Je n'arrive pas à lire {src[1]} ({e}).", r)
        if r is t:
            self.put(t, v)
            return
        self.clear(t)
        self.put(t, v)

    def read(self, r, kind, path):
        if kind == "read":
            text = self.read_line()
            if text is None:
                raise self.err("LonelyBaka", None, r)
            v = looks_number(text.strip())
            self.chat.line(r.full, lines.read(r, fmt(v)))
            return v
        full = os.path.join(self.base_dir, path)
        if not os.path.exists(full):
            raise self.err("FileBaka", f"Je ne trouve pas « {path} ».", r)
        with open(full, encoding="utf-8") as f:
            content = f.read().splitlines()
        if kind == "read_all":
            return [looks_number(x) for x in content]
        pos = self.files.get(full, 0)
        self.files[full] = pos + 1
        return looks_number(content[pos]) if pos < len(content) else None

    def do_drop(self, node):
        t = self.holder(node.target)
        self.order(t, node.polite)
        self.clear(t)

    def do_inc(self, node):
        t = self.holder(node.target)
        self.order(t, node.polite)
        self.count(t, True)

    def do_dec(self, node):
        t = self.holder(node.target)
        self.order(t, node.polite)
        self.count(t, False)

    def do_op(self, node):
        t = self.holder(node.target)
        if not (isinstance(t, Row) or t.cap == "counter"):
            raise self.err("JobBaka", f"{node.target} ne compte pas : {node.op} est pour les compteuses.", t)
        self.order(t, node.polite)
        a = self.get(t)
        b = self.operand(node.source)
        if b is None:
            raise self.err("EmptyHandsBaka", f"{node.source[1]} n'a rien dans les mains.")
        if not (is_number(a) and is_number(b)):
            raise self.err("TypeBaka", f"{node.op} ne marche qu'avec des nombres.", t if isinstance(t, Waifu) else None)
        if node.op == "+=":
            v = a + b
        elif node.op == "-=":
            v = a - b
            if v < 0:
                raise self.err("UnderflowBaka", f"{fmt(a)} − {fmt(b)} descend sous zéro !")
        elif node.op == "*=":
            v = a * b
        else:
            if b == 0:
                raise self.err("ZeroBaka", None)
            v = a // b
        self.chat.line(self.boss.full if self.boss else "club",
                       f"{node.target} {node.op} {fmt(b)} → {fmt(v)}", detail=True)
        self.put(t, v)

    def do_write(self, node):
        w = self.resolve("writer", node.actor)
        self.order(w, node.polite)
        if node.what[0] == "lit":
            v = node.what[1]
        else:
            src = self.lookup(node.what[1])
            v = self.get(src)
        text = fmt(v)
        if node.deco == "sparkles":
            text = f"✧ {text} ✧"
        elif node.deco == "nya":
            text = f"{text} nya~"
        elif node.deco == "kaomoji":
            text = f"{text} (◕‿◕)"
        if node.path:
            full = os.path.join(self.base_dir, node.path)
            try:
                with open(full, "a", encoding="utf-8") as f:
                    f.write(text + "\n")
            except OSError as e:
                raise self.err("FileBaka", f"Je n'arrive pas à écrire dans « {node.path} » ({e}).", w)
            return
        self.chat.output(w.full, text, node.newline)

    def do_keep(self, node):
        k = self.resolve("keeper")
        self.order(k, node.polite)
        k.shelf[node.label] = self.get(self.lookup(node.target))

    def do_forget(self, node):
        k = self.resolve("keeper")
        self.order(k, node.polite)
        if node.label not in k.shelf:
            raise self.err("ShelfBaka", f"« {node.label} » n'est pas sur mon étagère.", k)
        del k.shelf[node.label]

    def do_pack(self, node):
        p = self.lookup(node.packer)
        if not isinstance(p, Waifu) or p.cap != "packer":
            raise self.err("JobBaka", f"{node.packer} n'est pas une packer.")
        self.order(p, node.polite)
        v = self.operand(node.source)
        if v is None and node.source[0] == "ref":
            raise self.err("EmptyHandsBaka", f"{node.source[1]} n'a rien dans les mains.")
        if p.hands is None:
            p.hands = []
        if isinstance(p.hands, list):
            p.hands = p.hands + [v]
        elif isinstance(p.hands, str):
            p.hands = p.hands + fmt(v)
        else:
            raise self.err("TypeBaka", "Je ne peux pas emballer dans un nombre.", p)

    def do_convert(self, node):
        c = self.resolve("converter")
        self.order(c, node.polite)
        t = self.holder(node.target)
        v = self.get(t)
        if node.to == "text":
            nv = fmt(v)
        elif node.to == "list":
            nv = list(v) if isinstance(v, (str, list)) else [v]
        else:
            if isinstance(v, bool):
                nv = int(v)
            elif is_number(v):
                nv = v
            else:
                nv = looks_number(str(v).strip())
                if not is_number(nv):
                    raise self.err("TypeBaka", f"{fmt(v, True)} ne ressemble pas à un nombre.", c)
        self.clear(t)
        self.put(t, nv)

    def do_send(self, node):
        f = self.resolve("fetcher")
        self.order(f, node.polite)
        data = fmt(self.get(self.lookup(node.target))).encode("utf-8")
        try:
            urllib.request.urlopen(urllib.request.Request(node.url, data=data, method="POST"), timeout=10).close()
        except Exception as e:
            raise self.err("FileBaka", f"Je n'arrive pas à envoyer vers {node.url} ({e}).", f)

    def do_say(self, node):
        w = self.lookup(node.who)
        who = w.full if isinstance(w, Waifu) else node.who
        self.chat.line(who, node.words)
        if isinstance(w, Waifu) and "aimes quoi" in node.words.lower():
            self.chat.line(who, f"Hmm... quelque chose qui commence par « {w.likes[0]} »...")

    # --- le club -----------------------------------------------------------
    def targets(self, who):
        if who is None:
            return [w for w in self.waifus() if w.cap != "boss"]
        w = self.lookup(who)
        if not isinstance(w, Waifu):
            raise self.err("NobodyBaka", f"{who} n'est pas une membre du club.")
        return [w]

    def do_ohayo(self, node):
        for w in self.targets(node.who):
            w.awake = True
        if self.boss:
            self.chat.line(self.boss.full, "Ohayo minna ! (◕‿◕✿)" if node.who is None else f"Ohayo {node.who} !")

    def do_oyasumi(self, node):
        for w in self.targets(node.who):
            w.awake = False
        if self.boss:
            self.chat.line(self.boss.full, "Oyasumi minna~ ☾" if node.who is None else f"Oyasumi {node.who}~")

    def do_tea(self, node):
        w = self.targets(node.who)[0]
        self.order(w, True)
        self.chat.line(w.full, "Pause thé ~ ♨")

    def do_wait(self, node):
        pass  # tout s'exécute dans l'ordre : il n'y a jamais rien à attendre

    def do_affection(self, node):
        ws = self.targets(node.who)
        if self.boss:
            word = {"arigatou": "Arigatou", "sugoi": "Sugoi", "headpat": "*headpat*", "baka": "Baka"}[node.word]
            self.chat.line(self.boss.full, f"{word} {node.who or 'minna'} !")
        for w in ws:
            if node.word == "arigatou":
                delta = 3
            elif node.word == "sugoi":
                delta = 1 if self.line - w.last_sugoi <= 10 else 5
                w.last_sugoi = self.line
            elif node.word == "headpat":
                delta = 4 if w.has("tsundere") else 1 if w.has("kuudere") else 2
            else:
                delta = -20
            self.chat.line(w.full, lines.reaction(w, node.word))
            self.change_affection(w, delta)

    def do_gift(self, node):
        w = self.targets(node.who)[0]
        food = node.food.lower()
        delta = 10 if food == w.likes else -5 if food == w.hates else 1
        self.chat.line(w.full, f"{node.food.capitalize()} !!" if delta == 10
                       else "...je déteste ça." if delta < 0 else "Merci.")
        self.change_affection(w, delta)

    # --- contrôle ----------------------------------------------------------
    def do_if(self, node):
        for test, body in node.branches:
            if self.judge(test):
                self.block(body)
                return
        if node.otherwise is not None:
            self.block(node.otherwise)

    def loop(self, body):
        """Rend False si la boucle doit s'arrêter (break)."""
        try:
            self.block(body)
        except Break:
            return False
        except Next:
            pass
        return True

    def do_while(self, node):
        while self.judge(node.test):
            if not self.loop(node.body):
                break

    def do_until(self, node):
        while not self.judge(node.test):
            if not self.loop(node.body):
                break

    def do_repeat_until(self, node):
        while True:
            if not self.loop(node.body):
                break
            self.line = node.line
            if self.judge(node.test):
                break

    def do_times(self, node):
        for _ in range(node.count):
            if not self.loop(node.body):
                break

    def do_forever(self, node):
        while self.loop(node.body):
            pass

    def do_break(self, node):
        raise Break()

    def do_next(self, node):
        raise Next()

    def do_return(self, node):
        if not self.frames:
            raise self.err("OwoBaka", "return n'a de sens que dans un jutsu.")
        raise Return()

    def do_try(self, node):
        try:
            self.block(node.body)
        except Baka as e:
            for kind, body in node.catches:
                if kind is None or kind == e.kind:
                    self.chat.line(self.boss.full if self.boss else "club", f"Gomen ! ({e.kind})", detail=True)
                    self.block(body)
                    break
            else:
                raise
        finally:
            if node.final is not None:
                self.block(node.final)

    def do_call(self, node):
        jutsu = self.program.jutsu.get(node.name)
        if jutsu is None:
            raise self.err("NobodyBaka", f"Aucun jutsu ne s'appelle {node.name}.")
        if len(node.args) != len(jutsu.params):
            raise self.err("OwoBaka", f"{node.name} attend {len(jutsu.params)} waifus, pas {len(node.args)}.")
        if len(self.frames) >= 200:
            raise self.err("TiredBaka", "Trop de jutsu les uns dans les autres !")
        bound = {p: self.lookup(a) for p, a in zip(jutsu.params, node.args)}
        self.frames.append({"names": bound, "clones": []})
        self.chat.line(self.boss.full if self.boss else "club", f"{node.name} no jutsu !", detail=True)
        try:
            self.block(jutsu.body)
        except Return:
            pass
        finally:
            frame = self.frames.pop()
            for c in frame["clones"]:
                self.chat.line(c.full, "*poof* (un nuage de fumée)", detail=True)
            self.line = node.line

    def do_clone(self, node):
        w = Waifu(node.name, "chan", node.cap, clone=True)
        w.likes, w.hates = self.rng.sample(FOODS, 2)
        target = Row(node.name, [w], True) if node.growing else w
        if node.growing and node.cap != "counter":
            raise self.err("JobBaka", "Seules les compteuses forment une rangée.")
        if self.frames:
            self.frames[-1]["names"][node.name] = target
            self.frames[-1]["clones"].append(w)
        else:
            self.globals[node.name] = target
        self.chat.line(w.full, "Kage bunshin ! Me voilà.", detail=True)

    def do_poof(self, node):
        t = self.lookup(node.name)
        ws = t.members if isinstance(t, Row) else [t]
        if not all(getattr(w, "clone", False) for w in ws):
            raise self.err("JobBaka", f"{node.name} n'est pas un clone : on ne la fait pas disparaître.")
        if self.frames and node.name in self.frames[-1]["names"]:
            del self.frames[-1]["names"][node.name]
        else:
            self.globals.pop(node.name, None)
        for w in ws:
            w.gone = True
        self.chat.line(ws[-1].full, "*poof*", detail=True)

    def do_start(self, node):
        plan = self.program.plans.get(node.name)
        if plan is None:
            raise self.err("NobodyBaka", f"{node.name} n'a pas de plan.")
        boss = self.lookup(node.name)
        boss.awake = True
        self.chat.line(boss.full, "Hajime !")
        saved, self.boss = self.boss, boss
        try:
            self.block(plan.body)
        finally:
            self.boss = saved
            self.line = node.line
