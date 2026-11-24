# Capstone Project Proposal

## Data-Efficient Wildlife Detection from Ugandan Field Footage
**UgaWildlifeVision: label recovery, class imbalance and small-data training strategies**

Joseph Walusimbi, B.Eng. Electronics and Computer Engineering, Year 3
Course unit: Machine Learning, Capstone Project

*Note: this proposal was reconstructed from the finished Capstone Report (objectives, Section 3.5 "Differences from the proposal", and Table 3). It is the plan that the report's results are consistent with, not the original submitted text.*

---

## Abstract

Manual review of wildlife video from Uganda's protected areas is slow, and detectors trained on small field datasets are prone to inflated test scores and poor transfer to new sites. This project proposes a lightweight seven-class wildlife detector (antelope, bird, chimpanzee, elephant, gorilla, hippo, hog) built by fine-tuning a COCO-pretrained YOLOv8-nano model on 1,173 annotated frames (3,909 bounding boxes) from nine recording sessions in the NESTLER Wild Animal Recognition Video Dataset. The work has three parts. First, the merged "monkey" annotations are split into gorilla and chimpanzee using the session each frame came from. Second, a session- and time-aware data split is designed to prevent leakage, and a leave-session-out experiment measures how well hippo and gorilla detection carries over to an unseen session. Third, a cumulative ablation ladder tests standard augmentation, copy-paste with SAM masks, class-imbalance handling and pseudo-labelling, each trained with three random seeds. Performance is reported as per-class precision, recall and mAP, with attention to the smallest class, and the final model is exported to ONNX and benchmarked for inference speed. The expected contribution is evidence on which inexpensive techniques help under scarce labels, and an honest estimate of how far a standard test score overstates real-world performance.

**Keywords:** wildlife detection, YOLOv8, small-data learning, class imbalance, data augmentation, pseudo-labelling, domain shift, ONNX

## 1. Background and problem

Video-based wildlife monitoring in Uganda's protected areas (Kibale, Queen Elizabeth and Bwindi Impenetrable National Parks) produces far more footage than rangers and researchers can review by hand. Detection models trained at one site tend to degrade at another because vegetation, light and camera angle change [1]. Building a large labelled dataset for every site is not realistic, so the question is which cheap, data-efficient techniques help most when labelled data is very small, and how honest a normal test score is.

Three problems make a small field dataset hard:

1. Frames from one video are near-duplicates, so the number of distinct scenes is far smaller than the frame count, and a random split leaks information between train and test.
2. Class imbalance. Some species have few examples (elephant, about 131 boxes, against about 1,219 for hippo).
3. Label quality. The source annotations give gorillas and chimpanzees the same "monkey" category, which must be repaired before training.

## 2. Aim and objectives

**Aim:** build and honestly evaluate a lightweight Ugandan wildlife detector, and establish which data-efficiency techniques are worth using when labelled footage is scarce.

Objectives:

1. Recover separate gorilla and chimpanzee labels from the recording session each frame came from.
2. Fine-tune a pretrained YOLOv8-nano detector on the corrected seven-class data (antelope, bird, chimpanzee, elephant, gorilla, hippo, hog).
3. Design a split by recording session and time that avoids leakage between training and test.
4. Measure how well hippo and gorilla detection carries over to a recording session never seen in training.
5. Test a ladder of data-efficiency techniques, one added at a time: standard augmentation, copy-paste, class-imbalance handling and pseudo-labelling.
6. Report per-class precision, recall and mAP, with particular attention to the smallest class.
7. Export the final model to ONNX and measure inference speed.

**Stretch:** a local-language species-name lookup table (Luganda, Runyankole, Rukiga, Rutooro, Runyoro) built with the Sunbird AI translation service, back-translation checked, and marked unverified until a speaker confirms each term.

## 3. Data

- **Dataset:** NESTLER Wild Animal Recognition Video Dataset (Zenodo record 17036940, v4, published 2 September 2025, doi:10.5281/zenodo.17036940, CC BY 4.0), produced by the NESTLER project (EU Horizon, grant agreement 101060762) [2]. The component used is `Safari_Wild_Animal_Detection.zip` (4.0 GB): annotated frames from Kibale, Queen Elizabeth and Bwindi Impenetrable National Parks, collected February to June 2025, covering elephants, chimpanzees, mountain gorillas, hippopotamuses, Uganda kob and warthogs.
- **Size and format:** 9 videos, 1,173 annotated frames and 3,909 bounding boxes, in COCO/YOLO-compatible JSON and TXT. The nine sessions are antelope, chimpanzees, elephant, gorillas, gorillas2, gorillas3, hippo, hippo2 and hog.
- **Capture:** field video recorded with a Canon EOS M50 Mark II and an iPhone 12 Pro Max, listed at 1920 x 1080. The footage is therefore handheld or tripod video, not fixed motion-triggered camera-trap footage, and some clips are portrait phone video.
- **Additional unlabelled videos** from the same record (`Gorilla.zip`, `Elephant.zip`, `Hippopotamus.zip`, `Warthog.zip`) for pseudo-labelling.
- **Limitation acknowledged up front:** no park or camera-location field exists, so cross-park generalisation cannot be tested; only cross-session generalisation can.

## 4. Methods

**4.1 Label repair.** Each session shows only one of gorilla or chimpanzee, so every "monkey" box is relabelled from its session folder.

**4.2 Split.** Hold out whole recording sessions for validation and test, so no session leaks across splits. Use leave-session-out testing specifically for hippo and gorilla.

**4.3 Model.** Fine-tune COCO-pretrained YOLOv8 or YOLO11 [3], [4] (nano and small), at 640 px. Fine-tuning baseline: lower learning rate, cosine schedule, and a layer-freezing comparison, with minimal augmentation.

**4.4 Ablation ladder (cumulative, each step on the previous one):**

| Step | Change |
|---|---|
| S0 | Fine-tuning baseline, minimal augmentation |
| S1 | Standard augmentation (mosaic, colour jitter, shift, scale, flip, mixup) [5], [6] |
| S2 | Copy-paste augmentation using SAM masks [7], [8] |
| S3 | Class-imbalance handling: sampling, class weights or focal loss [9], [10] |
| S4 | Pseudo-labelling on unlabelled Gorilla, Elephant, Hippopotamus and Warthog videos [11] |
| S5 | Synthetic images (optional) |

**4.5 Evaluation.** Precision, recall, mAP50 and mAP50-95, overall and per class. Every setting trained with three random seeds, reported as mean and standard deviation. Choices made on validation; test set scored once at the end.

**4.6 Deployment.** Export the best model to ONNX [12], check it matches the PyTorch model, and time it on CPU and GPU.

## 5. Expected outputs

- Trained YOLOv8-nano model and ONNX export, with a prediction script and usage instructions
- Results notebook with all tables and figures
- Code to build the dataset, train and evaluate
- Capstone report, and a dated project log
- (Stretch) local-language species-name table

## 6. Tools and resources

Ultralytics YOLO, PyTorch (CUDA), Segment Anything (SAM ViT-B), ONNX and ONNX Runtime, Python. One NVIDIA RTX-class GPU. About 4.3 GB of source data.

## 7. Risks and mitigation

| Risk | Mitigation |
|---|---|
| Near-duplicate frames inflate scores | Session- and time-aware splitting; leave-session-out test |
| Rare classes (elephant, bird) too few to learn | Ladder of imbalance techniques; per-class reporting |
| Gain from one seed is chance | Three seeds per setting, mean and standard deviation |
| Techniques give no gain | Report negative results honestly; they are still findings |
| Translation quality for local languages | Back-translation check; mark unverified until a speaker confirms |

## 8. Timeline

| Weeks | Work |
|---|---|
| 1-2 | Download data, inspect, repair labels, build splits |
| 3-4 | S0 baseline and S1 augmentation, three seeds each |
| 5-6 | S2 copy-paste (SAM masks) and S3 imbalance handling |
| 7 | S4 pseudo-labelling on new videos |
| 8 | Leave-session-out experiment, error analysis |
| 9 | ONNX export and speed benchmarks |
| 10 | Report writing; stretch: local-language table |

## 9. Success criteria

- Corrected seven-class dataset with no train/test leakage
- Per-class precision, recall and mAP for every ladder step, with seed spread
- A clear, evidence-based statement of which techniques helped
- A measured session-holdout gap for hippo and gorilla
- An ONNX model that matches the PyTorch model and runs in real time on CPU

## References

[1] S. Beery, G. Van Horn, and P. Perona, "Recognition in terra incognita," in Proc. Eur. Conf. Comput. Vis. (ECCV), 2018, pp. 456-473.

[2] NESTLER Project, "Wild Animal Recognition Video Dataset," ver. 4, Zenodo, Sep. 2, 2025. doi: 10.5281/zenodo.17036940. Accessed: Oct. 19, 2026.

[3] T.-Y. Lin et al., "Microsoft COCO: Common objects in context," in Proc. Eur. Conf. Comput. Vis. (ECCV), 2014, pp. 740-755.

[4] G. Jocher, A. Chaurasia, and J. Qiu, "Ultralytics YOLOv8," 2023. [Online]. Available: https://github.com/ultralytics/ultralytics. Accessed: Oct. 19, 2026.

[5] A. Bochkovskiy, C.-Y. Wang, and H.-Y. M. Liao, "YOLOv4: Optimal speed and accuracy of object detection," arXiv:2004.10934, 2020.

[6] H. Zhang, M. Cisse, Y. N. Dauphin, and D. Lopez-Paz, "mixup: Beyond empirical risk minimization," in Proc. Int. Conf. Learn. Represent. (ICLR), 2018.

[7] G. Ghiasi et al., "Simple copy-paste is a strong data augmentation method for instance segmentation," in Proc. IEEE/CVF Conf. Comput. Vis. Pattern Recognit. (CVPR), 2021, pp. 2918-2928.

[8] A. Kirillov et al., "Segment anything," in Proc. IEEE/CVF Int. Conf. Comput. Vis. (ICCV), 2023, pp. 4015-4026.

[9] A. Gupta, P. Dollar, and R. Girshick, "LVIS: A dataset for large vocabulary instance segmentation," in Proc. IEEE/CVF Conf. Comput. Vis. Pattern Recognit. (CVPR), 2019, pp. 5356-5364.

[10] T.-Y. Lin, P. Goyal, R. Girshick, K. He, and P. Dollar, "Focal loss for dense object detection," in Proc. IEEE Int. Conf. Comput. Vis. (ICCV), 2017, pp. 2980-2988.

[11] D.-H. Lee, "Pseudo-label: The simple and efficient semi-supervised learning method for deep neural networks," in Proc. ICML Workshop Challenges Represent. Learn., 2013.

[12] ONNX Project, "Open Neural Network Exchange." [Online]. Available: https://onnx.ai. Accessed: Oct. 19, 2026.
