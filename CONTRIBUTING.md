# Contributing

- **Firmware changes:** run `VOSS_SIM=1 python -m unittest discover tests` (CI runs it on every push).
- **CAD changes:** run `cd cad && ./tools/export.sh && python3 tools/collide.py && python3 tools/verify.py`,
  then `python3 tools/package_build.py` and `./tools/render.sh`. Commit the refreshed `build/` and `docs/img/`.
  Keep `voss/config.py` geometry in sync with `cad/voss.scad`.
- **Build reports:** open an issue with the "Build report" template. Measured servo dimensions are gold.

- By contributing, you agree your contributions are licensed under the project licences (MIT for software, CERN-OHL-S-2.0 for hardware); see `LICENSE`.
