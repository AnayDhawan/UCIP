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
| #87 uncertainty bands | Closed. 1000-replicate bootstrap; median rank interval 6 of 24 places; no ward's rank certain. | §6a |
| #88 weight cross-validation | Closed. PCA against published weighting: Kendall tau 0.913, 13 of 24 ranks identical. | §6b |
| #96 cross-resolution check | Added. 500 m rebuild moves 8 of 24 wards, and all 24 fall inside their 1 km bootstrap intervals. | §6c |
| #95 indicator audit | Added. `elderly_pct` carries district, not sub-district, information. | §10 |

§6c is the part worth submitting on. Two methods that share no machinery, a
bootstrap over cells and a rebuild at a different resolution, disagree about the
ordering and agree about which parts of the ordering carry information. That is
a stronger claim than either makes alone, and it is not a claim most indices of
this kind test at all.

§10 on `elderly_pct` is a negative result about our own indicator set. It is in
the paper on purpose. The same WorldPop raster is widely used the same way, and
documenting that it resolves a district boundary rather than a demographic
gradient is arguably more useful to other people than the index itself.

The dataset already has a DOI, `10.5281/zenodo.22923919` (#84), so the paper can
cite its own data properly, which is half of what a preprint is for.

## Needs you

**1. Authorship.** Single author, or do Yash and Shaurya belong on it? They
contribute to StudentSuite; I do not know what, if anything, either contributed
to this specific work, and guessing in either direction is wrong. Nobody should
appear on a paper without being asked.

**2. Affiliation.** "Independent researcher" is a legitimate and common choice
and is probably the accurate one. If you would rather list your school, ask them
first: some institutions require review before their name goes on a preprint,
and doing it the other way round is the kind of thing that causes a real
problem later.

**3. ORCID.** Free, takes ten minutes at <https://orcid.org/register>, and
permanently disambiguates your name from every other A. Dhawan. Worth doing
before the first preprint rather than after, because retrofitting it across
records is tedious.

**4. Server.** EarthArXiv is the obvious fit: it takes earth and environmental
science, requires no peer review, issues a DOI, and is free.
[eartharxiv.org](https://eartharxiv.org/). Submission is a moderation check for
scope, not review, and usually clears in a couple of days. Alternatives are
arXiv, which needs an endorsement in `physics.ao-ph` and is therefore slower for
a first submission, and SSRN, which is a worse fit for this subject.

**5. Licence for the manuscript.** The code is Apache-2.0 and the data has its
own per-source terms. A preprint is usually CC-BY-4.0. That is a separate
decision from the repository's licence and EarthArXiv will ask for it.

## Before you submit

- [ ] Fill authorship and affiliation in the manuscript header
- [ ] Read §10 in full. It is unusually candid about the index's own weaknesses,
      and that is deliberate, but you are the one whose name goes on it and you
      should agree with every sentence of it before it becomes permanent
- [ ] Convert to PDF. `pandoc docs/HVI-methodology-report.md -o ucip-preprint.pdf`
      is enough; most servers accept PDF only
- [ ] Check every figure in the manuscript still matches committed output. A
      pipeline refresh between now and submission changes numbers, and a
      preprint citing figures that no longer reproduce is worse than a late one.
      `python pipeline/run_pipeline.py --dry-run` will tell you whether anything
      has been rerun
- [ ] Cite the dataset DOI, `10.5281/zenodo.22923919`, in the references
- [ ] After it is posted: add the preprint DOI to `README.md` and
      `CITATION.cff`, and close #90

## What I deliberately did not do

Submit it. Fill in an author. Pick an affiliation. Invent an ORCID. Choose a
licence on your behalf. Each of those is permanent and attributable to you.
