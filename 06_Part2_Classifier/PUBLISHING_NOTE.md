# What is and is not in this folder

Included: Part 2 scripts, documentation (README, LOG, DATA_NOTES), per-image manifest (names, source,
hash; no pixels), build logs, all result tables and figures, per-run settings and curves, the exported
v1 model (`export\model.onnx`, 5.9 MB) and the species text used by the app.

**Not included, on purpose:** every image (the Entebbe zips, `raw\`, `cls_v1\`, `cls_v2\`, contact
sheets in `evidence\`, Ultralytics `train_batch*.jpg` / `val_batch*.jpg` sample images) because many
come from web sources and public datasets and must not be redistributed (see DATA_NOTES.md section 2);
training weights other than the exported model; console logs (UTF-16, large).
The evidence index (`evidence\README.md`) lists the withheld contact sheets; they exist in the
working archive. The installable app lives in a separate repo:
https://github.com/JosephWalusimbi-eng/ugawildlifevision-app
