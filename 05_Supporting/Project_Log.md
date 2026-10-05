> **Note on paths.** This is the dated working log, written as the project progressed. Folder names and paths in it
> (for example `wildlife-capstone\`, `runs\`, `analysis\`) refer to the working layout on the GPU computer and the
> laptop at the time. The final submission layout is described in `00_START_HERE.txt`; the raw runs, logs, cut-outs,
> dataset label files and source data are in the separate folder `Safari_Wild_Animal_Detection_working_archive`.

# Wildlife Capstone: Running Project Report

Plain-English log of what was done, why, and how. Newest entries go at the
bottom. Anything that is a guess rather than a measured fact is labelled
**Hypothesis**.

Project: detecting African wildlife (7 classes: antelope, bird, chimpanzee,
elephant, gorilla, hippo, hog) in Uganda safari video frames with YOLOv8n.

---

## Entry 1: Taking over the project (2026-10-02)

### Where things actually live
The handoff note (`HANDOFF_CLAUDE_CODE.md`) says the project is in
`C:\Users\mrjos\Downloads\wildlife-capstone` on the GPU machine. That is
correct, but there are two Windows accounts on the GPU machine
(Tailscale address 100.68.197.9, called "setgpu"):

| Account | Home folder | What is there |
|---|---|---|
| `benjamin` | `C:\Users\ssent` | A different project (OneAMR). Not this one. |
| `mrjos` | `C:\Users\mrjos` | **This capstone**: project folder, venv, datasets, runs |

I first looked in the `benjamin` account and found nothing from this project.
The student pointed out that the work is in the `mrjos` account. I confirmed
that the same SSH key logs in as `mrjos` and added an SSH shortcut,
`ssh setgpu-mrjos`, to the laptop's SSH config. All work for this project runs
through that shortcut.

The laptop folder `D:\Safari_Wild_Animal_Detection` holds a copy of the raw
dataset (`Safari_Dataset`), the handoff notes and two scripts. It has no GPU
and no Ultralytics, so it is used only for notes and quick checks.

### What was found on the GPU machine (account `mrjos`)
- `Downloads\wildlife-capstone` with `scripts\`, `venv\`, `runs\`, `weights\`
- `Downloads\Safari_Dataset` (the raw data; this resolves handoff step 3.1)
- `Downloads\wildlife-yolo` (the old, flawed split), `wildlife-yolo-lso`
  (leave-session-out split) and `visual_check`
- One earlier training run: `runs\detect\runs\S0_baseline`
- GPU confirmed: RTX 5070 Ti, 16 GB.

## Entry 2: Why the chimpanzee score was so low (the problem being fixed)

The first exploratory training run scored well overall (mAP50 0.691) but
chimpanzee mAP50 was only 0.092. The student's `split_check` output on the old
split shows why:

| Chimp data | Share of frames padded | Median chimp box size |
|---|---|---|
| train | 57% | 2.02% of the image |
| val | 100% | 0.29% |
| test | 100% | 0.39% |

The `chimpanzees` video starts as normal widescreen footage (112 frames) and
then switches to **portrait phone footage with blurred bars added on the
sides** (262 frames). The old split cut each video chronologically (first 70%
train, next 15% val, last 15% test), so the validation and test sets for
chimpanzees contained only the late, padded, far-away footage, while training
had a mix that included big close-ups. The model was being tested on a kind of
picture it had barely seen.

The confusion matrix showed almost no chimp/gorilla swapping (1 box each way),
so the labels themselves are fine. This was a data-split problem, not a
labelling bug.

**Hypothesis (not yet tested):** the late footage may also just be harder
(more distant, more hidden by leaves), independent of the padding.

## Entry 3: Checking the fix before using it (2026-10-02)

The handoff included an untested script, `prepare_dataset_v2.py`. Before
running it, two of its assumptions were checked on all 374 chimpanzee frames
(and on the other eight sessions for comparison):

1. **Is the "padded" test reliable?** The script compares how sharp the side
   strips are against the centre. Padded frames came out at 0.25 or lower;
   every normal frame in all nine sessions came out at 0.62 or higher. The
   cut-off of 0.35 sits in a clear gap, so it is safe.
2. **Is the picture area always in the same place?** The handoff measured it
   from a single frame (x = 656 to 1264 out of 1920). Measured across all 262
   padded frames, the left edge was 648 to 656 and the right edge 1256 to 1268,
   so one fixed crop is right to within a few pixels.
3. The padded frames are one unbroken block, frames 112 to 373. Exactly one
   switch from widescreen to portrait, as expected.
4. No other session has any padded frames.

Decision: run the script as written, with no changes.

## Entry 4: Rebuilding the dataset (2026-10-02)

Steps taken, in order:
1. Renamed the old dataset folder `wildlife-yolo` to `wildlife-yolo-naive`
   (kept untouched as the "before" evidence for the report).
2. Copied `prepare_dataset_v2.py` into the project's `scripts\` folder.
   `prepare_dataset.py` was not modified.
3. Ran it in the project's own Python environment to create a new
   `wildlife-yolo`.

What the new script does: it splits the chimpanzee video into a widescreen
part (`chimpanzees_land`) and a portrait part (`chimpanzees_port`), cuts the
blurred bars off the portrait frames, adjusts the box coordinates to match,
and then applies the same chronological 70/15/15 split to each part
separately. That way validation and test each contain both kinds of footage.

### Result
| Part | train | val | test |
|---|---|---|---|
| chimpanzees_land (112 frames) | 78 | 16 | 18 |
| chimpanzees_port (262 frames) | 183 | 39 | 40 |

All other sessions split exactly as before. Boxes written per class match the
original totals: antelope 347, bird 379, chimpanzee 1163, elephant 131,
gorilla 249, hippo 1219, hog 421, **total 3909**. Boxes dropped by cropping: 0.
Boxes clipped: 0 (every box was fully inside the picture area).

## Entry 5: Checking the rebuilt dataset (2026-10-02)

| Check | Result |
|---|---|
| Only `chimpanzees` was split into two formats | Yes |
| Frame counts match the expected 112 / 262 | Yes |
| Every image has a label file and vice versa; all box values within 0 to 1 | Yes |
| No frame appears in more than one split | 0 duplicates |
| Every class appears in train, val and test | Yes |
| Median chimp box size is similar across splits within each format | Yes (landscape about 5.0-5.7%, portrait about 0.9-1.2%) |

Images per split: train 849, val 180, test 191.
Chimpanzee boxes: train 871, val 154, test 138.
Elephant boxes are few: train 91, val 18, test 22. Expect noisy elephant scores.

Visual check (looked at 2 of 18 sample images so far): the cropped portrait
frame has no blurred side bars, and the two boxes sit on the two distant
chimps. The widescreen frame has six boxes on chimps in dense forest, tightly
placed. The other 16 samples still need a look.

An honest caveat: portrait chimps remain very small (about 1% of the image).
Fixing the split removes the unfair train/test mismatch, but it does not make
those animals easier to see. Chimpanzee may still score lower than other
classes, and that would be a legitimate finding.

## Open items / next steps
- Look at the remaining 16 visual-check images (`Downloads\visual_check2`).
- **Stop and report to the student** before any training (handoff rule).
- Then: S0 baseline, seed 0, with all augmentation switched off, using the
  absolute `project=` path. Needs the student's go-ahead before the long run.
- Keep: `wildlife-yolo-naive`, `runs\detect\runs\S0_baseline`,
  `prepare_dataset.py` (evidence for the naive-vs-fixed comparison).

## Changes made outside the project, for the record
- Laptop `C:\Users\mrjos\.ssh\config`: added hosts `setgpu` (login
  `benjamin`) and `setgpu-mrjos` (login `mrjos`).
- Laptop `C:\Users\mrjos\.ssh\gpu_setgpu`: private key copied from WSL by the
  student.
- Claude memory note `ssh-setgpu-from-windows` saved (needs a small update to
  mention the `mrjos` account).

---

## Entry 6: The earlier S0 run is not usable as the baseline (2026-10-02)

The student said an S0 baseline had been run earlier. I checked it
(`runs\detect\runs\S0_baseline`, `args.yaml` and `results.csv`):

| Setting | Earlier run | What a true S0 needs |
|---|---|---|
| Augmentation | **On** (mosaic 1.0, flip 0.5, colour jitter 0.015) | All off |
| Data split | Old chronological split (flawed for chimpanzees) | Fixed split |
| Where saved | `runs\detect\runs\...` (the path quirk) | `runs\<name>` |
| Length | Stopped at epoch 36 | Up to 100, stops early on plateau |

It was the exploratory run that exposed the chimpanzee problem (chimp mAP50
0.092), so it stays as the "naive" reference result for the report. But it is
not a no-augmentation baseline and was not trained on the fixed data, so it
cannot be compared with later ablation runs.

**Decision:** run a correct S0 (seed 0) on the rebuilt dataset, exactly as
specified in the handoff: every augmentation explicitly set to zero,
`imgsz=640`, `patience=20`, `batch=16`, absolute `project=` path, run name
`S0_baseline_seed0`. The student said to do whatever is necessary, which I took
as the go-ahead for this one run. Seeds 1 and 2 will wait until the seed-0
result has been looked at.

**Method note:** the training runs on `setgpu`, launched from a script
(`scripts\run_s0_seed0.ps1`), with all output written to
`logs\S0_baseline_seed0.log`. An epoch takes about 5 seconds on the RTX 5070 Ti,
so a full 100-epoch run is roughly 10 minutes. My first launch attempt
(a hidden background process) silently did not start and was retried; only
one training is running (checked: a single `yolo.exe`).

## Entry 7: S0 baseline, seed 0, on the fixed split (2026-10-02)

The run finished normally. Training stopped early at epoch 37 because nothing
improved for 20 epochs; the best model is from epoch 17. Total training time
was about 2.3 minutes. The SSH session did not drop. Run folder:
`runs\S0_baseline_seed0`. All figures below are on the **validation** set
(180 images, 629 boxes); the test set has not been used yet.

| Class | Val boxes | Precision | Recall | mAP50 | mAP50-95 |
|---|---|---|---|---|---|
| all | 629 | 0.764 | 0.654 | **0.682** | **0.435** |
| antelope | 78 | 0.559 | 0.410 | 0.377 | 0.268 |
| bird | 68 | 0.672 | 0.030 | 0.158 | 0.030 |
| chimpanzee | 154 | 0.780 | 0.630 | **0.672** | 0.441 |
| elephant | 18 | 0.936 | 0.807 | 0.828 | 0.666 |
| gorilla | 38 | 0.828 | 0.868 | 0.943 | 0.792 |
| hippo | 188 | 0.674 | 0.878 | 0.825 | 0.350 |
| hog | 85 | 0.898 | 0.953 | 0.970 | 0.496 |

### Main finding: the split fix worked
Chimpanzee mAP50 went from **0.092 to 0.672** and recall from 0.07 to 0.63.
The earlier run also had augmentation on and a different stopping point, so
the two runs differ in more than the split. The chimpanzee jump is far too big
to come from those small changes, but a strict like-for-like "naive split,
no augmentation" run has not been done. If the report needs that claim to be
airtight, that run costs about 3 minutes and should be added.

### Confusion matrix (normalised by true class)
- Chimpanzee: 66% found, 23% missed entirely (called background). Almost none
  confused with gorilla, so the label remap is still fine.
- Gorilla 74% and elephant 89% found.
- Hippo: 65% found, but hippo is also the model's most common wrong guess.
  Of true hogs, 22% were called hippo; of true gorillas, 14% hippo; of true
  antelope, 18% hippo.
- Bird: only 28% found, 71% missed. Birds are small and sit inside scenes
  dominated by other animals, as the handoff predicted.

### Surprise: antelope is now one of the weakest classes
Antelope mAP50 is 0.377. Only 15% of antelope boxes were found as antelope;
42% were missed and the rest were called hippo, hog, bird or chimpanzee.
**Hypothesis (untested):** antelope is a single video split chronologically,
so validation shows later footage that may look different from training, the
same kind of problem as the chimpanzee one but less obvious. I have not
checked this. A look at the antelope val frames next to train frames, and
box-size statistics like the chimp analysis, would settle it. The handoff's
`antelope` visual check was also marked "pay special attention".

### Caveats
- One seed only; seed-to-seed spread is unknown until seeds 1 and 2 run.
- Elephant has just 18 validation boxes, so its numbers are noisy.
- Validation results guide early stopping, so they are slightly optimistic;
  the test split is the honest final number.

### Next
Report to the student; wait for direction before seeds 1 and 2 and before
S1/S2. Candidate side checks: antelope domain-shift look; like-for-like naive
no-augmentation run.

---

## Entry 8: Antelope check, and the small-data strategy plan (2026-10-02)

### The antelope problem is a real data shift
Antelope is one video, cut chronologically (first 70% train, next 15% val,
last 15% test). I measured the antelope boxes in each part:

| Part | Frames | Antelope per frame | Median box size |
|---|---|---|---|
| train | 99 | 1.38 | 1.00% of image |
| val | 21 | 3.71 | 0.57% |
| test | 22 | 6.00 | 0.37% |

Looking at the frames: early footage is a close-up of one horned male; later
footage is a distant herd of 4 to 6 small animals. (The animals look like
Uganda kob, as the handoff said.) So the model is trained mostly on large,
single animals and tested on small, grouped ones. This is the same kind of
problem as the chimpanzee one, but caused by distance and herd size rather than
by padding, so there is no cropping trick that fixes it. **This explains the low
antelope score (mAP50 0.377).** It is now a measured finding, not a guess.

I checked every other class the same way. Chimpanzee is balanced within each
format after the earlier fix, and hog, bird and elephant are stable across
splits. Milder drift exists for hippo (median box 0.21% in train vs 1.81% in
val and test) and gorilla session 3 (25.6% train vs 14.3% test).

### Decision pending (belongs to the student)
Two honest options for antelope, with different meanings for the report:
1. **Keep the chronological split.** The test then measures "can a model
   trained on early footage cope with later, harder footage", which is a fair
   but strict test. The data-efficiency techniques in the proposal (scale
   augmentation, copy-paste of small animals, higher image size) are exactly
   what should help here, and showing that is part of the ablation story.
2. **Interleave blocks** (cut the video into short blocks with gaps between
   them, give each of train/val/test a share of early, middle and late blocks).
   This matches the proposal's wording ("blocked to avoid near-duplicate
   leakage") and removes the shift, but it makes antelope scores look better
   partly because the test is easier, and it would change the dataset, so all
   earlier runs would need repeating.

Until the student chooses, nothing about the split has been changed. Seeds 1
and 2 of S0 are being run on the current split; they are valid either way as
the "format-aware chronological split" condition for the report.

### Small-data strategy plan
From the proposal (Section 6.3), the ablation ladder, each step added on top of
the last, every configuration with 3 seeds:
- **S0** no augmentation baseline (running now).
- **S1** standard augmentation: mosaic, mixup, colour jitter, scale,
  translation, flip.
- **S2** copy-paste: first the built-in version (box-based), later the
  mask-based version using SAM if the simple one shows promise.
- **S3** class imbalance: repeat-factor / class-balanced sampling and
  class-weighted or focal loss (needs a custom training script).
- **S4** pseudo-labelling from the extra Zenodo videos, training data only,
  never leaking into val or test.
- **S5 (stretch)** synthetic images of the rarest class, training only.
- Fine-tuning settings from Section 6.2: lower learning rate, cosine schedule,
  early stopping, and a comparison of frozen versus unfrozen early backbone
  layers. GANs are deliberately excluded (reasoning in the proposal).

Extra ideas that fit the problems measured so far (proposed, not yet agreed
or tested; each would be a separate, clearly labelled experiment, kept off the
main ladder so the ladder stays comparable):
- **Higher image size (1280)** for tiny birds, distant chimps and antelope
  herds. The handoff already lists this as a side experiment.
- **A slightly larger model (YOLOv8s)**: the proposal mentions nano and small.
- **Tiling the image into overlapping crops (SAHI-style)** at test time for
  small objects such as birds.
- **Scale augmentation tuned upwards** specifically for the distance gap seen
  in antelope and hippo.
- **Test-time augmentation** at evaluation.

### Additional facts taken from the proposal (for the report)
- Bird boxes come only from incidental appearances in the hippo2 and hog
  sessions, so bird has no session of its own.
- The proposal says leave-session-out is only valid for hippo and gorilla,
  and other classes use a blocked within-session split, "stated explicitly as a
  weaker generalization test". The antelope finding supports that caveat.

---

## Entry 9: S0 baseline, all three seeds (2026-10-02)

Seeds 1 and 2 ran with the same settings as seed 0 (augmentation off, fixed
split, `imgsz=640`, `patience=20`, `batch=16`). Each stopped early:
seed 0 after 37 epochs (best at 17), seed 1 after 60 (best 40), seed 2 after 48
(best 28). Numbers are from the final validation pass of each run's best model,
on the **validation** set (180 images, 629 boxes). Spread is the sample
standard deviation over 3 seeds, so it is itself a rough estimate.

| Class | Seed 0 | Seed 1 | Seed 2 | mAP50 mean ± sd | mAP50-95 mean ± sd | Recall (mean) |
|---|---|---|---|---|---|---|
| **all** | 0.682 | 0.712 | 0.680 | **0.691 ± 0.018** | **0.440 ± 0.007** | 0.658 |
| antelope | 0.377 | 0.510 | 0.411 | 0.433 ± 0.069 | 0.307 ± 0.043 | 0.432 |
| bird | 0.158 | 0.144 | 0.224 | 0.175 ± 0.043 | 0.031 ± 0.014 | 0.047 |
| chimpanzee | 0.672 | 0.683 | 0.655 | 0.670 ± 0.014 | 0.434 ± 0.010 | 0.613 |
| elephant | 0.828 | 0.811 | 0.725 | 0.788 ± 0.055 | 0.661 ± 0.005 | 0.787 |
| gorilla | 0.943 | 0.995 | 0.980 | 0.973 ± 0.027 | 0.798 ± 0.005 | 0.947 |
| hippo | 0.825 | 0.856 | 0.784 | 0.822 ± 0.036 | 0.372 ± 0.042 | 0.811 |
| hog | 0.970 | 0.983 | 0.980 | 0.978 ± 0.007 | 0.475 ± 0.018 | 0.963 |

Mean precision (all classes): 0.771.

### What this says
- **The chimpanzee result is stable.** Across three seeds chimp mAP50 is 0.670
  with a small spread (0.014), so the improvement over the naive split's 0.092
  is not a lucky seed.
- **Two classes are clearly weak: bird (0.175) and antelope (0.433).** Bird
  recall is under 5%: the model almost never finds birds. Antelope varies a lot
  between seeds (0.38 to 0.51), consistent with the distribution-shift finding
  in Entry 8.
- **Gorilla and hog are near ceiling (0.97+).** Hippo is good at 0.5 overlap
  (0.82) but weaker at strict overlap (0.37), meaning boxes are found but not
  tightly placed.
- Elephant has 18 validation boxes, so its spread (0.055) is mostly noise from
  a tiny sample.
- **Reading differences between later techniques:** the overall spread is about
  0.02 mAP50. A technique that moves overall mAP50 by less than roughly 0.03
  cannot be told apart from seed noise with 3 seeds. Per-class differences need
  to be larger still (antelope about 0.15, bird about 0.1).

### Technical note
Training logs written by PowerShell's `*>` redirect are UTF-16 and contain
progress-bar control codes; the aggregation script strips these before reading.
The per-class numbers come from the log of the final validation pass, not from
`results.csv` (which has overall metrics only).

### Next
S1 (standard augmentation) and S2 (copy-paste), 3 seeds each, are the next
planned runs. They are cheap (a few minutes per run) but were not yet approved
by the student, so they have not been started.

---

## Entry 10: Decisions, and launching S1 and S2 (2026-10-02)

### Decisions (the student asked me to proceed "the best way forward")
1. **Antelope split: keep the chronological split for the main ablation
   ladder.** Reasons: (a) it is the strict, leakage-safe protocol the proposal
   argues for; (b) the antelope shift (Entry 8) is a measured property of the
   data, and the techniques on the ladder (scale augmentation, copy-paste of
   small animals) are the ones that should help with it, so the ladder can show
   whether they do; (c) changing the split now would invalidate the three S0
   seeds already done. An interleaved-block comparison run for antelope is kept
   as a later side experiment, so the report can show both sides.
2. **S1 and S2 go ahead now**, three seeds each, one after another.

### What was launched
One script, `scripts\run_s1_s2.ps1`, runs six trainings in order: S1 seeds 0, 1,
2, then S2 seeds 0, 1, 2. Everything else is held the same as S0 so that only
the augmentation changes: same dataset, `yolov8n.pt`, 100 epochs, early
stopping after 20 flat epochs, `imgsz=640`, `batch=16`, same seeds.

| Setting | S0 | S1 | S2 |
|---|---|---|---|
| mosaic | 0 | 1.0 | 1.0 |
| colour jitter (hsv h/s/v) | 0 | 0.015 / 0.7 / 0.4 | 0.015 / 0.7 / 0.4 |
| translate | 0 | 0.1 | 0.1 |
| scale | 0 | 0.5 | 0.5 |
| horizontal flip | 0 | 0.5 | 0.5 |
| mixup | 0 | 0.1 | 0.1 |
| copy-paste | 0 | 0 | **0.3** |
| rotate, shear, perspective, vertical flip | 0 | 0 | 0 |

Logs go to `logs\<run name>.log`; a file `logs\S1_S2_done.txt` appears when all
six are finished. Run names: `S1_augment_seed{0,1,2}`, `S2_copypaste_seed{0,1,2}`.

A caution for reading S2 later: Ultralytics' built-in copy-paste is the
simplified version. It works best with segmentation masks, and this dataset
only has boxes, so S2 may do little. If it shows no gain, that tells us the
mask-based SAM version has not been tested, not that copy-paste cannot help.
(**Hypothesis**, to be checked against the S2 results.)

---

## Entry 11: S1 and S2 results, and why S2 is not a real result (2026-10-02)

All six runs finished. Same validation set as before (180 images, 629 boxes),
three seeds each, mean ± standard deviation. Full per-seed numbers for every
run and class are in `results_val_per_seed.csv`.

### S1 (standard augmentation) versus S0 (no augmentation), mAP50

| Class | S0 | S1 | Change |
|---|---|---|---|
| **all** | 0.691 ± 0.018 | **0.767 ± 0.020** | **+0.075** |
| antelope | 0.433 ± 0.069 | 0.565 ± 0.043 | +0.132 |
| bird | 0.175 ± 0.043 | 0.242 ± 0.098 | +0.067 |
| chimpanzee | 0.670 ± 0.014 | 0.723 ± 0.022 | +0.053 |
| elephant | 0.788 ± 0.055 | 0.974 ± 0.025 | +0.186 |
| gorilla | 0.973 ± 0.027 | 0.978 ± 0.014 | +0.005 |
| hippo | 0.822 ± 0.036 | 0.907 ± 0.013 | +0.086 |
| hog | 0.978 ± 0.007 | 0.977 ± 0.012 | -0.001 |

mAP50-95 (strict box placement): overall 0.440 → 0.458 (+0.018). Biggest
gains: hippo +0.092, bird +0.061. One drop: **gorilla 0.798 → 0.714 (-0.084)**.

### How to read this
- **Standard augmentation clearly helps overall.** The overall gain (+0.075)
  is about four times the seed-to-seed spread, so it is not noise. This is the
  first real ablation finding.
- **It helps most where the data was thin or shifted:** elephant (+0.19, but
  only 18 validation boxes, so treat the size of this number with caution),
  antelope (+0.13), hippo (+0.09). Antelope is the class with the distance
  shift (Entry 8), and scale and translation augmentation is the kind of change
  that should help with it. **Hypothesis:** that is why it improved; not
  separately tested.
- **Bird improved by 0.067, but the spread is 0.098,** so this is within noise.
  Bird recall is still about 5%, so S1 did not fix it.
- **Hog and gorilla did not need it** (already near 0.97 at mAP50).
- **Gorilla box placement got looser** (mAP50-95 down 0.084) even though
  detection at 0.5 overlap did not change. **Hypothesis:** gorillas fill about a
  quarter of the frame, and scaling or shifting pushes some of them partly
  out of view, which makes the box edges less consistent. Not tested.
- Training length was similar (S0 37/60/48 epochs, S1 36/41/59).

### S2 (copy-paste 0.3): identical to S1, because the setting did nothing
S2 gave exactly the same numbers as S1 for every class and every seed, with the
same number of epochs. That is impossible if copy-paste were acting, so I
checked. `args.yaml` shows `copy_paste: 0.3` was passed correctly, but the
Ultralytics code (`CopyPaste.__call__` in `ultralytics\data\augment.py`) begins
with: `if len(labels["instances"].segments) == 0 or self.p == 0: return labels`.
This dataset has only boxes and no segmentation outlines, so the function exits
immediately and never pastes anything. With fixed seeds the S2 runs therefore
reproduce S1 exactly.

**Conclusion: the S2 numbers above must not be reported as "copy-paste has no
effect".** They show that the built-in copy-paste cannot run on box-only data.
This confirms the hypothesis written in Entry 10, in a stronger form: it is not
merely weak, it is switched off. For the report this is a legitimate and
useful finding about the tool, and it explains why the proposal's mask-based
version is needed.

### What a working S2 needs
Copy-paste needs animal outlines, which means generating masks from the boxes.
The proposal's plan is SAM (Segment Anything) prompted with each box. Two ways
to use them:
1. **Offline copy-paste (recommended):** write a script that cuts each animal
   out with its SAM mask and pastes it onto other *training* images (favouring
   rare and weak classes: elephant, bird, antelope), saves new images and boxes
   into the training folder only, then trains with S1 settings. Works with the
   normal detection model and is easy to audit. Val and test are never touched.
2. **Segmentation training:** convert training labels to outlines and train a
   `-seg` model so built-in copy-paste works. This changes the model type, so
   the results are less comparable to the rest of the ladder.

SAM would be run through the Ultralytics package already installed (its
weights are a one-time download of several hundred MB). I have not downloaded
or run anything yet.

### Updated ladder status
| Step | Status |
|---|---|
| S0 baseline | Done, 3 seeds |
| S1 standard augmentation | Done, 3 seeds; clear overall gain |
| S2 copy-paste | Built-in version void (no-op on box-only data); SAM version not yet built |
| S3 class imbalance | Needs custom script |
| S4 pseudo-labelling | Needs extra videos and a merge script |

---

## Entry 12: Building a real copy-paste (S2) with SAM masks (2026-10-02)

Because the built-in copy-paste cannot run on box-only data (Entry 11), I built
the proposal's mask-based version as an offline pipeline. Nothing in the
original dataset was changed.

### Step 1: cut animals out with SAM
SAM ("Segment Anything", `sam_b.pt`, about 358 MB, downloaded once from the
Ultralytics release page into the project folder) was given each **training**
box as a prompt and returned an outline. About 0.5 s per image on the GPU.
Script: `scripts\extract_cutouts.py`. Only the 849 training images were read, so
no validation or test pixel enters the pipeline.

Filters applied to avoid bad cutouts, with the reason:
- skip a box if more than 30% of it overlaps a neighbouring box (the outline
  would contain the neighbour as well);
- skip if the mask fills less than 25% or more than 97% of its box (bad outline);
- skip boxes smaller than 12 pixels on a side.

| Class | Boxes | Kept as cutouts | Main loss reason |
|---|---|---|---|
| antelope | 137 | 102 | bad outline (35) |
| bird | 244 | 112 | overlaps neighbour (84) |
| chimpanzee | 871 | 574 | overlaps neighbour (253) |
| elephant | 91 | 36 | overlaps neighbour (54) |
| gorilla | 167 | 39 | overlaps neighbour (91), bad outline (37) |
| hippo | 845 | 364 | overlaps neighbour (454) |
| hog | 263 | 197 | overlaps neighbour (35) |

### Step 2: look at the cutouts (a decision made from the pictures)
A contact sheet of random cutouts showed that **antelope, elephant, hippo and
the white-egret birds are cut cleanly**. **Gorilla masks are fragmented**: the
animals are dark and sit in dark forest, so SAM breaks them into pieces. Some
chimpanzee masks have the same problem. One "bird" cutout turned out to be a
hippo head (the bird box sat on a hippo).

**Decision:** paste only antelope, elephant and bird. These are exactly the
weak or rare classes, and their cutouts are clean. Gorilla and chimpanzee are
left out (gorilla is already near 0.97 mAP50, so it needs this least). Bird
cutouts that fill more than 80% of their box are dropped to remove
hippo-head-like mistakes (this removed 4 of 112).

### Step 3: build the training set with pasted animals
Script: `scripts\make_cp_dataset.py`. It produces a **new** dataset,
`wildlife-yolo-cp`, containing:
- all original train, val and test images and labels, unchanged (val and test
  are hard links to the very same files, so they cannot differ);
- **400 extra synthetic training images**. Each is a random original training
  frame with 1 to 3 cutouts pasted in. Class mix: elephant 40%, bird 30%,
  antelope 30%. Each pasted animal is scaled randomly (0.5x to 1.5x, adjusted
  for the source image resolution), may be mirrored, has softened edges, and is
  placed so it overlaps existing animals by at most 5%. Its new box is taken
  from the pasted outline. Result: 777 pasted animals (elephant 296, antelope
  243, bird 238).

I checked a sample visually. The boxes sit correctly on the pasted animals.
**Honest limits:** the scenes are often unrealistic (for example an elephant
placed in gorilla forest, or small floating animals), and the 296 elephant
pastes reuse only 36 distinct elephant cutouts from one video. The proposal
anticipated this risk ("copy-paste images may look unrealistic... treat as a
hypothesis"). The result will show whether it helps anyway.

### Step 4: train
S2 (SAM version), run names `S2sam_seed{0,1,2}`: the S1 settings exactly (same
augmentation, `copy_paste=0` because the built-in one is a no-op), same model,
epochs, early stopping, image size and seeds. The only difference from S1 is
the 400 extra pasted training images. Evaluated on the unchanged validation
set. Logs in `logs\`; `logs\S2sam_done.txt` marks completion.

### Also requested by the student: report, graphs, notebook
The final write-up will include metrics tables, graphs and a Jupyter notebook
that regenerates every figure from saved run data (`analysis\`). Data that the
notebook needs is being collected into `analysis\data\` as the experiments
finish; the first file is `shift_stats.csv` (box sizes per split, old and new).

---

## Entry 13: S2 with SAM masks: results (2026-10-02)

Three seeds (`S2sam_seed{0,1,2}`), same validation set. Epochs run: 37, 66, 49.
"Beyond noise" below means a Welch t-statistic above 2.8 in size over 3 seeds
(indicative only, not a formal test).

| Class | S1 mAP50 | S2sam mAP50 | S1 mAP50-95 | S2sam mAP50-95 | S1 recall | S2sam recall |
|---|---|---|---|---|---|---|
| **all** | 0.767 ± 0.020 | 0.746 ± 0.039 | 0.458 ± 0.004 | 0.467 ± 0.006 | 0.702 | 0.720 |
| antelope | 0.565 ± 0.043 | 0.472 ± 0.100 | 0.333 | 0.303 | 0.460 | 0.457 |
| bird | 0.242 ± 0.098 | 0.335 ± 0.136 | 0.092 | 0.096 | 0.049 | **0.289** |
| chimpanzee | 0.723 ± 0.022 | 0.712 ± 0.023 | 0.442 | 0.429 | 0.630 | 0.680 |
| elephant | 0.974 ± 0.025 | 0.859 ± 0.086 | 0.688 | 0.676 | 0.981 | 0.833 |
| gorilla | 0.978 ± 0.014 | 0.988 ± 0.011 | 0.714 | **0.857** | 0.961 | 0.989 |
| hippo | 0.907 ± 0.013 | 0.866 ± 0.046 | 0.464 | 0.413 | 0.867 | 0.814 |
| hog | 0.977 ± 0.012 | 0.989 ± 0.006 | 0.473 | 0.497 | 0.962 | 0.976 |

### What is solid
- **Bird recall rose from 4.9% to 28.9%** (beyond noise). This is the class the
  copy-paste was designed to help (small, rarely found), and it is the one
  clearly positive result. Bird mAP50 moved +0.09, but its spread is large
  (0.10 to 0.14), so that number alone is not conclusive.
- **Gorilla box tightness (mAP50-95) recovered** from 0.714 (S1) to 0.857
  (beyond noise), above even the S0 value of 0.798. Gorillas were not pasted.
  **I do not know why.** Hypotheses, untested: the 400 extra images re-use
  gorilla-scene backgrounds with extra variety; or this is a side effect of
  having more training images per epoch. This should be checked, not claimed.

### What is not distinguishable from noise
- Overall mAP50 (0.767 → 0.746), and the drops for elephant (-0.115),
  antelope (-0.093) and hippo (-0.041), all have seed spreads as large as the
  change. Elephant is scored on only 18 validation boxes. These may be real
  harm (hypothesis: the model over-fits to the 36 elephant cutouts, from one
  video, pasted 296 times) or noise; three seeds cannot tell.
- The small overall mAP50-95 rise (+0.009).

### Overall reading
SAM copy-paste is not a clear net improvement on this dataset and design. It
helped bird recall, which is the weakest class, and left everything else
within noise apart from the unexplained gorilla effect. Compared with the
standard augmentation step (clear, large, consistent gains) it is a minor
contribution. This is a legitimate ablation result and should be reported as
such, with the limits above (small and repetitive cutout library, unrealistic
scenes).

### Notebook, figures and tables for the report (requested by the student)
Everything is in `D:\Safari_Wild_Animal_Detection\analysis\` (copy in the
project folder on `setgpu`):
- `results_notebook.ipynb`: regenerates all figures and tables from saved data;
  `results_notebook.html` is the same, read-only, already executed.
- `figures\`: class balance; chimpanzee split fix (before/after); antelope
  shift; overall ablation; per-class ablation with error bars; bird and
  elephant detail; training curves; confusion matrices (old split, S0, S1,
  S2sam); plus `table_mean_sd.csv` and `table_significance.csv`.
- `data\`: the raw material (`results_val_per_seed.csv`, per-run
  `results.csv` files, confusion matrices, `shift_stats.csv`, the copy-paste
  manifest). `build_nb.py` rebuilds the notebook file.

### Ladder status
| Step | Status |
|---|---|
| S0 baseline | Done, 3 seeds |
| S1 standard augmentation | Done, 3 seeds; clear gain overall |
| S2 built-in copy-paste | Void (no-op on box-only data) |
| S2 SAM copy-paste | Done, 3 seeds; helps bird recall, otherwise within noise |
| S3 class imbalance | **Next**: needs a custom script |
| S4 pseudo-labelling | Needs extra Zenodo videos |
| Final: test-set evaluation, ONNX export, speed benchmark, Experiment A, language table | Not started |

---

## Entry 14: S3, class-imbalance handling: design and launch (2026-10-02)

The proposal names two remedies: repeat-factor / class-balanced sampling and a
class-weighted loss. They are tested **separately**, each on top of S1 (the
best confirmed setup so far), so each one's effect can be read on its own.
Three seeds each, six runs, launched in one script (`scripts\run_s3.ps1`).

### S3rfs: repeat-factor sampling (more copies of images with rare classes)
Script `scripts\make_rfs_dataset.py`, new dataset `wildlife-yolo-rfs` (val and
test hard-linked, so identical; training images only are repeated; the original
dataset is untouched). Method, in plain terms: for each class, take the share
of training images that contain it; a class seen in few images gets a repeat
factor of sqrt(0.3 / share); an image is repeated according to the rarest class
it contains, rounded to a whole number (1 to 4 copies; deterministic, so it is
not the random rounding of the original LVIS recipe).

| Class | Share of train images | Repeat factor |
|---|---|---|
| elephant | 7% | 2.04 |
| bird | 10% | 1.75 |
| antelope | 12% | 1.60 |
| gorilla | 12% | 1.56 |
| hog | 13% | 1.53 |
| chimpanzee, hippo | 31% | 1.00 |

Result: 434 images appear once and 415 appear twice (train list 1,264 entries,
49% longer; training epochs are correspondingly longer). Train boxes seen per
epoch: elephant 91 → 182, antelope 137 → 274, gorilla 167 → 334, bird 244 → 488.
Hippo also grows slightly (845 → 1,223) because it shares frames with rarer
classes. I chose the strength (t = 0.3, cap 4) as a moderate setting; it was
not tuned, so a stronger or weaker setting is a possible follow-up.

### S3w: class-weighted classification loss
Script `scripts\train_s3.py --class-weights`. The installed Ultralytics (8.4)
already multiplies its classification loss by a per-class weight if the model
carries a `class_weights` attribute, so I set that attribute through a training
callback; no library code is patched. Weights are inverse square-root of each
class's number of training boxes, scaled to average 1. Boxes seen in training:
antelope 137, bird 244, chimpanzee 871, elephant 91, gorilla 167, hippo 845,
hog 263, giving the largest weight to elephant and the smallest to
chimpanzee and hippo. The exact values are printed at the top of each
`logs\S3w_seed*.log`.

### What each run changes versus S1
| Run | Data | Loss |
|---|---|---|
| S1 (reference) | original | normal |
| S3rfs | original + repeated rare-class images | normal |
| S3w | original | rare classes weighted up |

Everything else is identical to S1 (augmentation, model, epochs, early
stopping, image size, seeds, validation set). `logs\S3_done.txt` marks the end.
S3 on top of the copy-paste data (the cumulative ladder from the proposal) is
deliberately left until we know whether either remedy works on its own.

---

## Entry 15: S4 preparation: the extra videos, and a leakage check that mattered (2026-10-02)

The student said to carry on without waiting, so while S3 trains (GPU busy) I
prepared S4 (pseudo-labelling), using only network and CPU.

### What the Zenodo record offers
The same Zenodo record as the dataset (10.5281/zenodo.17036940, licence
CC BY 4.0) also holds separate species video archives. The four that match the
proposal's S4 list were downloaded to `Downloads\zenodo_extra` on `setgpu`:
Warthog (3.4 MB), Gorilla (52.9 MB), Elephant (127 MB), Hippopotamus (135 MB).
They unpack to 9 video files. Other archives exist (buffalo, giraffe, zebra,
rhino, topi, impala, baboon, and a European animal set) but contain species our
model does not have, so they are not useful for S4. An archive called
`Elephants-Gorillas-Kobs_Detection_Dataset.zip` (813 MB) also exists; it was
not downloaded because it very likely overlaps the annotated dataset, and the
check below shows why that matters.

### Leakage check (the proposal requires pseudo-label sources never touch eval data)
For each video I took about 2 frames per second and compared each, using a
perceptual image hash (a 256-bit fingerprint of the picture), against all 1,220
annotated frames from all nine sessions, which include every validation and test
frame. A difference of 0 means the identical picture.

| Video | Size, length | Closest annotated frame (difference out of 256) | Verdict |
|---|---|---|---|
| Gorilla: 4 files (two are copies of one another) | 3840x2160, 9-12 s | **0** to `gorillas`, `gorillas2`, `gorillas3` | **Same footage as annotated sessions: unusable** |
| HIPPOPOTAMUS.CTPH.mp4 | 1920x1080, 54 s | **0** to `hippo2` | **Same footage: unusable** |
| Elephant_ANP.mp4 | 362x640 portrait, 30 s | 93 | New footage |
| Elephants. CTPH (long filename).mp4 | 1920x1080, 50 s | 79 | New footage |
| Hippopotamus.mp4 | 640x360, 46 s | 82 | New footage |
| Warthog.mp4 | 360x640 portrait, 29 s | 94 | New footage |

**Consequence:** had I pseudo-labelled "all the Gorilla and Hippopotamus videos"
as the handoff and proposal suggest, the model would have been trained on frames
identical to the validation and test images of gorillas and hippo2, which would
have inflated results without any warning. Only the four new videos are used.
(Values near 80 to 94 are what unrelated pictures give; matching frames give 0.)
The result also means no new gorilla footage is available for S4.

Other properties to note: the new videos are lower resolution and two are
portrait phone footage, so they differ from the training data. The proposal
treats this as a domain-shift variable to be measured, not assumed helpful.
They cover only elephant, hippo and hog (warthog), so S4 can add examples for
those classes only. It cannot help bird, antelope or gorilla.

---

## Entry 15b: S3 results: neither imbalance remedy beats S1 (2026-10-02)

Both remedies were checked to be active before reading results (the S2 lesson):
the RFS runs trained on a 1,264-image list (79 batches per epoch against 54 for
S1), and the S3w logs print the class weights actually used (elephant 1.59,
antelope 1.30, gorilla 1.17, bird 0.97, hog 0.94, hippo 0.52, chimpanzee 0.51;
`args.yaml` shows the intended datasets). Epochs run: S3rfs 36/30/64,
S3w 51/46/69. Validation set, 3 seeds, mean (sd). `*` = beyond seed noise
versus S1.

| mAP50 | S1 | S3rfs (sampling) | S3w (loss weights) |
|---|---|---|---|
| **all** | **0.767 (0.020)** | 0.730 (0.026) | 0.733 (0.017) |
| antelope | 0.565 (0.043) | 0.548 (0.057) | 0.538 (0.050) |
| bird | 0.242 (0.098) | 0.141 (0.100) | 0.204 (0.121) |
| chimpanzee | 0.723 (0.022) | 0.723 (0.025) | 0.701 (0.009) |
| elephant | 0.974 (0.025) | 0.892 (0.116) | 0.828 (0.048) * |
| gorilla | 0.978 (0.014) | 0.963 (0.049) | 0.978 (0.014) |
| hippo | 0.907 (0.013) | 0.857 (0.023) * | 0.898 (0.010) |
| hog | 0.977 (0.012) | 0.988 (0.004) | 0.985 (0.011) |

Overall mAP50-95 is unchanged (0.457 and 0.458 against 0.458). Recall: no
change beyond noise for the weak classes (bird 0.051 and 0.114 against 0.049;
antelope 0.503 and 0.469 against 0.460).

### Reading
- **Neither remedy improved the weak classes** (bird and antelope), and the
  rare class they were designed for, elephant, scored *lower* than in S1. The
  overall mAP50 is lower by about 0.035, which is within the seed spread, so the
  honest statement is "no gain", not "harm".
- **A caution about the elephant comparison:** S1's elephant score (0.974) is
  very high for a class with 91 training boxes and only 18 validation boxes. The
  S0 value was 0.788 and S3 values sit between. With 18 boxes a single seed can
  move this by 0.1, so S1's elephant number may itself be on the lucky side;
  I cannot tell from this data. The reliable conclusion is that imbalance
  handling gave no measurable benefit beyond what standard augmentation
  already gave.
- **Possible reasons (hypotheses, untested):** the imbalance in this dataset is
  only about 9:1 (not extreme); mosaic and scale augmentation in S1 already
  show rare classes in many contexts; the rare classes' difficulty is mostly
  scale and distance (bird, antelope), which re-weighting cannot fix. The S3
  strengths (t = 0.3; mean-normalised inverse-sqrt weights) were chosen once and
  not tuned.
- **Ladder consequence:** S1 remains the best configuration for the main
  comparison. S3 remedies are reported as tested and not adopted.

---

## Entry 16: A new finding: the models do not recognise new footage of the same species (2026-10-02)

### Trigger
Pseudo-labelling the four new videos with S1's best model (seed 0, validation
mAP50 0.780) at confidence 0.6 kept **only 4 of 305 sampled frames**. Looking at
the predictions showed why: the model often calls real elephants "hippo", with
low confidence. That sits oddly beside a validation elephant score of 0.97.

### Why validation hides this
Elephant (and every class that comes from a single session) is trained and
validated on the same video, only a few seconds apart in time. The validation
score measures "same scene, next few seconds", not "a different elephant, a
different place". This is exactly the concealed generalisation gap the
proposal set out to expose. For multi-session classes (hippo, gorilla) the
leave-session-out experiment (Experiment A, still to run) measures it directly;
for the others this external check is the only evidence we have.

### Method: external species check (exploratory)
The four new videos each show one known species (elephant ×2, hippo, warthog =
hog), and were shown to be new footage in Entry 15. For every model (5 configs
× 3 seeds = 15 models), on about 2 frames per second (305 frames), at
confidence ≥ 0.25: is the highest-confidence detection in the frame the
video's species? This gives species recognition only. **It does not test box
accuracy**, uses video-level labels (a video could contain a second species),
and frames from one video are highly correlated, so the effective sample is
four videos. Treat as indicative. Script `scripts\external_check.py`; data
`analysis\data\external_check.csv`.

Share of frames whose top detection is the right species (mean over 3 seeds):

| Config | Elephant (portrait, 362x640) | Elephant (1080p) | Hippo (640x360) | Warthog (portrait) |
|---|---|---|---|---|
| S0 | 0.00 | 0.04 | 0.23 | 0.01 |
| S1 | 0.00 | 0.23 | 0.58 | 0.17 |
| S2sam | 0.03 | **0.65** | 0.41 | 0.33 |
| S3rfs | 0.01 | 0.07 | **0.82** | 0.32 |
| S3w | 0.02 | 0.09 | 0.36 | 0.22 |

Seed-to-seed spreads are large (up to ±0.39), so only big differences count.

### Reading
- **Recognition on unseen footage is poor and varies a lot,** far below what
  validation suggests. The portrait phone clips (elephant 362x640, warthog) are
  the hardest; a model trained only on landscape footage meets a different
  aspect ratio, resolution and viewpoint.
- **Standard augmentation (S1) helps over no augmentation** here too (hippo
  0.23 → 0.58, elephant 1080p 0.04 → 0.23), which supports the in-domain result.
- **SAM copy-paste (S2sam) stands out for the 1080p elephant video:** 0.65
  against 0.23 for S1 (spread ±0.22, so not conclusive from 3 seeds). This is
  the only place where S2 looks clearly useful, and the validation set could
  not show it. **Hypothesis (untested):** pasting the same few elephants onto
  many backgrounds reduces reliance on the one elephant scene.
- S2sam is worse than S1 on the hippo video (0.41 against 0.58, with a large
  spread ±0.39), so it is not a uniform gain.
- **Imbalance remedies (S3) do not give a consistent benefit.** S3rfs is best
  on hippo, worst of the augmented configs on elephant; this looks like noise.

### Consequence for the report
1. Validation mAP is an optimistic, same-session number for classes that have a
   single session. The report should say so and show this external check.
2. This is the strongest argument for the proposal's cross-session design, and
   for collecting more varied footage as the single most valuable improvement.

## Entry 17: S4 (pseudo-labelling): design, yield and launch (2026-10-02)

Script `scripts\s4_pseudolabel.py`. Rules, set before looking at results:
- source frames: the 4 leak-checked videos only, 2 per second (305 frames);
- each video has one known species, so only detections of that species count
  (a conflicting class at confidence ≥ 0.3 means the model is unsure: frame
  dropped; any detection of the right species between 0.3 and 0.6 also drops the
  frame, because the unconfident animal would be taught as background);
- keep boxes with confidence ≥ 0.6; frames go into a copy of the **training**
  split only (`wildlife-yolo-ps2`; val/test hard-linked, unchanged).

Yield depended heavily on the labelling model:

| Model used to label | Frames kept (of 305) | Boxes |
|---|---|---|
| S1 seed 0 (best validation mAP50) | 4 | 4 |
| S2sam seed 0 | **38** (elephant CTPH 28, warthog 10) | 70 |

I used the S2sam model, because it recognises the new videos better (previous
entry); the choice of labelling model is not made using any validation or test
label. No frames survive from the portrait elephant video or the low-resolution
hippo video: the models are not confident there, so S4 cannot add examples for
those domains, which is the very footage that differs most from training.

**Label quality (inspected on a sample):** boxes sit on elephants and warthogs,
but they are **incomplete**: a herd of about seven elephants had three boxed,
and some boxes cover two overlapping elephants. Missed animals become
false background examples. This is the standard pseudo-label risk and is stated
here rather than corrected by hand (hand-fixing would no longer be
pseudo-labelling).

Training: `S4ps_seed{0,1,2}`, S1 settings exactly, on the training set plus the
38 pseudo-labelled frames (+4.5% images). With so few added frames I expect
little effect on validation; the result will say whether noisy extra labels
hurt. Logs `logs\S4ps_seed*.log`; `logs\S4_done.txt` marks completion.

---

## Entry 18: S4 (pseudo-labelling) results (2026-10-02)

Three seeds `S4ps_seed{0,1,2}` (epochs run in `logs\`), S1 settings plus 38
pseudo-labelled training frames (70 boxes; Entry 17). Validation set, mean (sd).

| mAP50 | S1 | S4 | | mAP50-95 | S1 | S4 |
|---|---|---|---|---|---|---|
| **all** | 0.767 (0.020) | 0.751 (0.017) | | **all** | 0.458 (0.004) | 0.454 (0.005) |
| antelope | 0.565 | 0.553 | | elephant | 0.688 (0.028) | **0.739 (0.006)** * |
| bird | 0.242 | 0.215 | | gorilla | 0.714 | 0.741 |
| chimpanzee | 0.723 | 0.716 | | hippo | 0.464 | 0.426 |
| elephant | 0.974 | 0.958 | | hog | 0.473 | 0.451 |
| gorilla | 0.978 | 0.956 | | | | |
| hippo | 0.907 | 0.881 | | | | |
| hog | 0.977 | 0.980 | | | | |

(`*` = beyond seed noise.)

### Reading
- **S4 gave no measurable gain.** All mAP50 differences are inside seed noise,
  and overall mAP50 is nominally 0.016 lower. This is not surprising: only 38
  frames (+4.5% images) were added, from only two of the four videos, labelled
  incompletely.
- The one flagged difference (elephant mAP50-95 up by 0.05) should be treated
  with suspicion: roughly 120 comparisons have been made across the report
  (8 classes × 3 metrics × several pairs), so a handful are expected to look
  "significant" by chance at this threshold. It would need more seeds to trust.
- **The S4 models must not be scored on the four new videos** (the external
  check of Entry 16): their frames were used to train these models, so that
  test would be contaminated. S4 is judged on the validation set only.
- **What this says about S4 as a technique here:** pseudo-labelling needs the
  labelling model to be confident on the new footage. Footage that differs most
  from training (portrait phone clips, low-resolution video) is exactly where
  confidence is lowest, so it yields no labels; the footage that does pass is
  the footage most like what the model already knows. That limits what S4 can
  add, and is a reportable finding.
- A fair follow-up (not done): lower confidence threshold, or labelling in
  several rounds. Both raise the risk of wrong labels; I did not pursue them
  because the threshold was fixed before seeing results and the boxes were
  already incomplete at 0.6.

### Multiple-comparison caveat (applies to Entries 9 to 18)
Welch t over 3 seeds with |t| > 2.8 was used as a rough "beyond noise" flag.
With so many comparisons, and only 3 seeds each, a few flags will be false
alarms. Conclusions that rest on a single flagged cell (S4 elephant mAP50-95)
are weaker than conclusions backed by several related cells (S1 improving
overall mAP50, elephant, antelope, hippo together).

---

## Entry 19: Status at end of session (2026-10-02, usage limit reached)

Done and recorded above: S0, S1, S2 (void built-in, then SAM version), S3
(sampling and loss weights), S4, external-footage check, results notebook.
Experiment A (leave-session-out) models are trained: `ExpA_lso_seed{0,1,2}` on
`wildlife-yolo-lso2` (corrected validation split, Entry 17 area; train 314 /
val 58 / test 148 images, test = whole `gorillas3` and `hippo` sessions).

**In progress when the session ended:** the first test-set evaluation of all 18
default-split models and the 3 Experiment A models (`scripts\eval_test.py`; it
writes `C:\Users\mrjos\test_default.csv` and `test_lso.csv` on `setgpu`, and
copies go to `analysis\data\` once finished). Not yet read or analysed.

**Still to do:**
1. Read the test CSVs; compare hippo and gorilla test mAP, default split vs
   leave-session-out (the Experiment A result); report the test numbers.
2. ONNX export and inference benchmark on the chosen config (S1).
3. Add S3, S4, external-check and Experiment A figures to the notebook
   (`analysis\build_nb.py`); it currently covers S0, S1, S2sam only.
4. Optional: matched "old split, no augmentation" run for the chimpanzee claim;
   interleaved antelope split comparison; Sunbird language table (needs the
   student's API key).

---

## Entry 20: Test-set results and Experiment A (2026-10-02, after the usage-limit pause)

### Fixing the evaluation script first
The first attempt to score all models on the test split hung for over 30
minutes. I killed it and found the cause: Ultralytics' data-loader worker
processes stall on this Windows machine during validation. With `workers=0`
one model takes 11 seconds. All 21 models were then scored in one run
(`scripts\eval_test.py`; outputs `analysis\data\test_default.csv`,
`test_lso.csv`). Training was not affected (it never hung).

### Test split, default (chronological) split, mean over 3 seeds
This is the first and only use of the test set; configuration choice (S1) had
already been made on validation, so these numbers are not used for selection.

| mAP50 | S0 | S1 | S2 SAM | S3rfs | S3w | S4 |
|---|---|---|---|---|---|---|
| **all** | 0.612 | **0.713** | 0.658 | 0.687 | 0.693 | 0.690 |
| antelope | 0.136 | **0.492** | 0.402 | 0.431 | 0.362 | 0.418 |
| bird | 0.039 | 0.041 | 0.032 | 0.033 | 0.010 | 0.026 |
| chimpanzee | 0.750 | 0.781 | 0.797 | 0.790 | 0.767 | 0.772 |
| elephant | 0.826 | 0.973 | 0.900 | 0.939 | 0.946 | 0.995 |
| gorilla | 0.793 | 0.768 | 0.664 | 0.733 | 0.827 | 0.728 |
| hippo | 0.805 | **0.970** | 0.827 | 0.908 | 0.951 | 0.915 |
| hog | 0.935 | 0.962 | 0.986 | 0.977 | 0.986 | 0.975 |

mAP50-95 overall: S0 0.337, S1 0.370, S2 0.352, S3rfs 0.358, S3w 0.369, S4 0.359.

- **S1 is again the best (or tied) configuration,** and the benefit of
  standard augmentation is larger on test than on validation (+0.10 overall
  mAP50). This confirms the choice made on validation.
- **Antelope on test is the starkest case of the time shift** (Entry 8): with
  no augmentation only 0.136, with S1 0.492. The test frames show the most
  distant, biggest herds (6 animals per frame at 0.37% of the image).
- **Bird is essentially undetectable on test for every configuration**
  (mAP50 about 0.01 to 0.04; mAP50-95 under 0.01). Even SAM copy-paste, which
  raised bird recall on validation, gave no test gain. Bird is an unsolved
  class in this project and should be reported as such.
- Chimpanzee holds up on test (0.75 to 0.80), so the split fix is not a
  validation-only effect.
- The copy-paste, sampling, loss-weight and pseudo-label variants are not
  better than S1 overall on test either; the differences between them are
  mostly inside what seed spread would explain (a per-seed spread was not
  computed for test in this entry).

### Experiment A: leave-session-out (cross-session generalisation)
Models trained with the S1 settings on `wildlife-yolo-lso2` (gorillas,
gorillas2, hippo2 only) and scored on two sessions they never saw
(`gorillas3`, `hippo`), 3 seeds.

| Class | Default split, S1, test | Leave-session-out, test | Drop |
|---|---|---|---|
| gorilla mAP50 | 0.768 | **0.147 ± 0.031** | -0.62 |
| hippo mAP50 | 0.970 | **0.064 ± 0.087** | -0.91 |
| gorilla mAP50-95 | 0.463 | 0.042 ± 0.011 | |
| hippo mAP50-95 | 0.316 | 0.014 ± 0.020 | |

**Headline finding: when a whole recording session is held out, gorilla and
hippo detection collapses** (gorilla about 5x lower, hippo about 15x lower).
The standard chronological split reports 0.77 and 0.97. This is the
concealed-gap result the proposal was designed to expose, and it matches the
independent external-footage check (Entry 16).

**Caveats, stated plainly:**
- The two columns use *different test images* (sessions), and the
  leave-session-out models have much less training data (gorilla: 88 training
  frames, no chimpanzee/antelope/hog) and cannot be compared point-for-point.
  Part of the drop is simply less data.
- The held-out `hippo` session shows mostly tiny, distant hippos (median box
  0.21% of the image in its training part, Entry 8), so scale is a second
  reason, separate from "new session".
- The hippo spread (±0.087 on a mean of 0.064) is as large as the mean.
- Three seeds, one held-out session per class: this shows a large gap, not a
  precise size for it.
- The corrected validation set (last 15% of each training session) still comes
  from the training sessions, so early stopping did not "see" the new session.

### Updated ladder status
S0, S1, S2 (SAM), S3 (rfs, w), S4 done; S1 selected. Remaining: ONNX export and
speed benchmark; notebook update for the new results; optional extras.

---

## Entry 21: ONNX export and inference benchmark (2026-10-02)

Model: the chosen configuration S1, seed 0 (`runs\S1_augment_seed0\weights\best.pt`).
Seed 0 was picked because it had the highest validation mAP50 of the three S1
seeds (0.780); this is a choice of one model to export, not a claim about
S1's expected accuracy (the 3-seed mean is 0.767).

**Environment change (needed for the task):** `onnx 1.23.1` and
`onnxruntime 1.30.0` (plus `protobuf`, `flatbuffers`, `ml_dtypes`) were
installed into the project's venv with pip. A dry run first showed pip would add
only those new packages and leave torch and numpy untouched, as the handoff
requires.

**Export:** Ultralytics, ONNX opset 17, 640x640 fixed input, simplified graph.
Saved as `weights\S1_seed0_best.onnx`. Script `scripts\export_bench.py`.

**Accuracy parity (validation set, 180 images):**

| Format | mAP50 | mAP50-95 |
|---|---|---|
| PyTorch (.pt) | 0.7783 | 0.4568 |
| ONNX | 0.7757 | 0.4516 |

The export loses 0.003 mAP50 and 0.005 mAP50-95, which is negligible (the
two paths use different batch sizes and slightly different preprocessing).

**Size and speed** (batch 1, 640x640, model forward pass only, median of 200
runs, GPU timings with synchronisation; CPU = this PC's CPU, 60 runs):

| Setup | Median ms | 95th percentile ms |
|---|---|---|
| PyTorch, RTX 5070 Ti, fp32 | 3.29 | 3.75 |
| PyTorch, RTX 5070 Ti, fp16 | 5.91 | 6.18 |
| PyTorch, CPU | 17.81 | 20.36 |
| **ONNX Runtime, CPU** | **13.34** | 14.47 |

Reading: ONNX Runtime on CPU is about 25% faster than PyTorch on the same CPU
and gives about 75 frames per second for the detector alone, which is plenty
for review of camera-trap video on a laptop. Half precision was *slower* than
fp32 on this tiny model (hypothesis: casting overhead dominates for a
3-million-parameter network); I did not investigate. These figures exclude
reading the image, resizing and non-maximum suppression (the full
`predict` pipeline measured about 14 ms inference + 1 ms post-processing per
image during validation). They come from one desktop PC and say nothing about
a low-power field device (Raspberry Pi class); that would need a measurement
on the target hardware.

Sizes: the PyTorch checkpoint is 6.23 MB (stored in half precision) and the
ONNX file 12.27 MB (full precision).

---

## Entry 22: Notebook brought up to date; where the project stands (2026-10-02)

`analysis\results_notebook.ipynb` (and `.html`) was rebuilt and re-executed
without errors. It now covers all six configurations (S0, S1, S2 SAM, S3
sampling, S3 loss weights, S4) on validation with seed spread and noise flags,
plus new sections for the test-set results, Experiment A, the external-footage
check, and the ONNX export and latency. New figures: `09_test_per_class`,
`10_experiment_A`, `11_external_check`, `12_latency`, and the new
`table_test_mAP50.csv`; the earlier figures and tables were regenerated with all
configurations. The summary section at the end of the notebook was rewritten
to match the final findings. A copy of `analysis\` is kept in the project
folder on `setgpu`.

### Where everything stands
| Item | Status |
|---|---|
| Split fix (chimpanzee) | Done and verified; documented before/after |
| Ablation ladder S0 to S4, 3 seeds each | Done; S1 selected |
| Test-set evaluation | Done (Entry 20) |
| Experiment A (leave-session-out) | Done (Entry 20) |
| External-footage check | Done (Entry 16) |
| ONNX export and benchmark | Done (Entry 21) |
| Notebook with figures and tables | Done (this entry) |
| Local-language lookup table (Sunbird AI) | **Not started: needs the student's API key**, and a native speaker to check Luganda and western Uganda terms |

### Open items and honest limits
- Bird is not solved (test mAP50 about 0.03); more footage with birds, or a
  higher-resolution/tiled approach, would be the next experiment.
- A matched "old split, no augmentation" run would make the chimpanzee
  before/after claim airtight; about 3 minutes of GPU time.
- The interleaved-antelope-split comparison was planned as a side experiment
  and has not been run.
- S3 and S4 settings were fixed once and not tuned; negative results apply to
  those settings.
- Everything was run on one PC; no field-device (Raspberry Pi class) timing.
- No automated test of the SAM cutout or pseudo-label scripts beyond the visual
  checks described; the scripts are in `scripts\` on `setgpu`.

---

## Entry 23: Matched "old split" run: launch (2026-10-02)

**Why:** the chimpanzee claim (mAP50 0.09 → 0.67) compared an exploratory run on
the old split (augmentation on, stopped at epoch 36) with S0 on the fixed split
(augmentation off). Anyone reading it could say augmentation and stopping point
also changed. The matched run removes that: **old chronological split, exactly
the S0 settings** (all augmentation zero, `imgsz=640`, `patience=20`,
`batch=16`, seeds 0, 1, 2). Run names `N0_naive_seed{0,1,2}`.

**A trap found and avoided:** the old dataset's own `data.yaml`
(`wildlife-yolo-naive\data.yaml`) still says `path: ...\wildlife-yolo`. After
the folder rename in Entry 4, that path points at the *fixed* dataset, so using
the file would have silently trained on the fixed split and "confirmed" the fix
trivially. I wrote a corrected config outside the dataset folder,
`wildlife-capstone\configs\data_naive.yaml`, with `path` set to
`wildlife-yolo-naive`, and use that. (The old dataset's files were not edited.)
The old dataset's label cache files may be regenerated by Ultralytics when the
runs start; the images and label text files are unchanged.

Scoring plan: (1) each run's own validation result (what a student using the old
split would have reported); (2) the same models on the **fixed** validation and
test sets, which is the fair common yardstick.

## Entry 24: Matched old-split result: the chimpanzee claim, tested properly (2026-10-02)

Three seeds, old chronological split, **exactly the S0 settings** (augmentation
off). Confirmed beforehand that the runs read the corrected config
(`args.yaml` shows `data_naive.yaml`, mosaic 0, flip 0). Epochs run: 40, 47, 60.

Chimpanzee mAP50, mean ± sd over 3 seeds:

| Trained on | Scored on | Chimp mAP50 | Chimp recall |
|---|---|---|---|
| old split | **old** validation | **0.143 ± 0.048** | 0.12 |
| old split | **fixed** validation | 0.481 ± 0.016 | 0.46 |
| **fixed** split | **fixed** validation | **0.670 ± 0.014** | 0.61 |
| old split | fixed test | 0.680 ± 0.031 | |
| fixed split | fixed test | 0.750 ± 0.026 | |

### What this shows
- **The chimpanzee problem is confirmed with matched settings.** With the
  exact same S0 training recipe, the old split gives chimp mAP50 0.14 (the
  earlier exploratory run, with augmentation on, gave 0.09) and the fixed split
  gives 0.67. So the difference is not caused by augmentation or stopping.
  The matched run closes the gap in the evidence flagged in Entry 7.
- **But "the split" has two parts and both matter.** Scoring the old-split
  models on the fixed validation set lifts chimp from 0.14 to 0.48. So roughly
  0.34 of the 0.53 total gain comes from evaluating on a better-composed set
  (landscape and padded frames both present, padding cropped), and a further
  0.19 comes from training on the fixed split. On the test set the training
  effect is smaller (0.68 vs 0.75).
- **Why cropping probably also helps by itself (hypothesis, untested):** an
  uncropped padded frame is 1920 px wide with only a 608 px strip of picture;
  after shrinking to 640 px the chimps are about 1.8 times smaller than in the
  cropped frame. A matched check of this would be an old-split run with only the
  crop applied.
- **A fair statement for the report:** "A format-aware split with the padding
  removed raised validation chimpanzee mAP50 from 0.14 to 0.67 under identical
  training settings; about two-thirds of that gain appears already when the old
  models are scored on the fixed evaluation set, so the evaluation set's
  composition was a large part of the original problem." mAP values on two
  differently composed evaluation sets are not strictly comparable.
- Other classes under the old split behave similarly to the fixed split on
  validation (overall mAP50 0.640 vs 0.691), as expected since only chimpanzee
  changed. Bird, antelope: higher on old-split validation but near zero or low
  on the fixed test, again showing the time-shift problems found earlier.

Data: `analysis\data\n0_on_naive_val.csv`, `n0_on_fixed_val.csv`,
`n0_on_fixed_test.csv`; figure `analysis\figures\02b_chimp_matched_check.png`
(new section 1.1b of the notebook).

---

## Entry 25: Final capstone report drafted (2026-10-02)

The student has no report template, so I wrote the final report in the
standard structure of the proposal: Summary; 1 Introduction and objectives;
2 The dataset; 3 Methods; 4 Results (split fix, validation ablation, test set,
unseen sessions, new videos, ONNX); 5 Discussion and limitations; 6 Conclusions
and future work; Appendix (reproducibility, references). It was written in
Claude Docs (exports to Word or PDF) with the notebook figures embedded and the
key tables inline. Title: "Data-Efficient Wildlife Detection from Ugandan Field
Footage: Capstone Report". Link:
https://claude.ai/code/artifact/1f6b2e99-bca5-45e2-aee1-ed6e155695ba

While drafting, I re-checked claims against the data and corrected two:
"S1 beat S0 on every new video" (they tied at 0% on the portrait elephant clip)
and "other classes scored 0.55 to 0.99" in the exploratory run (bird was 0.40).
Statements that are guesses (for example, why copy-paste helped on a new
elephant video, or the unexplained gorilla box-tightness change) are labelled as
untested in the text. The Sunbird language table is stated as not built.
The student still needs to check the author line, add the university and
supervisor details, and read the report against their own course requirements.

---

## Entry 26: Metrics audit and gap-filling (2026-10-02)

The student asked whether all required metrics (confusion matrix etc.) are in
hand. Audit result: precision, recall, mAP50 and mAP50-95 per class, seed and
configuration existed (validation and test), but the report lacked precision,
recall and F1 tables, a confusion matrix and any error analysis (the proposal
asks for false positives/negatives). Added to the report as Section 4.7:

- Precision / recall / F1 per class on the test set for S0 and S1
  (`analysis\data\test_prf1.csv`; from `test_default.csv`; Ultralytics reports
  P and R at the F1-maximising confidence; F1 computed per seed then averaged).
- An error-count table for S1 seed 0 on the test set at confidence 0.25,
  overlap 0.5 (`analysis\data\error_counts.csv`): found correctly, found with the
  wrong class, missed, false-alarm boxes. Script `scripts\test_plots_errors.py`.
- A threshold sweep (0.001 to 0.5): wrong-class matches 23 of 662 at 0.001, 5 at
  0.05, 3 at 0.1, none from 0.25 up. Script `scripts\conf_sweep.py`.
- An image of example errors (`analysis\data\test_plots\error_examples.jpg`).
- Test-set confusion matrices, PR and F1 curves for S0 and S1 seed 0 from the
  Ultralytics validator (`analysis\data\test_plots\`).

**An inconsistency I could not resolve, and how it is handled:** the library's
normalised confusion matrix shows large cross-species cells (for example about
25% of gorillas predicted as hippo), but my own matching finds no wrong-class
boxes at confidence 0.25 and only 23 of 662 at 0.001. I checked three gorillas3
frames by hand: all predicted boxes were gorilla. I do not know how the library
builds those cells (it was not investigated), so the report relies on my
count table, states its settings, and says the library matrices were not
reconciled. A reader wanting a confusion matrix should know this is a known
loose end.

Also: the final trained model files were copied to the laptop,
`D:\Safari_Wild_Animal_Detection\model\S1_seed0_best.pt` (6.2 MB) and
`S1_seed0_best.onnx` (12.3 MB). Originals on `setgpu`:
`C:\Users\mrjos\Downloads\wildlife-capstone\runs\S1_augment_seed0\weights\best.pt`
and `...\weights\S1_seed0_best.onnx`.

---

## Entry 27: Confusion-matrix discrepancy resolved (2026-10-02)

The student asked whether the unreconciled matrices were a problem and whether
we could do better. Yes on both, and it is now resolved.

**Cause:** I read the Ultralytics source (`utils\metrics.py`,
`ConfusionMatrix.process_batch`, and `models\yolo\detect\val.py` line 259): the
detection validator builds the matrix with `conf=self.args.conf`, i.e. the
validation confidence threshold, which defaults to **0.001**. The matrices I had
(and every matrix saved during training) were therefore built from all boxes
down to 0.1% confidence.

**Test (S1 seed 0, test set, library matrix rebuilt at two thresholds):**

| Threshold | Correct species | Wrong species | Missed | False alarms |
|---|---|---|---|---|
| 0.001 (library default) | 356 | 229 | 77 | 17,426 |
| 0.25 (working threshold) | 473 | 2 | 187 | 170 |
| My count table, 0.25, overlap 0.5 | 460 | 0 | 202 | 186 |

At 0.25 the library matrix agrees with my own count (differences come from its
0.45 overlap rule against my 0.5). Neither method was wrong; the earlier figure
was drawn at a threshold nobody would use, which made it look as if gorillas
were often called hippos. They are not: at 0.25 there are 2 species mix-ups out
of 662 animals (one gorilla called elephant, one hippo called hog).

**Changes:** report Section 4.7 now shows the 0.25 test-set matrix for S1 and
explains the threshold trap; the "not reconciled" note is gone. The notebook's
confusion-matrix section now warns about the 0.001 default and adds the 0.25
test-set matrices for S0 and S1 (`figures\08b_confusion_test_conf025.png`).
Files: `analysis\data\test_plots\S0s0_conf0.25_*`, `S1s0_conf0.25_*`.
Script used for the check: `scripts\cm_compare.py` (kept in the project for
reproducibility; its logic is two `model.val(..., conf=...)` calls reading
`results.confusion_matrix.matrix`).

---

## Entry 28: Full project backup to the laptop (2026-10-02)

The student asked for a complete project folder on the laptop, because every
run and script existed only on `setgpu` (which went offline once in a power cut).
Created `D:\Safari_Wild_Animal_Detection\wildlife-capstone\` (about 760 MB):
`scripts/`, `configs/`, `logs/`, `runs/` (all training runs and weights),
`cutouts/`, `analysis/` (notebook, figures, data), `weights/` (ONNX), the report,
plus `BACKUP_README.md` (layout and how to rebuild what is left out) and
`requirements_exact.txt` (exact package versions of the working environment).
Also `D:\Safari_Wild_Animal_Detection\dataset_labels\`: label files, configs and
manifests (no images) for the six dataset variants.

Method: packed on `setgpu` with `tar`, copied with `scp`, unpacked locally.
Verification: archive sizes matched exactly before and after the copy, and the
unpacked file counts match the source (scripts 30, configs 1, logs 33, runs 646,
cutouts 1425, analysis 74, weights 2); `PROJECT_REPORT.md` is byte-identical to
the master copy. The temporary archives were deleted on both machines.

Deliberately not copied (and why): the Python environment (rebuildable, see
README), dataset images (rebuildable from `Safari_Dataset` with the saved
scripts and seeds; the originals are already on the laptop), `sam_b.pt` (358 MB,
downloads automatically), and the downloaded extra videos (re-downloadable from
Zenodo). Disk check beforehand: D: had 31 GB free (earlier notes said the laptop
disks were nearly full, so the copy was kept small on purpose).

---

## Entry 29: Can the weak points be fixed? A 1280-pixel test; predict.py; next steps (2026-10-02)

### Question from the student
Bird (almost never found), antelope (weak), chimpanzee (middling), poor results on
unseen sessions, and no field-hardware timing: fix them, or record them as
limitations?

### What was tried: higher input resolution (the cheapest fix for small animals)
S1 settings exactly, but `imgsz=1280` and `batch=8` (to fit memory), seeds 0 to 2
(`runs\S1_1280_seed{0,1,2}`; epochs run 55, 90, 66; script `scripts\train_hr.py`,
`scripts\run_hr.ps1`). Scored at 1280 on validation and test with
`scripts\eval_test.py --imgsz 1280` (new option). Data:
`analysis\data\hr_val.csv`, `hr_test.csv`.

| mAP50, mean of 3 seeds | val 640 | val 1280 | test 640 | test 1280 | test recall 640 | test recall 1280 |
|---|---|---|---|---|---|---|
| all | 0.767 | 0.730 | 0.713 | 0.689 | 0.68 | 0.67 |
| antelope | 0.565 | 0.549 | 0.492 | 0.486 | 0.40 | 0.55 |
| bird | 0.242 | 0.160 | 0.041 | 0.020 | 0.00 | 0.01 |
| chimpanzee | 0.723 | 0.711 | 0.781 | 0.758 | 0.73 | 0.68 |
| elephant | 0.974 | 0.837 | 0.973 | 0.858 | 0.98 | 0.74 |
| gorilla | 0.978 | 0.966 | 0.768 | 0.800 | 0.71 | 0.80 |
| hippo | 0.907 | 0.901 | 0.970 | 0.919 | 0.94 | 0.92 |
| hog | 0.977 | 0.988 | 0.962 | 0.984 | 0.96 | 0.99 |

Test mAP50-95 overall: 0.370 (640) vs 0.344 (1280).

**Reading:** higher resolution did not help overall and did not help bird at all.
Antelope recall rose (0.40 to 0.55) without a better mAP50. Elephant dropped.
**Decision:** record the weak points as limitations, citing this experiment as
evidence that the simplest remedy was tried; the real fixes need more data (bird
examples, footage from more places) or hardware (field timing). Added to the
report's Discussion. 640 remains the chosen setting.

Technical note: an SSH connection reset during this run cut the live log stream,
but training continued (results files kept updating) and the final logs are
complete. All three runs finished normally.

### predict.py and HOWTOUSE.txt (a way to run the model)
`wildlife-capstone\predict.py`: runs the model on an image, a folder of images or a
video; writes annotated copies, `detections.csv` and a per-class summary; options
for confidence, frame skipping, model file (.pt or .onnx), device, output folder.
`HOWTOUSE.txt` explains it in plain English, including the known limits.

Tested on `setgpu`: a folder of two test images (antelope and hog, boxes correct on
visual check); the 29-second warthog video at every 10th frame (72 frames, annotated
video written; the model called many warthogs "hippo", consistent with the new-
footage weakness); the ONNX model on CPU; and three bad inputs (missing file,
missing model, wrong file type), each giving a clear message.

**A problem found and fixed during testing:** with a GPU present, Ultralytics'
ONNX loader asks for the `onnxruntime-gpu` package and tries to pip-install it
automatically. That hung, and repeated test attempts left several stuck pip
processes. I stopped my own processes (the machine is shared; another user's jobs
were left alone) and confirmed the environment was unchanged (torch
2.12.0.dev20260408+cu128, onnxruntime 1.30.0, no onnxruntime-gpu installed).
Fix in `predict.py`: it sets `YOLO_AUTOINSTALL=false` so it never installs
packages, and runs ONNX models on the CPU, which needs only plain `onnxruntime`.
After the fix the ONNX test completed in seconds.

### Next step written up: the local-language species-name table
`wildlife-capstone\NEXT_STEPS.md` holds the plan (languages, request count,
storage format, back-translation check, native-speaker verification, a
`--language` option for predict.py). Blocked only on a Sunbird AI API key and on
speakers to check terms. The report's Conclusions now state it as the planned
next step.

### Report export
The Claude Docs report is exported by the student from the document itself (click
the document's name, then Export, then Word or PDF). My attempt to export it to a
file automatically was refused by the docs tool, so this is a manual step.

---

## Entry 30: Clean-up and consolidation (2026-10-02)

The student exported the final report to Word and asked for one clean project
folder on both machines, with redundant files removed.

### Laptop: `D:\Safari_Wild_Animal_Detection` is now the single project folder
Before deleting anything I compared duplicates by checksum and file count.
- **Deleted (byte-identical duplicates):** top-level `prepare_dataset.py`,
  `visualize_samples.py`, `EXECUTION_PLAN.md`, and the top-level `analysis\`
  (identical to the project copy). Also the duplicate ONNX and an unused stock
  model file `yolo26n.pt` in `weights\` (5.5 MB; not used by any experiment;
  re-downloadable), then the empty `weights\`. The final model lives in `model\`.
- **Moved, not deleted:** the early exploratory images and old-split confusion
  matrix went to `evidence\`; the contents of the nested `wildlife-capstone\`
  folder were merged up into the root and the empty wrapper folder removed.
  File counts before and after the merge are identical (scripts 32, runs 709, logs
  36, cutouts 1425, analysis 85, configs 1, model 2, dataset_labels 7081,
  Safari_Dataset 1229).
- **Fixed:** `predict.py` now finds the model in `model\` next to it (with a
  fallback to one folder up); `HOWTOUSE.txt` and `BACKUP_README.md` paths updated
  to the single-folder layout. `predict.py` default-model resolution was checked.
- Added: `Data-Efficient Wildlife Detection from Ugandan Field Footage Capstone
  Report.docx` (the student's Word export of the final report).

### `setgpu`: `C:\Users\mrjos\Downloads\wildlife-capstone` plus datasets
- **Deleted:** 38 stray `runs\detect\val*` folders (all created today by my
  evaluation calls, 0 MB, no weights; the one important folder,
  `runs\detect\runs\S0_baseline`, the original exploratory run, was kept);
  `wildlife-yolo-ps` (an unused 4-frame pseudo-label variant, superseded by
  `-ps2`); `visual_check2` (my sanity images, regenerable); `weights\` (dup ONNX
  and the unused stock model) after copying both final model files into a new
  `model\` folder; my helper scripts in the home folder.
- **Kept on purpose:** `wildlife-yolo-naive` and `runs\detect\runs\S0_baseline`
  (evidence), the six other dataset variants, `wildlife-yolo-lso` (the student's
  original leave-session-out set), `visual_check` (the student's), `zenodo_extra`
  (needed to re-run the pseudo-label and new-video checks), `Safari_Dataset`,
  the Python environment, `sam_b.pt`, and all runs including the void
  `S2_copypaste` runs (evidence for Entry 11).
- **Not touched:** two installer files in Downloads (`python-3.12.5-amd64.exe`,
  `python-manager-26.3.msix`): not created by this project, left for the owner.
- The machine is shared with other accounts; only the `mrjos` project files were
  changed.

### Why the data folders are not inside the project folder on `setgpu`
Many scripts have the data folders' absolute paths written in them
(`C:\Users\mrjos\Downloads\wildlife-yolo...`); moving them would break those
scripts, so the layout was left as it is and documented.

---

## Entry 31: Which documents are still valid (2026-10-02)

The student asked whether the proposal and the other documents in the project
folder are still valid. Each was read against what was actually done.

| Document | Verdict | Action |
|---|---|---|
| `Capstone_Proposal_Wildlife_Detection.docx` | Valid as a record of the plan; **not** an accurate description of the finished work (split design, models tried, ladder structure, S4/S5, language table all differ) | Left unchanged (it is the submitted document). Differences listed in `PROPOSAL_VS_DELIVERED.md` and in the report as new Section 3.5 |
| `README.md` (original setup guide) | Out of date: old paths, an S0 command that leaves augmentation on, no fixed split | Marked SUPERSEDED at the top, kept for history |
| `EXECUTION_PLAN.md` | Out of date for the same reasons, plus the `project=runs` path problem | Marked SUPERSEDED at the top, kept for history |
| `HANDOFF_CLAUDE_CODE.md` | Historical brief; all its tasks are done | The student removed it from the laptop folder on purpose. A copy still exists on `setgpu` |
| `requirements.txt` | Loose (no versions) | `requirements_exact.txt` records the real versions |

Also noted: one fact in the proposal that the work corrected is the frame count
(1,173 stated; 1,220 image files present). The student must re-export the Word
report to include the new Section 3.5.


---

## Entry 32: Lecturer-ready submission folder and professional report (2026-10-02)

The student asked for only what a lecturer needs in the folder, including a professional report.

**Report.** The Claude Docs report was rebuilt as a formatted Word document (A4, cover page, table of contents with page
numbers, numbered and captioned figures and tables, running header and page numbers, references): 17 pages including the
cover, 9 figures, 10 tables. Text is the same as the online report with all later corrections (including new Section 3.5,
the 1280-pixel test, F1 and error analysis, and the confusion matrix at confidence 0.25). The table of contents was filled
in using Microsoft Word on this PC, and a PDF was exported from the same file. Page-by-page inspection found and fixed a
blank page, two chart legends covering bars (figures regenerated in the notebook), a small confusion-matrix image
(white margins cropped) and a table separated from its introductory sentence.

**Folder.** `D:\Safari_Wild_Animal_Detection` now holds only: `00_START_HERE.txt`, `01_Report` (Word and PDF),
`02_Model_and_Demo` (model, `predict.py`, `HOWTOUSE.txt`, exact package versions), `03_Results` (notebook .ipynb and
.html, figures, result tables), `04_Code` (all scripts and a README), `05_Supporting` (proposal, differences from it,
this log, next steps, early evidence). About 35 MB.

**Archive, nothing deleted.** Moved to `D:\Safari_Wild_Animal_Detection_working_archive` (5.1 GB): `runs` (709 files),
`logs` (36), `cutouts` (1,425), `dataset_labels` (7,081), `Safari_Dataset` (1,229), the old setup guides, the previous Word
export, notebook build scripts and diagnostic images. File counts before and after the move were identical.

**Checks:** `predict.py` finds the model in the new layout; the notebook was re-executed from `03_Results` and ran
without error (self-contained); control characters in text files were checked after a path-escaping fault corrupted
one file, and it was repaired.

The `setgpu` working copy was not changed by this step.
