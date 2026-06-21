# Stale final.mp4 / deliverable naming regression (2026-06-06)

## Symptom
`videos/TO_UPLOAD/final.mp4` appeared instead of the expected `<TITLE>.mp4`, or an old temp final was left behind after the app already wrote the correct title-named MP4.

## Root cause
Two issues showed up during subtitle/style iteration:
1. `main()` wrote the render target to a generic `final.mp4` instead of deriving the deliverable filename from `--title`.
2. After fixing the title-named output, the intermediate/temp `final.mp4` was not cleaned up, so both files existed in `TO_UPLOAD`.

## Contract
- The only 2026-06-06 contract is: `TO_UPLOAD/<TITLE>.mp4` is the deliverable.
- No extra `final.mp4` should remain in `TO UPLOAD` after a successful run.

## Fix
- Render directly to `TO_UPLOAD/dest = TO_UPLOAD / f"{args.title}.mp4"`.
- Verify `dest` after render.
- Prefer deleting intermediate temp finals before starting a new run.
