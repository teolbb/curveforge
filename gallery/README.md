# Recipe gallery

Worked, real-world tuned recipes — each annotated with the use case, the
reasoning behind every parameter, and what to push if you want more or less
of something. Use them as starting points; tune to your room and taste.

| Recipe | One-line summary |
|---|---|
| [`harman-8.yml`](harman-8.yml) | First-order Harman bass shelf at +8 dB. The community default for music. |
| [`harman-8-with-sub-lift.yml`](harman-8-with-sub-lift.yml) | Harman +8 + a wide sub-bass bump at 20 Hz for visceral immersion. |
| [`harman-immersive-low-sibilance.yml`](harman-immersive-low-sibilance.yml) | Harman +8 + sub-bass lift + gentle high-shelf cut. Full immersion without harshness. |
| [`olive-warm.yml`](olive-warm.yml) | Olive-Welti RR1_G with a slightly darker treble tilt. For warm, room-friendly listening. |
| [`bnk-classical.yml`](bnk-classical.yml) | Brüel & Kjær 1974 — modest bass, smooth treble taper. Good for classical and jazz. |
| [`toole-monitoring.yml`](toole-monitoring.yml) | Toole's "preserve what good speakers do" target. For directionally well-behaved monitors. |
| [`reference-flat.yml`](reference-flat.yml) | Zero correction baseline for measurement comparisons. |

## How to use a gallery recipe

```sh
# 1. Copy and edit
cp gallery/harman-8-with-sub-lift.yml my-living-room.yml

# 2. Edit the output path inside it
# 3. Build
curveforge build my-living-room.yml

# 4. Inspect (requires the [plot] extra)
curveforge plot my-living-room.yml

# 5. Load `<output>.targetcurve` into Dirac Live as a custom target
```
