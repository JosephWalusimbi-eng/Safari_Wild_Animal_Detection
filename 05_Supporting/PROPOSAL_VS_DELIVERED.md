# Proposal versus what was delivered

The proposal (`Capstone_Proposal_Wildlife_Detection.docx`, September 2026) is a record of
the plan and should be left as submitted. It is accurate as a plan, but it is no longer an
accurate description of the finished work. This table lists every place the two differ.
(The final report, Section 3.5, carries the same table.)

| Topic | Proposal said | What was done | Why / status |
|---|---|---|---|
| Frame count | 1,173 frames (and "1,176 summed") | 1,220 image files in the nine session folders; all used | The folders hold more files than the Zenodo description states. The 3,909 boxes and per-class totals match exactly. |
| Main split (Section 6.1) | Hold out whole sessions for validation and test; frame-level blocked split only for single-session classes | Each session cut in time order 70/15/15 for every class; chimpanzee video split into widescreen and padded-portrait parts, bars cropped, each part cut separately | A first run showed the time cut left only distant, padded footage in chimpanzee validation and test. Whole-session holdout was used only in Experiment A. |
| Model (Section 6.2) | YOLOv8 or YOLO11, nano and small variants | YOLOv8-nano only | Small variant not tried. |
| Fine-tuning settings | Lower learning rate, cosine schedule, early stopping, freezing versus unfreezing early layers | Early stopping (patience 20) and Ultralytics default optimiser settings | No learning-rate, cosine or freezing comparison was run. |
| S0 baseline | "Minimal augmentation" | No augmentation at all | Ultralytics turns augmentation on by default; it was set to zero to get a true floor. |
| Cumulative ladder | Each step added on top of the previous one | S2, S3, S4 each added to S1 separately, not stacked | Keeps each effect readable on its own; a stacked run was not done. |
| S2 copy-paste | Pasted animals with SAM masks | Done offline: 400 synthetic training images, elephant, bird, antelope only (gorilla and chimpanzee masks too fragmented) | The built-in Ultralytics copy-paste is a no-op on box-only labels and was shown to be void. |
| S3 imbalance | Repeat-factor or class-balanced sampling, and class-weighted or focal loss | Repeat-factor sampling and class-weighted loss, tested separately | Focal loss not tried. |
| S4 pseudo-labelling | Extra videos (Gorilla, Elephant, Hippopotamus, Warthog) | Four new videos used; all four Gorilla files and the 1080p hippo clip are the same footage as annotated sessions and were excluded; 38 frames labelled | Leak check by image fingerprint. No new gorilla footage exists in the record. |
| S5 synthetic images (stretch) | Optional diffusion/inpainting experiment | Not done | Stretch item. |
| Seeds | At least three per configuration | Three per configuration | As planned. |
| Metrics | Precision, recall, F1, mAP50, mAP50-95, confusion matrix, error analysis | All reported; F1 and error analysis for S0 and S1 on test only; confusion matrix drawn at confidence 0.25 | Library default (0.001) matrices were misleading and were not used. |
| Experiment A | Hippo (2 sessions) and gorilla (3 sessions) leave-session-out | Done on a corrected dataset with a clean validation split | The original leave-session-out set had no validation folder. |
| ONNX and speed | Export and latency as a proxy for field use | Exported; CPU and GPU latency on one desktop PC | Not timed on a field device. |
| Antelope identity | "Uganda kob, to be visually confirmed" | Confirmed visually | |
| Local-language table (6.6) | Stretch feature: 7 classes in English plus Ugandan languages via Sunbird AI | Not built; plan written in `NEXT_STEPS.md` | Needs the Sunbird AI API key and native-speaker checks. |
| Work not in the proposal | | Chimpanzee padding problem and fix with a matched old-split check; antelope time shift; 1280-pixel test; external check on new videos; leakage check of extra videos; `predict.py` | Added because the experiments required or exposed them. |
| Timeline | 10 weeks | Experiments run over a few days of compute | |
