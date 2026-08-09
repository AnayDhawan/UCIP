-- Guard bounded scores and positive ordering values from invalid writes.

alter table wards
    add constraint chk_hvi_range check (hvi >= 0 and hvi <= 100),
    add constraint chk_rank_positive check (rank > 0);

alter table grid_cells
    add constraint chk_hvi_range check (hvi >= 0 and hvi <= 100),
    add constraint chk_elderly_pct_range check (elderly_pct >= 0 and elderly_pct <= 100),
    add constraint chk_slum_pct_range check (slum_pct >= 0 and slum_pct <= 100),
    add constraint chk_impervious_pct_range check (impervious_pct >= 0 and impervious_pct <= 100);

alter table nbs_recommendations
    add constraint chk_priority_positive check (priority > 0);
