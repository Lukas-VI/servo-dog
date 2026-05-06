# Reference Research

## Lukas-VI/servo-dog

Repository: https://github.com/Lukas-VI/servo-dog

Observed state on 2026-04-29:

- Public repository.
- One commit on `main`: `03c4b61fd100d7e2a9fbb7c465e6f9d52f3ba897`.
- Files visible from GitHub: `README.md`, `LICENSE`.
- README content is only `# servo-dog`.
- License is MIT.

Conclusion: this repository currently has no implementation to port or compare
against. It should not steer our control architecture until it gains actual
servo, gait, vision, or deployment code.

## Current Useful References

- Existing local `edog-brain` remains the authoritative source for serial frames
  and action ID mapping.
- Existing local `edog-track` remains useful only for task-state behavior and old
  color thresholds.
- New Python mainline should continue to prefer direct serial control plus
  dry-run testing over copying the old Qt/LCM structure.

