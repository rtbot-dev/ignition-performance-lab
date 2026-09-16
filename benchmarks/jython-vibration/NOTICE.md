# Attribution and software provenance

Ignition is supplied by Inductive Automation under its software license agreement.
The launcher requires explicit acceptance. No claim of endorsement is made.
https://inductiveautomation.com/ignition/license

Our distributable image contains the benchmark project on the official
Python base. The separate gateway service pulls the official Ignition image
directly from Inductive Automation. We do not republish Ignition binaries.
No Coprocessor or other third-party Ignition module is included.

The six bundled excerpts are from the IMS bearing dataset supplied by the Center
for Intelligent Maintenance Systems, University of Cincinnati, and hosted in the
NASA Prognostics Data Repository. Citation: J. Lee, H. Qiu, G. Yu, J. Lin, and
Rexnord Technical Services (2007), Bearing Data Set. Source and zero-based channel
indices are in provenance.json. NASA's catalog identifies the dataset as public
and links its license field to https://www.usa.gov/government-works.
https://data.nasa.gov/dataset/ims-bearings

The setup image uses the official Python Docker image. Its software keeps its
respective upstream licenses. No separate web dashboard is included.

Katenaria developed this benchmark and also develops Coprocessor. This experiment
measures Jython without Coprocessor installed. Reader results may be different.
