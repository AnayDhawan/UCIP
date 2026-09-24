-- Remove the elderly share from the cell table (issue #167).
--
-- The value came from WorldPop's India age-sex product, which applies district
-- age structure to a population raster. Across the Mumbai grid it took two
-- meaningful values, one per revenue district, so it recorded which district a
-- cell sits in and not how old its residents are. No ward-level 60+ source
-- exists in the open Census tables, so the indicator was removed from the index
-- rather than published under a demographic label it does not earn.
--
-- Run this after the frontend deploy that stops selecting the column. Until
-- then the API's database path would fail on the missing column and serve the
-- snapshot instead, which is correct but logged as a fault.
--
-- The per-ward contribution is not a column: it lives inside the `contrib`
-- jsonb on `wards`, and the next sync replaces that object without the key.

begin;

alter table grid_cells drop constraint if exists chk_grid_cells_elderly_pct_range;
alter table grid_cells drop constraint if exists chk_elderly_pct_range;
alter table grid_cells drop column if exists elderly_pct;

commit;
