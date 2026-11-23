# Part 2 - Smartphone wildlife species identification

Part 1 (finished, in the `Safari_Wild_Animal_Detection` repo) built a 7-class **detector** that
draws boxes. Part 2 builds a **species classifier**: point a phone at an animal and it names the
species. It uses both the Part 1 data and the new photos from the Uganda Wildlife Conservation
Education Centre (UWEC), Entebbe. Classification needs no boxes, only one folder per species.

Delivery plan: **v1 = Progressive Web App** (runs in the phone's browser, installable, works
offline; the model runs on the phone via ONNX Runtime Web). **Later = Android app** using the
same exported model.

Read in this order: this file -> `DATA_NOTES.md` (sources, corrections, classes, splits,
caveats) -> `LOG.md` (dated record of every step and decision) -> `results\`.

## Folder layout

| Path | What it holds |
|---|---|
| `raw\entebbe_main`, `raw\entebbe_reptiles` | Unpacked Entebbe zips (unchanged originals) |
| `manifest.csv` | One row per Entebbe image: corrected class, source, leakage group, keep/drop, note |
| `cls_v1\` | The built classification dataset: `train\ val\ test\ uwec_test\<class>\*.jpg`, `index.csv`, `classes.txt` |
| `cls_v1_build_log.txt` | Per-class, per-split counts printed by the build |
| `scripts\` | Every script used (below) |
| `runs\` | Training runs copied back from the GPU machine (weights, `results.csv`, `args.yaml`, plots) |
| `logs\` | Console logs of training and evaluation |
| `results\v1\` | Metrics CSVs, confusion matrices, `figures\` |
| `export\` | `model.onnx`, `labels.json`, `export_check.json` for the PWA |
| `DATA_NOTES.md`, `LOG.md` | Data documentation and the dated project log |

## Scripts (run in this order)

| Script | Does | Runs on |
|---|---|---|
| `build_manifest.py --raw ..\raw --out ..\manifest.csv` | Inventory + source + label corrections | any PC |
| `build_cls_dataset.py --manifest ..\manifest.csv --raw ..\raw --safari <Safari_Dataset> --labels <dataset_labels\wildlife-yolo\labels> --out ..\cls_v1` | Builds the dataset (Safari crops + Entebbe photos, leakage-safe splits, caps, near-duplicate removal) | any PC |
| `run_part2_v1.ps1` | Trains 4 models (n-cls x 3 seeds, s-cls x 1) then evaluates them | GPU machine |
| `train_cls.py` | One training run; all settings fixed in the file | GPU machine |
| `evaluate_cls.py` | test + uwec_test: predictions, top-1/top-5, per-class, confusion matrices, threshold table | GPU machine |
| `make_figures.py --runs ..\runs --results ..\results\v1 --best <run>` | Report figures from the saved CSVs | any PC |
| `export_cls.py --run <run> --data ..\cls_v1 --out ..\export` | ONNX export + check that the PWA preprocessing matches + CPU timing | GPU machine or PC |
| `check_preprocess.py --run <run> --onnx <model.onnx> --data ..\cls_v1` | Proves predict = torchvision = PWA preprocessing = ONNX | PC |
| `make_aug_dataset.py --src ..\cls_v1 --safari <Safari_Dataset> --out ..\cls_v2 --k 2` | v2: phone-domain augmented training copies (val/test unchanged) | PC |
| `run_part2_v2.ps1` | v2 training (3 seeds) + evaluation | GPU machine |
| `make_species_json.py`, `make_icons.py` | PWA content and icons | PC |
| `contact_sheet.py` | Contact sheets used for visual checks (evidence\) | PC |

## The PWA (`pwa\`)

| File | Role |
|---|---|
| `index.html`, `styles.css`, `app.js` | The app. `app.js` copies the preprocessing in `export_cls.py` exactly |
| `sw.js` | Offline cache. **Bump `CACHE` whenever any file changes** |
| `manifest.webmanifest`, `icons\` | Install-to-home-screen metadata (icons from `make_icons.py`) |
| `model\model.onnx`, `labels.json` | Exported classifier (from `export\`) |
| `model\species.json` | Names, facts, safety notes, local names (from `make_species_json.py`) |
| `model\config.json` | Model version and "not sure" threshold |
| `vendor\` | ONNX Runtime Web 1.31.1 (MIT licence), WASM build, bundled for offline use |
| `serve.py` | Local test server: `python serve.py`, then open http://localhost:8000 |

To update the model: run `export_cls.py`, copy `model.onnx` and `labels.json` into
`pwa\model\`, update `config.json`, bump `CACHE` in `sw.js`.
For phone testing the folder must be served over **HTTPS** (e.g. GitHub Pages). It contains
no training images, only the model.

## Environment

Same as Part 1. GPU machine `setgpu` (account `mrjos`), project
`C:\Users\mrjos\Downloads\wildlife-capstone\part2`, venv at `..\venv`: Python 3.12,
`ultralytics==8.4.171`, PyTorch nightly cu128 (RTX 5070 Ti). **Do not upgrade PyTorch there.**
`workers=0` in training and evaluation because Ultralytics loader workers hang on that machine.
Local scripts were run with Python 3.10 + Pillow, numpy, matplotlib.

## Rules this part follows

1. The team's own UWEC phone photos (`uwec_test`) are **never trained on**. They are the honest
   real-world test.
2. Splits are by recording session or photo group, never by single image (Part 1 lesson).
3. Web-sourced images are for internal training only and are never redistributed
   (`DATA_NOTES.md` section 2).
4. Nothing from Part 1 is modified.
