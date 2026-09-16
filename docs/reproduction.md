# Share a reproduction

Record:

- Repository commit and benchmark version; any local edits.
- Host CPU model, RAM, OS and other significant running workloads.
- Docker version and Docker Desktop VM CPU/memory settings where applicable.
- Gateway CPU quota, worker count, container memory and JVM heap.
- Input count, samples per burst, cadence, duration and arrival schedule.
- Fresh or warmed gateway; preceding runs and warmup duration.
- Queue trajectory, publisher lateness, wrong results, missed flags and missing IDs.

Attach the selected benchmark's raw `results/Jython-*.json`, matching
`resources-Jython-*.json`, and `environment.json` after reviewing for private data.
Do not attach `.env`, gateway volumes, credentials, production records or unreviewed
logs. Keep successful and failed runs. Do not infer universal capacity from one host.

The bundled recordings and official Docker image make the experiment repeatable;
they do not make different hardware or startup states identical.
