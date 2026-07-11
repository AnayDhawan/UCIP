"""M4 — Nature-Based Solutions rule engine + ecological plantability filter (F3+F4).

Planned (sprint Aug 4):
- Plantability flag per cell/ward: restoration-suitable AND not native
  grassland/savanna (Bastin 2019 potential, Veldman 2019 constraint).
- Rules (each fired rule carries a rationale string + citation):
    HVI high + canopy low + plantable      -> native trees + green corridors [Bastin]
    HVI high + canopy low + NOT plantable  -> cool roofs + reflective pavements + cooling centres [Veldman]
    impervious high + flood-prone          -> rain gardens + WSUD
    density high + open space low          -> pocket parks
    elderly high + hospital access low     -> cooling centres priority
- Output: nbs_recommendations rows per ward (intervention, rationale, citation, priority).
The "ward REJECTED for trees, assigned cool roofs" moment is the headline demo beat.
"""

raise NotImplementedError("Sprint M4 (Aug 4) — see docstring.")
