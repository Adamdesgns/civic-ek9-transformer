# Yellow EK9 transformer

`blender/civic-ek9-transformer.blend` is a separate, editable conversion of the reference-corrected yellow hatchback. Open at frame 180 for the robot; scrub back to frame 1 for the car. The original refined car file remains the input and is unchanged.

## Animation

- Frames 1–20: car.
- Frames 25–65: doors open, glazing folds, and the structural frame begins to unfold.
- Frames 65–150: legs extend, rear panels move to the lower legs, and the front panels form the chest.
- Frames 126–174: head and hands deploy.
- Frames 180–210: robot hold.

The controls are named `CTRL.*` in **EK9 • ARTICULATION CONTROLS**. The hip, knee, ankle, shoulder, elbow, wrist, and head controls form an editable parent hierarchy. Panel carriers are children of their corresponding limbs. The animation uses rigid transforms: exterior pieces retain their original dimensions and remain present throughout. A separate ground-contact carrier keeps the lowest unfolding part above the stage.

The head, hands, and sternum use moving stow frames: their folded poses travel with the torso/forearms before deployment. Interpolating these from fixed car-world positions made them travel through the legs during the late stages; the moving carriers avoid that path.

This is an authored visual conversion, not a physics-driven mechanism. Ground clearance and transform validity are checked; complete self-collision-free packing of all interior components is not established. It has no game export or gameplay integration yet.

## Panel arrangement

The front bumper, lamps, and forward bonnet form two chest assemblies. The rear bonnet sections cover the thighs. Doors and their trim become shoulder wings. Front wheels sit at the shoulders; rear wheels sit at the calves. The rear quarter panels, hatch panel, taillights, and rear bumper form lower-leg armor and feet. Roof, glazing, seats, floor sections, and trim fold into a rear pack.

The new mechanical frame has machined joint drums, layered abdomen plates, paired struts, hoses, shaped limb shells, segmented hands, and a yellow helmet with blue eyes. It uses the existing EK9 material slots and the project's existing hard-surface geometry helpers.

## Rebuilding and checking

Run from the project root with Blender 5.2:

```powershell
blender -b blender/civic-ek9-yellow-refined.blend --python-exit-code 1 --python tools/civic-ek9/build_transformer.py -- hero car front back mid
blender -b blender/civic-ek9-transformer.blend --python-exit-code 1 --python tools/civic-ek9/check_transformer.py
```

The check compares every original car vertex against the folded pieces, samples 70 animation frames for finite transforms and unchanged scale, checks all meshes remain visible and assigned, and measures the minimum floor clearance. It also checks the stowed mechanical assemblies' basic exterior bounds. The review renders cover the car, front, rear, three-quarter robot, and intermediate conversion.

`ek9/transformer.py` contains the character geometry, panel assignment, and animation. `ek9/rkit.py` supplies the project's reused machined-part helpers. `tools/civic-ek9/render_transformer_preview.py` renders a small animation without changing the saved scene.

## Verified result — 2026-09-30

- 440,095 source vertices retained in the car pose; maximum position deviation 0.000000492 m.
- 73 controls, including the common ground carrier, and 21 new mechanical mesh assemblies.
- 70 sampled frames pass finite-transform, unit-scale, visibility, and assignment checks.
- Head-to-torso and hand-to-forearm distance checks keep the deploying parts with their carriers throughout the sequence.
- Floor sweep passes a 1 mm tolerance. Its minimum is -0.104 mm at the original car tire; the finished robot's lowest vertex is 0.5 mm above the floor.
- Finished robot height: 3.9405 m. Stowed mechanical assemblies pass the basic exterior extent check.
- TypeScript and scoped ESLint pass. ESLint excludes the existing nested `.claude` and `.codex` worktrees, as in the preceding car correction.
- The source car's SHA-256 remains `11C17650C757151022FB6CCC100B6CE9588A8F6AC59C7BFF052D007EBE097032`.

Review evidence is saved in `blender/renders/civic-ek9/2026-09-30-transformer/`. Changes are local and uncommitted under the project's instructions.
