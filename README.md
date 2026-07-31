# Network Emulation Paper Repository

This repository contains the LaTeX source, reproduction scripts, and the full set of experiment results for the paper titled:

A Lightweight Kernel-Native Emulation Framework for Transport Dynamics and Labeled Trace Generation in Heterogeneous Handovers

## Structure

- `PAPER/` — paper source and PDF
- `scripts/` — emulation and orchestration scripts
- `results/raw/` — run-level CSV and JSON outputs
- `results/derived/` — summary CSVs and table payloads
- `results/figures/` — plots and exported figures

## Reproducibility

The main reproduction entry point is:

```bash
python3 scripts/batch_runner.py
```

This script uses the configuration in `scripts/config.json` and invokes the emulation harness in `scripts/lftp-migration-test.sh`.

## Notes

The repository is intended to be used as the single Git repository for the paper and its associated experiments.

The workspace root may still contain legacy copies of raw result files, but `paper_repo/results/` is the canonical home for all results used by the paper.

The repository currently preserves the old flat `results/` path only where required by existing paper references; new outputs should land in the subfolders above.
