# Reproduce Pack A Native

## Reproducción limpia

Activa el venv, exporta el toolchain HEP externo y limita los threads:

```bash
source "$HOME/atlas_dihiggs/llp_recast/.venv/bin/activate"
export MG5_HOME="$HOME/.local/mg5amcnlo/3.5.3"
export MG5_BIN="$MG5_HOME/bin/mg5_aMC"
export PYTHIA8="$HOME/.local/pythia8308"
export PYTHIA8_CONFIG="$PYTHIA8/bin/pythia8-config"
export FASTJET3="$HOME/.local/fastjet-3.4.0"
export FASTJET_CONFIG="$FASTJET3/bin/fastjet-config"
export PATH="$MG5_HOME/bin:$PYTHIA8/bin:$FASTJET3/bin:$PATH"
export LD_LIBRARY_PATH="$PYTHIA8/lib:$FASTJET3/lib:${LD_LIBRARY_PATH:-}"
export OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 MKL_NUM_THREADS=2 MAKEFLAGS="-j2"
```

El runner resuelve MadGraph en este orden: `MG5_BIN`, `command -v mg5_aMC`,
`$HOME/.local/mg5amcnlo/3.5.3/bin/mg5_aMC`. Si no existe, termina como
`BLOCKED` e imprime el comando completo para configurarlo.

La reproducción desde una shell limpia (con `MG5_BIN` inicialmente ausente)
es este comando único. Extrae el ZIP en limpio, captura el exit status del
runner y deja el log completo en
`$HOME/atlas_dihiggs/ufos/pack_a_native_clean.log`:

```bash
env -u MG5_BIN bash -lc 'set -u; source "$HOME/atlas_dihiggs/llp_recast/.venv/bin/activate"; export MG5_HOME="$HOME/.local/mg5amcnlo/3.5.3" PYTHIA8_CONFIG="$HOME/.local/pythia8308/bin/pythia8-config" FASTJET_CONFIG="$HOME/.local/fastjet-3.4.0/bin/fastjet-config" OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 MKL_NUM_THREADS=2 MAKEFLAGS=-j2; export PATH="$MG5_HOME/bin:$PATH"; export LD_LIBRARY_PATH="$HOME/.local/pythia8308/lib:$HOME/.local/fastjet-3.4.0/lib:${LD_LIBRARY_PATH:-}"; repro="$HOME/atlas_dihiggs/ufos/.pack_a_native_clean"; rm -rf "$repro"; mkdir -p "$repro"; unzip -q "$HOME/atlas_dihiggs/ufos/pi_ufo_baseline_v1_runtimefix.zip" -d "$repro"; set +e; bash "$repro/pi_ufo_baseline_v1_runtimefix/scripts/run_validation_pack_a_native.sh" 2>&1 | tee "$HOME/atlas_dihiggs/ufos/pack_a_native_clean.log"; status=${PIPESTATUS[0]}; set -e; echo "runner_exit_status=$status"; exit "$status"'
```

El runner ejecuta las pruebas estáticas, pytest, la construcción de
`A_PI_NATIVE_200`, la importación de MadGraph 3.5.3, `g g > H > h2 h2`, 100
eventos y la inspección del LHE. En éxito imprime `PACK_A_NATIVE_RUNTIME_PASS`
y termina con código 0. Los logs de etapa quedan bajo
`.pack_a_native_clean/pi_ufo_baseline_v1_runtimefix/build/A_PI_NATIVE_200/`.

## Qué es inmutable y qué se reproduce

- `pi_ufo_baseline_v1.zip` no se toca ni se reextrae.
- `pi_ufo_baseline_v1_runtimefix.zip` contiene el runtime-fix aplicado; no
  hace falta ningún parche manual.
- “reproducible from the ZIP in the documented external HEP toolchain.”
- La extracción usa `.pack_a_native_clean` como directorio desechable y no
  colisiona con `runs/A_PI_NATIVE_RUNTIMEFIX/`.

## Resultado esperado

```
[...] STAGE OK: static_tests
[...] STAGE OK: pytest
[...] STAGE OK: build_point
[...] STAGE OK: mg5_smoke
[...] PACK_A_NATIVE_RUNTIME_PASS
```

Se espera sigma positiva, 100 eventos, exactamente dos PDG 9000006 finales por
evento, LLP estable, sin Pythia, sin Pack AA y sin tocar Pack B.

## Re-derivar entregables individuales

```bash
cd "$HOME/atlas_dihiggs/ufos/.pack_a_native_clean/pi_ufo_baseline_v1_runtimefix"
python3 -m pytest tests/ -q
python3 scripts/materialize_internal_masses.py \
  --model-dir model/LLscalar_v3_UFO_runtime --pdg 24 \
  --check-against 79.82435974619784
```
