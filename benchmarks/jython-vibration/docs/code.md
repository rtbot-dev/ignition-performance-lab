# Follow the code

1. **[The calculation](../project/ignition/script-python/benchmark_full/code.py):**
   `calculate` parses one burst, calls `_compute_metrics`, and flattens the output.
   `reference` independently checks the result; `Ledger` tracks work and verification.
2. **[Input and output handling](../project/ignition/script-python/load_benchmark/code.py):**
   `generate` publishes recorded bursts. `on_input` is called by the tag event,
   calculates the indicators and publishes outputs. The listener verifies results.
3. **[The control panel](../project/ignition/script-python/docker_lab/code.py):**
   `tick` handles run/stop commands, status and resource observations.

Click **View computation** in the local lab to read the shipped numerical module
without GitHub or Designer. The page is a generated read-only copy; CI checks it
against the source. If the source changes, regenerate it with
`python3 scripts/build_code_view.py`. For live modifications after installation,
use Designer's project script library; the static viewer is not a live editor.
