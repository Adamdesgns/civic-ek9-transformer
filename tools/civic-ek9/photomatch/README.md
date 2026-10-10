# EK9 photo-match

Checks the model against the #111040 photos (`refs/ref_images/ek9-gallery/`).

1. `camfit.py marks.json cam.json`: fits a pinhole camera (Blender world) to landmarks whose model positions are known. `marks_*.json` hold the picks for photos 64 and 65. Pick new points on `gridcrop.py` enlargements.
2. `blender -b blender/civic-ek9-car.blend --python tools/civic-ek9/photomatch/camrender.py -- cam.json out.png`: renders the model through the fitted camera, with a transparent film and no ground.
3. `overlay.py photo.jpg out.png overlay.png`: draws the model's edges in cyan over the photo.
4. `backproj.py cam.json photo.jpg render.png front`: back-projects the photo's and the model's nose silhouettes onto the centreline, per row, in design (f, z). It subtracts `dims.RIDE`, which is hard-coded as 0.010.

The side-profile landmarks all lie near the flank, so a side fit cannot determine the camera's distance (see docs/civic-ek9.md, Reference and datums). Compare features at the same depth.
