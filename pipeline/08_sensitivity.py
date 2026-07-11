"""M5 — Weight-perturbation sensitivity check (council blind-spot fix #3).

Planned (sprint Aug 5, cheap + high-signal):
- Perturb each HVI weight +/-20% (Monte Carlo or one-at-a-time).
- Recompute ward ranking per perturbation; measure top-5 ranking stability
  (e.g. Kendall tau / rank-change counts).
- One chart for the methodology page: "the ward priority order is stable under
  +/-20% weight perturbation." Preempts the hardest researcher-judge question:
  "did you validate these literature weights for Mumbai?"
"""

raise NotImplementedError("Sprint M5 (Aug 5) — see docstring.")
