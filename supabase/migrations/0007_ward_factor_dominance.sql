-- Record which indicator drives each ward's score (issue #97).
--
-- The index is a weighted sum of seven indicators and `contrib` already stores
-- each factor's contribution per ward, but nothing said whether one of them was
-- carrying the ward on its own. A ward scoring high because it has almost no
-- tree cover is a different recommendation problem from one scoring high across
-- all seven, and a planner needs to tell them apart.
--
-- Computed in the pipeline (pipeline/_hvi.py) rather than derived in SQL, so
-- the threshold lives in one place and the published GeoJSON, the CSV export
-- and the database all carry the same answer. Deriving it here as well would be
-- a second definition to keep in sync.
--
-- Nullable on purpose: a ward whose contributions are all zero has no dominant
-- factor, and inventing one would be worse than saying nothing.

begin;

alter table wards
    add column if not exists dominant_factor text,
    add column if not exists dominant_share numeric,
    add column if not exists single_factor_dominated boolean;

-- A share is a fraction of total absolute contribution, so it cannot leave 0..1.
alter table wards
    drop constraint if exists wards_dominant_share_range;
alter table wards
    add constraint wards_dominant_share_range
    check (dominant_share is null or (dominant_share >= 0 and dominant_share <= 1));

comment on column wards.dominant_factor is
    'Indicator with the largest absolute contribution to this ward''s HVI.';
comment on column wards.dominant_share is
    'That indicator''s share of the ward''s total absolute contribution, 0 to 1. An even spread across the seven indicators is about 0.14.';
comment on column wards.single_factor_dominated is
    'True when dominant_share is at least 0.5, i.e. one indicator accounts for half or more of the movement in the score. See DOMINANCE_THRESHOLD in pipeline/_hvi.py.';

commit;
