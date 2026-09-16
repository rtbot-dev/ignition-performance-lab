# Ignition Performance Lab

**Find the sustainable limit of your own analytics workload.**

Runnable experiments from [Katenaria](https://katenaria.com), built around the
method: hold a representative load, observe waiting work over time, then increase
inputs until processing cannot keep up. Capacity depends on the computation,
resource allocation, runtime and machine. There is no universal tag-count limit.

## Start locally

Install and start Docker Desktop, download or clone this repository, and run:

```sh
./lab.sh
```

Windows PowerShell: `./lab.ps1`. On macOS, double-click **Start Lab.command**.
The first launch asks you to accept Ignition's license. It downloads the official
Ignition image and opens a local Perspective interface. The gateway starts idle.
Choose input count, cadence and duration, then run. No Designer or PLC is required.

**Open:** http://localhost:9088/data/perspective/client/performance-lab

Watch the queue, CPU and heap in the lab. Independently inspect the gateway's CPU
and memory in Docker Desktop's **Stats** tab. All computation and recorded results
stay on your machine. Source code, configuration and data provenance are included.

## Benchmarks

| Experiment | Question | Status |
|---|---|---|
| [Jython vibration analytics](benchmarks/jython-vibration/) | When do per-tag vibration calculations build up a sustained backlog? | Validated locally on Apple Silicon / Docker Desktop |

The first experiment replays real IMS bearing recordings: 20,480 accelerometer
samples per burst, about one second of vibration. It computes 14 statistical
indicators with 22 output updates and checks every result against an independent
reference. It tests gateway computation, not acquisition from a physical PLC.

## What to observe

1. Start at low load and let the runtime warm up.
2. Keep cadence and resources fixed; increase input tags between runs.
3. Hold each load for at least 60 seconds. Ignore startup transients and examine
   whether waiting work settles or continues to grow. Repeat near the boundary.
4. Treat missed events as overload. Treat incorrect results or a late publisher
   as an invalid test, not proof of processing capacity.

See [measurement definitions](docs/methodology.md) and the benchmark's
[operating instructions](benchmarks/jython-vibration/README.md).

## Repository layout

```text
benchmarks/
  jython-vibration/
    benchmark.json      Experiment identity and tested environment
    compose.yaml        Pinned runtime and explicit resource limits
    Dockerfile          Project seed only; no Ignition binaries
    project/            Inspectable Ignition scripts and Perspective views
    corpus.json         Input recordings
    provenance.json     Record identities and source checksums
    plans/              Historical experiment recipes
    analyze.py          Queue-trend analysis of raw results
    test_benchmark.py   Numerical and methodology tests
scripts/                Shared launch, validation and packaging tools
docs/                   Method, contribution and reproduction guidance
.github/                Automated tests and reproduction issue template
lab.sh / lab.ps1         Single entry point; optional benchmark name
```

Each benchmark owns its workload and runtime configuration. Shared scripts handle
launching and packaging. New benchmarks get new folders; existing published tests
can remain reproducible. Run one lab at a time unless their host ports differ.

Local `.env`, gateway state and `results/` are ignored by Git. To stop this lab:

```sh
cd benchmarks/jython-vibration
docker compose stop
```

## Reproduce and contribute

Use [the reproduction checklist](docs/reproduction.md) when sharing results.
We welcome failures, corrections and independent measurements. Do not post secrets
or production plant data. [Adding an experiment](CONTRIBUTING.md) describes the
small contract each benchmark must meet.

## Disclosure and licensing

Katenaria also develops Coprocessor. This first benchmark tests **Jython alone**;
Coprocessor is not installed. We publish the method and code so results can be
checked independently.

Benchmark code is MIT licensed. Ignition, container dependencies and the IMS data
retain their own terms; see [NOTICE](benchmarks/jython-vibration/NOTICE.md).
Ignition is downloaded from its official image, never redistributed in our seed
image. Its trial and license requirements still apply. This project is not
endorsed by Inductive Automation. Windows and AMD64 execution need independent
verification; providing a launcher is not a claim they have been tested.
