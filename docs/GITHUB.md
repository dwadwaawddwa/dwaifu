# dwaifu sur GitHub

GitHub reconnaît un langage grâce à Linguist. dwaifu n'y est pas encore, donc un
dépôt dwaifu affiche aujourd'hui « Python » (à cause de `.gitattributes`).
L'extension `.uwu` n'est utilisée par aucun langage de Linguist (vérifié le 2026-11-02).

## Ce qui marche déjà

| Où | Résultat |
| --- | --- |
| GitHub, avec `.gitattributes` | `.uwu` coloré et compté comme Python |
| VS Code, avec `vscode-dwaifu/` | `.uwu` reconnu comme « dwaifu », coloration propre |

## Pour que GitHub affiche « dwaifu »

Règles de Linguist ([CONTRIBUTING.md](https://github.com/github-linguist/linguist/blob/main/CONTRIBUTING.md#language-extension-and-filename-usage-requirements)) :

- au moins **2000 fichiers `.uwu`** indexés par la recherche GitHub sur la dernière année, forks exclus ;
- répartis sur beaucoup de dépôts `utilisateur/dépôt` différents (les fichiers de l'auteur du langage sont filtrés) ;
- Linguist refuse explicitement les langages « très récents ou hobby ».

Une fois ce seuil atteint, la pull request sur `github-linguist/linguist` contient :

1. Une entrée dans `lib/linguist/languages.yml` :
   ```yaml
   dwaifu:
     type: programming
     color: "#ff8fc8"
     extensions:
     - ".uwu"
     tm_scope: source.dwaifu
     ace_mode: text
   ```
2. La grammaire `vscode-dwaifu/syntaxes/dwaifu.tmLanguage.json`, publiée dans son
   propre dépôt public sous licence MIT, ajoutée avec `script/add-grammar`.
3. Des exemples réels dans `samples/dwaifu/` (`examples/*.uwu` et `stdlib/maths.uwu`).
4. Le lien de recherche qui prouve l'usage : `https://github.com/search?type=code&q=path%3A*.uwu`.

## Pour aider la recherche GitHub à trouver les `.uwu`

- Ajouter le topic `dwaifu` au dépôt.
- Garder les exemples dans des fichiers `.uwu` (pas seulement dans le README).
- Un modèle de dépôt (« template repository ») avec `club:` + `.gitattributes` permet
  aux autres de démarrer un projet dwaifu en un clic.
