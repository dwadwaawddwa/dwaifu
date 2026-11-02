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

## Le dépôt

| Dossier | Contenu |
| --- | --- |
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
