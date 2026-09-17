# Connect Designer and change the computation

This is your local Ignition gateway. You can edit its project with Ignition Designer.
The **View computation** page is read-only; there is no browser code editor.

## Connect

1. Start the lab and keep the launcher terminal open. At the end it prints the
   **Gateway URL**, **Username**, **Password**, and project name.
2. Open that gateway URL (normally `http://localhost:9088`). Download and install
   **Designer Launcher** from the gateway if you do not already have it.
3. In Designer Launcher, choose **Add Designer**, enter the printed gateway URL,
   and launch it. Use `localhost`, not the container's internal IP.
4. Sign in with username **benchmark** and the password printed by the launcher.
   Open project **performance-lab**.
5. In the Project Browser, open **Scripting → Project Library → benchmark_full**.
   This is the numerical code used by the input tag callbacks.

If you selected another port, use that port throughout. The initial password is
also in `benchmarks/jython-vibration/.env` in the installation directory printed by
the launcher. An existing Docker volume retains its original password. Do not
share the password or expose this gateway to the Internet.

## Change the calculation, keep the same outputs

Stop the experiment and wait for it to finish draining before editing.
For a first experiment, change `_compute_metrics(samples, device_id, channel_id)`
while keeping its returned metric names and meanings unchanged. `samples` is a
list of acceleration values. Keep `calculate`, payload parsing, `LAYOUT`, `FIELDS`,
and the `Ledger` instrumentation intact.

Save the project in Designer. Then, from the installation's
`benchmarks/jython-vibration` directory, run:

```sh
docker compose restart gateway
```

Restarting clears cached harness state and requires a fresh correctness check.
Refresh the lab and start at low load. The independent `reference(payload)`
calculation checks whether your revised implementation produces the same metrics.
A failed check blocks the measured run; it is not a performance result.

Designer saves live inside the gateway Docker volume. A gateway restart preserves
those saves. Relaunching the package can re-run its preparation container and copy
the shipped project over them. Export your edited project from Designer before
relaunching, upgrading, or resetting the lab. Removing the volume deletes edits.

## Test a different computation

Supported through project editing, not a generic paste-and-run form. If your
algorithm returns different metrics, update the harness contract together:

- `calculate(payload)` returns a dictionary keyed by every entry in `FIELDS`.
- `LAYOUT` and `FIELDS` describe the numeric output tags being published.
- `reference(payload)` independently returns the expected values for those same
  keys. Do not make it call `calculate`: that would invalidate verification.
- The corpus and parser must match your chosen input format.

Also update the workload name, sample count, documentation and any hard-coded
output-count labels before publishing results. The bundled labels describe the
original vibration workload; they do not automatically describe arbitrary code.
Restart the gateway and recheck correctness after every change. Keep the exact
code with your results and compare only matched workloads and resource settings.

The static **View computation** page shows the shipped code, not your live edits.
Designer is the source of truth for a modified running project.
