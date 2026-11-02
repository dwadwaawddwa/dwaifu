"""kawaii explain : chaque ligne V3 et les phrases V2 qu'elle devient."""

V2_CAP = {"boss": "bossing", "reader": "reading", "writer": "writing", "counter": "counting",
          "judge": "comparing", "keeper": "keeping", "packer": "packing",
          "converter": "converting", "guesser": "guessing", "fetcher": "fetching"}
VERDICT = {"==": "same", "!=": "not same", ">": "bigger", "<": "smaller",
           ">=": "not smaller", "<=": "not bigger", "empty": "empty", "not empty": "not empty"}


class Explainer:
    def __init__(self, program):
        self.program = program
        self.out = []

    def who(self, cap, explicit=None):
        if explicit:
            return explicit
        found = [m["name"] for m in self.program.members if m["cap"] == cap]
        return found[0] if len(found) == 1 else f"<{cap} ?>"

    def lit(self, v):
        if v[0] == "ref":
            return v[1]
        from .runtime import fmt
        return fmt(v[1], inner=True)

    def test(self, t):
        j = self.who("judge", t["judge"])
        if t["op"] in ("empty", "not empty"):
            pre = [f"{self.lit(t['left'])} show it to {j}", f"{j} compare it with empty"]
        elif t["right"][0] == "ref":
            pre = [f"{self.lit(t['left'])} show it to {j}", f"{t['right'][1]} show it to {j}", f"{j} compare"]
        else:
            pre = [f"{self.lit(t['left'])} show it to {j}", f"{j} compare it with {self.lit(t['right'])}"]
        return pre, f"{j} says {VERDICT[t['op']]}"

    def emit(self, depth, v3, v2):
        pad = "    " * depth
        self.out.append((pad + v3 if v3 else "", [pad + p for p in v2]))

    def body(self, nodes, depth):
        for n in nodes:
            self.node(n, depth)

    def node(self, n, d):
        k = n.kind
        t = getattr(n, "target", None)
        if k == "club":
            for m in n.members:
                self.emit(d, f"{m['name']}-{m['suffix']} : {m['cap']}",
                          [f"born waifu named {m['name']}", f"{m['name']} is made for {V2_CAP[m['cap']]}"]
                          + [f"{m['name']} personality is {p}" for p in m["pers"]])
        elif k == "row":
            self.emit(d, n.text, [f"line up {', '.join(n.members)} as number {n.name}"
                                  + (" that grows" if n.growing else "")])
        elif k == "alias":
            self.emit(d, n.text, [f"(surnom : {n.name} veut dire {n.member})"])
        elif k == "assign":
            s = n.source
            pre = [f"{t} drop it"]
            if s[0] == "lit":
                v2 = pre + [f"{t} take {self.lit(s)}"]
            elif s[0] == "move":
                v2 = pre + [f"{s[1]} give it to {t}"]
            elif s[0] == "copy":
                k_ = self.who("keeper")
                v2 = pre + [f"{s[1]} give it to {k_}", f"{k_} keep it as copie",
                            f"{k_} bring copie to {s[1]}", f"{k_} bring copie to {t}", f"{k_} forget copie"]
            elif s[0] in ("read", "read_file", "read_all"):
                r = self.who("reader")
                what = {"read": "read", "read_file": f'read from "{s[1]}"',
                        "read_all": f'read everything from "{s[1]}"'}[s[0]]
                v2 = [f"{r} drop it", f"{r} {what}"] + ([] if r == t else pre + [f"{r} give it to {t}"])
            elif s[0] == "guess":
                g = self.who("guesser")
                v2 = [f"{g} drop it", f"{g} guess between {s[1]} and {s[2]}"] + \
                     ([] if g == t else pre + [f"{g} give it to {t}"])
            elif s[0] == "recall":
                v2 = pre + [f"{self.who('keeper')} bring {s[1]} to {t}"]
            elif s[0] in ("first", "last"):
                v2 = pre + [f"{s[1]} unpack {'last ' if s[0] == 'last' else ''}to {t}"]
            else:
                f = self.who("fetcher")
                v2 = [f'{f} fetch "{s[1]}"'] + pre + [f"{f} give it to {t}"]
            self.emit(d, n.text, v2)
        elif k in ("inc", "dec"):
            self.emit(d, n.text, [f"{t} count {'up' if k == 'inc' else 'down'}"])
        elif k == "op":
            name = {"+=": "add", "-=": "subtract", "*=": "multiply", "/=": "divide"}[n.op]
            src = self.lit(n.source)
            self.emit(d, n.text, ["hire a counting waifu as T", f"(T reçoit une copie de {src})",
                                  f"do {name} with {t}, T", "fire T"])
        elif k == "write":
            w = self.who("writer", n.actor)
            deco = {"sparkles": " with sparkles", "nya": " nya", "kaomoji": " in kaomoji"}.get(n.deco, "")
            tail = " without newline" if not n.newline else f' to "{n.path}"' if n.path else ""
            if n.what[0] == "ref" and n.what[1] != w:
                v2 = [f"{n.what[1]} show it to {w}", f"{w} write what she sees{deco}{tail}"]
            elif n.what[0] == "ref":
                v2 = [f"{w} write it{deco}{tail}"]
            else:
                v2 = [f"{w} write {self.lit(n.what)}{deco}{tail}"]
            self.emit(d, n.text, v2)
        elif k == "drop":
            self.emit(d, n.text, [f"{t} drop it"])
        elif k == "keep":
            k_ = self.who("keeper")
            self.emit(d, n.text, [f"{t} show it to {k_}", f"{k_} keep it as {n.label}"])
        elif k == "forget":
            self.emit(d, n.text, [f"{self.who('keeper')} forget {n.label}"])
        elif k == "pack":
            self.emit(d, n.text, [f"{self.lit(n.source)} show it to {n.packer}", f"{n.packer} pack it"])
        elif k == "convert":
            c = self.who("converter")
            self.emit(d, n.text, [f"{t} give it to {c}", f"{c} turn it into {n.to}", f"{c} give it to {t}"])
        elif k == "send":
            f = self.who("fetcher")
            self.emit(d, n.text, [f"{t} show it to {f}", f'{f} send it to "{n.url}"'])
        elif k == "say":
            self.emit(d, n.text, [f'{n.who} tell everyone "{n.words}"'])
        elif k in ("ohayo", "oyasumi"):
            verb = "wake up" if k == "ohayo" else "go sleep"
            self.emit(d, n.text, [f"{verb} everyone" if n.who is None else f"{n.who} {verb}"])
        elif k == "tea":
            self.emit(d, n.text, [f"{n.who} take a break"])
        elif k in ("if",):
            for i, (test, body) in enumerate(n.branches):
                pre, cond = self.test(test)
                head = n.text if i == 0 else "else if …"
                self.emit(d, head, pre + [("if " if i == 0 else "ara ara if ") + cond + ":"])
                self.body(body, d + 1)
            if n.otherwise is not None:
                self.emit(d, "else:", ["ara ara:"])
                self.body(n.otherwise, d + 1)
            self.emit(d, "desu", ["end"])
        elif k in ("while", "until"):
            pre, cond = self.test(n.test)
            self.emit(d, n.text, pre + [f"repeat {k} {cond}:"])
            self.body(n.body, d + 1)
            self.emit(d + 1, "", ["(et on recompare à chaque tour)"] + pre)
            self.emit(d, "desu", ["end"])
        elif k == "repeat_until":
            pre, cond = self.test(n.test)
            self.emit(d, n.text, ["repeat forever:"])
            self.body(n.body, d + 1)
            self.emit(d + 1, f"until … (fin du bloc)", pre + [f"if {cond}:", "    stop repeating", "end"])
            self.emit(d, "", ["end"])
        elif k == "times":
            self.emit(d, n.text, [f"repeat {n.count} times:"])
            self.body(n.body, d + 1)
            self.emit(d, "desu", ["end"])
        elif k == "forever":
            self.emit(d, n.text, ["repeat forever:"])
            self.body(n.body, d + 1)
            self.emit(d, "desu", ["end"])
        elif k in ("break", "next", "return"):
            self.emit(d, n.text, [{"break": "stop repeating", "next": "next round", "return": "stop the recipe"}[k]])
        elif k == "jutsu":
            self.emit(d, n.text, [f"recipe {n.name} with {', '.join(n.params)}:"])
            self.body(n.body, d + 1)
            self.emit(d, "desu", ["end"])
        elif k == "call":
            self.emit(d, n.text, [f"do {n.name} with {', '.join(n.args)}"])
        elif k == "clone":
            self.emit(d, n.text, [f"hire a {V2_CAP[n.cap]} waifu as {n.name}"])
        elif k == "poof":
            self.emit(d, n.text, [f"fire {n.name}"])
        elif k == "try":
            self.emit(d, "try:", ["onegai:"])
            self.body(n.body, d + 1)
            for kind, body in n.catches:
                self.emit(d, f"catch {kind or ''}:", [f"gomen if {kind}:" if kind else "gomen:"])
                self.body(body, d + 1)
            if n.final is not None:
                self.emit(d, "finally:", ["daijoubu:"])
                self.body(n.final, d + 1)
            self.emit(d, "desu", ["end"])
        elif k == "plan":
            self.emit(d, n.text, [f"{n.boss}'s plan:"])
            self.body(n.body, d + 1)
            self.emit(d, "desu", ["end"])
        elif k == "start":
            self.emit(d, n.text, [f"start {n.name}"])
        elif k == "wait":
            self.emit(d, n.text, [f"wait for {'everyone' if n.name.lower() == 'minna' else n.name}"])
        elif k == "gacha":
            self.emit(d, n.text, [f'gacha {"team from " if n.club else ""}"{n.path}"'])
        else:
            self.emit(d, n.text, ["(politesse : change l'affection, pas le calcul)"])


def explain(program):
    ex = Explainer(program)
    ex.body(program.body, 0)
    width = min(40, max(len(v3) for v3, _ in ex.out) + 2) if ex.out else 0
    rows = []
    for v3, v2 in ex.out:
        for i, phrase in enumerate(v2):
            left = v3 if i == 0 else ""
            arrow = "→" if i == 0 and v3 else " "
            rows.append(f"{left:<{width}}{arrow}  {phrase}".rstrip())
    return "\n".join(rows)
