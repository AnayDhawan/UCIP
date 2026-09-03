-- Migrate ward and cell geometry from jsonb to real PostGIS geometry (issue #69).
--
-- 0001_init.sql stored geometry as `geom_geojson jsonb` on purpose: PostgREST
-- cannot cast a GeoJSON payload into a `geometry` column on insert without an
-- RPC or trigger round-trip, the frontend read straight off the committed
-- GeoJSON snapshots, and nothing needed a spatial query during the build. That
-- was the right call then and is the wrong one now.
--
-- What real geometry unlocks:
--   * ST_Contains, so a lat/lon can be resolved to its ward. That is the
--     point-to-ward lookup behind the public API and the "find my ward" button,
--     and it is the single feature a non-expert actually wants.
--   * Spatial joins and nearest-neighbour queries, without pulling every
--     polygon into the client first.
--   * A GiST index, so those queries stay fast as more cities land.
--
-- Both columns are kept for now. `geom_geojson` stays the source of truth for
-- this release so a partially-migrated database still serves the site, and
-- 07_load.py writes both. Dropping it is a separate migration once the API and
-- frontend have been running off `geom` for a release.

create extension if not exists postgis;

-- ---------------------------------------------------------------- columns ----
-- Ward boundaries are MultiPolygon (several BMC wards are split across
-- non-contiguous parts); grid cells are always a single square Polygon.
alter table wards      add column if not exists geom geometry(MultiPolygon, 4326);
alter table grid_cells add column if not exists geom geometry(Polygon, 4326);

-- ---------------------------------------------------------------- backfill ---
-- ST_GeomFromGeoJSON parses the existing jsonb, so no data leaves the database
-- and no pipeline re-run is needed to populate the new columns.
--
-- ST_Multi normalises a Polygon into a MultiPolygon so both shapes satisfy the
-- ward column's type constraint. ST_MakeValid guards against self-intersecting
-- rings, which do occur in real administrative boundary data and would
-- otherwise make ST_Contains raise rather than return false.
update wards
   set geom = ST_Multi(ST_MakeValid(ST_GeomFromGeoJSON(geom_geojson::text)))
 where geom is null
   and geom_geojson is not null;

update grid_cells
   set geom = ST_MakeValid(ST_GeomFromGeoJSON(geom_geojson::text))
 where geom is null
   and geom_geojson is not null;

-- ----------------------------------------------------------------- indexes ---
create index if not exists wards_geom_idx      on wards      using gist (geom);
create index if not exists grid_cells_geom_idx on grid_cells using gist (geom);

-- ----------------------------------------------------------------- triggers --
-- Keep `geom` derived from `geom_geojson` automatically.
--
-- The alternative was changing pipeline/07_load.py to send geometry twice, but
-- it cannot: PostgREST has no way to cast a GeoJSON payload into a geometry
-- column on insert, which is the original reason 0001_init.sql chose jsonb.
-- Deriving it in the database instead means the pipeline keeps writing exactly
-- what it writes today, and the two representations cannot drift, because there
-- is only one write path and it is this trigger.
create or replace function sync_geom_from_geojson()
returns trigger
language plpgsql
set search_path = public, pg_catalog
as $$
begin
    if new.geom_geojson is null then
        new.geom := null;
    else
        new.geom := ST_MakeValid(ST_GeomFromGeoJSON(new.geom_geojson::text));
        -- wards.geom is typed MultiPolygon; normalise a single Polygon into one.
        if TG_TABLE_NAME = 'wards' then
            new.geom := ST_Multi(new.geom);
        end if;
    end if;
    return new;
end;
$$;

drop trigger if exists wards_sync_geom on wards;
create trigger wards_sync_geom
    before insert or update of geom_geojson on wards
    for each row execute function sync_geom_from_geojson();

drop trigger if exists grid_cells_sync_geom on grid_cells;
create trigger grid_cells_sync_geom
    before insert or update of geom_geojson on grid_cells
    for each row execute function sync_geom_from_geojson();

-- ------------------------------------------------------------ ward_at() ------
-- Resolve a coordinate to its ward, with the headline figures attached.
--
-- Returns zero rows for a point outside every ward rather than raising, so the
-- API layer can answer "you are not in Mumbai" as an ordinary 404 rather than an
-- error.
--
-- Argument order is (lat, lon), matching how humans and the browser geolocation
-- API give coordinates. ST_MakePoint takes (x, y) which is (lon, lat), and
-- getting that backwards silently returns nothing, so it is done in one place
-- here rather than at each call site.
create or replace function ward_at(lat double precision, lon double precision)
returns table (
    ward_id text,
    hvi      numeric,
    rank     integer,
    n_cells  integer,
    contrib  jsonb
)
language sql
stable
parallel safe
set search_path = public, pg_catalog
as $$
    select w.ward_id, w.hvi, w.rank, w.n_cells, w.contrib
      from wards w
     where w.geom is not null
       and ST_Contains(w.geom, ST_SetSRID(ST_MakePoint(lon, lat), 4326))
     limit 1;
$$;

-- The function reads only the columns already exposed by the "public read"
-- policy in 0005_add_rls_policies.sql, so it grants no access that a plain
-- select would not. Declared stable and parallel safe so PostgREST can cache
-- and parallelise it.
grant execute on function ward_at(double precision, double precision) to anon, authenticated;
