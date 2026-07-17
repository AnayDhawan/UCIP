-- UCIP initial schema — wards, grid cells, NBS recommendations, interventions, citations.
-- Locked decision: Supabase + PostGIS from Day 0, GeoJSON snapshots are the demo-safe fallback
-- (see docs/methodology.md, ucip/TODO.md).
--
-- Geometry storage: `geom_geojson jsonb` (raw GeoJSON), not a native PostGIS `geometry` column.
-- Rationale: PostgREST inserts can't cast a GeoJSON payload into `geometry` without an RPC/trigger
-- round-trip, and the frontend + demo path already reads straight off the GeoJSON snapshot files
-- (locked decision), never off live PostGIS geometry. jsonb gets a working REST upsert with zero
-- extra moving parts; postgis stays enabled for any future server-side spatial query need.

create extension if not exists postgis;

create table if not exists wards (
    ward_id      text primary key,          -- BMC split-ward code, e.g. 'F/N', 'C'
    ward_gid     integer not null,
    hvi          numeric,                   -- 0-100, mean of member grid_cells
    rank         integer,                   -- 1 = most vulnerable
    n_cells      integer,
    contrib      jsonb,                     -- per-factor contribution breakdown (mean over cells)
    geom_geojson jsonb not null             -- WGS84 (EPSG:4326) GeoJSON geometry
);

create table if not exists grid_cells (
    grid_id           text primary key,     -- e.g. 'cell_0001'
    ward_id           text references wards(ward_id),
    area_m2           numeric,
    lst_c             numeric,
    ndvi              numeric,
    ndvi_prev         numeric,
    pop_density_km2   numeric,
    elderly_pct       numeric,
    slum_pct          numeric,
    hospital_dist_m   numeric,
    impervious_pct    numeric,
    hvi               numeric,              -- 0-100
    contrib           jsonb,                 -- per-factor contribution breakdown (weight x z-score)
    worldcover_class  integer,
    dist_to_water_m   numeric,
    plantable         boolean,
    geom_geojson      jsonb not null         -- WGS84 (EPSG:4326) GeoJSON geometry
);

create index if not exists grid_cells_ward_id_idx on grid_cells (ward_id);

create table if not exists interventions (
    name         text primary key,          -- e.g. 'Native tree planting + green corridors'
    category     text,                      -- greening | reflective | water | siting
    citation     text,
    description  text
);

create table if not exists nbs_recommendations (
    id           bigint generated always as identity primary key,
    ward_id      text references wards(ward_id),
    grid_id      text references grid_cells(grid_id),  -- null for ward-level-only rows
    intervention text references interventions(name),
    rationale    text not null,
    citation     text not null,
    priority     integer not null,
    cell_count   integer
);

create index if not exists nbs_recommendations_ward_id_idx on nbs_recommendations (ward_id);

create table if not exists methodology_refs (
    short_name  text primary key,           -- e.g. 'reid2009', 'bastin2019'
    citation    text not null,
    doi         text,
    "usage"     text,                       -- what it justifies, mirrors docs/references.md
    verified    boolean default false
);
