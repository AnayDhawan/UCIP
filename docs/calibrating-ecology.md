# Calibrating the plantability filter for a new city

This is the part of the city template that cannot be automated, and the part
where a mistake is worse than not using the tool at all.

Everything else in UCIP travels. The Heat Vulnerability Index recomputes its
weights from each city's own data. The grid derives its projection from the
bounding box. The indicators are standardised per city, so "hot" means hot for
that city.

The plantability filter does not travel. It encodes assumptions about Mumbai's
ecology, and applied unexamined elsewhere it will confidently recommend
planting trees on habitat that should stay open. That is the failure
[Veldman et al. 2019](https://doi.org/10.1126/science.aay7976) describe in
their response to [Bastin et al. 2019](https://doi.org/10.1126/science.aax0848),
and refusing to make it is what distinguishes this project from a
greening-is-always-good map.

A wrong index gives a city a bad priority order. A wrong plantability filter
gives it a scientific justification for destroying a grassland.

## What the filter actually asserts

Three claims, in `pipeline/_nbs.py`. Each is true for Mumbai and none is true
everywhere.

### 1. WorldCover class 30 is native habitat to protect

```python
WORLDCOVER_GRASSLAND = 30
```

ESA WorldCover class 30 is "herbaceous vegetation". In Mumbai that is mostly
genuine open habitat, so the filter refuses to plant it.

**This is the claim most likely to be wrong elsewhere, in both directions.**

- In a **tropical grassland or savanna** biome (the Cerrado, the Deccan, East
  African savanna, the Terai), class 30 is ancient, species-rich and
  fire-adapted. Planting it is habitat destruction that looks like climate
  action. The refusal must stay, and may need to widen.
- In a **temperate city** where class 30 is mown amenity grass, motorway verge
  or abandoned lot, refusing to plant it is simply wrong. You will reject the
  easiest planting sites in the city and recommend cool roofs instead.

There is no way to tell these apart from the raster. Class 30 means the same
pixel signature and two opposite things on the ground.

### 2. Built-up, water, wetland and mangrove cannot be planted

```python
WORLDCOVER_NONPLANTABLE = {50, 80, 90, 95}
```

Class 50 built-up, 80 permanent water, 90 herbaceous wetland, 95 mangrove.
This one travels well and rarely needs changing. Note that it protects
mangroves by refusing them, which is correct: a mangrove is already doing the
job, and "planting" it means replacing it.

Classes deliberately **not** listed, and worth a thought for your city:

| Class | What it is | Why it is currently plantable |
|---|---|---|
| 10 | Tree cover | Already treed; the filter allows it, but a hot cell with existing canopy rarely triggers the rule anyway |
| 20 | Shrubland | Often degraded and genuinely plantable, but in a Mediterranean or fynbos biome it is native habitat and should join class 30 |
| 40 | Cropland | Plantable in principle. Whether that is socially acceptable is not an ecological question and the filter does not try to answer it |
| 60 | Bare / sparse | Plantable in a temperate city, often native desert elsewhere |

**If your city is Mediterranean, semi-arid or in a fynbos, chaparral, matorral
or karoo biome, class 20 probably belongs with 30.** Shrubland in those systems
is not degraded forest waiting to be restored.

### 3. Room to plant is the local 75th percentile of imperviousness

```python
is_plantable(worldcover_class, impervious_pct, thresholds["impervious_p75"])
```

A cell is refused if it is more sealed than three quarters of the city's cells.

Relative rather than absolute, which travels better than a fixed number: "very
sealed for this city" means something in Mumbai and in Nairobi, where "over
60% impervious" would not.

But it still assumes a distribution shape. In a compact, uniformly dense city
the 75th percentile sits somewhere meaningful. In a city with a dense core and
large open tracts, the distribution is bimodal, the percentile lands in the
empty middle, and the cutoff separates almost nothing.

**Plot your city's `impervious_pct` histogram before trusting this.** If it is
bimodal, a percentile is the wrong instrument and you want a threshold chosen
by looking at the two modes.

## What to do, in order

1. **Name the biome.** Not the country or the climate zone: the biome. "Deccan
   plateau, semi-arid to tropical dry deciduous" is useful. "India" is not.

2. **Find out what class 30 is there.** The literature you want is regional
   restoration and land-cover ecology, not global restoration-potential
   mapping, since global maps are exactly what Veldman was arguing with. Look
   for work on whether the region's open habitat is ancient grassland or
   degraded forest. That dispute usually already exists in print for any given
   region, and you are picking a side with evidence rather than inventing one.

3. **Check class 20 as well.** See above.

4. **Plot the imperviousness histogram.** One command against your city's
   `cells.geojson`. Decide whether a percentile is meaningful.

5. **Write down what you decided and why**, in `ecology.notes` in the city
   config. Not "calibrated for Pune", but which classes you treat as native,
   what evidence, and what you were unsure about. The next person needs your
   reasoning, not your conclusion.

6. **Only then set `calibrated: true`.**

## What `calibrated: true` claims

That a person read the regional literature, decided which land-cover classes
are native open habitat in this city, and checked the impervious cutoff
against the real distribution.

It does not claim the answer is right. It claims someone competent looked.

`validate_cities.py` warns while the flag is false:

```
[WARN] pune.json: ecology.calibrated is false, so this city's plantability
       recommendations are not trustworthy yet.
```

That warning is doing its job. Flipping the flag to silence it, without doing
the work, converts an honest "we have not checked this" into a false claim that
we have. **It is the one field in the whole config that cannot be inferred,
derived or defaulted, which is why the scaffolder refuses to set it and offers
no flag to.**

## Worked example: Mumbai, calibrated

```json
"ecology": {
  "biome": "Tropical coastal, moist deciduous and mangrove",
  "calibrated": true
}
```

Coastal western India. Class 30 is mostly genuine open habitat, so it is
refused. Mangrove (95) is refused as already-functioning habitat rather than a
planting site. Imperviousness is unimodal across the 541 cells, so a percentile
cutoff is meaningful. Class 20 is sparse enough not to matter.

## Worked example: Pune, not calibrated

```json
"ecology": {
  "biome": "Deccan plateau, semi-arid to tropical dry deciduous",
  "calibrated": false,
  "notes": "NOT calibrated. Pune sits on the Deccan plateau and its surroundings
            include genuinely native grassland and scrub, which Mumbai's coastal
            thresholds were never designed to distinguish..."
}
```

Pune is the harder case and that is why it ships uncalibrated rather than
guessed. The Deccan has native grassland and scrub that Mumbai's thresholds
cannot tell from degraded land, and class 20 shrubland there is a real
candidate for protection rather than planting. Until someone reads the Deccan
restoration literature and decides, Pune's plantability output should not be
acted on.

That is not a gap in the project. A tool that says "I have not been checked
here" is more useful than one that guesses confidently.

## Related

- `pipeline/_nbs.py`, where all three assumptions live
- `docs/adding-a-city.md` §5, the short version of this page
- `docs/references.md` for the Bastin and Veldman citations
- Issue #110, which asked for this guide
