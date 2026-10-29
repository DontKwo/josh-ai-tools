# Engineering & Human Reviewability Directives

## Code Structure & Readability
- Prefer straightforward loops and explicit state transitions over nested comprehensions or generator reductions.
- Decompose multi-operation equations into named intermediate terms (`term1`, `term2`, `num`, `denom`, `exp`). Expressions may extend up to 140 characters. Never artificially split equations across lines.
- Name engineering and thermodynamic calculation functions descriptively (e.g. `compute_T0_from_T`, `calc_ISP_from_TSFC`, `eval_m_prop`).
- Suffix ambiguous quantities with physical units (`_kg`, `_m`, `_pa`, `_deg`, `_psi`, `_kw`). Use standard domain shorthand (`gam`, `cp`, `R`, `T04`, `TSFC`, `ISP`, `GLOW`, `TW0`, `dV`). Provide unit conversion helpers (`lb2kg`, `deg2rad`) or use `pint.UnitRegistry`.
- Place physical constants as keyword defaults in signatures (`gam: float = 1.4`, `cp: float = 1005.0`, `R: float = 287.0`).
- Structure modular computation scripts into discrete problem functions (`prob1()`, `prob2()`, `main()`).
- Use explicit forward time-stepping loops (`for t_step in t:`) and plain lists for simulation.
- Favor plain dictionaries and data structures over abstract base classes or deep inheritance in numerical code.
- Accumulate constraint violations in dictionary counters instead of aborting loops with exceptions.
- Never write multi-line docstrings (`Args:`, `Returns:`) for short mathematical functions. Never use decorative divider banners.

## Multi-Language Standards
- Python: Use Matplotlib with raw LaTeX labels (`r'$T_0/T_x$'`), `plt.grid(True)`, and shared axes.
- C++: Use `#pragma once`, `#define M_PI`, templated solvers, capture lambdas (`[&]`), and Eigen.
- MATLAB: Use `readmatrix`, in-place table filtering, and anonymous function handles.
