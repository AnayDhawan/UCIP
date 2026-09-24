# Preprint submission: what is done, and what needs you

Issue #90 asked for a preprint with a DOI, linked from the README, and said
plainly that **authorship and affiliation are Anay's call and this should not
be actioned unilaterally**. That is why this file exists instead of a
submission.

A preprint DOI is permanent and public. Posting one under someone's name, with
an affiliation, is not a step to take on their behalf.

## Done

The manuscript is `../HVI-methodology-report.md`, and it is submission-ready in
substance.

The issue named three gaps to close first. All three are closed, and two more
were added since:

| Gap | Status | Where |
|---|---|---|
| #65 ground-truth validation | Closed. Pooled within-station Pearson r = 0.716 against NOAA GSOD. | §6d |
| #87 uncertainty bands | Closed. 1000-replicate bootstrap; median rank interval 7 of 24 places, widest 19; no ward's rank certain. | §6a |
| #88 weight cross-validation | Closed. PCA against equal weighting: Kendall tau 0.754, 4 of 24 ranks identical, 3 of the top 5 shared. Dropping `child_pct` lifts tau to 0.957. | §6b |
| #96 cross-resolution check | Added. 500 m rebuild moves 13 of 24 wards, and all 24 fall inside their 1 km bootstrap intervals. | §6c |
| #95 indicator audit | Added. `elderly_pct` carried district, not sub-district, information and was removed. Real ward-level `child_pct` is the one age indicator. | §4, §10 |

§6c is the part worth submitting on. Two methods that share no machinery, a
bootstrap over cells and a rebuild at a different resolution, disagree about the
ordering and agree about which parts of the ordering carry information. That is
a stronger claim than either makes alone, and it is not a claim most indices of
this kind test at all.

§10 on `elderly_pct` is a negative result about our own indicator set, and the
indicator was removed on the strength of it. It is in the paper on purpose. The same WorldPop raster is widely used the same way, and
documenting that it resolves a district boundary rather than a demographic
gradient is arguably more useful to other people than the index itself.

The dataset already has a DOI, `10.5281/zenodo.22923919` (#84), so the paper can
cite its own data properly, which is half of what a preprint is for.

## Decided

Recorded 2026-09-24, so nobody has to ask again.

- **Authorship.** Anay Dhawan, sole author. No co-authors.
- **Affiliation.** None. Listed as an independent researcher, and no school is named.
- **Server.** EarthArXiv. Earth and environmental science, no peer review, free, issues a DOI. Submission is a moderation check for scope and usually clears in a couple of days. arXiv is the alternative, but a first submission there needs an endorsement in `physics.ao-ph`.
- **Manuscript licence.** CC-BY-4.0. This is the licence on the paper's text: anyone may copy, share and build on it if they credit the author. It is separate from the code's Apache-2.0 and from the data's per-source terms.

## Still open

**ORCID iD.** An ORCID account exists, but the iD itself (the `0000-0000-0000-0000` number) has not been given, and it has to go in the header.

**Email on the paper.** Whether `dhawansanay@gmail.com` is printed on it. That is public and permanent.

**A new dataset release, before submitting.** The Zenodo record the paper cites is at v1.0.2. That release predates two changes the paper describes: the plantability correction (section 7) and the eighth indicator `child_pct`. Someone who downloads v1.0.2 will not reproduce the paper's numbers. Tag a new release first, let the release workflow archive it, and the concept DOI then resolves to data that matches. Section 11 already tells readers to cite a later release than 1.0.2.

## Before you submit

- [ ] Give the ORCID iD and decide about the email; both go in the manuscript header
- [ ] Cut a new release so the archived data matches the paper
- [ ] Read section 10 in full. It is candid about the index's own weaknesses, on purpose, but your name goes on it and you should agree with every sentence before it becomes permanent
- [ ] Convert to PDF. `pandoc docs/HVI-methodology-report.md -o ucip-preprint.pdf` is enough, and most servers accept PDF only. Remove the italic draft-status note at the top first
- [ ] Check every figure still matches committed output. A pipeline refresh between now and submission changes numbers, and a preprint citing figures that no longer reproduce is worse than a late one. The twice-weekly refresh will move the satellite-derived values, so do this check on the day
- [ ] After it is posted: add the preprint DOI to `README.md` and `CITATION.cff`, and close #90

## What was deliberately not done

The paper has not been submitted, and no ORCID iD or email has been invented. Both are permanent and attributable, and the iD in particular has to be the real one.

## A note on how the paper was written

It was rewritten in plain prose after the numbers changed, and checked mechanically for em dashes, curly quotes, the usual filler vocabulary and negative parallelisms. Every figure was recomputed from the committed output files and not copied from the earlier draft. Two claims in it were checked against the code before being written down: the cooling-centre rule's comparison operator, and the count of hot, bare cells that are built-up land.
