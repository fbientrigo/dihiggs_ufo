# Pack AA operator commands

From any working directory run the absolute or repository-root wrapper: `bin/pack-aa preflight`, `validate-config CONFIG.yaml`, `run CONFIG.yaml`, `status`, `results`, `inspect-event RUN INDEX`, `demo`, or `clean --confirm`. Exit codes: 0 success, 1 AA1/config, 2 AA0/provenance, 3 runtime/AA2+, 21 stale pointer, 22 unsafe clean.
