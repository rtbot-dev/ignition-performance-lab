# Publication protocol, revision 1

Question: How can an integrator identify whether a fixed analytics workload has
outgrown a specific gateway configuration?

Primary evidence: sustained growth in inferred waiting work, before loss. Secondary:
missed-event flags, missing verified identities after drain, heap, and latency.

Pinned runtime: official Ignition 8.3.4 multiarchitecture image digest in Compose.
Three CPU quota, three Jython tag-script workers, default five-event per-tag queue,
2 GiB JVM heap, 4 GiB container limit. Six original IMS recordings; 20,480 readings
per burst; one burst per input per second; evenly staggered arrivals.

Exploration: low-load correctness check; 40, 80, 120, 160, 90, 100, 110 inputs for
60 seconds each (stop earlier on actual missedEvents). Confirmation: 100 for
180 seconds, then 110 for up to 120 seconds. Include all runs, including failures.
No fit or universal extrapolation of an exact maximum is claimed.

Published example: the clean default release validation (preflight, 40-input
low-load stage, then 80, 100 and 120). In this fresh session, 80 held and 100
built up waiting work and overflowed. The earlier, longer-running research
session held 100 for 180 seconds and overflowed at 110. Both observations are
published: a single input count is not an immutable gateway limit. Warmup
history and host activity differ; the experiment does not isolate their causal
contributions. Untested loads between successful and overloaded stages remain
untested, not inferred exact thresholds.

Generator validity: maximum lateness <=100 ms at the one-second cadence.
Correctness: all 22 output values, tolerance 1e-8 + 1e-6*abs(reference), exact count.
Observe once per second. Remove startup first 10 s and input end/drain from trend;
truncate before first sampled missedEvents. Review full ten-second averages,
overall least-squares slope, and final twenty-second slope. The automatic labels
are descriptive, not formal statistical capacity guarantees. Final publication
requires visual review of trajectories and confirmation runs.

Safety: stop at actual missed-event flags, incorrect/duplicate outputs, observer
error, high retained heap, or bounded outstanding work. An incomplete drain with
no confirmed overflow stops the suite to prevent contamination of later stages.

No external service was stressed. Only the isolated local test gateway receives
load. No paid campaign or LinkedIn post changes are part of this experiment.

Release checks are separate from the research sequence: a fresh gateway was
started through start.sh. The first check used a shortened plan
(preflight then 80), exposing cold-start overflow when the 40-input warmup was
omitted. Keep that result; it is not a warmed steady-state comparison.
