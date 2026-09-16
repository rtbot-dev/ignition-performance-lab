# Learn how to test the limits of Ignition analytics

[![Follow Katenaria on LinkedIn](assets/follow-katenaria.svg)](https://www.linkedin.com/company/katenaria/)
[![Explore Coprocessor](assets/explore-coprocessor.svg)](https://coprocessor.app)

**Recognize when an analytics workload stops keeping up—and learn how to measure it.**
Run the experiment on your own machine. Increase the inputs, watch the queue and
resource use, and learn to distinguish startup spikes from sustained overload. Real data, inspectable
code, and results you can reproduce.

Built by **[Katenaria](https://katenaria.com)** for Ignition system integrators.
Follow our experiments, share your findings, and help us test what comes next.

## Try the lab

With Docker running, download the launcher for your platform:

[**Run experiment · macOS**](https://github.com/rtbot-dev/ignition-performance-lab/releases/download/v0.1.1/Run-experiment-mac.command) · [**Windows**](https://github.com/rtbot-dev/ignition-performance-lab/releases/download/v0.1.1/Run-experiment-windows.cmd) · [**Linux**](https://github.com/rtbot-dev/ignition-performance-lab/releases/download/v0.1.1/Run-experiment-linux.sh)

Open the downloaded launcher; on Linux, run `sh Run-experiment-linux.sh`.
It downloads a verified package, starts an isolated Ignition container, and opens
the lab. Accept Ignition's license when prompted, then click **Run test** in the UI.
First-run OS security prompts may appear. Docker Compose is required.

[Launcher details and source](docs/launchers.md) · [Run from source](benchmarks/jython-vibration/#run)

## Pick an experiment

| Experiment | What you will discover |
|---|---|
| [**Jython vibration analytics →**](benchmarks/jython-vibration/) | Replay real bearing recordings and find when computation stops keeping up. |

Setup, methodology, dataset details and tested platforms live inside each experiment.

## What happens on your machine?

[**Share a reproduction**](https://github.com/rtbot-dev/ignition-performance-lab/issues/new?template=reproduction.md) · [**Suggest the next experiment**](https://github.com/rtbot-dev/ignition-performance-lab/issues/new) · [**Add a benchmark**](CONTRIBUTING.md)

**Want more analytics power inside Ignition?** We also build **Coprocessor**, a
C++ computation engine for Ignition. [Explore what it can do](https://coprocessor.app)
or [talk to us about your workload](mailto:services@katenaria.com).

<sub>This first benchmark runs Jython alone, without Coprocessor. Limits depend on workload and resources. [MIT license](LICENSE) · [Third-party notices](benchmarks/jython-vibration/NOTICE.md)</sub>
