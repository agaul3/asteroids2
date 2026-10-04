# Asset generation

Generated with the built-in ImageGen tool, with transparent background enabled
for every image. The final PNGs are copied into `assets/sprites/`; original
generation outputs remain in the Codex generated-images directory.

The supplied references at
`/Users/adamgault3/Developer/bootdev/asteroids2/references/` were inspected for
visual direction: dark graphite materials, warning yellow, cyan light,
magenta accents, and angular industrial styling. No website scripts or
instructions from saved pages were used. The sprites are newly generated;
the reference images are not distributed with the game.

## player.png

Use case: stylized-concept. Create ONE production-ready transparent-background 2D game sprite of a Cyberpunk 2077 inspired futuristic rocketship. Style references are the provided Night City images: glossy graphite industrial metal, hard angular yellow armor, vivid cyan lighting and subtle magenta accents. Strict orthographic TOP DOWN view, no perspective, ship nose pointing UP. Compact long triangular silhouette: razor pointed central nose, tightly swept wedge wings that only widen toward the rear; overall solid body width about 2/3 its height, entirely inside an isosceles triangle with point at top and base bottom. Symmetric main hull with asymmetric armor paint details, dark graphite panel seams, vivid warning-yellow armor shoulder plates, luminous cyan cockpit and twin engine nozzles, tiny magenta cable inserts. Metallic illustrated high-quality detailed 2D sprite, strong readable large panels at 40 pixels height. Centered alone with generous transparent margin, no text, no logos, no shadow plane, no scene, no other objects, no baked checkerboard. Very short cyan engine glow at rear only; no long exhaust trail. Ship nose at top, engines bottom.

## Asteroid prompts

Each asteroid used the following prompt, substituting its description below:

Use case: stylized-concept. Asset type: ONE transparent-background top-down 2D game asteroid sprite. Cyberpunk 2077 Night City inspired palette, detailed metallic illustration with realistic rocky facets and sharply readable silhouette. {description} Strict overhead orthographic game sprite, centered isolated alone, approximately circular overall dimensions, entire asteroid visible with transparent margin on all sides, solid continuous body and small restrained neon glow. Upper-left lighting with enough surface brightness to be visible against a BLACK game background. Readable large surface features at diameters 40, 80 and 120 pixels. No ground shadow, no scene, no lettering, no UI, no logos, no other objects. Truly transparent background.

- **asteroid-mineral.png:** ONE irregular roughly circular asteroid, dark graphite faceted mineral rock with crater pits and thick luminous CYAN veins splitting its surface; sparse small embedded industrial metal plates. Clearly asteroid rock, jagged irregular silhouette.
- **asteroid-scrap.png:** ONE irregular roughly circular asteroid made of dark mineral rock fused with wrecked industrial machinery: battered YELLOW armor panels, steel ribs, exposed cables, tiny RED warning lights. Mostly rock, not a spaceship, asymmetrical angular silhouette.
- **asteroid-crystal.png:** ONE irregular roughly circular asteroid made of dark purple-black volcanic rock with several chunky luminous MAGENTA crystal outcrops and purple fissures. Distinct large faceted crystals and rock craters; lopsided roughly round silhouette.

## shot.png

Use case: stylized-concept. Asset type: ONE transparent PNG sprite of a futuristic CYAN LASER BOLT for a top-down Cyberpunk 2077 themed asteroids game. Single short, narrow, straight energy projectile pointing vertically UP, centered on transparent background. White hot thin central core, crisp cyan inner shell, small cyan-blue outer glow, tapered ends, no hardware and no scene. Visually reads as a compact laser beam segment, not a spaceship or bullet casing. Bolt body aspect ratio approximately 1:3 width:height, no longer than three widths. Intended in-game size 10 by 20 pixels including halo. One beam only, orthographic flat view, all glow alpha fades into genuine transparency. No text, no ground, no frame, no checkerboard.

## Preview

`uv run python tools/preview_assets.py` regenerates `assets/preview.png`
using the game's renderer. Its lower row shows actual gameplay sizes.
