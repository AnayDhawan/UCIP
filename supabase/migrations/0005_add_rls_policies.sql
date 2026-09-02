-- Lock down anon key to read-only. Pipeline writes use the service_role key,
-- which bypasses RLS entirely, so no write policy is needed for it.
-- Public site only ever SELECTs these 5 tables.

alter table wards enable row level security;
alter table grid_cells enable row level security;
alter table interventions enable row level security;
alter table nbs_recommendations enable row level security;
alter table methodology_refs enable row level security;

create policy "public read" on wards
    for select to anon, authenticated using (true);

create policy "public read" on grid_cells
    for select to anon, authenticated using (true);

create policy "public read" on interventions
    for select to anon, authenticated using (true);

create policy "public read" on nbs_recommendations
    for select to anon, authenticated using (true);

create policy "public read" on methodology_refs
    for select to anon, authenticated using (true);
