# Vendored third-party files

| File | Project | Version | License |
| --- | --- | --- | --- |
| `three.min.js` (the 9 classes the dust intro uses, tree-shaken and minified with esbuild) | [three.js](https://github.com/mrdoob/three.js) | 0.187.0 | MIT, Copyright 2010-2026 three.js authors |
| `gsap.min.js` (core, CSSPlugin, ScrollTrigger, Observer ES modules, bundled and minified with esbuild) | [GSAP](https://gsap.com) | 3.15.1 | GSAP Standard "no charge" license, https://gsap.com/standard-license |

Motion timings in `../overlord_motion.js` are ported from the motion tokens of
[Arc](https://github.com/kuratlielia/arc-library) (MIT).

Vendored rather than loaded from a CDN so the intro works without network access.

Colour, radius, shadow and type tokens in `../../app.py` (OVERLORD_HEAD palette) and the landing page are ported
from the Neutral theme of [Astryx](https://github.com/meta/astryx) (MIT, Copyright Meta Platforms, Inc. and affiliates).
