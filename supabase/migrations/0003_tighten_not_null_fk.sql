-- UCIP Batch E (#22): NOT NULL tightening + FK documentation.
-- Verified against current data snapshots:
--   wards_hvi.geojson          → ward_gid non-null in all 24 wards
--   cells_hvi.geojson          → ward_id non-null in all 541 cells
--   nbs_recommendations.json   → ward_id present in every row (grid_id absent)
--
-- No column is made NOT NULL that current data needs null for.

-- ── wards: tighten nullable columns verified non-null ────────────────
alter table wards
    alter column ward_gid set not null;

alter table wards
    alter column hvi set not null;

alter table wards
    alter column rank set not null;

alter table wards
    alter column n_cells set not null;

-- ── grid_cells: ward_id FK NOT NULL ─────────────────────────────────
-- Every grid cell belongs to a ward; ward_id is always present in snapshots.
alter table grid_cells
    alter column ward_id set not null;

-- ── nbs_recommendations: ward_id NOT NULL ───────────────────────────
-- Ward-level recommendations always carry a ward_id.
-- Grid-level rows (with grid_id) are not yet in the dataset; keeping
-- grid_id nullable for future use — see note below.
alter table nbs_recommendations
    alter column ward_id set not null;

-- ── nbs_recommendations: natural-key FK documentation ────────────────
-- interventions.name is used as the FK target for the `intervention`
-- column.  This is a deliberate natural-key choice: intervention names
-- are stable domain vocabulary (never renamed in practice), and using
-- them avoids a surrogate-id join that would obscure the data model in
-- a dataset this small (~24 wards, ~69 rows).  If intervention names
-- ever need to change, a migration can add a surrogate key then.
comment on column nbs_recommendations.intervention is
    'FK → interventions(name).  Natural key: names are stable domain vocabulary; '
    'surrogate id not warranted at current dataset scale.';
