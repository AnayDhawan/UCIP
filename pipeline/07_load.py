"""M2-M4 — Load results into Supabase (PostGIS) + write GeoJSON snapshots.

Planned:
- Upsert grid_cells, wards, nbs_recommendations, interventions, methodology_refs
  (schema per TRD B11, migrations in ../supabase/migrations/).
- ALWAYS also write GeoJSON snapshots to ../data/ — committed to the repo as the
  demo-safe fallback (judged demo must survive a dead DB; locked decision #6).
"""

raise NotImplementedError("Sprint M2-M4 — see docstring.")
