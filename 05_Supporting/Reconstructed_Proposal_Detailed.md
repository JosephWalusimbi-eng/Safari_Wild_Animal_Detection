# Capstone Project Proposal

## Data-Efficient Wildlife Detection from Ugandan Field Footage
**UgaWildlifeVision: label recovery, class imbalance and small-data training strategies**

Joseph Walusimbi, B.Eng. Electronics and Computer Engineering, Year 3
Course unit: Machine Learning, Capstone Project

*Note: this is the extended version of the proposal, giving definitions and the rationale for each design decision. It was reconstructed from the finished Capstone Report (its objectives, Section 3.5 and Table 3) and from the Zenodo record of the dataset. It is the plan that the report's results are consistent with, not the original submitted text.*

---

## Abstract

Manual review of wildlife video from Uganda's protected areas is a bottleneck for population monitoring, and object detectors trained on small, field-collected datasets are vulnerable to three problems: temporal redundancy between frames, class imbalance, and label errors at the taxonomy level. Together with domain shift between recording sessions, these make conventional test scores unreliable indicators of deployed performance. This proposal sets out a controlled study of data-efficiency techniques for a seven-class Ugandan wildlife detector (antelope, bird, chimpanzee, elephant, gorilla, hippo, hog), fine-tuned from COCO-pretrained YOLOv8-nano weights on 1,173 annotated frames and 3,909 bounding boxes from nine field-video sessions in the NESTLER Wild Animal Recognition Video Dataset (Kibale, Queen Elizabeth and Bwindi Impenetrable National Parks, February to June 2025). The method comprises (i) recovery of separate gorilla and chimpanzee labels from session identity; (ii) a session- and time-aware split that avoids train/test leakage, supplemented by a leave-session-out experiment that quantifies the generalisation gap for hippo and gorilla; (iii) a cumulative ablation ladder of standard augmentation, copy-paste augmentation using Segment Anything masks, class-imbalance handling (repeat-factor sampling, class weights, focal loss) and pseudo-labelling on unlabelled clips; and (iv) evaluation by per-class precision, recall, mAP50 and mAP50-95 over three random seeds per setting, with the test set scored once. The selected model is exported to ONNX and its agreement with the PyTorch model and CPU/GPU latency are measured to assess suitability for modest field hardware. The study aims to identify which inexpensive techniques yield gains beyond seed variance under scarce labels, and to provide an honest estimate of the gap between standard test performance and performance on unseen sessions.

**Keywords:** wildlife detection, YOLOv8, small-data learning, class imbalance, data augmentation, pseudo-labelling, domain shift, ONNX

## 1. Background and problem statement

### 1.1 Context

Uganda's protected areas, including Kibale, Queen Elizabeth and Bwindi Impenetrable National Parks, are monitored with video. Reviewing this footage manually to establish which species are present, in what numbers and how often is slow and labour-intensive, and it is the bottleneck in turning recordings into population information. Automating the first pass with an object detector would allow reviewers to inspect only the frames that contain animals.

An **object detector** is a model that, for an input image, outputs a set of bounding boxes, each with a class label and a confidence score in [0, 1]. This differs from image classification, which assigns one label to the whole image, and from semantic or instance segmentation, which assigns labels per pixel. Detection is the appropriate formulation here because both the identity and the location of each animal are needed, for example to count individuals in a herd.

### 1.2 Why small, field-collected datasets are difficult

Supervised detectors need labelled examples, and producing bounding-box annotations manually is expensive. General-purpose benchmarks contain hundreds of thousands to millions of annotated images; this project has about one thousand. Three properties of the data make the small-data regime harder still.

1. **Temporal redundancy.** Frames sampled from one video are highly correlated, because consecutive frames show nearly the same scene, background and animals. The number of statistically independent scenes is therefore far smaller than the frame count. Two consequences follow: (a) the model has less real diversity to learn from than the image count suggests, and (b) random frame-level train/test splits place near-duplicates on both sides, which is **data leakage** and inflates test scores.
2. **Class imbalance.** Class frequencies are skewed (about 1,219 hippo boxes against about 131 elephant boxes, roughly 9 to 1). Standard training minimises an average loss over examples, so frequent classes dominate the gradient and rare classes are under-fitted.
3. **Label noise at the taxonomy level.** The source annotations assign gorillas and chimpanzees the same category, "monkey". A classifier cannot separate two classes that share one label, so the labels must be corrected before training.

A further issue is **domain shift**: a model trained on one distribution of images degrades on another when vegetation, illumination, camera angle, subject distance or sensor changes [1]. Models trained at one site frequently degrade at others, and a held-out frame from a familiar session does not measure this.

### 1.3 Research questions

1. Which inexpensive data-centric techniques improve a wildlife detector trained on very little data?
2. How well does a conventional test score predict performance on a recording session the model has never seen?

## 2. Aim and objectives

**Aim:** build and evaluate a lightweight detector for Ugandan wildlife, and establish, with controlled experiments and an honest evaluation protocol, which data-efficiency techniques are worthwhile when labelled footage is scarce.

Objectives, each with its rationale:

1. **Recover separate gorilla and chimpanzee labels from the recording session each frame came from.** Each session shows only one of the two species, so the session folder is a reliable source of the true class. This is cheaper and more accurate than relabelling by hand.
2. **Fine-tune a pretrained YOLOv8-nano detector on the corrected seven-class data** (antelope, bird, chimpanzee, elephant, gorilla, hippo, hog). Pretraining is what makes about 1,000 images workable (Section 5.3).
3. **Design a split by recording session and time that avoids leakage between training and test.** Without this, the reported score measures memorisation of scenes rather than generalisation.
4. **Measure how well hippo and gorilla detection carries over to a recording session never seen in training.** This directly quantifies domain shift, which the standard split hides.
5. **Test a ladder of data-efficiency techniques, one added at a time:** standard augmentation, copy-paste, class-imbalance handling and pseudo-labelling. Adding one change per step makes each effect attributable.
6. **Report per-class precision, recall and mAP, with attention to the smallest class.** An aggregate score can conceal a failing class.
7. **Export the final model to ONNX and measure its speed.** This tests whether the model is deployable on modest hardware.

**Stretch goal:** a local-language species-name lookup table (Luganda, Runyankole, Rukiga, Rutooro, Runyoro) built with the Sunbird AI translation service. Each term is verified by back-translation to English and flagged unverified until a native or fluent speaker confirms it. A static lookup table is used because it adds no inference-time cost and no translation dependency to the detector.

## 3. Data

### 3.1 Source and provenance

- **Dataset:** NESTLER Wild Animal Recognition Video Dataset, Zenodo record 17036940 (version 4, published 2 September 2025), doi:10.5281/zenodo.17036940 [2].
- **Producer:** the NESTLER project (oNe hEalth SusTainabiLity partnership between EU-AFRICA for food security), funded by the EU Horizon programme, grant agreement 101060762.
- **Licence:** Creative Commons Attribution 4.0 International (CC BY 4.0). Reuse, including modification, is permitted with attribution.
- **Record contents:** 14 files, 10.3 GB in total. These include a Bulgarian fox, jackal, raven and vulture classification set; a set of African species clips from Rwanda and Uganda; an elephant, gorilla and kob detection set (851.6 MB); and the component used here.

### 3.2 The component used: Safari_Wild_Animal_Detection.zip

| Property | Value |
|---|---|
| Archive size | 4.0 GB |
| Locations | Kibale, Queen Elizabeth and Bwindi Impenetrable National Parks, Uganda |
| Collection period | February to June 2025 |
| Species | Elephant, chimpanzee, mountain gorilla, hippopotamus, Uganda kob, warthog |
| Content | 9 videos, 1,173 annotated frames, 3,909 bounding boxes |
| Capture devices | Canon EOS M50 Mark II; iPhone 12 Pro Max |
| Video resolution | 1920 x 1080 |
| Annotation | Bounding boxes with class labels, in COCO/YOLO-compatible JSON and TXT |
| Ethics statement | No animals disturbed, trapped or manipulated; permits obtained; no personal data |

The nine sessions (one per video) are named antelope, chimpanzees, elephant, gorillas, gorillas2, gorillas3, hippo, hippo2 and hog. Each is a continuous recording from one place with one camera, so frames within a session share background, illumination and viewpoint. The session is therefore the natural unit of independence, and the natural unit to keep intact when splitting.

**Nature of the footage.** The capture devices are a mirrorless camera and a phone, so the data are field video rather than fixed, motion-triggered camera-trap imagery. This matters for transfer: footage is framed by an operator, subject distance varies, and some clips are portrait phone video, which later required special handling (see the chimpanzee padding repair in the report).

### 3.3 Supplementary material for pseudo-labelling

The same record provides small unlabelled clips (`Gorilla.zip`, `Elephant.zip`, `Hippopotamus.zip`, `Warthog.zip`), used as an unlabelled pool for pseudo-labelling.

### 3.4 Known limitations of the data

- **No location metadata.** The archive does not record which park or camera position each video came from, so generalisation across parks cannot be tested; only generalisation across recording sessions can.
- **Single-session classes.** Most species appear in one or two sessions, so a "new session" test for them leaves very little training diversity.
- **Frame-count discrepancy.** The record states 1,173 frames. The report later finds 1,220 image files in the nine session folders; the 3,909 box count matches either way.

## 4. Label repair

The raw annotations use a single "monkey" category for both gorillas and chimpanzees. Because each session contains exactly one of the two species, every "monkey" box is relabelled from the folder of the session it belongs to. The result is a fixed seven-class vocabulary in the order antelope, bird, chimpanzee, elephant, gorilla, hippo, hog. Bird has no session of its own; birds are annotated inside hippo2 and hog frames, usually small and in scenes dominated by larger animals, which anticipates that it will be the hardest class.

## 5. Methods

### 5.1 Data splitting

A **training set** is used to fit model parameters. A **validation set** is used for model selection, early stopping and comparison of techniques; it influences decisions, so its score is optimistically biased. A **test set** is used once, after all decisions are made, to estimate generalisation. Keeping the test set untouched is what makes its score an unbiased estimate.

The proposal specifies holding out whole recording sessions for validation and test. Rationale: because frames within a session are near-duplicates, any split that divides a session across sets leaks information. Splitting by session removes this leakage and measures generalisation to a new scene, which is the quantity that matters operationally.

In addition, a **leave-session-out experiment** is planned for hippo and gorilla: train with one session of the species withheld, then test on exactly that session. The drop from the standard-split score to the held-out-session score estimates the domain-shift gap.

### 5.2 Why YOLO

YOLO ("You Only Look Once") is a family of **single-stage detectors** [3]: one convolutional network predicts box coordinates, objectness and class probabilities directly from the full image in a single forward pass. Two-stage detectors (Faster R-CNN) [4] first propose regions and then classify them, which is generally slower. Transformer-based detectors (DETR and variants) [5] remove hand-designed components such as anchors and non-maximum suppression but typically need more data and longer schedules to converge, which is a poor fit for a dataset of about 1,000 images. YOLOv8 was selected because it trains quickly on a single consumer GPU, has well-maintained pretrained weights, a standardised training and evaluation API (Ultralytics) [6], and a one-line export path to ONNX [7]. The proposal leaves open YOLO11 as an alternative.

### 5.3 Model size and transfer learning

YOLOv8 is released at five scales (n, s, m, l, x) that differ in depth and width, and hence in parameter count, memory and latency. The proposal compares **nano** and **small**. A small model is favoured for three reasons: with about 1,000 images larger models overfit more readily; training is cheaper, allowing three seeds per setting; and inference must be fast enough for modest hardware.

**Transfer learning and fine-tuning.** All models start from weights pretrained on **COCO** (Common Objects in Context; roughly 118,000 training images, 80 classes [8]). The early layers of a convolutional network learn generic features (edges, textures, shapes) that transfer across tasks [9], so only a modest amount of task-specific data is needed to adapt the later layers and the detection head. **Fine-tuning** means continuing gradient-based training from these pretrained weights on the target data, usually at a reduced learning rate so that useful pretrained features are not overwritten. The new head is re-initialised for the seven classes.

The planned fine-tuning baseline (S0) varies three choices:

- **Lower learning rate.** The learning rate scales the parameter update at each step; a smaller value suits fine-tuning because the starting point is already good.
- **Cosine schedule.** The learning rate decays along a half-cosine curve from its initial value towards zero [10], giving large updates early and small, stabilising updates late, with no hand-tuned step points.
- **Freezing comparison.** Freezing the backbone's early layers (excluding them from gradient updates) reduces the number of trainable parameters and the risk of overfitting; the proposal compares frozen and fully trained variants.

The input resolution is 640 x 640 pixels, the standard YOLO training size, which keeps training cost manageable.

### 5.4 Random seeds and variance

Training is stochastic (weight initialisation of new layers, data order, augmentation sampling). A **random seed** fixes this randomness so a run is reproducible. Running each setting with three seeds (0, 1 and 2) allows the run-to-run standard deviation to be estimated, and results are reported as mean and standard deviation. This guards against attributing a chance difference to a technique: an apparent gain smaller than the seed spread is not evidence of an effect. With only three seeds the estimate of spread is itself rough, which is acknowledged as a limitation.

### 5.5 The ablation ladder

An **ablation study** changes one component at a time while holding everything else fixed, so that any change in the metric can be attributed to that component. The proposal arranges the techniques as a cumulative ladder.

| Step | Change | Rationale |
|---|---|---|
| S0 | Fine-tuning baseline, minimal augmentation | Reference point; every later step is measured against it |
| S1 | Standard augmentation | Cheapest way to increase effective data diversity |
| S2 | Copy-paste with SAM masks | Targets rare and small classes by synthesising new compositions |
| S3 | Class-imbalance handling | Addresses the roughly 9:1 skew in box counts |
| S4 | Pseudo-labelling on unlabelled videos | Adds data without annotation cost |
| S5 | Synthetic images (optional) | Further data expansion if time allows |

**S1: standard augmentation.** **Data augmentation** applies random label-preserving transformations to training images, which enlarges the effective training distribution and acts as a regulariser. The YOLO set includes HSV colour jitter, translation, scaling, horizontal flip, **mosaic** (four images tiled into one, so each sample contains objects at varied scales, positions and contexts) [11] and **mixup** (a convex blend of two images and their labels) [12]. This matters most when scenes are few, because it forces the model to rely on object appearance rather than on one memorised background.

**S2: copy-paste with SAM masks.** Copy-paste augmentation cuts object instances out of one image and pastes them onto others, creating new object-background pairings and extra examples of rare or small classes [13]. It needs **instance masks**, but the dataset has only boxes. The **Segment Anything Model (SAM)** [14] is a promptable segmentation model that returns a mask from a box prompt, so masks can be generated from the existing boxes without manual outlining. Pasting is aimed at the classes that benefit most: elephant, bird and antelope.

**S3: class-imbalance handling.** Three standard methods are planned. **Repeat-factor sampling** [15] oversamples images that contain rare classes, with a repeat factor derived from class frequency. **Class weights** scale the loss contribution of each class inversely to its frequency. **Focal loss** down-weights well-classified examples by a factor (1 - p)^gamma [16] so that training focuses on hard examples. All three act on the optimisation signal rather than on the data content.

**S4: pseudo-labelling.** The current model predicts boxes on unlabelled images; predictions above a confidence threshold are retained as **pseudo-labels** [17] and added to the training set, and the model is retrained. This is a form of self-training: it exploits unlabelled data at no annotation cost, but errors in the pseudo-labels can reinforce themselves (confirmation bias), so a high threshold is used. The unlabelled pool is the Gorilla, Elephant, Hippopotamus and Warthog clips.

**S5: synthetic images (optional).** Fully synthetic training images generated or composed by software.

### 5.6 Evaluation metrics

- **Intersection over Union (IoU):** the area of overlap of a predicted and a true box divided by the area of their union; it ranges from 0 to 1. A prediction counts as a **true positive** if its class is correct and its IoU with a not-yet-matched true box meets a threshold; otherwise it is a **false positive**, and any unmatched true box is a **false negative**.
- **Precision** = TP / (TP + FP): the fraction of predicted boxes that are correct.
- **Recall** = TP / (TP + FN): the fraction of true animals found.
- **F1** = the harmonic mean of precision and recall.
- **Average precision (AP):** the area under the precision-recall curve for one class [18], obtained by sweeping the confidence threshold. **Mean average precision (mAP)** is the mean of AP over classes. **mAP50** uses an IoU threshold of 0.5; **mAP50-95** averages AP over IoU thresholds from 0.5 to 0.95 in steps of 0.05 [8], so it also rewards tight localisation.

Rationale: mAP summarises performance over all operating points and so is not tied to one confidence threshold, while precision and recall at a chosen threshold describe behaviour in use. Reporting them **per class** exposes weak classes that an overall mean hides; particular attention is paid to the smallest class.

**Protocol.** Choices are made on the validation set. The test set is scored once at the end. Every setting uses three seeds.

### 5.7 Deployment: export to ONNX

**ONNX** (Open Neural Network Exchange) is an open specification for representing a trained neural network as a computation graph of standardised operators [7], together with its weights, in a framework-independent file. **ONNX Runtime** is an inference engine [19] that executes ONNX graphs on CPUs, GPUs and other accelerators through pluggable execution providers, applying graph optimisations such as operator fusion and constant folding.

The alternatives, and why ONNX was preferred:

| Option | Characteristics | Limitation for this project |
|---|---|---|
| PyTorch checkpoint (.pt) | Native format; full flexibility | Requires the whole PyTorch stack at inference; heavy for deployment |
| TorchScript | Serialised, Python-independent PyTorch graph | Still tied to the PyTorch runtime and its operator set |
| TensorRT | NVIDIA's optimising inference engine; very fast | NVIDIA GPUs only; the compiled engine is specific to a GPU model and TensorRT version |
| OpenVINO | Intel's toolkit, optimised for Intel CPUs, GPUs and VPUs | Best on Intel hardware; narrower target |
| TensorFlow Lite | Compact runtime for mobile and microcontrollers | Native to TensorFlow; PyTorch conversion is indirect and operator coverage can be incomplete |
| Core ML | Apple's on-device format | Apple devices only |
| **ONNX** | **Vendor-neutral interchange format with a mature CPU runtime** | **Not always the fastest option on a specific accelerator** |

ONNX was chosen for portability. The deployment target (a park office laptop or a small field computer) is not fixed and may have no GPU, and ONNX Runtime performs well on plain CPUs. ONNX is also a common intermediate representation, so the same file can later be converted to TensorRT, OpenVINO or TFLite once a device is chosen. Ultralytics supports ONNX export directly.

**Verification.** Export can introduce numerical differences, so the exported model is scored on the validation set and compared with the PyTorch model; the proposal's criterion is agreement within a small tolerance. Latency is then measured as milliseconds per image at batch size 1, reporting the median and the 95th percentile (which captures the slow tail), on CPU and GPU. Batch size 1 reflects frame-by-frame use.

## 6. Expected outputs

- Trained YOLOv8-nano weights and an ONNX export, with a prediction script and instructions for use
- A results notebook containing all tables and figures, so every reported number is reproducible
- The code used to build the dataset, train and evaluate
- The capstone report and a dated project log
- Stretch: the local-language species-name table

## 7. Tools and resources

| Tool | Role |
|---|---|
| Ultralytics YOLO | Model definitions, pretrained weights, training, validation and export |
| PyTorch with CUDA | Deep learning framework; CUDA runs the computation on an NVIDIA GPU, whose parallel hardware accelerates the matrix operations in training |
| Segment Anything (ViT-B) | Mask generation for copy-paste |
| ONNX and ONNX Runtime | Export and CPU inference benchmarking |
| Python | Data preparation, experiment scripting and analysis |

Compute: one NVIDIA RTX-class GPU. Storage: about 4.3 GB of source data plus training outputs.

## 8. Risks and mitigation

| Risk | Consequence | Mitigation |
|---|---|---|
| Near-duplicate frames across splits | Inflated test scores | Session- and time-aware splitting; leave-session-out experiment |
| Very few examples of rare classes (elephant, bird) | Under-fitted classes; unstable per-class scores | S2 and S3 techniques; per-class reporting with seed spread |
| Differences smaller than seed noise | False conclusions about techniques | Three seeds per setting; mean and standard deviation |
| Techniques give no gain | Appearance of a failed project | Report negative results as findings; state that they apply only to the settings tried |
| Dataset lacks location metadata | Cannot test cross-park generalisation | State as a limitation; test cross-session only |
| Translation errors in local-language terms | Misleading species names | Back-translation check; unverified flag until a speaker confirms |

## 9. Timeline

| Weeks | Work |
|---|---|
| 1-2 | Download data, inspect, repair labels, build splits |
| 3-4 | S0 baseline and S1 augmentation, three seeds each |
| 5-6 | S2 copy-paste (SAM masks) and S3 imbalance handling |
| 7 | S4 pseudo-labelling on the unlabelled clips |
| 8 | Leave-session-out experiment and error analysis |
| 9 | ONNX export and speed benchmarks |
| 10 | Report writing; stretch: local-language table |

## 10. Success criteria

- A corrected seven-class dataset with no train/test leakage
- Per-class precision, recall and mAP for every ladder step, with seed spread
- An evidence-based statement of which techniques helped and which did not
- A measured generalisation gap for hippo and gorilla on unseen sessions
- An ONNX model that agrees with the PyTorch model within tolerance and runs in real time on a CPU

## References

[1] S. Beery, G. Van Horn, and P. Perona, "Recognition in terra incognita," in Proc. Eur. Conf. Comput. Vis. (ECCV), 2018, pp. 456-473.

[2] NESTLER Project, "Wild Animal Recognition Video Dataset," ver. 4, Zenodo, Sep. 2, 2025. doi: 10.5281/zenodo.17036940. Accessed: Oct. 19, 2026.

[3] J. Redmon, S. Divvala, R. Girshick, and A. Farhadi, "You only look once: Unified, real-time object detection," in Proc. IEEE Conf. Comput. Vis. Pattern Recognit. (CVPR), 2016, pp. 779-788.

[4] S. Ren, K. He, R. Girshick, and J. Sun, "Faster R-CNN: Towards real-time object detection with region proposal networks," in Adv. Neural Inf. Process. Syst. (NeurIPS), vol. 28, 2015.

[5] N. Carion et al., "End-to-end object detection with transformers," in Proc. Eur. Conf. Comput. Vis. (ECCV), 2020, pp. 213-229.

[6] G. Jocher, A. Chaurasia, and J. Qiu, "Ultralytics YOLOv8," 2023. [Online]. Available: https://github.com/ultralytics/ultralytics. Accessed: Oct. 19, 2026.

[7] ONNX Project, "Open Neural Network Exchange." [Online]. Available: https://onnx.ai. Accessed: Oct. 19, 2026.

[8] T.-Y. Lin et al., "Microsoft COCO: Common objects in context," in Proc. Eur. Conf. Comput. Vis. (ECCV), 2014, pp. 740-755.

[9] J. Yosinski, J. Clune, Y. Bengio, and H. Lipson, "How transferable are features in deep neural networks?," in Adv. Neural Inf. Process. Syst. (NeurIPS), vol. 27, 2014.

[10] I. Loshchilov and F. Hutter, "SGDR: Stochastic gradient descent with warm restarts," in Proc. Int. Conf. Learn. Represent. (ICLR), 2017.

[11] A. Bochkovskiy, C.-Y. Wang, and H.-Y. M. Liao, "YOLOv4: Optimal speed and accuracy of object detection," arXiv:2004.10934, 2020.

[12] H. Zhang, M. Cisse, Y. N. Dauphin, and D. Lopez-Paz, "mixup: Beyond empirical risk minimization," in Proc. Int. Conf. Learn. Represent. (ICLR), 2018.

[13] G. Ghiasi et al., "Simple copy-paste is a strong data augmentation method for instance segmentation," in Proc. IEEE/CVF Conf. Comput. Vis. Pattern Recognit. (CVPR), 2021, pp. 2918-2928.

[14] A. Kirillov et al., "Segment anything," in Proc. IEEE/CVF Int. Conf. Comput. Vis. (ICCV), 2023, pp. 4015-4026.

[15] A. Gupta, P. Dollar, and R. Girshick, "LVIS: A dataset for large vocabulary instance segmentation," in Proc. IEEE/CVF Conf. Comput. Vis. Pattern Recognit. (CVPR), 2019, pp. 5356-5364.

[16] T.-Y. Lin, P. Goyal, R. Girshick, K. He, and P. Dollar, "Focal loss for dense object detection," in Proc. IEEE Int. Conf. Comput. Vis. (ICCV), 2017, pp. 2980-2988.

[17] D.-H. Lee, "Pseudo-label: The simple and efficient semi-supervised learning method for deep neural networks," in Proc. ICML Workshop Challenges Represent. Learn., 2013.

[18] M. Everingham, L. Van Gool, C. K. I. Williams, J. Winn, and A. Zisserman, "The Pascal visual object classes (VOC) challenge," Int. J. Comput. Vis., vol. 88, no. 2, pp. 303-338, 2010.

[19] ONNX Runtime developers, "ONNX Runtime." [Online]. Available: https://onnxruntime.ai. Accessed: Oct. 19, 2026.
