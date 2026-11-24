# Part 2 project log

Dated record of each step, decision and result. Newest at the bottom.

## 2026-11-22 - Entry 1: examined the new Entebbe data

- Three zips in `Entebbe Wildlife datasets\`. `jolly_hakimu_joseph_Datase.zip` is
  `Entebbe _dataset.zip` minus 9 files, so it is not used.
- 5,190 files; 5,187 images, no bounding boxes (folders by animal only).
- File evidence shows 4 sources (see `DATA_NOTES.md` section 2): only 47 images are the team's
  UWEC phone photos; the rest are images.cv (3,930), iNaturalist-style (~700) and web downloads
  (~500, one Shutterstock watermark). The owner states the team took the photos and shared them
  by WhatsApp; that matches the 47, not the others. Decision: record the source per image, use
  the web images for internal training only, never redistribute them.
- Initial wrong reasoning, corrected: I first treated non-native species (tigers, kangaroos) as a
  sign of web images. UWEC keeps non-native animals; the team's photos include white tigers
  behind the UWEC fence. Source is now judged from file evidence only.
- Mislabels found on contact sheets (`DATA_NOTES.md` section 3). Two Samsung originals are stored
  rotated; all scripts apply the EXIF rotation.

## 2026-11-22 - Entry 2: scope decision

- The owner's goal is a smartphone tool that **identifies species**, not one that draws boxes,
  and there is no time to draw boxes by hand. -> Part 2 = image classification. Part 1 is
  left untouched.
- Delivery: PWA first, Android app later.
- Uses both datasets: Part 1 boxes become crops (only source for kob, warthog, gorilla and most
  hippo/chimp images), plus the Entebbe photos.

## 2026-11-22 - Entry 3: class list and dataset `cls_v1`

- Proposed 20 classes with >= ~30 images, plus `other`. Owner approved and asked to **also
  include** the low-data species: added lion, buffalo, cheetah, kudu, hyena, flagged LOW-DATA
  (training images: 6, 1, 4, 14, 10). Species with 4–10 images go to `other`.
- Built `cls_v1` with `build_cls_dataset.py`: 3,636 train / 553 val / 559 test / 47 uwec_test.
  Safari crops keep the Part 1 split; Entebbe photos are split 80/10/10 by group; caps
  400/60/60 per class; 62 val and 40 test near-duplicates of training images removed.
- Checked that Ultralytics 8.4.171 aligns class folders by name across splits and allows empty
  folders, so a class missing from a split cannot shift labels. Every class folder is still
  created in every split.

## 2026-11-22 - Entry 4: v1 training started

- GPU machine shared with another user's job (2 Python processes, ~9 GB, 94% use). A 224-px
  classifier needs ~2 GB, so it runs alongside with batch 64.
- `run_part2_v1.ps1`: YOLOv8n-cls seeds 0/1/2 + YOLOv8s-cls seed 0, 60 epochs, patience 15,
  AdamW lr 0.001, cosine, ImageNet-pretrained. Launched detached (WMI) at 17:06.

## 2026-11-22 - Entry 5: v1 results (evidence: `results\v1\`, `runs\v1_*`, `logs\`)

All 4 runs finished without error (17:06–17:34; early stop at epochs 33/39/44/39).

| Run | best val top-1 | test top-1 (n=559) | test macro | **UWEC top-1 (n=47)** |
|---|---|---|---|---|
| v1_n_seed0 | 0.901 | 0.900 | 0.732 | **0.213** |
| v1_n_seed1 | 0.899 | 0.909 | 0.727 | **0.149** |
| v1_n_seed2 | 0.910 | 0.918 | 0.781 | **0.213** |
| v1_s_seed0 | 0.911 | 0.914 | 0.809 | **0.234** |

- **Main finding: a 0.90 test score falls to about 0.2 on real phone photos.** This is the same
  lesson as Part 1 (normal test scores overstate real-world performance).
- UWEC per class (v1_n_seed2): zebra 5/5, tiger 3/3, cheetah 2/5, lion 0/9, buffalo 0/9,
  chimpanzee 0/7, bird 0/8, crocodile 0/1. Regular classes only (excluding lion, buffalo and
  cheetah): 7–8 of 24 across runs.
- Why: classes whose training images are varied photos (zebra, tiger) transfer. Chimpanzee has
  1,172 images but nearly all come from **one** Part 1 video, so it is called "gorilla" on phone
  photos. Part 1 birds are tiny video egrets, while the UWEC birds are an owl, parrots and
  ostriches behind fences (predicted frog/fish/gorilla). Buffalo → elephant, and lion fails
  (low-data classes, as expected).
- The larger model (s) gives no clear gain (val +0.002) at 3.4× the size.

## 2026-11-22 - Entry 6: model for the app, threshold, export check

- Chosen by **validation** top-1 (not test or UWEC): `v1_n_seed2` (0.910), the best small model.
- Threshold 0.7 (`results\v1\threshold.csv`): on test, 94% of photos answered at 94% accuracy.
  **On UWEC the model is confidently wrong:** above 0.9 it still answers 43% of photos at 25%
  accuracy. A threshold cannot fix a data gap, so the app carries an "early test version" notice.
- **Bug found and fixed:** the first ONNX check agreed with PyTorch on only 97.5% of images (max
  probability difference 0.36). `check_preprocess.py` isolated it: ONNX = PyTorch (1e-6), and
  Ultralytics = torchvision Resize(224) + CenterCrop(224); my resize/crop geometry differed by
  one pixel (rounding vs truncation). After matching torchvision exactly: 606/606 agree, max
  difference 0.0 (`export\export_check.json`, `export\check_preprocess_v1.txt`).
- ONNX model 5.9 MB, about 8 ms per image on this laptop's CPU (Python).

## 2026-11-22 - Entry 7: PWA built and tested (`pwa\`)

- Static PWA: ONNX Runtime Web 1.31.1 (WASM, 1 thread, files bundled in `pwa\vendor`, no CDN),
  camera/gallery input, top-3, confidence, "not sure" below threshold, low-data warning,
  safety notes, local-language names (shown only when verified), facts for the Part 1 classes,
  offline via service worker. Photos never leave the phone.
- **Bug found and fixed:** ORT's `import()` rejected the relative WASM path; now an absolute URL.
- Browser test (Chrome, localhost): same top-1 as Python on all 5 test images, including the
  4000×3000 EXIF-rotated Samsung photo (gorilla 0.92 in browser vs 0.87 in Python; the browser
  resizes slightly differently). About 40–50 ms per image. Service worker active with all 15
  files cached (works offline). The test images were removed from `pwa\` afterwards, because
  web-sourced images must not be hosted.

## 2026-11-22 - Entry 8: v2 = phone-domain augmentation (owner's suggestion)

- What augmentation can and cannot fix: it targets **domain shift** (fences, WhatsApp
  compression, animal small in frame, source style). It **cannot** create the missing variety
  for chimpanzee (one video) or birds (video egrets vs owls/parrots/ostriches). Those need more
  varied photos, so a flat chimp/bird result would not mean augmentation failed.
- Recipe fixed **before** any v2 result (`make_aug_dataset.py`): K=2 copies per training image;
  Safari crops re-cut with random context U(0.15, 1.5); p=0.7 downscale + JPEG q30–80 (+ blur);
  p=0.3 synthetic chain-link fence; p=0.5 colour jitter. Same probabilities for every class.
  Disclosure: the fence idea came from looking at the UWEC (test) photos.
- **Bug found on the contact sheet and fixed before training:** wide context around Part 1 birds
  (egrets on hippos) produced hippo pictures labelled "bird". Padding is now shrunk when a crop
  would take in a bigger animal of another class. Evidence:
  `evidence\05_v2_aug_samples_BEFORE_bird_context_fix.jpg` vs `06_..._AFTER_...`.
- First fix (shrink padding at 50% overlap) was not enough
  (`evidence\06_..._first_fix_still_flawed.jpg`). Tightened to 20% overlap, skip crops that are
  still dominated by another animal or are slivers (< 24 px), and narrowed colour jitter
  (60 of ~22,000 copies skipped). Final samples: `evidence\07_v2_aug_samples_FINAL.jpg`,
  `09_v2_bird_aug_samples_after_stricter_rule.jpg`.
- **Finding about Part 1 data, not my augmentation** (`evidence\08_...jpg`): some original v1 bird
  crops are junk (pale hippo skin labelled "bird", a sliver of hippo). Of 379 Part 1 bird boxes,
  175 lie at least 80% inside a bigger box of another class. Many are real (an Egyptian goose in
  front of hippos), others are not. Decision: **leave it for v2** so augmentation is the only
  change from v1; both v1 and v2 contain these. Cleaning is proposed as v3 (below). Part 1 itself
  is untouched but this may partly explain Part 1's near-zero bird score; worth a sentence in
  the report.
- **Transfer problem:** uploading the 423 MB `cls_v2` to the GPU machine timed out (81 MB in 15
  minutes; the link was slow, v1's 173 MB went fine earlier). Decision: build `cls_v2` **on the GPU
  machine** with the same script, seed and the Safari frames already there, instead of uploading
  images. Check: its per-class counts must equal the local build's
  (`cls_v2_build_log.txt` local vs `cls_v2_build_log_gpu.txt`).
- Design: same 3 seeds, model and settings as v1; val/test/uwec_test identical; only training
  images differ. Confound: 3× more training images means 3× more steps per epoch at the same
  epochs and patience. Comparison will report mean ± std over seeds, a paired per-image UWEC
  flip count, and regular vs low-data classes separately.

## 2026-11-23 - Entry 9: v2 results (evidence: `results\v2\`, `results\compare_v1_v2.md`, `runs\v2_*`, `logs\`)

`cls_v2` was built on the GPU machine and its per-class counts and augmentation step counts are
identical to the local build (`cls_v2_build_log.txt` vs `cls_v2_build_log_gpu.txt`). Three runs,
17:11-23:09, no errors.

| (mean ± std over 3 seeds) | v1 | v2 |
|---|---|---|
| test top-1 (n=559) | 0.909 ± 0.007 | 0.924 ± 0.006 |
| **UWEC phone photos, all (n=47)** | **0.191 ± 0.030** | **0.170 ± 0.046** |
| UWEC, regular classes (n=24) | 0.306 ± 0.020 | 0.208 ± 0.090 |
| UWEC, low-data classes (n=23) | 0.072 ± 0.054 | 0.130 ± 0.000 |

- **Result: this augmentation did not improve phone-photo accuracy.** Paired over the 3 seeds,
  8 image-seeds went wrong→right and 11 right→wrong (net −3 of 141): no detectable effect either
  way. In-distribution test rose by about 0.015, which is a "better on the easy test" signal of
  the kind Part 1 warned about.
- Per class: chimpanzee 0/7, bird 0/8 and buffalo 0/9 stay at zero in every run, as predicted in
  Entry 8 (the missing thing is varied photos of those animals, which augmenting cannot make).
  Cheetah went 0/0/2 → 3/3/3 of 5 and lion went 3/0/0 → 0/0/0 of 9; with 5 and 9 images each,
  neither is evidence. Zebra and tiger were already good and are noisy.
- Confound noted in advance: v2 has 3x more steps per epoch. Validation top-1 is no better
  (best 0.908/0.897/0.890 vs v1 0.901/0.899/0.910).
- **Decision by the pre-set rule (best validation, never test or UWEC): the PWA keeps `v1_n_seed2`.**
  v2 is kept as a documented negative result. Not run: tuning the recipe against UWEC, because with
  47 images that would only overfit the test set.
- What this says about the plan: the limit is the variety of real photos per animal, not the
  amount or style of training pixels. Next steps in priority order: (1) the team collects ~30+
  original phone photos per species at UWEC, (2) clean the Part 1 bird/chimp crops (Entry 8
  finding) and add a detector-crop step for small animals, (3) re-measure on new, unseen UWEC
  photos, since the current 47 have now been looked at repeatedly.

## 2026-11-23 - Entry 10: PWA published for phone testing

- On the owner's explicit instruction ("set this up"), published the app as a **new public repo**
  https://github.com/JosephWalusimbi-eng/ugawildlifevision-app with GitHub Pages at
  **https://josephwalusimbi-eng.github.io/ugawildlifevision-app/** (HTTPS, needed for camera and
  offline use on phones). Separate from the capstone repo; no training images, no `serve.py`.
  Contents: app code, `model\model.onnx` (v1_n_seed2, 5.9 MB), `labels.json`, `species.json`,
  icons, ONNX Runtime Web (MIT). README states "early test version" and the 1-in-5 UWEC result.
- Verified live: page 200; `model.onnx` byte-identical to the local file (MD5 match); `.wasm`
  served as `application/wasm`; in Chrome the model loads, returns 26 probabilities summing to 1,
  service worker active, 15 files cached. Not yet tested on a real phone (camera capture, install
  to home screen, offline mode): to do with the team.
- Republish procedure: copy changed files from `pwa\` into the repo, bump `CACHE` in `sw.js`, push.
  The local copy used for publishing was staged in the session scratchpad, not in this archive.

## 2026-11-23 - Entry 11: app renamed and disclaimers removed (owner's instruction)

- App name is now **UgaWildVision** (page title, header, install name). The repo and its URL are
  still `ugawildlifevision-app` (renaming the repo would change the link).
- Removed on the owner's instruction: the About-section line "A student capstone project (Part 2).
  Not for safety-critical decisions.", the yellow "Early test version … 1 time in 5" notice on the
  start screen, and the README's capstone and "not for safety decisions" wording. Kept: the README
  states the 47-photo UWEC result as a fact, and the per-animal "keep your distance" notes.
  Consequence to remember: phone users are no longer told on-screen that accuracy on real phone
  photos was about 0.2. Cache bumped to `ugawv-v1-5`. Other documents here still use the Part 1
  proposal name "UgaWildlifeVision" for the project.

## 2026-11-23 - Entry 12: start-screen note restored in shorter form (owner's instruction)

Added to the start screen: "Accuracy on real phone photos so far is about 1 in 5. Works best on a
close, clear photo." (1 in 5 = UWEC top-1 0.19 ± 0.03 over 3 seeds, n = 47; Entry 5/9.) Cache
`ugawv-v1-6`. If the model is retrained, update this number from the new UWEC/field result.

## 2026-11-24 - Entry 13: Part 2 report (tourism framing)

- Built `report/UgaWildVision_Part2_Report.docx` (+ PDF) with `report/build_report.py`, in the requested
  format (title, abstract, introduction, methodology, setup, results, analysis, discussion, limitations,
  conclusion), Times New Roman 12/14/16, justified, with contents, list of tables and list of figures.
- On the owner's instruction the report is framed around AI for advancing tourism in Uganda: 2024 figures
  (1,371,895 visitors, USD 1.28 billion, Ministry of Tourism), guiding and local-language gaps (UWEC to
  Parliament, 2018), 28.0% internet use (DataReportal 2025). Sources were looked up, not written from memory;
  citations are numbered automatically in order of first use.
- Extra figures from saved CSVs: `scripts/make_report_figures.py` -> `report/figures/` (charts and
  diagrams only, no photos).
- Title page: Joseph Walusimbi (2401600068) and Joanita Namuyiga (2401600382), owner's instruction.
- Word COM field update hung twice: (1) a stale `~$` lock file from a killed run made Word show a hidden
  "file in use" prompt; (2) two XML elements were out of schema order (`pgNumType` after `cols`,
  `tblCellMar` after `tblLook`), so Word showed a hidden "unreadable content" prompt. Fixed the order;
  `report/update_fields.ps1` then refreshes contents and lists and exports the PDF.

## 2026-11-24 - Entry 14: languages (text and audio)

- `scripts/sunbird_languages.py`: names in Luganda (lug), Runyankole (nyn), Rutooro (ttj), Ateso (teo) and
  Kiswahili (swa) via Sunbird AI `POST /tasks/translate` (Sunflower), back-translation to English, and
  speech via `POST /tasks/audio/speech` (no Rutooro voice). API keys come from environment variables only
  (`SUNBIRD_API_KEY`, `_2`, `_3`); nothing secret is stored. Cache and CSV: archive `evidence/sunbird/`;
  CSV copied to `results/sunbird_names.csv`.
- Single-word machine translation is unreliable (e.g. Ateso for lion -> "Ekingok", back-translated "Dog";
  "Uganda kob" -> sentences about Uganda). Automatic check: shown only if the back-translation names the
  same animal and the output is not just the English word. All names stay `verified=false`.
- Visitor languages chosen by a fixed rule on UBOS Tourism Satellite Account 2023, Table 2.9 (2019:
  1,542,620 visitors, 297,726 leisure): include if >= 2% of all or of leisure visitors.
  In: Kiswahili 33.7/12.4%, French 16.4/7.2%, German 3.9/10.1%, Dutch 1.6/4.1%. Out: Italian 0.6/1.98%,
  Spanish 0.4/1.6%, Arabic (UAE + other Middle East) 0.8/0.7%, Russian not reported separately.
  `scripts/add_visitor_languages.py` writes French/German/Dutch common names (checked against Wikipedia
  titles); the app speaks them with the phone's own voice (Web Speech API).
- App: language menu extended, "Listen" button, audio cached by the service worker, QR code
  (`icons/qr.png`, decoded and checked) and printable `install.html`.

## 2026-11-24 - Entry 15: field-guide redesign, facts, republish, presentation

- App redesigned on the owner's request after a "pocket field guide" example: Animals tab (photo cards,
  search, group chips), animal page (photo with credit, local name + Listen, IUCN status, danger, Few-photos
  tag, taxonomy incl. Swahili name, facts), camera tab for identification (preprocessing and model code
  unchanged: browser test hippo 98% in 29 ms), "I saw it!" sightings stored on the phone, About with QR.
- `scripts/build_catalog.py`: guide photos = lead image of the English Wikipedia article, accepted only if
  the Commons licence is CC0 / PD / CC BY / CC BY-SA (giraffe's GFDL-only photo rejected; Rothschild's giraffe
  used); 800 px; author/licence/source stored and shown. Taxonomy + IUCN status from Wikidata (bird class
  set to Aves by hand; fox and snake taxonomy filled by hand). No training image is shown anywhere.
- `scripts/add_facts.py`: facts for the 18 species without any (owner: "interesting facts").
- Language check tightened: a name also passes if it equals the Kiswahili/Luganda Wikipedia article title
  (rescued Kiboko, Twiga, Ndege); more than four words fails (caught "Kudu ni mji wa Kenya ..."). Result:
  44 of 125 Sunbird names pass (Kiswahili 14, Luganda 12, Runyankole 8, Rutooro 5, Ateso 5), 39 with audio.
- Republished (owner approved): commits 1de6085 and 780b413 in ugawildlifevision-app; live files checked 200.
- Presentation: `report/UgaWildVision_Part2_Presentation.pptx` (12 slides) built by `report/build_deck.py`
  from the old template (Walusimbi_Namuyiga.pptx); title photos are the team's own UWEC photos.
- The owner's Internet Download Manager was intercepting the browser test's image/audio loads; closed at the
  owner's request.

## 2026-11-24 - Entry 16: home page, How-to-use tab, navigation

- Owner's request: QR code on a landing page, "UgaWildVision" clickable to home, proper UX flow, and a
  "How to use this app" tab. Added a Home view (hero with "Identify an animal" / "Browse animals", language
  chips, animal of the day, stats incl. animals seen, QR + install card with the browser's install prompt where
  offered), a How-to-use view (7 steps + safety note), brand link to #home, and hash routes
  (#home, #animals, #animal/<class>, #identify, #sightings, #help, #about) so the phone's Back button works.
  Tab bar: Home, Animals, camera, Sightings, How to use; About is linked from Home and How to use.
- Browser test (localhost): all routes, Back from an animal page, brand link, model "Ready", no console errors.
- `pwa/serve.py` made multi-threaded (the single-threaded server stalled during tests). Published as d37d616.
- IDM (owner's download manager) relaunches when the browser loads media; closed again at the owner's request.

## 2026-11-24 - Entry 17: short report, plain diagrams, UWEC wording

- "Entebbe images" renamed "the UWEC dataset" everywhere (owner: UWEC and Entebbe are the same place); the
  report states this and that the four sources describe who took each image, not a second location.
- Short version added without touching the full report: `python report/build_report.py --short` writes
  `report/UgaWildVision_Part2_Report_Short.docx` (+ PDF, 35 pages; full report stays 53 pages). It has a
  ~180-word abstract, condensed related work (all citations kept), and drops repeated figures/tables, the
  label-correction and dataset-parameter tables, the full translated-names tables, model-size and
  engineering/literature-comparison sections, and the appendix. `report/update_fields.ps1 <name>` refreshes
  either document and exports its PDF.
- Block diagrams (approach, app flow) redrawn as plain black boxes and arrows, no colour; used in both reports
  and on the Methodology slide.

## 2026-11-24 - Entry 18: three-source wording, plain English, dataset slide, 8-minute deck

- Owner's wording change, system-wide: three image sources all contribute - the NESTLER Safari video dataset
  (official name: NESTLER Wild Animal Recognition Video Dataset, Zenodo 10.5281/zenodo.17036940; Safari part =
  Kibale, Queen Elizabeth, Bwindi, Feb-Jun 2025), internet images (images.cv 3,930; iNaturalist-style 1,016; other
  web 194) and our own 47 UWEC photos. NESTLER + internet images are used for training, validation and testing;
  the 47 own photos stay a real-world test only (kept out of training so one test is independent) - explained in
  the report. Figures now say "NESTLER Safari" instead of "Part 1" (approach diagram, dataset chart).
- Report text rewritten in plain student-level English (`report/plain_text.py`, applied by position in
  `build_report.py`). Short version uses the owner's own edits from the Downloads copy
  (`UgaWildVision_Part2_Report_Short_Edited.docx`) wherever the owner edited a paragraph. Title page follows the
  owner's layout (NAME / STUDENT NO. table, "Capstone Project Report", "Year 3, Semester 1").
- New report subsection 3.1 "Dataset size and splits": 4,795 images (2,312 NESTLER, 1,284 images.cv, 972
  iNaturalist-style, 180 other web, 47 own); 3,636 / 553 / 559 + 47; and what validation is for (stop training,
  pick best epoch/run without touching test sets; limit: validation looks like training data, ~0.90 for every
  run, so it cannot predict the UWEC 0.15-0.23).
- Axes: all bar charts start at 0; only the v1-v2 validation line chart starts at 0.6 (now stated in its caption).
- Owner's Downloads deck updated for an 8-minute talk (`report/update_downloads_deck.py`; saved as
  "... - updated.pptx", original untouched): new Results analysis slide, dataset-and-splits slide content with
  validation card, QR on the last slide, timing in the speaker notes (total 7:35).
- Guide rebuilt for 8 minutes with a decisions-and-rejected-options table (`report/build_guide.py`, local only).

## 2026-11-24 - Entry 19: internet image sources named

- Owner asked what "internet images" means. Sources, from the files: images.cv (www.images.cv; 3 ready-made 256 px sets:
  tiger 2,280, leopard 1,400, fox 250; meta.json says "provide_by www.images.cv"); iNaturalist (1,016 photos from 603
  observations; observation number in each file name; 8 random numbers checked against iNaturalist's public API, all
  matched the species); other websites (194 pictures saved with a browser, sites not recorded, one Shutterstock watermark).
- `results/image_sources.csv` (5,140 rows: file name, source, id, iNaturalist link, class) lists every internet image.
  Report table, figures, deck, guide now name the sources; "iNaturalist-style" became "iNaturalist".
