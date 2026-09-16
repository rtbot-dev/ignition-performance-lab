# Measuring sustainable capacity

The question is whether a fixed computation can keep up with a fixed arrival rate
under a specified resource allocation, not how many tags Ignition can store.

For Jython, record successful publications P and callback entries S. P − S is an
estimate of events waiting to start **before event loss**. Publications and callback
entry observations are not a single atomic snapshot: short races add noise.
After a missed-event flag, the difference also includes dropped events and must
not be plotted as queue length. The UI marks it unknown and interrupts the curve.

Sustained positive growth after startup means the offered load is unsustainable,
even when every submitted job eventually drains. A startup rise followed by a
plateau or decline is not, by itself, overload. Use time averages and repeated
longer runs near a boundary. The included classifier makes its tolerance explicit.
A finite flat run is evidence for that observation window, not a lifetime guarantee.

Count missed-event flags separately from missing output identities: a flag is not
an exact lost-event count. Verify each output against an independent reference.
Reject runs whose publisher misses its intended schedule or whose results are wrong.

The lab CPU trace uses JVM process CPU time divided by elapsed wall time: 100%
means one CPU equivalent. Heap is used JVM heap / maximum JVM heap. Docker Stats
reports container CPU and memory, which includes memory beyond Java heap. CPU quota
is not physical core pinning. On Docker Desktop, record its Linux VM allocation too.

The UI and observer add overhead inside the tested gateway. They are included in
this experiment's cost. Keep the same observer settings when comparing runs.
