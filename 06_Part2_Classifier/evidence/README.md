# Evidence index (Part 2)

Each file backs a claim in `..\LOG.md`. Contact sheets include web-sourced images:
**internal use only, do not publish** (see `..\DATA_NOTES.md` section 2).

| File | Backs | LOG entry |
|---|---|---|
| `00_image_audit_script.py`, `00_image_audit_exif_sizes_md5.csv` | Per-image size, camera make/model, date and MD5 for all 5,187 Entebbe images: source analysis and duplicates | 1 |
| `01_contact_sheet_possible_own_photos.jpg` | Which photos are the team's UWEC phone shots (fences, white tigers), and the mislabels (zebras in `buffaloes`, bison) | 1 |
| `02_contact_sheet_part1_species_in_new_data.jpg` | New-data photos of the Part 1 species; "antelopes" are gazelles; "baboons" are *Cercopithecus* monkeys | 1 |
| `03_ostrich_folder_exif_rotation_check.jpg` | Samsung originals are stored rotated; the `ostriches` folder really holds ostriches (plus the UWEC owl) | 1 |
| `05_v2_aug_samples_BEFORE_bird_context_fix.jpg` | Label-noise bug: "bird" context crops showing hippos | 8 |
| `06_v2_aug_samples_AFTER_bird_context_fix.jpg` | Same samples after the fix | 8 |
| `..\export\check_preprocess_v1.txt`, `..\export\export_check.json` | Preprocessing bug fixed; ONNX = PyTorch = PWA spec (606/606) | 6 |
| `..\results\v1\*` | All v1 metrics, confusion matrices and figures | 5 |
| `..\runs\v1_*\` | Ultralytics outputs per run: `args.yaml` (exact settings), `results.csv` (per epoch), plots | 4–5 |
| `..\logs\` | Console logs of every training and evaluation run, plus the progress timestamps | 4–5 |
| `..\cls_v1_build_log.txt`, `..\cls_v1\index.csv` | Dataset counts and per-image split/source/group | 3 |
| `10_v1_vs_v2_comparison.md`, `..\results\v2\*`, `..\runs\v2_*` | Augmentation experiment: no gain on UWEC | 9 |
| `06_..._first_fix_still_flawed.jpg`, `07_v2_aug_samples_FINAL.jpg`, `08_...jpg`, `09_...jpg` | Augmentation label-noise bugs and the Part 1 bird-crop finding | 8 |
