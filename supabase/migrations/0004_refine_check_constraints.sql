-- UCIP Batch E refine (#21 follow-up): rename CHECK constraints to table-prefixed names + add n_cells guard.
-- 0002_add_check_constraints.sql is immutable (already applied in #44) — this migration refines it forward.
-- Renames generic constraint names (chk_hvi_range etc) to descriptive chk_<table>_* names
-- and adds the missing chk_wards_n_cells_positive guard.
-- Verified against current data snapshots:
--   wards_hvi.geojson  → hvi ∈ [26.8, 73.6], rank ∈ [1, 24], n_cells ∈ [2, 61]
--   cells_hvi.geojson  → hvi ∈ [8.4, 83.2], elderly_pct ∈ [4.8, 5.6],
--                         slum_pct ∈ [0, 45.7], impervious_pct ∈ [0, 88.1]
--   nbs_recommendations.json → priority ∈ [1, 3]
-- All existing data passes these constraints; no rows violate the ranges below.

-- ── wards: drop generic names, re-add with table prefix ─────────────
alter table wards drop constraint if exists chk_hvi_range;
alter table wards drop constraint if exists chk_rank_positive;
-- n_cells guard is new (no prior constraint to drop)
alter table wards drop constraint if exists chk_wards_hvi_range;
alter table wards drop constraint if exists chk_wards_rank_positive;
alter table wards drop constraint if exists chk_wards_n_cells_positive;

alter table wards add constraint chk_wards_hvi_range check (hvi >= 0 and hvi <= 100);
alter table wards add constraint chk_wards_rank_positive check (rank > 0);
alter table wards add constraint chk_wards_n_cells_positive check (n_cells > 0);

-- ── grid_cells: drop generic names, re-add with table prefix ────────
alter table grid_cells drop constraint if exists chk_hvi_range;
alter table grid_cells drop constraint if exists chk_elderly_pct_range;
alter table grid_cells drop constraint if exists chk_slum_pct_range;
alter table grid_cells drop constraint if exists chk_impervious_pct_range;
alter table grid_cells drop constraint if exists chk_grid_cells_hvi_range;
alter table grid_cells drop constraint if exists chk_grid_cells_elderly_pct_range;
alter table grid_cells drop constraint if exists chk_grid_cells_slum_pct_range;
alter table grid_cells drop constraint if exists chk_grid_cells_impervious_pct_range;

alter table grid_cells add constraint chk_grid_cells_hvi_range check (hvi >= 0 and hvi <= 100);
alter table grid_cells add constraint chk_grid_cells_elderly_pct_range check (elderly_pct >= 0 and elderly_pct <= 100);
alter table grid_cells add constraint chk_grid_cells_slum_pct_range check (slum_pct >= 0 and slum_pct <= 100);
alter table grid_cells add constraint chk_grid_cells_impervious_pct_range check (impervious_pct >= 0 and impervious_pct <= 100);

-- ── nbs_recommendations: drop generic name, re-add with table prefix ─
alter table nbs_recommendations drop constraint if exists chk_priority_positive;
alter table nbs_recommendations drop constraint if exists chk_nbs_priority_positive;

alter table nbs_recommendations add constraint chk_nbs_priority_positive check (priority > 0);
