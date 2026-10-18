# Archive Directory

This directory stores legacy scripts, prototype code, and superseded intermediate documentation that have been consolidated into the primary project artifacts.

## Contents

### 1. `docs/` (Superseded & Intermediate Markdown Documentation)
The following files were intermediate drafting notes, literature summaries, and standalone reports that have been unified into [`CURRENT_STATUS.md`](../CURRENT_STATUS.md) and [`paper_draft.md`](../paper_draft.md):
- `BASELINE_EXPERIMENTS_REPORT.md` (Pristine baseline evaluation; incorporated into manuscript Sections 4 & 5)
- `IMPAIRMENTS_EXPERIMENTS_REPORT.md` (Parametric sweep report; incorporated into manuscript Sections 6 & 7)
- `COMPREHENSIVE_EXPERIMENTS_ANALYSIS_AND_LITERATURE_EVALUATION.md` (Literature cross-validation reference)
- `PLOTS_DESCRIPTION_AND_VALIDATION.md` (Visual analysis notes)
- `theory.md` (Theoretical transport models; incorporated into manuscript Section 3)
- `NEW_PAPER_AND_JOURNAL_STORY.md`, `NEW_PAPER_STORY.md`, `NEW_PAPER_STORY_ADDITIONS`, `PAPER_STORYLINE.md` (Brainstorming storylines; unified in `CURRENT_STATUS.md`)
- `paper_idea.md` (Legacy scratch file)

### 2. `legacy_code/` (Prototype & Deprecated Codebases)
- `original_scripts/`: Early emulation scripts prior to production refactoring in `scripts/`.
- `MANUAL_ANALYSIS/`: Prototype Python parsing and plotting routines, superseded by `analyze_baseline_results.py` and `analyze_impairments_results.py`.

### 3. Standalone Prototype Scripts
- `analyze_sweeps.py`: Early prototype tool created to analyze Experiment 3 (TCP CUBIC parametric sweeps only). Superseded by [`analyze_impairments_results.py`](../analyze_impairments_results.py).
