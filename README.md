# Cyberpunk Asteroids

A Pygame asteroids game with a yellow-armored rocketship, neon mineral,
industrial scrap, and magenta crystal asteroids, and cyan laser bolts.

Run with Python 3.13+ and uv:

```sh
uv run main.py
```

Controls: **W/S** move, **A/D** rotate, **Space** fires. The ship is 1.625×
its original size, with a matching enlarged triangle hitbox (radius 32.5;
approximately 43 × 65 pixels before rotation). Movement, shot speed, cooldown,
and asteroid spawning/splitting remain unchanged. The laser glow is decorative;
its hitbox remains a circle with radius 5. The player's nose faces down at zero
rotation, as before.

Transparent PNG artwork lives in `assets/sprites/`; the renderer loads assets
relative to the source directory, crops empty margins, and caches scaled and
rotated surfaces. Each asteroid chooses one of three styles and a starting
orientation using a separate cosmetic random generator. All three styles can
appear at each of the existing asteroid sizes.

See `assets/preview.png` for the artwork and in-game scale samples, and
`assets/PROMPTS.md` for generation prompts and reference notes.

Run the headless integration checks:

```sh
uv run python -m unittest discover -s tests
```

Combat feedback uses the same cyan, magenta, and warning-yellow palette:

- Successful shots trigger a 0.12-second muzzle flash and electronic zap.
- Asteroid destruction triggers a 0.55-second nova, real sprite fragments,
  and sparks colored to match its variant. Laser hits add a bass/metal impact.
- Nonfatal player collisions trigger a 0.55-second shield rupture, hull
  flicker, and armor/shield sound. Controls stay active; there is no invulnerability.
- Fatal damage triggers a separate 1.4-second ship destruction and power-down
  cue. Gameplay freezes immediately, while effects finish. A persistent
  **FLATLINED** screen then shows the final score. Close the window to exit.

Original stereo 44.1 kHz WAV effects are in `assets/audio/`. They load once,
with channels reserved for player feedback. If audio is unavailable, the game
continues silently. Rebuild the deterministic audio assets with:

```sh
uv run python tools/generate_sfx.py
```

Watch and hear the animation reel:

```sh
uv run python tools/preview_combat.py
```

The reel cycles through firing, all three asteroid novas, shield damage, and
fatal destruction. Press **Esc** or close its window to exit. Reproduce the
static animation contact sheet and updated asset gallery with:

```sh
uv run python tools/preview_combat.py --headless
uv run python tools/preview_assets.py
```

These write `assets/combat-preview.png`, `assets/game-over-preview.png`,
and `assets/preview.png`. Gameplay
effects use elapsed time and independent cosmetic randomness, and never enter
collision groups.
