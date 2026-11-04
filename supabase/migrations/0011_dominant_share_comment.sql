-- Correct the dominant_share column comment.
--
-- 0007 described an even spread across seven indicators as about 0.14. Mumbai's
-- index now runs on five (the elderly share was removed in 0008, and the child
-- and slum shares are optional inputs Mumbai's run does not carry), so an even
-- spread is 0.2. Comment only; no data changes.

comment on column wards.dominant_share is
    'That indicator''s share of the ward''s total absolute contribution, 0 to 1. With five indicators, an even spread is 0.2.';
