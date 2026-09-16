# Adding a benchmark

Create `benchmarks/<lowercase-name>/` with:

- `benchmark.json`: id matching the directory, version, title, tested platforms.
- `README.md`: question, controls, workload, interpretation and known limitations.
- `NOTICE.md`: software and dataset provenance.
- `compose.yaml`: unique project name, pinned images, explicit CPU/memory limits,
  localhost-only ports and relative local result mounts.
- `Dockerfile` and `project/`: seed image and inspectable Ignition project.
- `plan.json`: a documented recipe; never silently start stress on launch.
- `test_benchmark.py`: independent correctness tests and instrumentation checks.

The shared launcher builds a `prepare` service, starts the Compose stack, and
opens the lab. For now, new benchmarks use the same Perspective project name,
port 9088 and credential variables as the first benchmark. Do not silently alter
these assumptions; extend the launcher when a different runtime is needed.

Keep computation, publisher, observer and UI logically separate. Show scheduled
versus delivered rates, numerical correctness, dropped-event indicators and
resource use. Bound runs and provide a stop control. Never reset trial licenses
automatically or expose a gateway publicly.

Run `python3 scripts/validate.py` before proposing changes. CI runs static,
numerical and classifier checks; it does not certify actual Ignition execution.
Document a manual container run separately. Changes to workload, resource defaults
or measurement semantics require a benchmark version change and a changelog entry.

Tag releases and cite the exact commit plus image digest in publications. Keep raw
results, including failed runs, in a release evidence attachment rather than
committing mutable local results. Use `python3 scripts/package.py` for a clean
source ZIP. Evidence archives must be separately reviewed for private data.
