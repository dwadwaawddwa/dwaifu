"""Les erreurs Baka de dwaifu."""

# Réplique par défaut de chaque erreur (la membre concernée la dit).
DEFAULT_LINES = {
    "OwoBaka": "Owo ? Je ne comprends pas cette ligne.",
    "NobodyBaka": "C'est qui, ça ?",
    "NoBossBaka": "Il n'y a pas de présidente dans ce club !",
    "HonorificBaka": "Ara ara~ une -chan ne donne pas d'ordres.",
    "NoSuffixBaka": "C'est qui, ça ? Il manque -sama ou -chan.",
    "WhoBaka": "Qui doit le faire ?",
    "JobBaka": "Ce n'est pas mon travail !",
    "SleepyBaka": "Zzz... je dors encore...",
    "FullHandsBaka": "J'ai déjà les mains pleines !",
    "EmptyHandsBaka": "Je n'ai rien dans les mains !",
    "FingersBaka": "Je n'ai que dix doigts !",
    "OverflowBaka": "Je n'ai plus de doigts !",
    "UnderflowBaka": "Je suis déjà à zéro !",
    "TypeBaka": "Ça ne se fait pas avec ça !",
    "ZeroBaka": "On ne partage pas en zéro paquet !",
    "ShelfBaka": "Ce n'est pas sur mon étagère.",
    "FileBaka": "Je ne trouve pas ce fichier...",
    "LonelyBaka": "Senpai ne répond plus... je vais attendre pour toujours ?",
    "TiredBaka": "Le club est épuisé...",
    "HeartbreakBaka": "Je quitte le club. (╥﹏╥)",
}

# Erreurs trouvées avant le départ : on ne peut pas les attraper.
STATIC = {"OwoBaka", "NobodyBaka", "NoBossBaka", "HonorificBaka", "NoSuffixBaka"}


class Baka(Exception):
    def __init__(self, kind, message=None, line=None, waifu=None):
        self.kind = kind
        self.message = message or DEFAULT_LINES.get(kind, "")
        self.line = line
        self.waifu = waifu
        super().__init__(f"{kind}: {self.message}")

    def describe(self):
        where = f" ligne {self.line}" if self.line else ""
        who = f" — {self.waifu}" if self.waifu else ""
        return f"(╥﹏╥) {self.kind}{where}{who} : « {self.message} »"
