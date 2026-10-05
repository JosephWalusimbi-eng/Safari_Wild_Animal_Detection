CODE USED IN THE PROJECT
========================
These scripts were run on the GPU computer (Windows, NVIDIA RTX 5070 Ti). They contain
absolute paths to that machine (C:\Users\mrjos\Downloads\...); edit those paths to run them
elsewhere. They are included so every step is inspectable. They are not needed to use the
model (see ..\02_Model_and_Demo) or to re-run the figures (see ..\03_Results).

Data preparation
  scripts\prepare_dataset.py       Original build: repairs the gorilla/chimpanzee labels, converts
                                   COCO boxes to YOLO format, original time-ordered split.
  scripts\prepare_dataset_v2.py    The FIXED split (chimpanzee video split by format, padding cropped).
  scripts\split_check.py, box_stats.py, visualize_samples.py
                                   Checks used to find the split problem and to inspect boxes.
  scripts\make_lso2.py             Experiment A dataset (leave-session-out, clean validation split).
  configs\data_naive.yaml          Corrected config for training on the original split.

Techniques tested
  scripts\extract_cutouts.py       Cuts animals out of training frames with SAM (Segment Anything).
  scripts\make_cp_dataset.py       Builds the copy-paste training set (S2).
  scripts\make_rfs_dataset.py      Repeat-factor sampling dataset (S3).
  scripts\s4_pseudolabel.py        Pseudo-labelling of new videos (S4); s4_probe.py checks the videos
                                   for overlap with annotated data (leakage check).
  scripts\train_s3.py, train_hr.py Training with class weights / at a different image size.

Running the experiments (PowerShell, one per group of runs)
  scripts\run_s0_seed0.ps1, run_s0_seeds12.ps1, run_s1_s2.ps1, run_s2sam.ps1, run_s3.ps1,
  run_s4.ps1, run_expA.ps1, run_n0.ps1, run_hr.ps1

Evaluation and export
  scripts\eval_test.py             Scores trained models on a split, per class.
  scripts\external_check.py        Species check on four new videos.
  scripts\test_plots_errors.py     Error counts and example errors; cm_compare.py and conf_sweep.py
                                   check confusion matrices and thresholds.
  scripts\export_bench.py          ONNX export, accuracy check and speed benchmark.
  scripts\sam_test.py, s4_look.py, status.ps1   Small helpers.

Software versions: see ..\02_Model_and_Demo\requirements_exact.txt.
