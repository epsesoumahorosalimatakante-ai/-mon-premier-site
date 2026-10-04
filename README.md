# Artchille Design Pub — animation motion design

Vidéo promotionnelle de 34 s (1920×1080, 30 i/s) pour l'imprimerie **Artchille Design Pub**.

- **Vidéo finale** : [`video/artchille-design-pub.mp4`](video/artchille-design-pub.mp4)
- **Animation en direct** : ouvrir `index.html` dans un navigateur (lecture en boucle)

## Scènes
1. Apparition du logo — « Impression · Design · Publicité »
2. « Vos idées prennent vie » — du petit au grand format
3. Grand format : bâches, roll-up, panneaux, stickers & véhicules (impression du panneau en direct)
4. Petit format : cartes de visite, flyers, dépliants, étiquettes, invitations
5. Nos qualités : haute définition, couleurs, rapidité, prix
6. Logo + contact

## Modifier et réexporter
- Textes, numéro de téléphone (`00 00 00 00 00`) : directement dans `index.html`
- Musique : `python3 tools/musique.py` (ou remplacer `video/musique.m4a` par votre propre fichier)
- Export vidéo : `node tools/render.mjs` (nécessite Playwright et ffmpeg)
