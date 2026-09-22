# Routing test evidence

The routing tests construct all candidate names, provider choices, host snapshots,
evidence hashes and evaluation records synthetically in their fixture builders.
These inputs test the public contract and arithmetic only. They are not live
TypeSafe results, real host attribution, calibrated quality thresholds, measured
model prices, or qualification evidence. No key or paid API call is required.

`test_routing.py` covers the routing helper/CLI and injected provider seam.
`test_routing_evaluation.py` covers held-out, per-scope comparison to both baselines.
`test_routing_packaging.py` copies the promised generated helper into isolated
standalone/native layouts, removes the fixture source, then executes its API/CLI.
Default HTTP TLS, redirect refusal and wall-clock deadlines remain subject to
independent security/reliability review without assuming a private HTTP library.
