# Pack B operator layer

This is the isolated Pack B implementation for the frozen Pack A stable-LLP
handoff. It validates immutable input hashes, the frozen point contract, the
Pythia 8.308 installation, and the dated Pack B output root. It does not run
MadGraph, create events, modify Pack A, or inspect Pack AA state as an input.

```bash
python3 pack_b/operator/pack_b_preflight.py \
  pack_b/operator/config.json \
  --manifest scratch/pack_b_20260722T092951Z/preflight_manifest.json

c++ -O2 -std=c++17 pack_b/operator/pack_b_smoke.cc \
  -o scratch/pack_b_20260722T092951Z/pack_b_smoke \
  $(/home/fabi/.local/pythia8308/bin/pythia8-config --cxxflags --libs)
scratch/pack_b_20260722T092951Z/pack_b_smoke
python3 pack_b/tests/test_pack_b_preflight.py
pack_b/mission/DEFERRED_HEAVY_COMMANDS.sh
```

The final command prints the exact later full-generation invocation. Do not
claim production validation until a real event handoff is supplied and its
output is checked.
