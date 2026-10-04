# -mon-premier-site

## Présentation Motion Design — Théodore Carmel

Vidéo de présentation (51 s, 1920×1080, 30 i/s) : **Théodore Carmel**, monteur vidéo et concepteur d'affiches guinéen avec 3 ans d'expérience.

- 🎬 Vidéo finale : [`presentation/theodore-carmel-presentation.mp4`](presentation/theodore-carmel-presentation.mp4)
- 🌐 Version web animée : ouvre `presentation/index.html` dans un navigateur, puis clique pour lancer l'animation et le son.

### Déroulé (51 s)
| Temps | Scène |
|---|---|
| 0–6 s | Intro : photo dans un anneau lumineux et nom « Théodore Carmel » |
| 6–12,5 s | Discussion : « Tu connais quelqu'un qui fait du montage vidéo et des affiches ? » |
| 12,5–16 s | Barre de recherche : « théodore carmel » |
| 16–21 s | Terminal : origine Guinée, spécialités, 3 ans d'expérience |
| 21–26 s | Globe : localisation en Guinée, puis vers le monde |
| 26–33 s | Outils Adobe : Premiere Pro, After Effects, Photoshop, Illustrator, Audition |
| 33–40 s | Profil : statistiques et exemples de réalisations |
| 40–45 s | Compteur : 1 095 jours de création, puis « 3 ANS D'EXPÉRIENCE » |
| 45–51 s | Outro : contact **05 65 40 31 11** |

### Régénérer la vidéo
```bash
cd presentation
python3 soundtrack.py audio/soundtrack.wav     # bande-son (numpy)
node render.mjs 30                               # images → frames/ (Playwright)
ffmpeg -framerate 30 -i frames/f%05d.jpg -i audio/soundtrack.wav \
  -c:v libx264 -crf 18 -pix_fmt yuv420p -c:a aac -b:a 192k -shortest theodore-carmel-presentation.mp4
```
