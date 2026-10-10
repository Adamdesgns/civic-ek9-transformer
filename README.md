# Yellow Civic Type R EK9 Transformer

Adam's editable yellow Honda Civic Type R EK9 and its car-to-robot animation, modeled against the 1999 TopRank #111040 reference car.

![Yellow Civic transformer](evidence/transformer/hero.png)

## Open the model

Use Blender 5.2 and open **[civic-ek9-transformer.blend](blender/civic-ek9-transformer.blend)**. Frame **1** is the car; frame **180** is the robot. Scrub the timeline between them to see the conversion.

- **[Refined yellow car](blender/civic-ek9-yellow-refined.blend)** — the final car used as input to the transformer.
- **[Transformation MP4](exports/yellow-hatchback-transforming.mp4)** — small phone-friendly preview, 8.53 seconds.
- **[Animated preview](evidence/transformer/conversion.gif)** and **[review images](evidence/transformer/)**.
- **[Animation and rebuild notes](docs/ek9-transformer.md)**.

On a Blender file's GitHub page, use **Download raw file**, or download the whole repository with **Code → Download ZIP**. This repository is public; no sign-in is required to browse or download it.

## Contents

The repository preserves the Blender scenes, procedural Python source in `blender/civic-ek9_build/`, tools in `tools/civic-ek9/`, review evidence, the MP4, and the yellow reference gallery. `blender/civic-ek9-car.blend` is an earlier workspace snapshot; use `civic-ek9-yellow-refined.blend` for the final yellow car. Automatic Blender backups and Python caches are excluded.

This is a standalone asset backup from the local Transformers work. It does not contain the full browser game. The animation has no game integration yet, and full physical clearance between all folding parts has not been established.

## Rebuild

From this repository's root, with Blender 5.2 on your command path:

```powershell
blender -b blender/civic-ek9-yellow-refined.blend --python-exit-code 1 --python tools/civic-ek9/build_transformer.py -- hero car front back mid
blender -b blender/civic-ek9-transformer.blend --python-exit-code 1 --python tools/civic-ek9/check_transformer.py
```

The first command regenerates the transformer scene and review renders. Make a working copy before rebuilding if you want to retain manual edits. Historical reports in `docs/` describe the September 2026 build; the GitHub backup was prepared on October 10, 2026.

## Credits and license

The project originated from [scottstts/Transformers](https://github.com/scottstts/Transformers). Reused source and derived source are preserved under **GPL-3.0-only**; see [LICENSE](LICENSE) and [ATTRIBUTION.md](ATTRIBUTION.md). Third-party reference photos and drawings retain their own rights and are not relicensed by the source-code license.
