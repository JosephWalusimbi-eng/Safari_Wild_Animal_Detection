# Part 2 data notes

Everything a reader needs to know about the images behind the Part 2 species classifier:
where they came from, what was corrected, and what the numbers can and cannot claim.

## 1. Inputs

| Input | What it is | Used as |
|---|---|---|
| `Safari_Dataset` (Part 1, Zenodo doi:10.5281/zenodo.17036940, CC BY 4.0) | Video frames from Ugandan parks with 3,909 animal boxes, 7 classes | Each box cut out as a crop (15% context added). Boxes under 32 px were skipped. |
| `Entebbe _dataset.zip` | 4,990 images in folders by animal group | Photos by folder label, after the corrections below |
| `Entebble datasets.zip` | 200 images: cobras, crocodiles, pythons, tortoises, vipers | Same |
| `jolly_hakimu_joseph_Datase.zip` | Same content as `Entebbe _dataset.zip` minus 9 bird/crocodile files | **Not used** (duplicate) |

The zips are in `..\Entebbe Wildlife datasets\`; the unpacked copy used is `raw\`.

## 2. Where the Entebbe images come from

The team photographed animals at the Uganda Wildlife Conservation Education Centre (UWEC),
Entebbe, and shared the photos over WhatsApp. The file evidence shows that most images in the
folders were **not** taken on those visits. `build_manifest.py` records a `source` for every image:

| Source | Images | Evidence |
|---|---|---|
| `own_phone` (team photos at UWEC) | 47 | Phone photos through enclosure fences. 960×1280 / 867×1156 WhatsApp copies with camera data removed, plus Samsung originals. |
| `images_cv` | 3,930 | `meta.json` from images.cv in the fox, leopard and tiger folders. 256×256, already split 70/15/15. |
| `inat_style` | ~700 | Named `Genus_species_<observationID>_<n>.jpg` / `obs_<id>_<n>.jpg`, 500 px: the iNaturalist download format. |
| `web` | ~500 | Browser-download names (`images (3).jpg`, `download.webp`). `cheetahs/images (3).jpg` has a **Shutterstock watermark**. |

Consequences (agreed with the project owner on 2026-11-22):
- Web-sourced images may be used **for internal training only**. They must **never be
  redistributed** (not in a dataset release, not in the PWA bundle, not in the report as figures).
  iNaturalist licences vary per photo; images.cv and Shutterstock terms are restrictive.
- The report may say "photographed at UWEC" **only** about the 47 `own_phone` images.
- Species is not evidence of source: UWEC keeps non-native animals (e.g. tigers).

## 3. Label corrections (folder names are not reliable)

Found by eye on contact sheets; applied in `build_manifest.py` (`OVERRIDES`, `FOLDER_CLASS`):

| Folder | Problem | Fix |
|---|---|---|
| `buffaloes/27–31.jpeg` | Zebras | → zebra |
| `buffaloes/images (4).jpg` | American bison | dropped |
| `buffaloes/images.jpg` | Domestic / water buffalo | dropped |
| `primates/baboons` | *Cercopithecus* monkeys, not baboons | → monkey |
| `herbivores/antelopes` | Gazelles, not Uganda kob | → gazelle (an "other" species, not `uganda_kob`) |
| `ostriches/*` | One file is the UWEC owl | → bird (all birds share one class) |
| 5 exact duplicates | Same file twice | second copy dropped |

Two Samsung originals are stored rotated, with the rotation in their camera data. Every
script applies it (`ImageOps.exif_transpose`). Without that, the model would see sideways
animals.

## 4. Classes (v1)

26 classes: 20 regular, 5 low-data, 1 `other`.
- **Regular:** uganda_kob, bird, chimpanzee, elephant, gorilla, hippo, warthog (mostly Part 1
  crops), tiger, leopard, fox, frog, snake, fish, zebra, monkey, crocodile, tortoise, giraffe,
  rhino, squirrel.
- **LOW-DATA (user decision 2026-11-22: include them, with this note):** lion, buffalo, cheetah,
  kudu, hyena. Each has under 20 images, and most of the lion, buffalo and cheetah photos are
  UWEC phone shots held out for testing. Training images: lion 6, buffalo **1**, cheetah 4,
  kudu 14, hyena 10. **Expect these to be recognised poorly or not at all until more photos are
  collected.** Any accuracy reported for them rests on a handful of images.
- **`other`:** ~25 species with 4–10 web images each (kangaroo, koala, jackal, aardvark, gazelle,
  impala, …). It lets the app answer "not one of my species" instead of forcing a guess. It does
  not yet contain non-animal images (people, empty enclosures), which is a known gap.

## 5. Splits (leakage-safe)

| Images | Rule |
|---|---|
| Safari crops | Exactly the Part 1 split of the frame they come from (`dataset_labels\wildlife-yolo`), i.e. chronological blocks per recording session. |
| Entebbe web / iNat / images.cv | Split by **group** with a fixed hash, 80/10/10. All photos of one iNaturalist observation share a group. |
| `own_phone` (UWEC) | **`uwec_test` only, never trained on.** This is the real-world phone test. |
| Near-duplicates | Any val/test image within 4 bits (64-bit dHash) of a training image was removed (62 val, 40 test). |
| Caps | At most 400 train / 60 val / 60 test images per class, so tiger and leopard (images.cv) and chimp and hippo (video crops) cannot dominate. |

Final counts: `cls_v1_build_log.txt`; per-image list: `cls_v1\index.csv`.

## 6. What the test numbers mean

- `test` is **in-distribution**: the same sources as training (web/iNat/images.cv photos,
  Part 1 crops from the same sessions). It overstates real-world accuracy, as Part 1 showed for
  detection.
- `uwec_test` (47 images) is the honest phone test, but it is **small** and covers only 8 classes:
  bird 8, chimpanzee 7, tiger 3, zebra 5, crocodile 1, lion 9, buffalo 9, cheetah 5. Report it
  with its counts and do not generalise beyond it.

## 7. What would most improve this

More photos taken by the team on a phone at UWEC: about 30+ per species, from varied angles and
distances, through the fence as a visitor would see it. Sort them into one folder per species
and send the original files (not WhatsApp copies, which strip the date and time). No boxes are
needed.
