"""build_report.py - builds UgaWildVision_Part2_Report.docx (Part 2 report).

    python build_report.py

Numbers come from ..\\results, ..\\runs, ..\\export, ..\\cls_v1_build_log.txt and LOG.md.
Figures: ..\\results\\... (from make_figures.py / make_compare_figure.py) and figures\\ (make_report_figures.py).
After building, update_fields.ps1 lets Word fill in the contents, list of tables and list of figures.
"""
import re
from pathlib import Path
from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK, WD_LINE_SPACING
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt, Cm, RGBColor

HERE = Path(__file__).resolve().parent
P2 = HERE.parent
FIG = HERE / "figures"
OUT = HERE / "UgaWildVision_Part2_Report.docx"
FONT = "Times New Roman"
BLACK = RGBColor(0, 0, 0)
LANG_CSV = P2 / "results" / "sunbird_names.csv"
LANG_NAMES = {"luganda": "Luganda", "runyankole": "Runyankole", "rutooro": "Rutooro", "ateso": "Ateso", "kiswahili": "Kiswahili"}


sys_path_added = False


def visitor_lang():
    import sys as _sys
    _sys.path.insert(0, str(P2 / "scripts"))
    import add_visitor_languages as avl
    return avl


def selection_figure(rows, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({"font.family": "Times New Roman", "font.size": 11})
    fig, ax = plt.subplots(figsize=(9, 3.8))
    langs = [r["language"] for r in rows]
    xs = range(len(rows))
    pa = [100 * r["visitors"] / 1_542_620 for r in rows]; pl = [100 * r["leisure"] / 297_726 for r in rows]
    ax.bar([x - 0.2 for x in xs], pa, width=0.38, color="#2a78d6", label="share of all visitors")
    ax.bar([x + 0.2 for x in xs], pl, width=0.38, color="#eb6834", label="share of leisure & holiday visitors")
    for x, a_, l_ in zip(xs, pa, pl):
        ax.text(x - 0.2, a_ + 0.5, f"{a_:.1f}", ha="center", fontsize=9)
        ax.text(x + 0.2, l_ + 0.5, f"{l_:.1f}", ha="center", fontsize=9)
    ax.axhline(2.0, color="#333333", ls="--", lw=1); ax.text(len(rows) - 0.5, 2.6, "2% rule", ha="right", fontsize=9)
    ax.set_xticks(list(xs)); ax.set_xticklabels([l + ("" if r["included"] == "yes" else "\n(not included)") for l, r in zip(langs, rows)])
    ax.set_ylabel("percent of 2019 visitors"); ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", color="#dddddd", lw=0.6); ax.set_axisbelow(True); ax.legend(frameon=False, fontsize=9)
    fig.tight_layout(); fig.savefig(path, dpi=200, facecolor="white"); plt.close(fig)


def lang_data():
    import csv as _csv
    rows = list(_csv.DictReader(open(LANG_CSV, encoding="utf-8")))
    by = {}
    for r in rows:
        by.setdefault((r["class"], r["english"]), {})[r["language"]] = r
    table = []
    for (cls, eng), d in by.items():
        row = [eng]
        for lang in LANG_NAMES:
            r = d.get(lang)
            if not r:
                row.append("-"); continue
            mark = "" if r["auto_check"].startswith("pass") else " (x)"
            aud = " *" if r["audio_file"] else ""
            row.append(f"{r['translated']}{aud}{mark}")
        table.append(row)
    stats = {lang: (sum(1 for r in rows if r["language"] == lang and r["auto_check"].startswith("pass")),
                    sum(1 for r in rows if r["language"] == lang),
                    sum(1 for r in rows if r["language"] == lang and r["audio_file"])) for lang in LANG_NAMES}
    return table, stats


def lang_figure(stats, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({"font.family": "Times New Roman", "font.size": 11})
    fig, ax = plt.subplots(figsize=(8, 3.4))
    langs = list(LANG_NAMES)
    ok = [stats[l][0] for l in langs]; tot = [stats[l][1] for l in langs]; au = [stats[l][2] for l in langs]
    xs = range(len(langs))
    ax.bar([x - 0.2 for x in xs], ok, width=0.38, color="#2a78d6", label="passed back-translation check")
    ax.bar([x + 0.2 for x in xs], [t - o for t, o in zip(tot, ok)], width=0.38, color="#eb6834", label="failed check (hidden in app)")
    for x, o, t, a in zip(xs, ok, tot, au):
        ax.text(x - 0.2, o + 0.3, str(o), ha="center", fontsize=10)
        ax.text(x + 0.2, t - o + 0.3, str(t - o), ha="center", fontsize=10)
    ax.set_xticks(list(xs)); ax.set_xticklabels([f"{LANG_NAMES[l]}\n(audio: {a})" for l, a in zip(langs, au)])
    ax.set_ylabel("animal names"); ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", color="#dddddd", lw=0.6); ax.set_axisbelow(True); ax.legend(frameon=False, fontsize=9)
    fig.tight_layout(); fig.savefig(path, dpi=200, facecolor="white"); plt.close(fig)

# ----------------------------------------------------------------------------- content
# Items: ("h1"|"h2"|"h3", text) ("p", text) ("bul", [..]) ("num", [..]) ("eq", text, no)
#        ("tab", key, caption, header, rows, widths) ("fig", key, path, caption, width_cm) ("pb",)
# Text may reference {F:key} and {T:key}; they are replaced by the figure / table number.

C = []
add = C.append

# ---------------- 1 Introduction
add(("h1", "1. Introduction"))
add(("h2", "1.1 Background: tourism in Uganda"))
add(("p", "Tourism is one of Uganda's most important sources of income and jobs. In 2024 the country received "
     "1,371,895 international visitors, 7.7% more than the 1,274,210 of 2023, and inbound tourism earned a "
     "record USD 1.28 billion, about 16% of the country's total exports [@mtwa2024]. The Uganda Tourism "
     "Satellite Account for 2024 puts tourism's direct contribution at UGX 6.99 trillion, about 3.3% of the "
     "economy [@tsa2024], and tourism is the country's fifth-largest employer, with 876,512 direct jobs "
     "[@wb_jobs]. Domestic tourism is growing as well: more than 3.2 million Ugandans travelled within the "
     "country in 2024 [@tsa2024]."))
add(("p", "Uganda's tourism rests largely on its natural assets: national parks, wildlife and primates. The "
     "national Tourism Development Master Plan 2014-2024 set out to develop these products and to grow domestic "
     "tourism, with a target of more than USD 1.4 billion in annual receipts [@masterplan]. Conservation "
     "education centres are part of this offer. The Uganda Wildlife Conservation Education Centre (UWEC) in "
     "Entebbe, a zoo and education centre that shows many of the country's animals at close range, reported "
     "more than 483,000 visitors a year in 2024, mostly from domestic tourism [@uwec_visitors]."))
add(("h2", "1.2 Issues facing wildlife tourism"))
add(("p", "The value of a wildlife visit depends heavily on interpretation: on someone telling the visitor what "
     "animal they are looking at, how it lives, how to stay safe around it and what it is called. In Uganda this "
     "depends mostly on human guides, and several problems are documented:"))
add(("bul", [
    "Guiding skills are uneven. The World Bank notes that infrastructure and branding alone will not turn "
    "visitors into livelihoods without workers who can deliver high-quality experiences, and that earlier "
    "training efforts were not enough [@wb_jobs].",
    "Local-language information is scarce. In 2018 the UWEC board chairperson told Parliament that guides "
    "often could not give the names of animals in local languages, and that many animal labels in parks were "
    "misspelt [@dispatch]. Most UWEC visitors are Ugandans, many of them school groups, for whom a local name "
    "makes an animal easier to remember.",
    "Visitors speak many languages. In the most recent survey with a country breakdown (2019), Kenya alone "
    "supplied 26.4% of visitors, and the largest groups of holiday visitors came from the USA, the United "
    "Kingdom, Kenya, Germany and Australia [@tsa2023]. Information is mostly in English.",
    "Guides cannot be everywhere. Self-guided visitors, large school groups and visitors at busy times often see "
    "animals without anyone to explain them.",
    "Connectivity is limited. Only 28.0% of Ugandans used the internet in January 2025, although mobile "
    "connections equalled 76.2% of the population [@datareportal]. Network coverage in parks is also patchy, "
    "so a tool that needs a server will often fail where it is needed."]))
add(("h2", "1.3 How artificial intelligence can help"))
add(("p", "Smart tourism uses information technology, and increasingly artificial intelligence (AI), to enrich "
     "the visitor experience and to help destinations manage it [@gretzel]. Reviews of AI and automation in "
     "tourism describe applications from recommendation and forecasting to conversational agents and visitor "
     "services [@tussyadiah,@samara], and mobile applications are the main channel through which tourists use "
     "these services on site [@dorcic]. For wildlife tourism, the most direct AI service is automatic species "
     "identification from a photograph, which has been studied mainly for scientific camera-trap monitoring "
     "[@tuia,@norouzzadeh]. Deep convolutional neural networks (CNNs) now identify animals in millions of "
     "camera-trap images [@norouzzadeh,@tabak,@willi], produce ecological estimates without manual checking "
     "[@whytock], and are packaged in platforms and two-stage detect-then-classify pipelines "
     "[@velez,@beery19,@pwild]."))
add(("p", "Placed on a visitor's phone, the same technology can act as a digital guide that is always "
     "available: the visitor photographs an animal, and the app names the species, gives short facts and a "
     "safety note, and shows the name in local languages. If the model runs on the phone, the tool also works "
     "without a network. It does not replace guides; it supports them, serves visitors who have no guide, and "
     "can carry consistent, checked local-language content."))
add(("p", "This report describes Part 2 of the UgaWildlifeVision project, which builds such a tool, "
     "UgaWildVision. Part 1 audited and corrected the NESTLER wild-animal video dataset from Ugandan parks "
     "[@nestler] into a seven-class detection dataset and trained a YOLOv8-nano detector; the dataset, "
     "software and report were published on Zenodo [@z_data,@z_soft,@z_report]. Part 2 changes the task from "
     "drawing boxes in park video to naming the species in a visitor's phone photo, and delivers it as an "
     "offline app that runs entirely on the phone."))

add(("h2", "1.4 Related technical work"))
add(("h3", "1.4.1 Generalisation to new places and cameras"))
add(("p", "The best-documented weakness of wildlife classifiers is poor transfer to new conditions. Beery et "
     "al. showed that models perform very well at the camera locations they were trained on but generalise "
     "poorly to new locations, with classifiers hit hardest [@beery18]. Schneider et al. found that accuracy dropped "
     "for species photographed at locations not seen in training, and named training-set size, class imbalance "
     "and location among the critical factors [@schneider]. Norman et al. tested whether CNN-based classification "
     "generalises across habitats within a single survey [@norman]. The WILDS benchmark made the same point "
     "across many domains, including camera traps (iWildCam): out-of-distribution performance is "
     "substantially lower than in-distribution performance, and standard remedies do not close the gap [@wilds]. "
     "A tourist's phone photo is a new domain for any model trained on camera-trap or web images, which is why "
     "this work keeps a test set of the team's own phone photos that is never used for training or tuning."))
add(("h3", "1.4.2 Training data from public image sources"))
add(("p", "Because local labelled data are scarce, many projects borrow images from public sources. Shepley "
     "et al. trained detectors on Flickr and iNaturalist photos and found that they transferred better to "
     "new camera-trap sites than models trained on camera traps alone, and that adding 5-10% target-domain "
     "images helped further [@shepley]. Large citizen-science collections such as iNat2021 [@inat21] and the "
     "TreeOfLife-10M data behind the BioCLIP foundation model [@bioclip] show how far such data can be pushed. "
     "Gadot et al. found that classifying detector crops rather than whole images improved macro-averaged "
     "F1 by about 25% on a large camera-trap dataset [@gadot], which is relevant because Part 2 mixes whole "
     "photos with crops from Part 1."))
add(("h3", "1.4.3 Running models on the phone"))
add(("p", "On-device inference needs small networks. MobileNetV3 was designed for mobile CPUs [@mobilenet], and "
     "benchmarks of Android devices show large differences in neural-network speed across phone chipsets "
     "[@aibench]. The Ultralytics YOLOv8 family includes small image-classification models (YOLOv8n-cls and "
     "YOLOv8s-cls) pretrained on ImageNet [@yolov8]. Models can be exported to the ONNX format and run in a web "
     "browser with ONNX Runtime Web, which compiles to WebAssembly (WASM) [@ort]. Progressive web apps (PWAs) "
     "use service workers to install to the home screen and work offline from a single web code base, and "
     "have been proposed as a unifier of web and native mobile development [@pwa]; for tourists this means no "
     "app-store download and no need for a network once the app is installed."))
add(("h3", "1.4.4 Augmentation, confidence and evaluation practice"))
add(("p", "Data augmentation is the usual first response to limited data [@shorten]; RandAugment reduces the "
     "search over augmentation policies to two parameters [@randaug] and is the default in Ultralytics "
     "classification training. A tool used by tourists also needs to know when it is unsure. Modern networks "
     "tend to be over-confident [@guo]; under dataset shift their confidence becomes even less reliable "
     "[@ovadia], although the maximum softmax probability remains a useful baseline signal for rejecting "
     "doubtful inputs [@hendrycks]. Finally, data leakage between training and test sets is a widespread cause "
     "of over-optimistic results in machine-learning-based science [@kapoor]; Part 1 of this project met it "
     "directly when a time-ordered split hid a class. Training here uses the AdamW optimiser [@adamw] with an "
     "ImageNet-pretrained backbone."))

add(("h2", "1.5 Problem statement"))
add(("p", "Tourism earns Uganda more than USD 1.28 billion a year and rests largely on wildlife [@mtwa2024,@masterplan], "
     "yet the visitor's experience of that wildlife depends on guide interpretation that is uneven, rarely "
     "available in local languages and absent for self-guided visitors [@wb_jobs,@dispatch], at sites where "
     "network access cannot be assumed [@datareportal]. There is no freely available tool that lets a visitor "
     "photograph an animal at a Ugandan wildlife site and receive, offline, the species name, short facts, a "
     "safety note and local-language names. Building one with AI raises a technical problem: the only labelled "
     "data available are Part 1 park video frames and about 5,200 images shared by the team from Entebbe, most "
     "of which turned out to come from public image collections rather than from the team's own visits "
     "(Section 2.2), and there is no time to draw bounding boxes. The question is therefore whether a small "
     "classifier trained mostly on such images can identify animals in real visitors' phone photos at a "
     "tourist site such as UWEC, and what most limits it."))
add(("h2", "1.6 Objectives"))
add(("p", "The main objective is to develop and honestly evaluate an AI-based smartphone tool that identifies "
     "Ugandan wildlife species from a visitor's photo, to improve the experience of wildlife tourism in Uganda. "
     "The specific objectives are to:"))
add(("num", [
    "build a leakage-safe image-classification dataset from the Part 1 frames and the Entebbe images, with "
    "the source of every image recorded and mislabelled folders corrected;",
    "train small YOLOv8 classification models suitable for phones and select one using the validation set only;",
    "measure accuracy both on an in-distribution test set and on the team's own phone photos taken as "
    "visitors at UWEC, which are never trained on;",
    "test whether phone-style data augmentation narrows the gap between the two;",
    "deliver the model in an offline progressive web app for visitors, with species facts, safety notes and "
    "local-language names, after proving that the app's preprocessing matches training."]))
add(("h2", "1.7 Significance for tourism"))
add(("bul", [
    "Visitors: an always-available, free digital guide that works without a network and keeps photos on the phone.",
    "Guides and UWEC: consistent species facts, safety notes and checked local-language names that support, "
    "rather than replace, human interpretation, including for large school groups.",
    "Domestic tourism: information in local languages makes wildlife sites more engaging for the Ugandans who "
    "form most of UWEC's visitors.",
    "The sector: an evidence-based measure of how far current AI can go with the data available, and of what "
    "data the sector would need to collect to make such tools reliable."]))
add(("h2", "1.8 Contributions"))
add(("bul", [
    "A documented 26-class dataset (cls_v1) with per-image source, group and split, label corrections and "
    "near-duplicate removal.",
    "A two-level evaluation that separates in-distribution accuracy (0.909) from accuracy on real visitor phone "
    "photos (0.191) over three seeds.",
    "A pre-registered augmentation experiment (v2) reported as a negative result.",
    "A working offline PWA for visitors, UgaWildVision, published over HTTPS, whose ONNX model agrees with "
    "PyTorch on 606 of 606 test images."]))
add(("h2", "1.9 Organisation of the report"))
add(("p", "Section 2 describes the methodology, Section 3 the experimental setup and parameters, Section 4 the "
     "results, Section 5 a graphical analysis of the results, and Section 6 the discussion, including what the "
     "results mean for tourism. Section 7 lists the limitations and the issues met during the work, and "
     "Section 8 gives the conclusions and future work."))

# ---------------- 2 Methodology
add(("h1", "2. Methodology"))
add(("h2", "2.1 Overview of the proposed approach"))
add(("p", "The approach has five stages ({F:pipeline}): (1) audit the inputs and record the source and "
     "correct label of every image; (2) build a classification dataset with leakage-safe splits; (3) "
     "fine-tune pretrained YOLOv8 classifiers with several random seeds; (4) select a model on validation "
     "accuracy and evaluate it on two test sets; and (5) export the model and run it inside a progressive "
     "web app. Image classification was chosen over detection because it needs only one folder of photos per "
     "species and no boxes. The trade-off is that a classifier names one animal per photo and works best when "
     "the animal fills much of the frame."))
add(("fig", "pipeline", FIG / "fig_pipeline.png", "Overview of the proposed approach, from data sources to the phone app.", 15.5))

add(("h2", "2.2 Data sources and audit"))
add(("p", "Two inputs were used. The first is the Part 1 Safari dataset: 1,220 video frames from Ugandan "
     "parks with 3,909 boxes in seven classes [@nestler,@z_data]. Each box was cut out as a crop with 15% extra context "
     "on each side; boxes shorter than 32 pixels were skipped. The second is three zip files of Entebbe "
     "images in folders by animal. One zip was an exact subset of another and was not used, leaving 5,187 "
     "images. A script (build_manifest.py) recorded for each image its size, camera data (EXIF), MD5 hash, "
     "folder, corrected class and likely source. The file evidence showed four sources ({T:sources})."))
add(("tab", "sources", "Sources of the 5,187 Entebbe images, as recorded in manifest.csv.",
     ["Source", "Images", "Evidence"],
     [["images.cv", "3,930", "meta.json files from images.cv; 256 x 256 pixels; already split 70/15/15"],
      ["iNaturalist-style", "1,016", "File names in the iNaturalist download format (Genus_species_<id>), 500 px"],
      ["Web downloads", "194", "Browser download names (\"images (3).jpg\"); one Shutterstock watermark"],
      ["Team phone photos (UWEC)", "47", "Phone photos through enclosure fences; Samsung originals and WhatsApp copies"]],
     [4.0, 1.8, 10.0]))
add(("p", "Only the 47 team photos can be described as taken at UWEC. The web-sourced images were used for "
     "internal training only and are never redistributed, in the app or in this report; no figure in this "
     "report contains a web-sourced photo. Species was not used as evidence of source, because UWEC also "
     "keeps non-native animals such as tigers."))
add(("h2", "2.3 Label corrections"))
add(("p", "Folder names were not reliable labels. Contact sheets of every folder were inspected by eye and "
     "the corrections in {T:labels} were applied in the manifest. Two Samsung originals were stored rotated "
     "with the rotation in their EXIF data; every script applies the EXIF rotation before use."))
add(("tab", "labels", "Label corrections applied to the Entebbe images.",
     ["Folder", "Problem found", "Action"],
     [["buffaloes (5 files)", "Pictures of zebras", "Relabelled zebra"],
      ["buffaloes (2 files)", "American bison; domestic/water buffalo", "Dropped"],
      ["primates/baboons", "Cercopithecus monkeys, not baboons", "Relabelled monkey"],
      ["herbivores/antelopes", "Gazelles, not Uganda kob", "Moved to other"],
      ["ostriches", "One photo is the UWEC owl", "Kept as bird (all birds share one class)"],
      ["5 exact duplicates", "Same file twice", "Second copy dropped"]],
     [4.2, 6.0, 5.6]))
add(("h2", "2.4 Class list"))
add(("p", "The dataset has 26 classes. Twenty regular classes have at least about 30 images: uganda_kob, "
     "bird, chimpanzee, elephant, gorilla, hippo and warthog (mostly Part 1 crops), and tiger, leopard, fox, "
     "frog, snake, fish, zebra, monkey, crocodile, tortoise, giraffe, rhino and squirrel. Five low-data "
     "classes were included at the team's request and flagged in the app: lion (6 training images), buffalo "
     "(1), cheetah (4), kudu (14) and hyena (10). An \"other\" class gathers about 25 species with 4-10 images "
     "each (for example kangaroo, jackal, gazelle and impala), so that the app can answer \"not one of my "
     "species\" instead of forcing a guess."))
add(("h2", "2.5 Leakage-safe splitting"))
add(("p", "Splits were made by recording session or photo group, never by single image, because near-identical "
     "images on both sides of a split inflate test scores [@kapoor]. The rules are summarised in {T:splitrules}; "
     "the resulting counts per class are shown in {F:splitcounts} in Section 5."))
add(("tab", "splitrules", "Splitting rules used to build cls_v1.",
     ["Images", "Rule"],
     [["Part 1 crops", "Same split as the Part 1 frame they come from (time-ordered blocks per recording session)"],
      ["images.cv, iNaturalist-style, web", "Split 80/10/10 by group with a fixed hash; all photos of one iNaturalist observation share a group"],
      ["Team UWEC phone photos", "uwec_test only; never used for training, validation or tuning"],
      ["Near-duplicates", "Any val/test image within 4 bits (64-bit dHash) of a training image removed (62 val, 40 test)"],
      ["Class caps", "At most 400 train / 60 val / 60 test images per class"]],
     [5.0, 10.8]))
add(("h2", "2.6 Model: YOLOv8 image classifier"))
add(("p", "The classifier is YOLOv8n-cls from Ultralytics [@yolov8]: a convolutional backbone pretrained on "
     "ImageNet followed by a classification head that pools the final feature map and maps it to one score "
     "z_k per class. With the 26-class head it has 1,471,594 parameters and needs 3.4 GFLOPs per 224 x 224 "
     "image. The larger YOLOv8s-cls (5,114,042 parameters, 12.6 GFLOPs) was trained once for comparison. "
     "The scores are turned into class probabilities by the softmax function, and training minimises the "
     "cross-entropy between the predicted probabilities and the true class y:"))
add(("eq", "p_k = exp(z_k) / Σ_j exp(z_j),     k = 1, ..., 26", "1"))
add(("eq", "L = − log p_y", "2"))
add(("p", "Fine-tuning starts from the pretrained weights and updates all layers. The optimiser is AdamW [@adamw] "
     "with a cosine learning-rate schedule. During training, Ultralytics applies RandAugment [@randaug], random "
     "horizontal flips, colour jitter and random erasing to every training image."))
add(("h2", "2.7 Phone-domain augmentation (v2)"))
add(("p", "The second experiment (v2) asked whether making training images look more like phone photos "
     "would close the gap to the UWEC test set. The recipe was fixed before any v2 result was seen, and every "
     "step uses the same probability for every class so that it cannot become a class shortcut. For each "
     "training image, K = 2 augmented copies were added:"))
add(("num", [
    "Part 1 crops are re-cut from the original video frame with random context of U(0.15, 1.5) times the "
    "box size, so the animal is sometimes small in the frame. Padding is reduced when the crop would take "
    "in more than 20% of a bigger box of another class, and crops under 24 pixels are skipped.",
    "With probability 0.7, the image is downscaled so its shorter side is U(80, 500) pixels, scaled back up "
    "and re-saved as JPEG at quality U(30, 80) (like a WhatsApp copy); with probability 0.3 a Gaussian blur "
    "is added.",
    "With probability 0.3, a synthetic chain-link fence is drawn over the image.",
    "With probability 0.5, exposure, contrast and saturation are jittered."]))
add(("p", "Validation, test and UWEC images are identical in v1 and v2; only the training images differ. "
     "Disclosure: the fence idea came from looking at the UWEC photos, which are the test domain."))
add(("h2", "2.8 Model selection and evaluation protocol"))
add(("p", "The model for the app is chosen by the best validation top-1 accuracy, never by test or UWEC "
     "accuracy. Two test sets are reported: test (559 images from the same sources as training) and "
     "uwec_test (the 47 team phone photos). The metrics are:"))
add(("eq", "top-1 = (1/N) Σ_i 1[argmax_k p_ik = y_i]", "3"))
add(("eq", "top-5 = (1/N) Σ_i 1[y_i is among the five most probable classes of image i]", "4"))
add(("eq", "macro accuracy = (1/|C|) Σ_c (correct in class c / images in class c)", "5"))
add(("p", "Top-1 is the share of photos named correctly; top-5 is the share whose true class is among the "
     "five most probable; macro accuracy averages per-class accuracy over the classes present, so that large "
     "classes do not dominate. For the app's \"not sure\" rule, coverage at threshold t is the share of photos "
     "whose top probability is at least t, and selective accuracy is the top-1 accuracy on those photos only "
     "[26]. Results over seeds are given as mean ± population standard deviation. For v1 against v2, "
     "each UWEC image is also paired across matching seeds and counted as wrong-to-right or right-to-wrong."))
add(("h2", "2.9 Export and preprocessing equivalence"))
add(("p", "The selected PyTorch model is exported to ONNX [@ort]. The app must prepare each photo exactly as "
     "training did, or its predictions will differ. Ultralytics classification uses torchvision Resize(224) "
     "(shorter side to 224 pixels) followed by CenterCrop(224) and scaling to [0, 1]. A check script "
     "(check_preprocess.py) compares four paths on every validation and test image: Ultralytics predict, "
     "torchvision, a re-implementation of the app's resize and crop, and ONNX Runtime."))
add(("h2", "2.10 Progressive web app design"))
add(("p", "UgaWildVision is a static PWA ({F:pwa}). The user takes a photo or picks one from the gallery. "
     "The app applies the EXIF rotation, resizes and centre-crops the image with the same geometry as "
     "training, and runs the ONNX model with ONNX Runtime Web 1.31.1 (WASM, one thread, bundled with the app, "
     "not loaded from a CDN). It shows the top three species with their confidence. If the top confidence is "
     "below 0.7, it says it is not sure and asks for a closer, clearer photo. Each species page shows facts, a "
     "safety note for dangerous animals, and a warning for the five low-data classes. The species file has "
     "slots for local-language names in Luganda, Runyankole, Rutooro and Ateso, as text and as audio. These "
     "are being generated with the Sunbird AI translation and text-to-speech service for Ugandan languages "
     "[@sunbird], and each name is marked unverified until a native speaker confirms it; the app shows only "
     "verified names. A service worker caches all files, so the app works offline, and photos "
     "never leave the phone. The app is published over HTTPS on GitHub Pages, which phones require for "
     "camera access and offline use. For a tourist, this means the app can be opened from a link or QR code "
     "at the entrance, installed in seconds, and then used anywhere in the site without a network."))
add(("fig", "pwa", FIG / "fig_pwa.png", "Inference flow inside the UgaWildVision progressive web app.", 15.5))
add(("p", "Around the classifier, the app is designed as a pocket field guide for visitors ({F:appscreens}). An "
     "Animals tab shows every species as a photo card with search and group filters (mammals, birds, reptiles, "
     "amphibians, fish). Each animal has a page with a large photo, its name in the chosen language with a "
     "Listen button, tags for its IUCN conservation status and danger level, a taxonomy table (Latin and "
     "Swahili names, class, order, family) and short facts, such as the tree-climbing lions of Ishasha or the "
     "return of rhinos to Ziwa Rhino Sanctuary. A camera button in the tab bar opens identification, and an "
     "\"I saw it!\" button records sightings, which a Sightings tab keeps on the phone with a count of "
     "animals seen. Guide photos are openly licensed images from Wikimedia Commons (CC0, public domain, CC BY "
     "or CC BY-SA only), credited on each photo and in the app; taxonomy and IUCN status come from Wikidata. "
     "No training image is shown in the app."))
add(("fig", "appscreens", FIG / "fig_app_screens.png", "The UgaWildVision field guide: animal list (left) and an animal page with name in Luganda, Listen button, status tags and taxonomy (right).", 15.5))
add(("p", "To reach visitors, the published site includes an install page (install.html) with a QR code "
     "({F:qr}) and short instructions for Android and iPhone. The page can be printed and displayed at a "
     "site entrance, or shared by guides; the app itself shows the same code so that one visitor can share "
     "it with another."))
add(("fig", "qr", FIG / "app_qr.png",
     "QR code that opens UgaWildVision (https://josephwalusimbi-eng.github.io/ugawildlifevision-app/).", 4.5))

# ---------------- 3 Experimental setup
add(("h2", "2.11 Local-language names with Sunbird AI"))
add(("p", "Most UWEC visitors are Ugandans [@uwec_visitors], and guides often lack local animal names "
     "[@dispatch], so the app gives each animal's name in four Ugandan languages: Luganda, Runyankole, "
     "Rutooro and Ateso, as text and, where possible, as audio. The names were generated with the Sunbird AI "
     "API [@sunbird] by a script (sunbird_languages.py) in four steps for each species and language:"))
add(("num", [
    "Translate the English name with the Sunflower translation model (POST /tasks/translate).",
    "Translate the result back to English, so that someone without the language can see what it means.",
    "Check automatically: the name passes only if the back-translation names the same animal and the result "
    "is not simply the English name again. Names that fail are kept for review but hidden in the app.",
    "For names that pass, synthesise speech (POST /tasks/audio/speech) where Sunbird has a voice: Luganda, "
    "Runyankole, Ateso and Kiswahili. Rutooro has no voice yet, so it is text only. The audio files are bundled with "
    "the app and cached for offline use."]))
add(("p", "All names are stored with verified = false. The app labels them \"machine translation, not yet "
     "checked\" until a native speaker confirms them, and a play button speaks the name. API keys are read "
     "from the environment and are never stored in files."))

add(("h2", "2.12 Choice of languages for international visitors"))
add(("p", "Ugandan languages serve domestic visitors; international visitors need their own languages. To avoid "
     "choosing these by preference, a fixed rule was applied to the most recent official table of visitors by "
     "country of residence, from the Uganda Tourism Satellite Account (2019 survey of 1,542,620 visitors, of whom "
     "297,726 came for leisure and holidays) [@tsa2023]: a language is included if visitors from countries where "
     "it is a main language make up at least 2% of all visitors or at least 2% of leisure and holiday visitors. "
     "English is always included. {T:langsel} and {F:langsel} show the result. Kiswahili (Kenya and Tanzania), "
     "French (DR Congo, Burundi, France and Belgium), German (Germany and Austria) and Dutch (the Netherlands) "
     "pass. Italian (1.98% of leisure visitors), Spanish, Arabic and Russian do not; Russia is not even reported "
     "separately. These languages can be added if new statistics show more visitors from those markets."))
_avl = visitor_lang()
_sel = _avl.language_selection()
add(("tab", "langsel", "Visitor languages and the share of 2019 visitors from countries where each is a main language (source: [@tsa2023]).",
     ["Language", "Countries counted", "Visitors", "% of all", "Leisure visitors", "% of leisure", "Included"],
     [[r["language"], r["countries"], f"{r['visitors']:,}" if r["visitors"] else "-",
       f"{100 * r['visitors'] / 1_542_620:.2f}" if r["visitors"] else "-", f"{r['leisure']:,}" if r["leisure"] else "-",
       f"{100 * r['leisure'] / 297_726:.2f}" if r["leisure"] else "-", r["included"]] for r in _sel],
     [2.2, 4.4, 2.0, 1.6, 2.2, 1.8, 1.6]))
selection_figure(_sel, FIG / "fig_lang_selection.png")
add(("fig", "langsel", FIG / "fig_lang_selection.png", "Share of 2019 visitors from countries speaking each candidate language, with the 2% inclusion rule.", 15.5))
add(("p", "Kiswahili names and audio come from Sunbird AI in the same way as the Ugandan languages. French, "
     "German and Dutch names are the everyday common names, checked against the titles of the matching "
     "Wikipedia articles in each language [@wikipedia]; Sunbird does not cover these languages. Their audio uses "
     "the phone's own speech voice through the Web Speech API [@webspeech], so no audio files are needed."))

add(("h1", "3. Experimental Setup"))
add(("h2", "3.1 Hardware and software"))
add(("tab", "hw", "Hardware and software used.",
     ["Item", "Value"],
     [["Training machine", "NVIDIA RTX 5070 Ti GPU (shared with another user's job during v1)"],
      ["Framework", "Ultralytics 8.4.171, PyTorch nightly with CUDA 12.8, Python 3.12"],
      ["Data preparation and figures", "Laptop, Python 3.10 with Pillow, NumPy, Matplotlib"],
      ["Export and check", "ONNX export via Ultralytics; ONNX Runtime (Python) on laptop CPU"],
      ["App runtime", "ONNX Runtime Web 1.31.1 (WASM, 1 thread), Chrome browser"],
      ["Hosting", "GitHub Pages (HTTPS)"]],
     [5.0, 10.8]))
add(("h2", "3.2 Training parameters"))
add(("p", "All settings were fixed in train_cls.py so that every run is comparable; {T:train} lists those that "
     "apply to classification training (copied from the saved args.yaml of each run)."))
add(("tab", "train", "Training parameters (identical for every run).",
     ["Parameter", "Value", "Note"],
     [["Models", "YOLOv8n-cls; YOLOv8s-cls", "ImageNet-pretrained"],
      ["Input size", "224 x 224", "Phone-friendly; images stored at up to 512 px"],
      ["Epochs (maximum)", "60", "Early stopping, patience 15 on validation top-1"],
      ["Batch size", "64", "Moderate, as the GPU was shared"],
      ["Optimiser", "AdamW", "lr0 = 0.001, final factor lrf = 0.01, cosine schedule"],
      ["Weight decay; warm-up", "0.0005; 3 epochs", "Ultralytics defaults"],
      ["Online augmentation", "RandAugment, flip 0.5, erasing 0.4", "HSV jitter h 0.015, s 0.7, v 0.4"],
      ["Seeds", "0, 1, 2 (n); 0 (s)", "deterministic = True"],
      ["Mixed precision", "AMP on", ""],
      ["Data-loader workers", "0", "Loader workers hang on this machine (Part 1 finding)"]],
     [4.2, 5.0, 6.6]))
add(("h2", "3.3 Dataset parameters"))
add(("tab", "dsparams", "Dataset build parameters (build_cls_dataset.py and make_aug_dataset.py).",
     ["Parameter", "Value"],
     [["Classes", "26 (20 regular, 5 low-data, 1 other)"],
      ["Crop context (Part 1 boxes)", "15% each side; boxes under 32 px skipped"],
      ["Stored image size", "Longest side at most 512 px"],
      ["Group split for Entebbe images", "80 / 10 / 10 by fixed hash"],
      ["Near-duplicate threshold", "64-bit dHash, 4 bits or fewer"],
      ["Caps per class", "400 train / 60 val / 60 test"],
      ["Final size (cls_v1)", "3,636 train / 553 val / 559 test / 47 uwec_test"],
      ["v2 copies per training image", "K = 2 (10,848 training images in total)"],
      ["v2 steps applied", "context crop 3,320; homogenise 5,069; fence 2,155; jitter 3,623; skipped 60"]],
     [6.0, 9.8]))
add(("h2", "3.4 Experiments"))
add(("tab", "runs", "Training runs.",
     ["Run", "Model", "Training data", "Seed", "Epochs run", "Best epoch"],
     [["v1_n_seed0", "YOLOv8n-cls", "cls_v1", "0", "33", "10"],
      ["v1_n_seed1", "YOLOv8n-cls", "cls_v1", "1", "39", "31"],
      ["v1_n_seed2", "YOLOv8n-cls", "cls_v1", "2", "44", "22"],
      ["v1_s_seed0", "YOLOv8s-cls", "cls_v1", "0", "39", "-"],
      ["v2_n_seed0", "YOLOv8n-cls", "cls_v2", "0", "41", "26"],
      ["v2_n_seed1", "YOLOv8n-cls", "cls_v2", "1", "47", "14"],
      ["v2_n_seed2", "YOLOv8n-cls", "cls_v2", "2", "27", "26"]],
     [3.0, 3.0, 2.6, 1.4, 2.6, 2.4]))
add(("p", "The four v1 runs took 6 to 8 minutes each (17:06 to 17:34 on 22 November 2026). Because v2 has "
     "three times as many training images, each v2 epoch has three times as many steps; this confound was "
     "noted before the v2 runs."))

# ---------------- 4 Results
add(("h1", "4. Results"))
add(("h2", "4.1 Training"))
add(("p", "All runs finished without error and stopped early. Validation top-1 rose above 0.8 within a few "
     "epochs and levelled off near 0.90 ({F:trainval}); training and validation loss are shown in "
     "{F:loss}. The best validation scores were 0.901, 0.899 and 0.910 for the three YOLOv8n-cls seeds and "
     "0.911 for YOLOv8s-cls. By the pre-set rule, v1_n_seed2 (0.910, the best small model) was selected for "
     "the app."))
add(("fig", "trainval", P2 / "results/v1/figures/training_curves.png", "Validation top-1 accuracy per epoch for the four v1 runs.", 14.5))
add(("fig", "loss", FIG / "fig_loss_curves.png", "Training and validation loss per epoch for the four v1 runs.", 15.5))
add(("h2", "4.2 Accuracy on the test set and on UWEC phone photos"))
add(("tab", "summary", "Accuracy of the v1 runs on the in-distribution test set and on the UWEC phone photos.",
     ["Run", "Best val top-1", "Test top-1", "Test top-5", "Test macro", "UWEC top-1", "UWEC top-5", "UWEC macro"],
     [["v1_n_seed0", "0.901", "0.900", "0.995", "0.732", "0.213", "0.468", "0.250"],
      ["v1_n_seed1", "0.899", "0.909", "0.998", "0.727", "0.149", "0.489", "0.308"],
      ["v1_n_seed2", "0.910", "0.918", "0.996", "0.781", "0.213", "0.383", "0.300"],
      ["v1_s_seed0", "0.911", "0.914", "0.996", "0.809", "0.234", "0.489", "0.297"],
      ["n, mean ± sd", "0.903 ± 0.005", "0.909 ± 0.007", "0.996", "0.747", "0.191 ± 0.030", "0.447", "0.286"]],
     [2.6, 2.1, 1.7, 1.7, 1.7, 2.1, 1.7, 1.7]))
add(("p", "On the test set, which comes from the same sources as the training data, the classifier names the "
     "species correctly about 91% of the time, and the true species is almost always among the top five. On "
     "the team's own UWEC phone photos it is right about 19% of the time (1 photo in 5), with the true "
     "species among the top five less than half the time ({T:summary}). Test macro accuracy (0.73 to 0.81) is "
     "lower than top-1 because several small classes are weak."))
add(("h2", "4.3 Per-class results"))
add(("p", "On the test set, 11 classes were classified perfectly by v1_n_seed2, while uganda_kob (44/60), "
     "bird (48/60) and gorilla (26/30) were the weakest of the large classes ({F:pctest}). On UWEC photos, "
     "only zebra and tiger transferred well ({T:uwecclass}, {F:pcuwec}). Chimpanzee, bird and buffalo were "
     "never correct in any run."))
add(("fig", "pctest", P2 / "results/v1/figures/per_class_test_v1_n_seed2.png", "Per-class accuracy of v1_n_seed2 on the test set (correct / images).", 11.5))
add(("tab", "uwecclass", "UWEC photos classified correctly, per class and per seed (YOLOv8n-cls).",
     ["Class", "UWEC photos", "v1 seeds 0 / 1 / 2", "v2 seeds 0 / 1 / 2", "Training images (v1)"],
     [["bird", "8", "0 / 0 / 0", "0 / 0 / 0", "244"],
      ["buffalo (low-data)", "9", "0 / 0 / 0", "0 / 0 / 0", "1"],
      ["cheetah (low-data)", "5", "0 / 0 / 2", "3 / 3 / 3", "4"],
      ["chimpanzee", "7", "0 / 0 / 0", "0 / 0 / 0", "400"],
      ["crocodile", "1", "0 / 1 / 0", "0 / 0 / 0", "36"],
      ["lion (low-data)", "9", "3 / 0 / 0", "0 / 0 / 0", "6"],
      ["tiger", "3", "2 / 2 / 3", "2 / 2 / 0", "400"],
      ["zebra", "5", "5 / 4 / 5", "4 / 5 / 2", "29"],
      ["Total", "47", "10 / 7 / 10", "9 / 10 / 5", ""]],
     [3.6, 2.4, 3.3, 3.3, 3.2]))
add(("fig", "pcuwec", P2 / "results/v1/figures/per_class_uwec_test_v1_n_seed2.png", "Per-class accuracy of v1_n_seed2 on the UWEC phone photos.", 12.5))
add(("h2", "4.4 Confusion matrices"))
add(("p", "{F:cmtest} and {F:cmuwec} show the confusion matrices of v1_n_seed2. On the test set nearly all "
     "mass lies on the diagonal. On UWEC photos most of it lies off the diagonal."))
add(("fig", "cmtest", P2 / "results/v1/cm_v1_n_seed2_test.png", "Confusion matrix of v1_n_seed2 on the test set (n = 559).", 14.0))
add(("fig", "cmuwec", P2 / "results/v1/cm_v1_n_seed2_uwec_test.png", "Confusion matrix of v1_n_seed2 on the UWEC phone photos (n = 47).", 13.0))
add(("h2", "4.5 Confidence threshold"))
add(("tab", "thresh", "Coverage and selective accuracy of v1_n_seed2 at different confidence thresholds.",
     ["Threshold", "Test: answered", "Test: accuracy when answered", "UWEC: answered", "UWEC: accuracy when answered"],
     [["0.0", "1.000", "0.918", "1.000", "0.213"],
      ["0.5", "0.991", "0.924", "0.936", "0.227"],
      ["0.6", "0.970", "0.934", "0.809", "0.211"],
      ["0.7 (app)", "0.936", "0.945", "0.766", "0.222"],
      ["0.8", "0.905", "0.953", "0.575", "0.222"],
      ["0.9", "0.853", "0.969", "0.426", "0.250"]],
     [2.4, 2.9, 3.6, 2.9, 3.6]))
add(("p", "At the app's threshold of 0.7, the model answers 94% of test photos at 94% accuracy. On UWEC "
     "photos it still answers 77% of photos, but only 22% of those answers are right; even above 0.9 it "
     "answers 43% of photos at 25% accuracy ({T:thresh})."))
add(("h2", "4.6 Phone-domain augmentation (v2)"))
add(("tab", "v1v2", "v1 against v2 (YOLOv8n-cls, mean ± standard deviation over three seeds).",
     ["Metric", "v1", "v2"],
     [["Best validation top-1", "0.903 ± 0.005", "0.898 ± 0.007"],
      ["Test top-1 (n = 559)", "0.909 ± 0.007", "0.924 ± 0.006"],
      ["UWEC top-1, all (n = 47)", "0.191 ± 0.030", "0.170 ± 0.046"],
      ["UWEC, regular classes (n = 24)", "0.306 ± 0.020", "0.208 ± 0.090"],
      ["UWEC, low-data classes (n = 23)", "0.072 ± 0.054", "0.130 ± 0.000"],
      ["Paired UWEC changes (141 image-seeds)", "-", "8 wrong→right, 11 right→wrong (net −3)"]],
     [6.6, 4.2, 5.0]))
add(("p", "Phone-style augmentation raised in-distribution test accuracy by about 0.015 but did not improve "
     "accuracy on the UWEC photos ({T:v1v2}). By the selection rule, the app keeps v1_n_seed2."))
add(("h2", "4.7 Export and app"))
add(("tab", "export", "Export check and app measurements for v1_n_seed2.",
     ["Measurement", "Value"],
     [["ONNX model size", "5.9 MB (26 classes)"],
      ["Top-1 agreement, ONNX vs PyTorch", "606 / 606 validation + test images; largest probability difference 0.0"],
      ["CPU time per image (Python, laptop)", "about 7.9 ms"],
      ["Time per image in the browser (Chrome, WASM)", "about 40-50 ms"],
      ["Browser vs Python on 5 test photos", "Same top-1 on all 5 (including a 4000 x 3000 EXIF-rotated photo)"],
      ["Offline cache", "Service worker active, 15 files cached"],
      ["Published app", "https://josephwalusimbi-eng.github.io/ugawildlifevision-app/"]],
     [6.6, 9.2]))

if LANG_CSV.exists():
    _ltab, _lstats = lang_data()
    _npass = sum(v[0] for v in _lstats.values()); _ntot = sum(v[1] for v in _lstats.values())
    _naud = sum(v[2] for v in _lstats.values())
    add(("h2", "4.8 Local-language names"))
    add(("p", f"Sunbird AI produced {_ntot} names (25 species in {len(_lstats)} languages). {_npass} of them passed the "
         f"back-translation check and are shown in the app, and {_naud} have audio ({{T:langnames}}, "
         "{F:langcheck}). Well-known animals with a common local word were translated reliably, for example "
         "lion (Luganda Empologoma, Runyankole Entare) and bird (Ekinyonyi). Animals with compound or foreign "
         "names, such as Uganda kob, chimpanzee or kudu, often came back as unrelated sentences or as the "
         "English word."))
    add(("tab", "langnames", "Animal names from Sunbird AI. * = audio available; (x) = failed the back-translation check and hidden in the app. None is yet verified by a native speaker.",
         ["English", "Luganda", "Runyankole", "Rutooro", "Ateso", "Kiswahili"], _ltab, [2.8, 2.6, 2.6, 2.6, 2.6, 2.6]))
    lang_figure(_lstats, FIG / "fig_lang_check.png")
    add(("fig", "langcheck", FIG / "fig_lang_check.png", "Sunbird AI animal names per language that passed or failed the automatic back-translation check.", 14.5))
    _avl2 = visitor_lang()
    add(("p", "{T:visitornames} lists the French, German and Dutch names used for international visitors."))
    add(("tab", "visitornames", "French, German and Dutch animal names (spoken by the phone's own voice; not yet checked by native speakers).",
         ["English", "French", "German", "Dutch"],
         [[_ltab[i][0]] + list(v) for i, v in enumerate(_avl2.NAMES.values())], [3.6, 4.0, 4.0, 4.0]))

# ---------------- 5 Results analysis
add(("h1", "5. Results Analysis"))
add(("h2", "5.1 The gap between test and phone photos"))
add(("p", "{F:testuwec} sets the two test sets side by side for each v1 run. All four runs score 0.90 to 0.92 "
     "on the test set and 0.15 to 0.23 on the UWEC photos. The gap is about 0.7 for every seed and for both "
     "model sizes, so it is a property of the data, not of one unlucky run. {F:runmetrics} adds top-5 and "
     "macro accuracy: on the test set top-5 is almost 1.0, while on UWEC photos even the five best guesses "
     "contain the right species less than half the time, so the errors are not near misses."))
add(("fig", "testuwec", P2 / "results/v1/figures/test_vs_uwec.png", "Top-1 accuracy on the test set and on UWEC phone photos for each v1 run.", 14.0))
add(("fig", "runmetrics", FIG / "fig_metrics_per_run.png", "Top-1, top-5 and macro accuracy for each v1 run: (a) test set, (b) UWEC phone photos.", 15.5))
add(("h2", "5.2 What the training data look like"))
add(("p", "{F:sources} shows where the data come from. Three-quarters of the Entebbe images are 256-pixel "
     "images.cv pictures, and only 47 are the team's phone photos. In the built dataset, Part 1 video crops "
     "and images.cv pictures make up most of the training set, and the UWEC test set consists entirely of a "
     "source that never appears in training. {F:splitcounts} shows the per-class counts: the low-data "
     "classes have more UWEC test photos than training images (buffalo 1 training image against 9 test "
     "photos; lion 6 against 9), so they cannot be expected to work."))
add(("fig", "sources", FIG / "fig_sources.png", "(a) Sources of the Entebbe images; (b) composition of cls_v1 by split and origin.", 15.5))
add(("fig", "splitcounts", FIG / "fig_split_counts.png", "Images per class and split in cls_v1.", 14.0))
add(("h2", "5.3 Where the errors go"))
add(("p", "{T:errors} lists what v1_n_seed2 predicted for each UWEC class. The errors follow the training "
     "data. Chimpanzee has 400 training images, but nearly all come from one Part 1 video, so a chimpanzee "
     "photographed through a fence is called monkey or gorilla. The Part 1 birds are small egrets in video "
     "frames, while the UWEC birds are an owl, parrots and ostriches, which the model calls frog or fish. "
     "Buffalo, with one training image, becomes elephant."))
add(("tab", "errors", "Predictions of v1_n_seed2 on the UWEC photos, by true class.",
     ["True class (n)", "Predicted classes (count)", "Mean confidence"],
     [["bird (8)", "frog 3, fish 2, gorilla 1, leopard 1, other 1", "0.84"],
      ["buffalo (9)", "elephant 6, other 3", "0.82"],
      ["cheetah (5)", "cheetah 2, leopard 2, snake 1", "0.69"],
      ["chimpanzee (7)", "monkey 3, gorilla 2, fish 1, kudu 1", "0.79"],
      ["crocodile (1)", "snake 1", "0.99"],
      ["lion (9)", "monkey 4, other 2, tiger 1, kudu 1, snake 1", "0.77"],
      ["tiger (3)", "tiger 3", "0.91"],
      ["zebra (5)", "zebra 5", "0.88"]],
     [3.6, 8.8, 3.4]))
add(("h2", "5.4 The model is confidently wrong on phone photos"))
add(("p", "{F:conf} compares the confidence of correct and wrong answers. On the test set, wrong answers "
     "are rare and mostly have lower confidence, so a threshold separates them well. On UWEC photos, 37 of "
     "47 answers are wrong and their mean confidence is 0.80; most lie above the 0.7 threshold. "
     "{F:thresh} shows the same effect as curves: raising the threshold improves test accuracy steadily, but "
     "on UWEC photos it removes answers without making the remaining ones more accurate."))
add(("fig", "conf", FIG / "fig_confidence.png", "Top-1 confidence of correct and wrong predictions of v1_n_seed2: (a) test set, (b) UWEC phone photos.", 15.5))
add(("fig", "thresh", P2 / "results/v1/figures/threshold_v1_n_seed2.png", "Share of photos answered and accuracy when answered, against the confidence threshold (v1_n_seed2).", 14.0))
add(("h2", "5.5 Effect of phone-domain augmentation"))
add(("p", "{F:v1v2} summarises the v2 experiment with seed spread. The test score rises slightly, while the "
     "UWEC scores overlap within their spread. Per class ({F:v1v2class}), chimpanzee, bird and buffalo stay at "
     "zero, cheetah improves and zebra, tiger and crocodile fall; with 1 to 9 photos per class, none of these "
     "changes is evidence on its own. The validation curves ({F:v1v2val}) show that v2 did not reach a "
     "better validation score either."))
add(("fig", "v1v2", FIG / "fig_v1_v2_summary.png", "v1 against v2: mean accuracy over three seeds, with one standard deviation as error bars.", 15.0))
add(("fig", "v1v2class", P2 / "results/compare_v1_v2.png", "Share of UWEC photos correct per class, v1 against v2 (mean of three seeds).", 15.0))
add(("fig", "v1v2val", FIG / "fig_val_curves_v1_v2.png", "Validation top-1 accuracy per epoch for the three v1 and three v2 seeds.", 15.0))
add(("h2", "5.6 Model size"))
add(("p", "YOLOv8s-cls has 3.5 times the parameters and 3.7 times the computation of YOLOv8n-cls, but its "
     "validation top-1 was only 0.001 above the best small model (0.911 against 0.910), and its UWEC accuracy "
     "(0.234) lies within the range of the small-model seeds ({T:summary}). For a phone app, the small model "
     "is the better choice."))

# ---------------- 6 Discussion
add(("h1", "6. Results Discussion and Analysis"))
add(("h2", "6.1 A high test score is not real-world accuracy"))
add(("p", "The main finding is a gap of about 0.7 between in-distribution test accuracy (0.909 ± 0.007) "
     "and accuracy on real phone photos (0.191 ± 0.030). It agrees with the camera-trap literature, where "
     "models that do very well at familiar locations fail at new ones [@beery18,@schneider,@wilds], and with Part 1 of this "
     "project, where gorilla detection fell from 0.77 to 0.15 mAP50 on an unseen session. The test set shares "
     "its sources, photographers and image style with the training set; the UWEC photos share none of them. "
     "Only the second measures what a user of the app will experience."))
add(("h2", "6.2 What transfers and why"))
add(("p", "The classes that transfer are those whose training images are many different photos of many "
     "different animals: zebra and tiger come from varied web and images.cv photos and were recognised at UWEC "
     "in almost every run. The classes that fail are those whose training images, however many, show little "
     "variety: 400 chimpanzee crops from essentially one video, and Part 1 birds that are a different kind of "
     "bird at a different scale. This matches the observation that the number of distinct scenes matters more "
     "than the number of images [@schneider], and the finding that a few target-domain images can help a model "
     "trained on public photos [@shepley]."))
add(("h2", "6.3 Why augmentation did not help"))
add(("p", "Phone-style augmentation targets the style of the image: compression, fences, blur and the animal "
     "being small. It cannot create what is missing, such as a chimpanzee seen from a new angle in a new place, "
     "or an owl when the training birds are egrets. This was predicted before the v2 runs, and the result "
     "agrees: classes that were zero stayed at zero. The small rise on the in-distribution test is the kind of "
     "\"better on the easy test\" signal that should not be trusted [@kapoor]. The augmentation recipe was not then "
     "tuned against the UWEC photos, because with 47 images that would only fit the test set."))
add(("h2", "6.4 Confidence and the \"not sure\" rule"))
add(("p", "The threshold of 0.7 works as intended on the test set but not on phone photos, where the model "
     "is wrong with high confidence. This is the over-confidence under dataset shift described in [@guo,@ovadia]: "
     "a softmax probability is a useful signal for rejecting doubtful inputs [@hendrycks] only when the inputs resemble "
     "the training data. The app therefore shows a short note on its start screen that accuracy on real phone "
     "photos is about 1 in 5, and asks for close, clear photos."))
add(("h2", "6.5 Engineering results"))
add(("p", "The engineering side worked. The ONNX model is 5.9 MB, runs in about 8 ms per image on a laptop "
     "CPU and about 40-50 ms in a browser, and gives exactly the same answer as PyTorch on all 606 checked "
     "images once the preprocessing geometry was matched. The PWA installs, runs offline and keeps photos on "
     "the phone. This is consistent with the case for small CNNs and web delivery on phones [@mobilenet,@aibench,@pwa]. "
     "The limiting factor is the data, not the model size or the delivery platform."))
add(("h2", "6.6 Comparison with the literature"))
add(("p", "Published wildlife classifiers report 88% to 99% accuracy within their own datasets [@norouzzadeh,@willi] and "
     "lower values on new locations, for example 68.7% top-1 for the best network on untrained locations in "
     "[@schneider]. Those systems are trained on hundreds of thousands to millions of images from the target cameras. "
     "This project has 3,636 training images and almost none from the target domain, so its 0.19 on phone "
     "photos is not surprising. The lesson from [@shepley] and from this work is the same: a modest number of "
     "real target-domain photos per species is likely to matter more than any further training technique."))

add(("h2", "6.7 What the results mean for tourism in Uganda"))
add(("p", "For tourism, the results say two things. First, the delivery side of an AI visitor tool is ready "
     "now. A 5.9 MB model runs offline on the phone in well under a second, needs no app store and no network, "
     "keeps visitors' photos private, and can carry facts, safety notes and local-language names for every "
     "species. This directly addresses the access problems in Section 1.2: limited connectivity "
     "[@datareportal], visitors without a guide, and the shortage of local-language information [@dispatch]."))
add(("p", "Second, recognition accuracy on real visitor photos is not yet good enough to rely on: about 1 photo "
     "in 5 at UWEC, with chimpanzee and birds, two of the animals visitors most want to see, never correct. "
     "Releasing the tool to tourists in this state would risk wrong information and lost trust. The cause is "
     "clear and fixable: the model has seen almost no photos taken the way visitors take them. Because "
     "tourism sites see the same animals every day, the sector is unusually well placed to collect exactly "
     "the data that is missing. Guides and staff photographing each animal over a few weeks would provide the "
     "30 or more varied photos per species that this work identifies as the main need."))
add(("p", "The most realistic near-term use is therefore as a guide's assistant and an education tool: at a "
     "site like UWEC, where the animals are known and fixed, the app can show checked facts, safety notes and "
     "names in Ugandan languages and in the main languages of international visitors (text and audio) for "
     "each animal, with recognition as a convenience that improves "
     "as site photos are added. This fits the smart-tourism view of technology as a support to the visitor "
     "experience rather than a replacement for people [@gretzel,@tussyadiah]."))

# ---------------- 7 Limitations
add(("h1", "7. Limitations"))
add(("h2", "7.1 Data"))
add(("bul", [
    "Only 47 of 5,187 Entebbe images are the team's own photos; the rest come from images.cv, iNaturalist-style "
    "downloads and the web. Those may be used for internal training only and cannot be published or "
    "redistributed.",
    "Five classes are low-data (buffalo has one training image), and most of their photos are UWEC test photos.",
    "Chimpanzee images come almost entirely from one Part 1 video. Many Part 1 bird crops are poor: 175 of "
    "379 bird boxes lie at least 80% inside a bigger box of another class, and some show only hippo skin.",
    "The \"other\" class contains only animals; it has no people, empty enclosures or non-animal images, so the "
    "app cannot say \"no animal\".",
    "Folder names were unreliable; corrections were made by eye and may have missed some errors."]))
add(("h2", "7.2 Evaluation"))
add(("bul", [
    "The UWEC test set is small (47 photos) and covers only 8 of the 26 classes; per-class results rest on 1 to "
    "9 photos.",
    "The same 47 photos have now been examined many times (including for the fence idea), so a fresh set of "
    "unseen phone photos is needed for the next honest measurement.",
    "Three seeds per setting; the standard deviations are rough.",
    "The v2 comparison is confounded by three times as many training steps per epoch."]))
add(("h2", "7.3 Model and app"))
add(("bul", [
    "The classifier names one animal per photo and works best when the animal fills the frame; there is no "
    "detector step for small or distant animals.",
    "Confidence is unreliable on phone photos, so the \"not sure\" rule gives only limited protection.",
    "At the time of writing the app had been tested in desktop Chrome, not yet on a range of real phones "
    "(camera capture, install to home screen, offline mode).",
    "Local-language names (text and audio) come from machine translation and speech synthesis and must be "
    "checked by native speakers before visitors see them.",
    "The tool has not yet been tried with real tourists, so its effect on the visitor experience has not been measured.",
    "Timings come from one laptop and one desktop browser, not from field devices.",
    "Machine translation of single animal names is unreliable for names without a common local word; the "
    "back-translation check is automatic and can both pass a wrong name and reject a right one."]))
add(("h2", "7.4 Issues encountered and how they were resolved"))
add(("tab", "issues", "Issues encountered during Part 2 and their resolution.",
     ["Issue", "Effect", "Resolution"],
     [["Most \"team\" images were from web sources", "Claims about UWEC and publication of images limited", "Source recorded per image; web images internal only; UWEC photos used only for testing"],
      ["Mislabelled folders (zebras in buffaloes, gazelles as antelope, monkeys as baboons)", "Wrong labels in training", "Corrected after visual check of contact sheets"],
      ["Samsung photos stored rotated", "Model would see sideways animals", "EXIF rotation applied in every script and in the app"],
      ["Preprocessing off by one pixel", "ONNX check agreed on only 97.5% of images", "Matched torchvision Resize + CenterCrop exactly; 606/606 agree"],
      ["ONNX Runtime Web rejected a relative WASM path", "App failed to load the model", "Absolute URL used"],
      ["Wide crop context around Part 1 birds showed hippos", "Hippo pictures labelled bird in v2", "Padding limited to 20% overlap with bigger boxes; dominated crops skipped"],
      ["Upload of the 423 MB v2 dataset timed out", "Could not train v2 on the GPU", "Dataset rebuilt on the GPU machine from the same script and seed; counts checked identical"],
      ["Shared GPU (another user's job)", "Less memory and time", "Small model, batch 64, runs scheduled alongside"],
      ["Ultralytics data-loader workers hang", "Training stalls", "workers = 0"],
      ["Web images must not be hosted", "Test images in the app folder", "Removed before publishing; app contains no training images"]],
     [5.2, 4.6, 6.0]))

# ---------------- 8 Conclusion
add(("h1", "8. Conclusion and Future Work"))
add(("h2", "8.1 Conclusion"))
add(("p", "Tourism is one of Uganda's leading export earners and depends on wildlife, but the visitor's "
     "experience of that wildlife is limited by uneven guiding, scarce local-language information and poor "
     "connectivity. This work set out to show how artificial intelligence can help, by building a free, "
     "offline smartphone tool that identifies animals from a visitor's photo and explains them."))
add(("p", "Part 2 built that tool, UgaWildVision, and measured it honestly. "
     "A 26-class YOLOv8n-cls classifier, trained on 3,636 images from Part 1 video crops and public image "
     "collections, reaches 0.909 ± 0.007 top-1 accuracy on an in-distribution test set. It was exported to a "
     "5.9 MB ONNX model that matches PyTorch exactly and runs offline inside a progressive web app on the "
     "phone. On the team's own phone photos from UWEC, however, it is right only 0.191 ± 0.030 of the time: "
     "zebra and tiger work, while chimpanzee, birds, lion and buffalo do not. Phone-style augmentation did not "
     "close the gap. The model is also confidently wrong on phone photos, so a confidence threshold cannot "
     "replace better data."))
add(("p", "The main conclusion is that the limit is the variety of real photos per animal, not the size of the "
     "model, the training technique or the delivery platform. The app and pipeline are ready to support "
     "tourism in Uganda; what they need is the right data, and tourism sites are well placed to provide it. "
     "With site-specific photos and checked local-language content, the tool can become a practical digital "
     "guide for the hundreds of thousands of domestic and international visitors to Ugandan wildlife sites."))
add(("h2", "8.2 Future work"))
add(("num", [
    "Collect about 30 or more original phone photos per species at UWEC, from varied angles and distances and "
    "through the fence, sent as original files rather than WhatsApp copies; train on part of them and keep a "
    "new, unseen set for testing.",
    "Clean the Part 1 bird and chimpanzee crops, and add a detector step that crops small or distant animals "
    "before classification [@beery19,@gadot].",
    "Add non-animal images (people, empty enclosures) to the \"other\" class.",
    "Test the app on several real phones (camera capture, installation, offline use, speed).",
    "Complete the local-language names and audio (Luganda, Runyankole, Rutooro, Ateso) with Sunbird AI "
    "[@sunbird] and have native speakers verify them before they are shown.",
    "Work with UWEC and the Uganda Wildlife Authority to pilot the app with visitors and guides, and measure "
    "its effect on the visitor experience.",
    "Extend the species list and content to the main national parks, so the same app serves visitors across "
    "Uganda's wildlife tourism circuit.",
    "Try stronger pretrained features, such as BioCLIP [@bioclip], and confidence calibration under shift [@guo,@ovadia].",
    "Build the planned Android app from the same ONNX model."]))

REFS = {
    "tuia": "D. Tuia, B. Kellenberger, S. Beery, B. R. Costelloe, et al., \"Perspectives in machine learning for wildlife conservation,\" Nature Communications, vol. 13, art. 792, 2022, doi: 10.1038/s41467-022-27980-y.",
    "norouzzadeh": "M. S. Norouzzadeh, A. Nguyen, M. Kosmala, A. Swanson, M. S. Palmer, C. Packer, and J. Clune, \"Automatically identifying, counting, and describing wild animals in camera-trap images with deep learning,\" Proc. National Academy of Sciences, vol. 115, no. 25, pp. E5716-E5725, 2018, doi: 10.1073/pnas.1719367115.",
    "tabak": "M. A. Tabak, M. S. Norouzzadeh, D. W. Wolfson, S. J. Sweeney, K. C. Vercauteren, and N. P. Snow, \"Machine learning to classify animal species in camera trap images: Applications in ecology,\" Methods in Ecology and Evolution, vol. 10, no. 4, pp. 585-590, 2019, doi: 10.1111/2041-210X.13120.",
    "willi": "M. Willi, R. T. Pitman, A. W. Cardoso, et al., \"Identifying animal species in camera trap images using deep learning and citizen science,\" Methods in Ecology and Evolution, vol. 10, pp. 80-91, 2019, doi: 10.1111/2041-210X.13099.",
    "whytock": "R. C. Whytock, J. Świeżewski, J. A. Zwerts, et al., \"Robust ecological analysis of camera trap data labelled by a machine learning model,\" Methods in Ecology and Evolution, vol. 12, no. 6, pp. 1080-1092, 2021, doi: 10.1111/2041-210X.13576.",
    "velez": "J. Vélez, W. McShea, H. Shamon, P. J. Castiblanco-Camacho, M. A. Tabak, C. Chalmers, P. Fergus, and J. Fieberg, \"An evaluation of platforms for processing camera-trap data using artificial intelligence,\" Methods in Ecology and Evolution, vol. 14, no. 2, pp. 459-477, 2023, doi: 10.1111/2041-210X.14044.",
    "beery19": "S. Beery, D. Morris, and S. Yang, \"Efficient pipeline for camera trap image review,\" KDD Workshop on Data Mining and AI for Conservation, 2019, arXiv:1907.06772.",
    "pwild": "A. Hernandez, Z. Miao, L. Vargas, S. Beery, R. Dodhia, P. Arbelaez, and J. M. Lavista Ferres, \"Pytorch-Wildlife: A collaborative deep learning framework for conservation,\" arXiv:2405.12930, 2024.",
    "beery18": "S. Beery, G. Van Horn, and P. Perona, \"Recognition in terra incognita,\" in Proc. European Conference on Computer Vision (ECCV), 2018, pp. 456-473.",
    "schneider": "S. Schneider, S. Greenberg, G. W. Taylor, and S. C. Kremer, \"Three critical factors affecting automated image species recognition performance for camera traps,\" Ecology and Evolution, vol. 10, no. 7, pp. 3503-3517, 2020, doi: 10.1002/ece3.6147.",
    "norman": "D. L. Norman et al., \"Can CNN-based species classification generalise across variation in habitat within a camera trap survey?\" Methods in Ecology and Evolution, 2023.",
    "wilds": "P. W. Koh, S. Sagawa, H. Marklund, et al., \"WILDS: A benchmark of in-the-wild distribution shifts,\" in Proc. 38th International Conference on Machine Learning (ICML), PMLR 139, 2021, pp. 5637-5664.",
    "shepley": "A. Shepley, G. Falzon, P. Meek, and P. Kwan, \"Automated location invariant animal detection in camera trap images using publicly available data sources,\" Ecology and Evolution, vol. 11, no. 9, pp. 4494-4506, 2021, doi: 10.1002/ece3.7344.",
    "inat21": "G. Van Horn, E. Cole, S. Beery, K. Wilber, S. Belongie, and O. Mac Aodha, \"Benchmarking representation learning for natural world image collections,\" in Proc. IEEE/CVF Conference on Computer Vision and Pattern Recognition (CVPR), 2021, pp. 12884-12893.",
    "bioclip": "S. Stevens et al., \"BioCLIP: A vision foundation model for the tree of life,\" in Proc. IEEE/CVF Conference on Computer Vision and Pattern Recognition (CVPR), 2024, pp. 19412-19424.",
    "gadot": "T. Gadot, Ş. Istrate, H. Kim, D. Morris, S. Beery, T. Birch, and J. Ahumada, \"To crop or not to crop: Comparing whole-image and cropped classification on a large dataset of camera trap images,\" IET Computer Vision, vol. 18, no. 8, pp. 1193-1208, 2024, doi: 10.1049/cvi2.12318.",
    "mobilenet": "A. Howard, M. Sandler, G. Chu, et al., \"Searching for MobileNetV3,\" in Proc. IEEE/CVF International Conference on Computer Vision (ICCV), 2019, pp. 1314-1324.",
    "aibench": "A. Ignatov, R. Timofte, W. Chou, K. Wang, M. Wu, T. Hartley, and L. Van Gool, \"AI Benchmark: Running deep neural networks on Android smartphones,\" in Proc. ECCV Workshops, LNCS 11133, 2018, pp. 288-314.",
    "yolov8": "G. Jocher, A. Chaurasia, and J. Qiu, \"Ultralytics YOLOv8,\" 2023. [Online]. Available: https://github.com/ultralytics/ultralytics",
    "ort": "ONNX Runtime developers, \"ONNX Runtime,\" 2021. [Online]. Available: https://onnxruntime.ai",
    "pwa": "A. Biørn-Hansen, T. A. Majchrzak, and T.-M. Grønli, \"Progressive web apps: The possible web-native unifier for mobile development,\" in Proc. 13th International Conference on Web Information Systems and Technologies (WEBIST), 2017, pp. 344-351, doi: 10.5220/0006353703440351.",
    "shorten": "C. Shorten and T. M. Khoshgoftaar, \"A survey on image data augmentation for deep learning,\" Journal of Big Data, vol. 6, art. 60, 2019, doi: 10.1186/s40537-019-0197-0.",
    "randaug": "E. D. Cubuk, B. Zoph, J. Shlens, and Q. V. Le, \"RandAugment: Practical automated data augmentation with a reduced search space,\" in Proc. IEEE/CVF CVPR Workshops, 2020, pp. 702-703.",
    "guo": "C. Guo, G. Pleiss, Y. Sun, and K. Q. Weinberger, \"On calibration of modern neural networks,\" in Proc. 34th International Conference on Machine Learning (ICML), PMLR 70, 2017, pp. 1321-1330.",
    "ovadia": "Y. Ovadia, E. Fertig, J. Ren, et al., \"Can you trust your model's uncertainty? Evaluating predictive uncertainty under dataset shift,\" in Advances in Neural Information Processing Systems (NeurIPS), 2019.",
    "hendrycks": "D. Hendrycks and K. Gimpel, \"A baseline for detecting misclassified and out-of-distribution examples in neural networks,\" in Proc. International Conference on Learning Representations (ICLR), 2017.",
    "kapoor": "S. Kapoor and A. Narayanan, \"Leakage and the reproducibility crisis in machine-learning-based science,\" Patterns, vol. 4, no. 9, art. 100804, 2023, doi: 10.1016/j.patter.2023.100804.",
    "nestler": "NESTLER Wild Animal Recognition Video Dataset, Zenodo, 2025, doi: 10.5281/zenodo.17036940 (CC BY 4.0).",
    "z_data": "J. Walusimbi, A. Babirye, and A. Sserwadda, \"UgaWildlifeVision Dataset: An annotated image dataset with detection and segmentation annotations for seven Ugandan wildlife species, corrected from the NESTLER video dataset (Part 1 of 2),\" Zenodo, 2026, doi: 10.5281/zenodo.23171670.",
    "z_soft": "J. Walusimbi, A. Babirye, and A. Sserwadda, \"UgaWildlifeVision Software: YOLOv8 wildlife detection model, training code, and SAM copy-paste augmentation pipeline (Part 2 of 2),\" Zenodo, 2026, doi: 10.5281/zenodo.23171907.",
    "z_report": "J. Walusimbi, A. Babirye, and A. Sserwadda, \"An annotated detection and segmentation dataset and a wildlife detection and recognition system for animal species in Uganda (UgaWildlifeVision Report),\" Zenodo, 2026, doi: 10.5281/zenodo.23172055.",
    "adamw": "I. Loshchilov and F. Hutter, \"Decoupled weight decay regularization,\" in Proc. International Conference on Learning Representations (ICLR), 2019.",
    "mtwa2024": "Ministry of Tourism, Wildlife and Antiquities, \"Uganda's tourism sector hits record high of US$1.28 billion in 2024,\" 2025. [Online]. Available: https://www.tourism.go.ug/single-post/uganda-s-tourism-sector-hits-record-high-of-us-1-28-billion-in-2024",
    "tsa2024": "SoftPower News, \"Tourism contributes Shs6.99 trillion to Uganda's economy, sustains 876,000 jobs\" (report on the Uganda Tourism Satellite Account 2024), 2025. [Online]. Available: https://softpower.ug/tourism-contributes-shs6-99-trillion-to-ugandas-economy-sustains-876000-jobs-report/",
    "wb_jobs": "World Bank, \"Why tourism is Uganda's best bet for creating jobs at scale,\" Africa Can End Poverty blog. [Online]. Available: https://blogs.worldbank.org/en/africacan/why-tourism-is-uganda-best-bet-for-creating-jobs-at-scale (accessed Nov. 2026).",
    "masterplan": "UN Tourism (UNWTO), \"Uganda launches Tourism Development Master Plan on World Tourism Day,\" Oct. 2014. [Online]. Available: https://www.untourism.int/archive/global/news/2014-10-10/uganda-launches-tourism-development-master-plan-world-tourism-day",
    "uwec_visitors": "Daily Monitor, \"UWEC reports increasing number of tourists,\" Feb. 2024. [Online]. Available: https://monitor.co.ug/uganda/news/national/uwec-reports-increasing-number-of-tourists-4541056",
    "dispatch": "The Dispatch, \"Tour guides ignorant of indigenous animal names - UWEC,\" Aug. 2018. [Online]. Available: https://www.dispatch.ug/2018/08/10/tour-guides-ignorant-indigenous-animal-names-uwec/",
    "datareportal": "S. Kemp, \"Digital 2025: Uganda,\" DataReportal, 2025. [Online]. Available: https://datareportal.com/reports/digital-2025-uganda",
    "gretzel": "U. Gretzel, M. Sigala, Z. Xiang, and C. Koo, \"Smart tourism: foundations and developments,\" Electronic Markets, vol. 25, no. 3, pp. 179-188, 2015, doi: 10.1007/s12525-015-0196-8.",
    "tussyadiah": "I. Tussyadiah, \"A review of research into automation in tourism: Launching the Annals of Tourism Research Curated Collection on Artificial Intelligence and Robotics in Tourism,\" Annals of Tourism Research, vol. 81, art. 102883, 2020, doi: 10.1016/j.annals.2020.102883.",
    "samara": "D. Samara, I. Magnisalis, and V. Peristeras, \"Artificial intelligence and big data in tourism: a systematic literature review,\" Journal of Hospitality and Tourism Technology, vol. 11, no. 2, pp. 343-367, 2020, doi: 10.1108/JHTT-12-2018-0118.",
    "dorcic": "J. Dorcic, J. Komsic, and S. Markovic, \"Mobile technologies and applications towards smart tourism - state of the art,\" Tourism Review, vol. 74, no. 1, pp. 82-103, 2019, doi: 10.1108/TR-07-2017-0121.",
    "tsa2023": "Uganda Bureau of Statistics and Ministry of Tourism, Wildlife and Antiquities, \"Uganda Tourism Satellite Account 2023: Measuring the contribution of tourism to the economy of Uganda,\" Kampala, 2023 (Appendix Table 2.9: purpose of visit by country of residence, 2019). [Online]. Available: https://www.ubos.org/wp-content/uploads/publications/03_2023Final_Uganda_Tourism_Satellite_Account_Report_Full_Version_2023_Web.pdf",
    "webspeech": "W3C Speech API Community Group, \"Web Speech API,\" draft specification. [Online]. Available: https://webaudio.github.io/web-speech-api/",
    "wikipedia": "Wikipedia, articles on each species in the French, German and Dutch editions, reached through the language links of the English articles (accessed Nov. 2026). [Online]. Available: https://www.wikipedia.org",
    "sunbird": "Sunbird AI, \"Sunbird AI API: translation, speech recognition and text-to-speech for Ugandan languages.\" [Online]. Available: https://sunbird.ai (accessed Nov. 2026).",
}

ABSTRACT = [
    "Tourism is one of Uganda's leading export earners, bringing in a record USD 1.28 billion in 2024, and "
    "it rests largely on wildlife. Yet a visitor's experience of that wildlife depends on guide interpretation "
    "that is uneven, rarely available in local languages and absent for self-guided visitors, at sites where "
    "network access cannot be assumed. This report describes how artificial intelligence (AI) can help, through "
    "UgaWildVision: a free smartphone tool that identifies an animal from a visitor's photo and shows facts, "
    "safety notes and local-language names, entirely offline. It is Part 2 of the UgaWildlifeVision project.",
    "A 26-class image-classification dataset was built from crops of the Part 1 Ugandan park video frames and "
    "from 5,187 images shared by the team from Entebbe. An audit showed that only 47 of these were the team's own "
    "phone photos taken as visitors at the Uganda Wildlife Conservation Education Centre (UWEC); the rest came from "
    "public image collections. Sources were recorded, mislabelled folders corrected, and the data split by "
    "session or photo group, with the 47 UWEC photos held out as a real-world test set. Small ImageNet-pretrained "
    "YOLOv8 classifiers were fine-tuned with three random seeds. The selected YOLOv8n-cls model (1.47 million "
    "parameters) reaches 0.909 ± 0.007 top-1 accuracy on an in-distribution test set but only "
    "0.191 ± 0.030 on the UWEC visitor photos; zebra and tiger transfer, while chimpanzee, birds, lion and "
    "buffalo do not, and the model is confidently wrong on phone photos. Phone-style augmentation did not close "
    "the gap (0.170 ± 0.046). The model was exported to a 5.9 MB ONNX file that agrees with PyTorch on 606 "
    "of 606 images and runs offline in a progressive web app in about 40-50 ms per photo.",
    "The delivery side of an AI visitor tool is therefore ready, but recognition on real visitor photos is "
    "limited by the variety of such photos in training, not by the model or the platform. Tourism sites are well "
    "placed to supply the missing data: about 30 or more varied phone photos per species would be the most "
    "useful next step, together with native-speaker checks of the local-language content.",
]
KEYWORDS = ("Keywords: tourism in Uganda, smart tourism, artificial intelligence, wildlife species "
            "identification, image classification, YOLOv8, progressive web app, domain shift")

ABBR = [("AI", "Artificial intelligence"), ("CNN", "Convolutional neural network"), ("dHash", "Difference hash (perceptual image fingerprint)"),
        ("EXIF", "Exchangeable image file format (camera data stored in a photo)"),
        ("GFLOPs", "Billions of floating-point operations"), ("GPU", "Graphics processing unit"),
        ("ONNX", "Open Neural Network Exchange (model file format)"), ("PWA", "Progressive web app"),
        ("UWEC", "Uganda Wildlife Conservation Education Centre, Entebbe"),
        ("WASM", "WebAssembly"), ("YOLO", "You Only Look Once (family of vision models)")]

APPENDIX = [
    ("h1", "Appendix A: Files and Reproducibility"),
    ("p", "All Part 2 material is in the folder 06_Part2_Classifier of the project repository. README.md "
     "describes the folder, DATA_NOTES.md the data, and LOG.md records every step and decision with its date. "
     "Results are in results\\v1 and results\\v2, per-run settings and curves in runs\\, and the exported model "
     "in export\\. The figures in this report were made by scripts\\make_figures.py, "
     "scripts\\make_compare_figure.py and scripts\\make_report_figures.py from the saved CSV files, and the "
     "report by report\\build_report.py. Image files are not included in the repository because most are "
     "web-sourced and must not be redistributed."),
    ("tab", "scripts", "Scripts used, in order.",
     ["Script", "Purpose"],
     [["build_manifest.py", "Inventory, source per image and label corrections"],
      ["build_cls_dataset.py", "Builds cls_v1 with leakage-safe splits, caps and near-duplicate removal"],
      ["train_cls.py, run_part2_v1.ps1", "Training runs (fixed settings)"],
      ["evaluate_cls.py", "Predictions, top-1/top-5, per-class accuracy, confusion matrices, threshold table"],
      ["make_aug_dataset.py, run_part2_v2.ps1", "v2 augmented dataset and training"],
      ["export_cls.py, check_preprocess.py", "ONNX export and preprocessing equivalence check"],
      ["make_species_json.py, make_icons.py", "App content and icons"],
      ["make_figures.py, make_compare_figure.py, make_report_figures.py", "Figures"]],
     [7.0, 8.8]),
]

# ----------------------------------------------------------------------------- docx helpers

def set_rfonts(el, name=FONT):
    rpr = el.get_or_add_rPr() if hasattr(el, "get_or_add_rPr") else el
    rf = rpr.find(qn("w:rFonts"))
    if rf is None:
        rf = OxmlElement("w:rFonts"); rpr.insert(0, rf)
    for a in ("w:asciiTheme", "w:hAnsiTheme", "w:eastAsiaTheme", "w:cstheme"):
        if rf.get(qn(a)) is not None:
            del rf.attrib[qn(a)]
    for a in ("w:ascii", "w:hAnsi", "w:eastAsia", "w:cs"):
        rf.set(qn(a), name)


def style_font(st, size, bold=None, italic=None):
    st.font.name = FONT; st.font.size = Pt(size); st.font.color.rgb = BLACK
    if bold is not None: st.font.bold = bold
    if italic is not None: st.font.italic = italic
    set_rfonts(st.element.get_or_add_rPr())


def field(par, instr, placeholder=""):
    r = par.add_run(); f = OxmlElement("w:fldChar"); f.set(qn("w:fldCharType"), "begin"); r._r.append(f)
    r = par.add_run(); t = OxmlElement("w:instrText"); t.set(qn("xml:space"), "preserve"); t.text = f" {instr} "; r._r.append(t)
    r = par.add_run(); f = OxmlElement("w:fldChar"); f.set(qn("w:fldCharType"), "separate"); r._r.append(f)
    r = par.add_run(placeholder)
    r2 = par.add_run(); f = OxmlElement("w:fldChar"); f.set(qn("w:fldCharType"), "end"); r2._r.append(f)
    return r


def fmt_par(p, align=WD_ALIGN_PARAGRAPH.JUSTIFY, before=0, after=6, spacing=1.5, keep=False):
    pf = p.paragraph_format
    pf.alignment = align; pf.space_before = Pt(before); pf.space_after = Pt(after)
    pf.line_spacing = spacing
    if keep: pf.keep_with_next = True


def cell_text(cell, text, bold=False, size=11, align=WD_ALIGN_PARAGRAPH.LEFT):
    cell.text = ""
    p = cell.paragraphs[0]; fmt_par(p, align=align, after=0, spacing=1.0)
    r = p.add_run(text); r.bold = bold; r.font.size = Pt(size); r.font.name = FONT


def set_cell_margins(table):
    tblPr = table._tbl.tblPr
    m = OxmlElement("w:tblCellMar")
    for side in ("top", "bottom"):
        e = OxmlElement(f"w:{side}"); e.set(qn("w:w"), "40"); e.set(qn("w:type"), "dxa"); m.append(e)
    for side in ("left", "right"):
        e = OxmlElement(f"w:{side}"); e.set(qn("w:w"), "80"); e.set(qn("w:type"), "dxa"); m.append(e)
    look = tblPr.find(qn("w:tblLook"))
    if look is not None:
        look.addprevious(m)
    else:
        tblPr.append(m)


def repeat_header(row):
    trPr = row._tr.get_or_add_trPr(); h = OxmlElement("w:tblHeader"); trPr.append(h)


def caption(doc, kind, num, text):
    p = doc.add_paragraph(style="Caption")
    fmt_par(p, align=WD_ALIGN_PARAGRAPH.CENTER, before=6 if kind == "Table" else 2, after=10 if kind == "Figure" else 4,
            spacing=1.0, keep=(kind == "Table"))
    r = p.add_run(f"{kind} "); r.bold = True
    fr = field(p, f"SEQ {kind} \\* ARABIC", str(num)); fr.bold = True
    r = p.add_run(f": {text}")
    return p


def page_number_footer(section, fmt=None, start=None):
    section.footer.is_linked_to_previous = False
    p = section.footer.paragraphs[0]; p.text = ""; p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = field(p, "PAGE", "1"); r.font.name = FONT; r.font.size = Pt(12)
    sp = section._sectPr
    for old in sp.findall(qn("w:pgNumType")):
        sp.remove(old)
    pg = OxmlElement("w:pgNumType")
    if fmt: pg.set(qn("w:fmt"), fmt)
    if start is not None: pg.set(qn("w:start"), str(start))
    # schema order: ... pgMar, paperSrc, pgBorders, lnNumType, pgNumType, cols, ...
    anchor = next((sp.find(qn(t)) for t in ("w:cols", "w:formProt", "w:vAlign", "w:noEndnote", "w:titlePg",
                                             "w:textDirection", "w:bidi", "w:rtlGutter", "w:docGrid")
                   if sp.find(qn(t)) is not None), None)
    if anchor is not None:
        anchor.addprevious(pg)
    else:
        sp.append(pg)


def margins(section):
    section.top_margin = section.bottom_margin = Cm(2.54)
    section.left_margin = Cm(3.0); section.right_margin = Cm(2.54)


# ----------------------------------------------------------------------------- build

def main():
    # numbering pass
    fnum, tnum = {}, {}
    for it in C + APPENDIX:
        if it[0] == "fig": fnum[it[1]] = len(fnum) + 1
        if it[0] == "tab": tnum[it[1]] = len(tnum) + 1

    # citation numbers in order of first appearance
    order = []
    for it in C + APPENDIX:
        texts = [it[1]] if it[0] == "p" else (it[1] if it[0] in ("bul", "num") else
                 [it[2]] if it[0] == "tab" else [it[3]] if it[0] == "fig" else [])
        for t in texts:
            for grp in re.findall(r"\[(@[^\]]+)\]", t):
                for k in grp.split(","):
                    k = k.strip()[1:]
                    if k not in REFS:
                        raise KeyError(k)
                    if k not in order:
                        order.append(k)
    cnum = {k: i + 1 for i, k in enumerate(order)}

    def cite(m):
        ns = sorted(cnum[k.strip()[1:]] for k in m.group(1).split(","))
        out, i = [], 0
        while i < len(ns):
            j = i
            while j + 1 < len(ns) and ns[j + 1] == ns[j] + 1:
                j += 1
            out.append(f"[{ns[i]}]" if j - i < 2 else f"[{ns[i]}]–[{ns[j]}]")
            if 0 < j - i < 2:
                out.extend(f"[{n}]" for n in ns[i + 1:j + 1])
            i = j + 1
        return ", ".join(out)

    def sub(text):
        text = re.sub(r"\[(@[^\]]+)\]", cite, text)
        text = re.sub(r"\{F:(\w+)\}", lambda m: f"Figure {fnum[m.group(1)]}", text)
        return re.sub(r"\{T:(\w+)\}", lambda m: f"Table {tnum[m.group(1)]}", text)

    doc = Document()
    st = doc.styles
    style_font(st["Normal"], 12)
    st["Normal"].paragraph_format.space_after = Pt(6)
    style_font(st["Heading 1"], 16, bold=True, italic=False)
    style_font(st["Heading 2"], 14, bold=True, italic=False)
    style_font(st["Heading 3"], 12, bold=True, italic=True)
    style_font(st["Caption"], 12, bold=False, italic=False)
    style_font(st["Title"], 16, bold=True)
    for name in ("Heading 1", "Heading 2", "Heading 3"):
        pf = st[name].paragraph_format
        pf.space_before = Pt(18 if name == "Heading 1" else 12); pf.space_after = Pt(6)
        pf.keep_with_next = True; pf.alignment = WD_ALIGN_PARAGRAPH.LEFT; pf.line_spacing = 1.15
    for name in ("List Bullet", "List Number"):
        style_font(st[name], 12)

    sec = doc.sections[0]; margins(sec)

    # ---------- title page
    def tp(text, size=12, bold=False, before=0, after=0, italic=False):
        p = doc.add_paragraph(); fmt_par(p, align=WD_ALIGN_PARAGRAPH.CENTER, before=before, after=after, spacing=1.15)
        r = p.add_run(text); r.font.size = Pt(size); r.bold = bold; r.italic = italic
        return p

    tp("SOROTI UNIVERSITY", 16, True, before=24)
    tp("SCHOOL OF ENGINEERING AND TECHNOLOGY", 14, True, before=6)
    tp("DEPARTMENT OF ELECTRONICS AND COMPUTER ENGINEERING", 14, True, before=6)
    tp("Artificial Intelligence for Advancing Wildlife Tourism in Uganda:", 16, True, before=72)
    tp("UgaWildVision, an Offline Smartphone Tool for Identifying Ugandan Wildlife Species", 16, True, before=0)
    tp("Part 2 of the UgaWildlifeVision Project", 14, False, before=24)
    tp("Research Project Report", 14, False, before=6)
    tp("Submitted by:", 12, True, before=60, after=4)
    tp("Joseph Walusimbi          Student No. 2401600068", 12)
    tp("Joanita Namuyiga           Student No. 2401600382", 12)
    tp("Programme: Bachelor of Engineering in Electronics and Computer Engineering", 12, before=18)
    tp("November 2026", 12, True, before=48)

    # ---------- front matter section (roman numbers)
    sec2 = doc.add_section(WD_SECTION.NEW_PAGE); margins(sec2)
    page_number_footer(sec2, fmt="lowerRoman", start=1)
    sec.footer.is_linked_to_previous = False
    sec.footer.paragraphs[0].text = ""

    def front_heading(text, in_toc=True):
        if not in_toc:
            p = doc.add_paragraph(); fmt_par(p, align=WD_ALIGN_PARAGRAPH.CENTER, before=18, after=6, spacing=1.15)
            r = p.add_run(text); r.bold = True; r.font.size = Pt(16)
            return p
        p = doc.add_paragraph(style="Heading 1"); p.add_run(text)
        p.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
        return p

    front_heading("Abstract")
    for t in ABSTRACT:
        p = doc.add_paragraph(t); fmt_par(p)
    p = doc.add_paragraph(); fmt_par(p); r = p.add_run(KEYWORDS); r.italic = True

    def toc_page(title, instr):
        doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)
        front_heading(title, in_toc=(title != "Table of Contents"))
        p = doc.add_paragraph(); fmt_par(p, align=WD_ALIGN_PARAGRAPH.LEFT, spacing=1.15)
        field(p, instr, "Right-click and choose Update Field.")

    toc_page("Table of Contents", 'TOC \\o "1-3" \\h \\z \\u')
    toc_page("List of Tables", 'TOC \\h \\z \\c "Table"')
    toc_page("List of Figures", 'TOC \\h \\z \\c "Figure"')
    doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)
    front_heading("List of Abbreviations")
    t = doc.add_table(rows=0, cols=2); t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for a, b in ABBR:
        row = t.add_row().cells; cell_text(row[0], a, bold=True, size=12); cell_text(row[1], b, size=12)
        row[0].width = Cm(3.0); row[1].width = Cm(12.5)

    # ---------- body section (arabic numbers)
    sec3 = doc.add_section(WD_SECTION.NEW_PAGE); margins(sec3)
    page_number_footer(sec3, fmt="decimal", start=1)

    first_h1 = True

    def render(items):
        nonlocal first_h1
        for it in items:
            k = it[0]
            if k == "h1":
                if not first_h1:
                    doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)
                first_h1 = False
                doc.add_paragraph(it[1], style="Heading 1")
            elif k == "h2":
                doc.add_paragraph(it[1], style="Heading 2")
            elif k == "h3":
                doc.add_paragraph(it[1], style="Heading 3")
            elif k == "p":
                p = doc.add_paragraph(sub(it[1])); fmt_par(p)
            elif k in ("bul", "num"):
                for x in it[1]:
                    p = doc.add_paragraph(sub(x), style="List Bullet" if k == "bul" else "List Number")
                    fmt_par(p, after=3)
            elif k == "eq":
                p = doc.add_paragraph(); fmt_par(p, align=WD_ALIGN_PARAGRAPH.LEFT, before=3, after=6)
                p.paragraph_format.left_indent = Cm(1.5)
                p.paragraph_format.tab_stops.add_tab_stop(Cm(15.4), alignment=2)  # right tab
                r = p.add_run(it[1]); r.italic = True
                p.add_run(f"\t({it[2]})")
            elif k == "tab":
                _, key, cap, header, rows, widths = it
                caption(doc, "Table", tnum[key], sub(cap))
                t = doc.add_table(rows=1, cols=len(header)); t.style = "Table Grid"
                t.alignment = WD_TABLE_ALIGNMENT.CENTER; set_cell_margins(t)
                for i, h in enumerate(header):
                    cell_text(t.rows[0].cells[i], h, bold=True)
                repeat_header(t.rows[0])
                for row in rows:
                    cells = t.add_row().cells
                    for i, v in enumerate(row):
                        cell_text(cells[i], sub(v))
                for row in t.rows:
                    for i, w in enumerate(widths):
                        row.cells[i].width = Cm(w)
                sp = doc.add_paragraph(); fmt_par(sp, after=0, spacing=1.0)
            elif k == "fig":
                _, key, path, cap, width = it
                p = doc.add_paragraph(); fmt_par(p, align=WD_ALIGN_PARAGRAPH.CENTER, before=6, after=0, spacing=1.0, keep=True)
                p.add_run().add_picture(str(path), width=Cm(width))
                caption(doc, "Figure", fnum[key], sub(cap))

    render(C)
    # references
    doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)
    doc.add_paragraph("References", style="Heading 1")
    unused = [k for k in REFS if k not in cnum]
    if unused:
        raise SystemExit(f"references never cited: {unused}")
    for i, ref in enumerate((REFS[k] for k in order), 1):
        p = doc.add_paragraph(); fmt_par(p, align=WD_ALIGN_PARAGRAPH.LEFT, after=4, spacing=1.15)
        p.paragraph_format.left_indent = Cm(1.0); p.paragraph_format.first_line_indent = Cm(-1.0)
        p.add_run(f"[{i}]\t{ref}")
        p.paragraph_format.tab_stops.add_tab_stop(Cm(1.0))
    render(APPENDIX)

    # Ask Word to refresh fields when opened (in case update_fields.ps1 is not run).
    doc.core_properties.title = "UgaWildVision Part 2 Report"
    doc.core_properties.author = "Joseph Walusimbi; Joanita Namuyiga"
    doc.save(OUT)

    intro_end = next(i for i, x in enumerate(C) if x[0] == "h1" and x[1].startswith("2."))
    intro_keys = set()
    for it in C[:intro_end]:
        texts = [it[1]] if it[0] == "p" else (it[1] if it[0] in ("bul", "num") else [])
        for t in texts:
            for grp in re.findall(r"\[(@[^\]]+)\]", t):
                intro_keys.update(k.strip()[1:] for k in grp.split(","))
    print("refs", len(REFS), "cited", len(cnum), "cited in introduction", len(intro_keys))
    print("figures", len(fnum), "tables", len(tnum), "->", OUT)


if __name__ == "__main__":
    main()
