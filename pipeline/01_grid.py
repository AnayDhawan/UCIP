"""M1/M2 — Generate the Mumbai analysis grid.

Planned (sprint Aug 1):
- Load BMC 24-ward boundaries from ../data/ (Datameet GeoJSON).
- Build a 1 km fishnet grid over the Mumbai bounding box (geopandas/shapely).
- Clip cells to ward geometry; assign each cell its ward_id.
- Write ../data/grid_1km.geojson.

Resolution is a parameter: rerun at 500 m later if time allows (locked decision #4).
"""

raise NotImplementedError("Sprint M1 (Aug 1) — see docstring.")
