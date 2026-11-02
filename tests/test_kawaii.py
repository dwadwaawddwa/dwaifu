import io
import os
import random
import shutil
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from kawaii.chat import Chat  # noqa: E402
from kawaii.errors import Baka  # noqa: E402
from kawaii.explain import explain  # noqa: E402
from kawaii.program import Program, check, rank  # noqa: E402
from kawaii.runtime import Interpreter  # noqa: E402

CLUB = """club:
    Yuki-sama   : boss
    Sora-chan   : counter
    Sakura-chan : counter
    Ren-chan    : counter
    Rin-chan    : counter
    Nana-chan   : judge
    Kiko-chan   : keeper
    Pia-chan    : packer
    Coco-chan   : converter
    Mio-chan    : writer
    Hikari-chan : reader
desu
ohayo
"""


class Run:
    def __init__(self):
        self.dir = tempfile.mkdtemp()

    def __call__(self, source, stdin="", seed=1, club=True, max_steps=200_000):
        path = os.path.join(self.dir, "prog.uwu")
        with open(path, "w", encoding="utf-8") as f:
            f.write((CLUB if club else "") + source)
        program = Program(path)
        check(program)
        out = io.StringIO()
        lines = iter(stdin.splitlines())
        interp = Interpreter(program, Chat(quiet=True, out=out), random.Random(seed),
                             lambda: next(lines, None), program.base_dir, max_steps=max_steps)
        interp.run()
        return out.getvalue()


class KawaiiTest(unittest.TestCase):
    def setUp(self):
        self.run = Run()

    def tearDown(self):
        shutil.rmtree(self.run.dir, ignore_errors=True)

    def baka(self, kind, source, **kw):
        with self.assertRaises(Baka) as ctx:
            self.run(source, **kw)
        self.assertEqual(ctx.exception.kind, kind, ctx.exception.describe())
        return ctx.exception

    # --- les exemples -----------------------------------------------------
    def example(self, name, stdin, seed=1):
        path = os.path.join(ROOT, "examples", name)
        program = Program(path)
        check(program)
        out = io.StringIO()
        lines = iter(stdin.splitlines())
        Interpreter(program, Chat(quiet=True, out=out), random.Random(seed),
                    lambda: next(lines, None), program.base_dir).run()
        return out.getvalue()

    def test_addition_example(self):
        self.assertEqual(self.example("addition.uwu", "12\n30\n"),
                         "Donne-moi deux nombres, Senpai !\n✧ 42 ✧\n")

    def test_guess_example_finds_the_secret(self):
        out = self.example("devine.uwu", "\n".join(str(i) for i in range(1, 101)), seed=3)
        self.assertTrue(out.endswith("Bravo Senpai ! ♡\n"))
        self.assertNotIn("Trop grand", out)

    def test_bonjour(self):
        self.assertEqual(self.example("bonjour.uwu", ""), "Konnichiwa, Senpai !\n")

    # --- les mains et les doigts ----------------------------------------
    def test_row_take_and_write(self):
        self.assertEqual(self.run("n = Sora ♡ Sakura\nn ← 42\nwrite n\n"), "42\n")

    def test_row_carries_and_borrows(self):
        out = self.run("n = Sora ♡ Sakura\nn ← 9\nn++\nwrite n\nn--\nn--\nwrite n\n")
        self.assertEqual(out, "10\n8\n")

    def test_row_too_small(self):
        self.baka("FingersBaka", "n = Sora ♡ Sakura\nn ← 150\n")

    def test_growing_row(self):
        out = self.run("n = Sora ♡ ...\nn ← 999\nn++\nwrite n\n")
        self.assertEqual(out, "1000\n")

    def test_single_counter_limits(self):
        self.baka("FingersBaka", "Sora ← 11\n")
        self.baka("OverflowBaka", "Sora ← 10\nSora++\n")
        self.baka("UnderflowBaka", "Sora ← 0\nSora--\n")

    def test_move_empties_the_giver(self):
        self.baka("EmptyHandsBaka", 'Mio ← "salut"\nRin ← 3\nKiko ← Mio\nwrite Mio\n')

    def test_copy_keeps_both(self):
        out = self.run("a = Sora ♡ Sakura\nb = Ren ♡ Rin\na ← 12\nb ← copy a\nwrite a\nwrite b\n")
        self.assertEqual(out, "12\n12\n")

    def test_ops_leave_source_untouched(self):
        out = self.run("a = Sora ♡ Sakura\nb = Ren ♡ Rin\na ← 7\nb ← 6\na *= b\nwrite a\nwrite b\n"
                       "a /= 4\nwrite a\na -= b\nwrite a\n")
        self.assertEqual(out, "42\n6\n10\n4\n")

    def test_zero_and_negative(self):
        self.baka("ZeroBaka", "a = Sora ♡ Sakura\na ← 5\na /= 0\n")
        self.baka("UnderflowBaka", "a = Sora ♡ Sakura\na ← 5\na -= 6\n")

    def test_count_on_text(self):
        self.baka("TypeBaka", 'Sora ← "abc"\nSora++\n')

    def test_boss_has_no_hands(self):
        self.baka("JobBaka", "Yuki ← 3\n")

    # --- le club ---------------------------------------------------------
    def test_sleeping_member(self):
        self.baka("SleepyBaka", "oyasumi Mio\nwrite 1\n")

    def test_honorifics(self):
        self.baka("HonorificBaka", "club:\n    Yuki-chan : boss\ndesu\n", club=False)
        self.baka("HonorificBaka", "club:\n    Yuki-sama : boss\n    Mio-sama : writer\ndesu\n", club=False)
        self.baka("NoSuffixBaka", "club:\n    Yuki-sama : boss\n    Mio : writer\ndesu\n", club=False)
        self.baka("NoBossBaka", "club:\n    Mio-chan : writer\ndesu\n", club=False)

    def test_unknown_name(self):
        self.baka("NobodyBaka", "Personne++\n")

    def test_who_with_two_writers(self):
        src = "club:\n    Yuki-sama : boss\n    Mio-chan : writer\n    Aki-chan : writer\ndesu\nohayo\n"
        self.baka("WhoBaka", src + "write 1\n", club=False)
        self.assertEqual(self.run(src + "Aki write 1\n", club=False), "1\n")

    def test_no_judge(self):
        src = "club:\n    Yuki-sama : boss\n    Sora-chan : counter\ndesu\nohayo\n"
        self.baka("JobBaka", src + "if Sora == 0:\ndesu\n", club=False)

    def test_baka_breaks_hearts(self):
        e = self.baka("HeartbreakBaka", "baka Mio\nbaka Mio\nbaka Mio\n")
        self.assertEqual(e.waifu, "Mio-chan")

    def test_rudeness_costs_affection(self):
        self.baka("HeartbreakBaka", "repeat 60 times:\n    write 1\ndesu\n")
        self.run("repeat 60 times:\n    write 1 onegai\ndesu\n")

    # --- contrôle --------------------------------------------------------
    def test_if_chain_and_aliases(self):
        src = ("Sora ← 7\n"
               "nani? Sora > 9:\n    write \"grand\"\n"
               "ehh? Sora == 7:\n    write \"sept\"\n"
               "ara ara:\n    write \"petit\"\nend\n")
        self.assertEqual(self.run(src), "sept\n")

    def test_loops_break_next(self):
        src = ("n = Sora ♡ Sakura\nn ← 0\n"
               "forever:\n    n++\n    if n == 3:\n        next\n    desu\n"
               "    if n > 5:\n        break\n    desu\n    write n\ndesu\n")
        self.assertEqual(self.run(src), "1\n2\n4\n5\n")

    def test_repeat_until_and_ganbatte(self):
        src = ("Sora ← 0\nrepeat:\n    Sora++\nuntil Sora >= 3\nwrite Sora\n"
               "ganbatte 2 times:\n    write \"!\"\ndesu\n")
        self.assertEqual(self.run(src), "3\n!\n!\n")

    def test_endless_loop_gets_tired(self):
        self.baka("TiredBaka", "forever:\n    Sora ← 1 onegai\ndesu\n", max_steps=500)

    def test_try_catch_finally(self):
        src = ("try:\n    Sora ← 10\n    Sora++\n"
               "catch OverflowBaka:\n    write \"trop\"\n"
               "finally:\n    write \"fin\"\ndesu\n")
        self.assertEqual(self.run(src), "trop\nfin\n")

    def test_uncaught_kind_passes_through(self):
        self.baka("OverflowBaka", "try:\n    Sora ← 10\n    Sora++\ncatch TypeBaka:\n    write 0\ndesu\n")

    def test_kawaii_try_aliases(self):
        src = ("kami-sama onegai:\n    Sora ← 11\ngomen:\n    write \"gomen\"\n"
               "daijoubu:\n    write \"daijoubu\"\ndesu\n")
        self.assertEqual(self.run(src), "gomen\ndaijoubu\n")

    # --- jutsu et clones -------------------------------------------------
    def test_jutsu_and_recursion(self):
        src = ("jutsu countdown(N):\n    if N == 0:\n        return\n    desu\n"
               "    write N\n    N--\n    countdown(N)\ndesu\n"
               "n = Sora ♡ Sakura\nn ← 3\ncountdown(n)\nwrite n\n")
        self.assertEqual(self.run(src), "3\n2\n1\n0\n")

    def test_stdlib_maths(self):
        src = ('gacha "maths.uwu"\n'
               "a = Sora ♡ Sakura\nb = Ren ♡ Rin\na ← 6\nb ← 7\nmultiply(a, b)\nwrite a\n"
               "b ← 5\ncount = Kiko\nadd no jutsu(a, b)\nwrite a\nwrite b\n")
        self.assertEqual(self.run(src), "42\n47\n0\n")

    def test_stdlib_divide(self):
        src = ('gacha "maths.uwu"\n'
               "club:\n    Q1-chan : counter\n    Q2-chan : counter\ndesu\nohayo\n"
               "a = Sora ♡ Sakura\nb = Ren ♡ Rin\nq = Q1 ♡ Q2\na ← 47\nb ← 5\ndivide(a, b, q)\n"
               "write q\nwrite a\nwrite b\n")
        self.assertEqual(self.run(src), "9\n2\n5\n")

    def test_clone_disappears_after_jutsu(self):
        src = ("jutsu f(A):\n    clone T: counter\n    T ← 4\n    A ← T\ndesu\n"
               "f(Sora)\nwrite Sora\nwrite T\n")
        self.baka("NobodyBaka", src)

    # --- étagère, paquets, conversion, fichiers -------------------------
    def test_keeper_and_packer(self):
        src = ("Sora ← 4\nkeep Sora as x\nSora ← 9\nSora ← recall x\nwrite Sora\n"
               "pack 1 into Pia\npack \"deux\" into Pia\nwrite Pia\n"
               "Mio ← first of Pia\nwrite Mio\nwrite Pia\n")
        self.assertEqual(self.run(src), '4\n[1, "deux"]\n1\n["deux"]\n')
        self.baka("ShelfBaka", "Sora ← recall rien\n")

    def test_convert(self):
        src = 'Mio ← "41"\nconvert Mio to number\nSora ← 0\nRin ← 3\nwrite Mio\nconvert Mio to list\nwrite Mio\n'
        self.assertEqual(self.run(src), "41\n[41]\n")
        self.baka("TypeBaka", 'Mio ← "abc"\nconvert Mio to number\n')

    def test_read_input_and_files(self):
        with open(os.path.join(self.run.dir, "notes.txt"), "w", encoding="utf-8") as f:
            f.write("5\nbonjour\n")
        src = ('Hikari ← read from "notes.txt"\nwrite Hikari\nHikari ← read from "notes.txt"\nwrite Hikari\n'
               'Hikari ← read from "notes.txt"\nif Hikari is empty:\n    write "fin"\ndesu\n'
               'Mio ← "écrit"\nwrite Mio to "out.txt"\n')
        self.assertEqual(self.run(src), "5\nbonjour\nfin\n")
        with open(os.path.join(self.run.dir, "out.txt"), encoding="utf-8") as f:
            self.assertEqual(f.read(), "écrit\n")
        self.baka("FileBaka", 'Hikari ← read from "absent.txt"\n')
        self.baka("LonelyBaka", "Hikari ← read\n")

    def test_decorations(self):
        self.assertEqual(self.run("Sora ← 4\nwrite Sora ✧\nwrite Sora nya\nwrite Sora (◕‿◕)\n"),
                         "✧ 4 ✧\n4 nya~\n4 (◕‿◕)\n")

    def test_plan(self):
        src = ("club:\n    Aya-sama : boss\ndesu\n"
               "plan Aya-sama:\n    write \"plan d'Aya\"\ndesu\nstart Aya\nwait Aya\n")
        self.assertEqual(self.run(src), "plan d'Aya\n")

    # --- avant le départ --------------------------------------------------
    def test_parse_errors(self):
        self.baka("OwoBaka", "if Sora == 0:\n    write 1\n")
        self.baka("OwoBaka", "Sora fait des trucs\n")
        self.baka("OwoBaka", 'write "pas fermé\n')
        self.baka("OwoBaka", "club:\n    Yuki-sama : chef\ndesu\n", club=False)

    def test_comments_are_ignored(self):
        src = ("<333\n  plusieurs lignes\n333>\nwrite 1 <3 un cœur <3\n"
               "write 2 ✿ fleur ✿\nwrite \"<3 dans un texte\" ^_^ sourire ^_^\n(╯°□°)╯ TODO\n")
        self.assertEqual(self.run(src), "1\n2\n<3 dans un texte\n")

    def test_explain_and_rank(self):
        path = os.path.join(ROOT, "examples", "addition.uwu")
        program = Program(path)
        text = explain(program)
        self.assertIn("left count up", text)
        self.assertIn("Nana compare it with 0", text)
        grade, _ = rank(program)
        self.assertIn(grade, ("S", "SS"))


if __name__ == "__main__":
    unittest.main()
