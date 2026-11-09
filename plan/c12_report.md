# Chunk 12: Report and final slides

- **Depends on:** chunk 11 (the final run)
- **Learn first:** Theory Guide §10 (self-test questions); you should be able to answer every one
- **Time:** 2-3 working sessions with Claude Code for the report, one in the Project chat for the slides;
  no compute
- **Read this yourself:** every sentence. You present and defend this.

## Goal

A report (due Dec 18) and a talk (Dec 15) where every number comes from `results/` and every claim is either
proved, cited, or labelled as measured.

## What to build

- `report/make_numbers.py`: reads `results/*.csv` (the chunk 11 run only) and writes `report/numbers.tex`, one
  `\newcommand` per number used in the text (for example `\kappaTwoLimit`, `\tinyConstant`, `\cgTinyErrSixForty`).
  The report body never contains a hand-typed result; only macros. Rerunning the script must reproduce the file
  exactly.
- `report/report.tex` (or Markdown converted with pandoc if you prefer; Overleaf works for LaTeX), about 10-12
  pages plus appendix, figures from `figures/`:
  1. The game and the linear system (model, A = I - Q, relabeling, closed forms as checks).
  2. The matrix: M-matrix, exact spectrum by reflections, kappa_2 and kappa_inf (chunk 1).
  3. Direct solvers: envelope fill formula, orderings, n^{3/2} flops for nested dissection, backward
     stability (chunk 2).
  4. Iterative solvers: CG against its bound, finite termination for b = 1, preconditioners, the SOR 3/4 law,
     the FFT solver (chunks 3, 5, 6).
  5. **Main result: accuracy of tiny probabilities** (chunks 4 and 7): cond_i = 2 E[T | event], normwise
     stopping fails as cond_tiny * rtol, the three fixes, and the structured condition number explaining GTH.
  6. Applications: ICM error (chunk 8), four players (chunk 9), optional extras (chunk 10).
  7. What is new here, what is known (cite), what is conjecture (the 3/4 law).
  Appendix: reproducibility (commit hash, machine, how to rerun), the test suite and what it checks.
- `checks/check_report.py`: every macro used in `report.tex` is defined in `numbers.tex`, every `\includegraphics`
  file exists, and `make_numbers.py` reproduces `numbers.tex` byte for byte.

## Slides

Build the final deck in the Claude Project chat (Slides artifact) from the figures and the report's numbers, so
you can edit it yourself. Ask Ming Gu for the time limit if it has not been announced. A good shape for about
12 minutes: problem (1 slide), the matrix and its exact spectrum (1), solvers predicted vs measured (2), the
tiny-probability problem (2), the fixes and why GTH works (2), applications (1), conclusions (1).

## Done when

- [ ] `python report/make_numbers.py && python checks/check_report.py` passes.
- [ ] The report compiles and every figure and number traces back to a CSV.
- [ ] David has read it; the Project chat has done a final sanity check of claims against the chunk reports.
- [ ] Committed as "chunk 12: report".
