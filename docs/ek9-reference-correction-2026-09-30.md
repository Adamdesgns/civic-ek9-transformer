# Yellow EK9 reference correction — 2026-09-30

Adam asked: “make it look like that. it is still not right”, then supplied Blender close-ups of the hood/headlight edge and the roof/window junction. The target remains TopRank #111040, using the existing local reference photos.

## Changed

- One smooth plan-view boundary now controls the headlight opening and its hood/fender pockets. Larger elliptical reflector bowls replace the small circular bowls.
- The yellow rail above the windows is continuous. The black B-pillar ends at the sash, and the door-window upper curve is smooth.
- Seat-belt upper anchors moved inside the inward-leaning pillars. Their old placement caused the triangular protrusions through the exterior trim.
- The cowl stops before it overlaps the fenders, removing the striped overlap at the windshield corners.
- Wider wheel spokes meet thinner rim lips. The handle cups and flaps are rounded and body-colour. Corner vents have dark recessed walls and floors.

## Files

Primary project: `C:/Users/steam/Projects/apps/transformers`.

- Generator: `blender/civic-ek9_build/ek9/{car,parts,cabin,side,wheels,mats}.py`.
- Models: `blender/civic-ek9-car.blend` and the distinctly named `blender/civic-ek9-yellow-refined.blend`.
- Tools: `tools/civic-ek9/reference_review.py`, `check_detail_fit.py`, `finalize_preview.py`.
- Design notes: `docs/civic-ek9.md`.
- Render evidence and check logs: `blender/renders/civic-ek9/2026-09-30-refined/`.

Working copy and untouched baseline: `C:/Users/steam/OneDrive/Documents/ChatGPT/Transformers/evidence/`.

## Validation

The final model passes `check_model.py`: mesh PASS and no hole clusters across the two sides, front and rear. Belt clearance is at least 23.8 mm; all 20 roof-rail probes pass. Python source syntax passes. Studio before/after images use identical cameras and lights; outdoor close-ups also inspect the saved model. The dealer photos are references, not calibrated camera overlays. Logs: `final-checks.log` and `final-build.log`.

TypeScript passes. ESLint passes when excluding the existing nested `.claude` worktree; the unfiltered repository command fails because it discovers two competing TypeScript configuration roots. No TypeScript or lint configuration was changed.

## State

Local Blender correction, awaiting Adam's visual review. No commit or push, following this project's instructions. No robot rig, game export, or deployment. The previous Blender model and source files are preserved before installing the correction.
