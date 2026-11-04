-- Correct the dominant_share column comment.
--
-- 0007 described an even spread across seven indicators as about 0.14. The index
-- now scores five (DIRECTIONS in pipeline/_indicators.py): the elderly share was
-- removed in 0008, and the under-7 and slum shares are carried as context and
-- never scored, so an even spread is 0.2. Comment only; no data changes.

comment on column wards.dominant_share is
    'That indicator''s share of the ward''s total absolute contribution, 0 to 1. With five indicators, an even spread is 0.2.';
