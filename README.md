# dwaifu ✿

Un langage de programmation où chaque variable est une waifu : elle a une capacité,
une personnalité, ne tient qu'une chose dans les mains et compte sur ses dix doigts.
La V3 s'écrit comme du pseudo-code. Les fichiers portent l'extension **`.uwu`**.

```
club:
    Yuki-sama   : boss
    Hikari-chan : reader, shy
    Sora-chan   : counter
    Sakura-chan : counter, explosive
    Ren-chan    : counter
    Rin-chan    : counter, tsundere
    Nana-chan   : judge
    Mio-chan    : writer
desu

left  = Sora ♡ Sakura                <3 dizaines ♡ unités <3
right = Ren ♡ Rin

ohayo
left  ← read onegai
right ← read onegai

until right == 0:
    left++  onegai
    right-- onegai
desu

write left ✧ onegai
arigatou minna
oyasumi
```

## Lancer un programme

Il faut Python 3.10 ou plus, rien d'autre à installer. Depuis le dossier du dépôt :

```bat
kawaii run examples\addition.uwu            :: avec le chat du club
kawaii run examples\addition.uwu --quiet    :: seulement la vraie sortie
kawaii run examples\devine.uwu --seed 42    :: hasard fixé
kawaii run prog.uwu --chatty                :: chaque doigt et chaque verdict
kawaii check prog.uwu --rank                :: vérifier sans lancer + rang kawaii
kawaii explain prog.uwu                     :: chaque ligne V3 et ses phrases V2
```

Ailleurs que sur Windows : `python -m kawaii run …` depuis le dossier du dépôt.
Les tests : `python -m unittest discover tests`.

Ce que l'interpréteur 0.1 ne fait pas encore :

- les lignes s'exécutent une par une, sans les tours simultanés de la V2 : `start Aya` joue
  le plan d'Aya jusqu'au bout puis revient, et `wait` ne fait rien ;
- les phrases V2 (`Sakura count up`…) ne sont pas encore acceptées dans un `.uwu` ;
- l'énergie n'est pas modélisée : `TiredBaka` sert seulement à arrêter une boucle sans fin
  (2 millions d'instructions, `--max-steps` pour changer) ;
- `+=`, `-=`, `*=`, `/=` calculent directement, avec les mêmes résultats et erreurs que les
  jutsu de `maths.uwu` ; diviser par 0 donne `ZeroBaka`.

Attention : chaque ordre sans `onegai` coûte 1 point d'affection (sur 50 au départ).
Une boucle impolie finit donc en `HeartbreakBaka`. C'est voulu.

## Le dépôt

| Dossier | Contenu |
| --- | --- |
| `kawaii/` | L'interpréteur : lexer, parser, runtime, chat, explain, CLI |
| `tests/` | 40 tests (`python -m unittest discover tests`) |
| `examples/` | `bonjour.uwu`, `addition.uwu`, `devine.uwu` |
| `stdlib/` | `maths.uwu` : `add`, `subtract`, `multiply`, `divide` écrits en dwaifu |
| `vscode-dwaifu/` | Extension VS Code : `.uwu` reconnu et coloré |
| `docs/GITHUB.md` | Comment GitHub reconnaît (ou pas encore) dwaifu |

La spécification complète (V2 et V3) est dans le doc de design du langage.

## Coloration dans VS Code

Copier le dossier `vscode-dwaifu` dans `%USERPROFILE%\.vscode\extensions\`, puis
redémarrer VS Code. Les `.uwu` s'ouvrent alors en langage « dwaifu ».

## Sur GitHub

GitHub n'affiche le nom d'un langage qu'une fois celui-ci ajouté à
[Linguist](https://github.com/github-linguist/linguist). D'ici là, `.gitattributes`
colore les `.uwu` comme du Python. Détails et marche à suivre : [docs/GITHUB.md](docs/GITHUB.md).

## Licence

MIT
