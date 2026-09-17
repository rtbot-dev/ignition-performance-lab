# Can your Ignition gateway keep up?

A reproducible Jython vibration workload and a method for testing sustained capacity.
Built by Katenaria, the company behind Coprocessor. **No Coprocessor module required.**

[Connect Designer / edit computation](docs/designer.md) · [Measurement method](docs/methodology.md) · [Share a reproduction](docs/reproduction.md) · [Test protocol](PROTOCOL.md)

## Run

From the repository root, run `./lab.sh jython-vibration` (macOS/Linux) or
`./lab.ps1 -Benchmark jython-vibration` (Windows PowerShell).
On macOS you can also double-click **Start Lab.command** in the repository root.
Docker Desktop must be installed and running.
The launcher asks you to accept the Ignition license and generates a local password.
Open the URL printed by the launcher (normally
http://localhost:9088/data/perspective/client/performance-lab) once the gateway
has started. If you chose another port, use the printed URL. Refresh if it is not ready.

The gateway starts **idle**. No Designer, PLC, database, or manual tag setup is needed.
Choose input tags, cadence and duration, then **Run test**. The first run automatically
checks correctness at low load. Start with 40 inputs for 60 seconds, then increase
the input count between runs. **Stop input** drains submitted work and preserves results.
Controls are locked during each run to keep its workload well defined.

The native Perspective panel shows waiting jobs, published/started/verified counts,
missed-event flags, JVM CPU and heap. CPU 100% means one CPU fully used; a three-CPU
quota can approach 300%. Heap is used Java heap divided by its configured maximum,
not the whole container's memory. Independently watch **Docker Desktop → Containers
→ katenaria-lab-jython-vibration → gateway → Stats**, or run `docker stats`.
Docker Desktop memory includes more than Java heap, so the two numbers differ.

Only localhost port 9088 is exposed. This is a separate trial gateway; never install
the load test in production. Our seed image contains project files only. Compose
pulls the official Ignition image separately. The source code is included for inspection.

Raw evidence is saved directly in your local `results/` folder. No separate dashboard,
cloud service or telemetry is required. From this benchmark folder, stop the lab with `docker compose stop`.
The normal trial license controls are available at http://localhost:9088; credentials
are stored locally in `.env`. The package never resets licensing automatically.

## Workload

Each input is a managed String tag with an ordinary Ignition valueChanged script.
The publisher is a separate open-loop gateway thread; input arrivals are evenly
staggered over each period. This measures computation, **not PLC/network capacity**.

Six real recordings from NASA's IMS bearing dataset contain 20,480 acceleration
measurements each, at 20 kHz: 1.024 seconds, approximately one second. They are replayed
at the selected cadence, not at the dataset's original recording schedule.
A reserved trailing token identifies the end of the burst and changes on every
publication; real zero acceleration values remain data.

The original multi-pass Jython calculation computes count, mean, variance, standard
deviation, RMS, third/fourth centered moments, skewness, kurtosis, peak-to-peak,
crest, clearance, impulse, and shape factors. Four output layouts publish 22
numeric fields (some metrics appear in multiple layouts). Each result is checked
against an independent centered math.fsum reference. A direct SDK listener observes
outputs without using another Jython tag-script worker.

`project/ignition/script-python/benchmark_full/code.py` is byte-for-byte identical
to the original kernel. See `provenance.json` for source and corpus checksums.
The harness uses the gateway managed-provider API to preserve timestamps; it is
version-specific. It has been tested on the pinned 8.3.4 image, not every version.

## Method

1. Verify the numerical outputs at low load, then run the 40-input stage as a
   low-load warmup. Cold-start and warmed capacity are different experiments.
2. Keep computation, cadence, CPU allocation, heap, and worker count fixed.
3. Increase inputs and hold each stage for at least 60 seconds unless actual loss
   or a safety guard requires an earlier stop.
4. Ignore startup (first 10 seconds) and drain. Examine waiting-work trends and
   ten-second averages before the first missed-event flag.
5. Refine and repeat the boundary; use longer observations near a plateau.
6. Change ONE resource or workload parameter, then repeat.

P = successful publications; S = callbacks entered. P-S estimates waiting work
before loss. It includes short publication/observer scheduling races; it is not
an inspection of Ignition's internal queue. Once missedEvents is reported, P-S
includes dropped jobs and is no longer a queue-size estimate. The chart stops
there. Missed-event flags count callbacks reporting overflow, **not lost jobs**.
Missing result identities after drain are exported separately.

A complete drain does not establish sustainable processing. Positive sustained
queue growth means input outpaces processing even if no event has yet been lost.
Our descriptive classifier checks the overall and final-20-second slopes plus
successive full ten-second means. Its slope deadband is max(0.1 jobs/s, 0.5% of
scheduled rate); this is disclosed noise tolerance, not a confidence interval.
Inspect small positive drifts and repeat longer rather than claiming zero drift.
Invalid schedule, bad numerical results, and safety stops are reported separately.

## Configuration and limits

Default gateway: 3 CPU quota, 3 script workers, 2 GiB JVM heap, 4 GiB container memory.
CPU quota is not physical-core pinning. Docker Desktop runs Linux in a VM; its CPU
and memory allocation and other host activity affect results. Keep the machine
quiet. The benchmark does not stop any other application.

Set input count, cadence and duration in the UI. Edit BENCH_CPUS in `.env` for CPU
allocation and restart with `docker compose up -d`. Worker count is explicitly set
in compose.yaml and recorded in each run. Historical plan files are retained as
experiment recipes; the interactive lab does not execute them automatically.
Our numbers are examples of a particular workload/environment, not Ignition's
universal tag capacity. Multiple software threads are not equivalent to dedicated
physical CPU cores.

Ignition is fetched from the official pinned image and governed by its own EULA.
Trial modules run for two hours; the package does not reset or circumvent licensing.
For another session, use the normal gateway trial controls where required.

## Evidence and sources

- Raw per-run JSON: `results/Jython-*.json`, including timestamped samples and missing IDs.
- UI resource traces: `results/resources-Jython-*.json`.
- JVM environment: `results/environment.json`.
- Classification source: `analyze.py` (no input-count-specific decisions).
- Exact image digest and allocation: `compose.yaml`.
- Source/corpus lineage: `provenance.json` and `corpus.json`.
- NASA: https://data.nasa.gov/dataset/ims-bearings
- Citation: J. Lee, H. Qiu, G. Yu, J. Lin, and Rexnord Technical Services (2007).
  IMS, University of Cincinnati. Bearing Data Set, NASA Prognostics Data Repository.
- Docker documentation: https://docs.inductiveautomation.com/docs/8.3/platform/docker-image

## Reset between independent reproductions

Stop the package, archive `results`, clear `runtime/STOP`, and remove ONLY this
package's gateway volume with `docker compose down -v`. This deletes the isolated
benchmark gateway. A fresh run regenerates the same project and starts idle.
Keep all failures and repeats in the evidence when reporting findings.

## Local validation scope

The native Perspective run/stop controls and live charts, plus the original automatic flow, have been exercised on Apple Silicon with Docker
Desktop. The upstream base images support AMD64 and ARM64, but Windows and
AMD64 execution are not claimed as tested until an external reproduction is run.
The PowerShell launcher is supplied for that reproduction. Instrumentation and
result verification run inside the gateway and are included in the measured cost.

## Cold-start observation

A separate clean-launch check jumped directly from correctness preflight to
80 inputs, omitting the default 40-input stage. It overflowed during startup.
This failed run is preserved. Do not present warmed capacity as cold-start
capacity; the default ramp includes low-load warmup before higher loads.

The historical `plans/publication.json` lists the stages used for the published
sequence. In this interactive version, enter those loads in the UI in that order.

### See where throughput stops keeping pace

Run several increasing input counts at the same cadence, using 60-second runs.
The throughput chart retains one point per completed run, plotting actual published
bursts per second against verified computations per second. The dashed diagonal
means processing keeps pace. A point below it means work accumulated or was lost;
inspect the waiting queue and missed-event counter to distinguish the two.

Rates use counter differences over the same interval, exclude the first 10 seconds
and all samples after input stops, and require at least 10 seconds of measurement.
Short safety-stopped runs may therefore have no point. Orange points indicate a
late publisher or correctness/observer problem and must not establish capacity.
Hover over points for input count, cadence, duration and missed-event flags.
The last 100 points persist in `results/throughput.json`; raw run files retain the
underlying counters. Compare points only with the same computation and resources.
The chart starts empty on a fresh install and fills as you run experiments.

**Run automatic scan** tests 20, 40, 60, 80, 100, 125, 150, 200, 250,
350 and 500 inputs at one burst per input per second. Each level lasts 60 seconds, followed by drain and preparation of the next
level. **Stop scan** cancels the entire scan. The main view presents only this automatic workflow; advanced users can change the computation in Designer. The scan stops on missed events,
correctness/safety failures, an invalid publisher schedule, or measured output
more than 2% below input together with backlog growth above 0.5 jobs/s over the
measurement interval. These are conservative scan stop rules, not universal
capacity thresholds: repeat loads around the first failing level and inspect the
queue trace. A complete scan can take over 12 minutes; resource limits may stop
it earlier. Existing result files and throughput points remain available.
