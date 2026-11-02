"""Le chat de groupe : ce que les membres disent pendant l'exécution."""

import sys


class Chat:
    """quiet : seule la vraie sortie (writer). chatty : chaque doigt et chaque verdict."""

    def __init__(self, quiet=False, chatty=False, out=None):
        self.quiet = quiet
        self.chatty = chatty
        self.out = out or sys.stdout
        self.pending_newline = False

    def _print(self, text):
        if self.pending_newline:
            self.out.write("\n")
            self.pending_newline = False
        self.out.write(text + "\n")

    def line(self, who, text, detail=False):
        if self.quiet or (detail and not self.chatty):
            return
        self._print(f"{who:<12}: {text}")

    def output(self, who, text, newline=True):
        if not self.quiet:
            self._print(f"{who:<12}: {text}")
            return
        self.out.write(text + ("\n" if newline else ""))
        self.pending_newline = False

    def banner(self, text):
        if not self.quiet:
            self._print(f"━━━━━━━━ ✿ {text} ✿ ━━━━━━━━")

    def prompt(self, value):
        if not self.quiet:
            self._print(f"> {value}")


def rude(w):
    if w.affection < 20:
        return "...encore un ordre sans onegai. Je vais finir par partir."
    if w.has("tsundere"):
        return "Hmph ! Tu pourrais dire onegai, baka."
    return "Hmph... et la politesse ?"


def fingers(w):
    n = w.hands
    if w.has("explosive"):
        return f"{n} doigts ! EXPLOSION !!! (ﾉ◕ヮ◕)ﾉ*:･ﾟ✧"
    if w.has("lazy"):
        return f"{n}... *bâille*"
    return f"{n} doigt{'s' if n > 1 else ''}."


def carry(w, left):
    if w.has("explosive"):
        return f"10 doigts ! {left.full}, prends un paquet ! EXPLOSION !!!"
    if w.has("tsundere"):
        return f"10. {left.full}, prends ce paquet. C'est pas pour toi que je le fais."
    return f"10 doigts ! {left.full}, prends un paquet !"


def verdict(left, right, v):
    return {
        "same": f"{left} et {right} : PAREIL !",
        "bigger": f"{left} est plus grand que {right}.",
        "smaller": f"{left} est plus petit que {right}.",
        "different": f"{left} et {right} : pas pareil.",
    }[v]


def read(w, value):
    if w.has("shy"):
        return f"...j-j'ai lu {value}... (⁄ ⁄•⁄ω⁄•⁄ ⁄)"
    return f"J'ai lu {value} !"


def reaction(w, word):
    if word == "baka":
        return "...(╥﹏╥)"
    if word == "headpat":
        if w.has("tsundere"):
            return "N-ne me touche pas ! ...mais merci."
        if w.has("kuudere"):
            return "...d'accord."
        return "(´｡• ᵕ •｡`)"
    if word == "sugoi":
        return "V-vraiment ? (〃▽〃)"
    if w.has("tsundere"):
        return "C-ce n'est pas comme si ça me faisait plaisir !"
    return "Hehe~"
