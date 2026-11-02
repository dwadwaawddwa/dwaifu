"""La commande kawaii : run, check, explain."""

import argparse
import random
import sys

from .chat import Chat
from .errors import Baka, STATIC
from .explain import explain
from .program import Program, check, rank
from .runtime import Interpreter


def make_reader(chat):
    def read_line():
        line = sys.stdin.readline()
        if line == "":
            return None
        line = line.rstrip("\r\n")
        if not sys.stdin.isatty():
            chat.prompt(line)
        return line
    return read_line


def load(path):
    program = Program(path)
    warnings = check(program)
    return program, warnings


def cmd_run(args):
    chat = Chat(quiet=args.quiet, chatty=args.chatty)
    try:
        program, warnings = load(args.file)
    except Baka as e:
        print(e.describe(), file=sys.stderr)
        return 2
    for w in warnings:
        print(w, file=sys.stderr)
    seed = args.seed if args.seed is not None else random.randrange(1_000_000)
    interp = Interpreter(program, chat, random.Random(seed), make_reader(chat),
                         program.base_dir, max_steps=args.max_steps)
    chat.banner("LE CLUB EST OUVERT")
    code = 0
    try:
        interp.run()
    except Baka as e:
        interp.stats["uncaught"] += 1
        if chat.pending_newline:
            print()
        print(e.describe(), file=sys.stderr)
        code = 1
    grade, detail = rank(program, interp.stats)
    chat.banner(f"RANG KAWAII : {grade}")
    if not args.quiet:
        print(f"{detail} · seed {seed}")
    return code


def cmd_check(args):
    try:
        program, warnings = load(args.file)
    except Baka as e:
        print(e.describe(), file=sys.stderr)
        return 2
    for w in warnings:
        print(w)
    print(f"✿ {args.file} : tout va bien, le club peut ouvrir.")
    if args.rank:
        grade, detail = rank(program)
        print(f"Rang kawaii : {grade} ({detail})")
    return 0


def cmd_explain(args):
    try:
        program, _ = load(args.file)
    except Baka as e:
        print(e.describe(), file=sys.stderr)
        return 2
    print(explain(program))
    return 0


def main(argv=None):
    for stream in (sys.stdout, sys.stderr, sys.stdin):
        try:
            stream.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass
    p = argparse.ArgumentParser(prog="kawaii", description="L'interpréteur du langage dwaifu (.uwu)")
    sub = p.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run", help="exécuter un programme")
    r.add_argument("file")
    r.add_argument("--quiet", action="store_true", help="seulement la vraie sortie du programme")
    r.add_argument("--chatty", action="store_true", help="chaque doigt et chaque verdict dans le chat")
    r.add_argument("--seed", type=int, help="fixe le hasard")
    r.add_argument("--max-steps", type=int, default=2_000_000, help="limite avant TiredBaka")
    c = sub.add_parser("check", help="vérifier sans exécuter")
    c.add_argument("file")
    c.add_argument("--rank", action="store_true", help="afficher le rang kawaii")
    e = sub.add_parser("explain", help="montrer les phrases V2 de chaque ligne")
    e.add_argument("file")
    args = p.parse_args(argv)
    return {"run": cmd_run, "check": cmd_check, "explain": cmd_explain}[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
