"""update_downloads_deck.py - updates the owner's end-of-semester deck for an 8-minute talk.

    python update_downloads_deck.py <deck_with_new_slide.pptx> <figures folder> <out.pptx>

The owner's own edits are kept: text is only changed on the slides listed below. Slide order afterwards:
1 Title, 2 Abstract, 3 Tourism, 4 How AI helps, 5 Methodology, 6 Experimental setup, 7 Results,
8 Results analysis (new), 9 Discussion, 10 Limitations, 11 Conclusion, 12 Thank you.
"""
import copy, sys
from pathlib import Path
from PIL import Image
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.oxml.ns import qn
from pptx.util import Emu, Pt

src, FIG, out = sys.argv[1], Path(sys.argv[2]), sys.argv[3]
prs = Presentation(src)
S = list(prs.slides)
assert len(S) == 12, len(S)


def shp(slide, name):
    for s in slide.shapes:
        if s.name == name:
            return s
    raise KeyError(name)


def fill(shape, paras):
    """paras: list of str, or list of [(text, bold), ...]; copies the template paragraph / run formatting."""
    txb = shape.text_frame._txBody
    tpl = list(txb.findall(qn("a:p")))
    tpl_runs = [p.findall(qn("a:r")) for p in tpl]
    for p in tpl:
        txb.remove(p)
    for i, para in enumerate(paras):
        k = min(i, len(tpl) - 1)
        while k > 0 and not tpl_runs[k]:
            k -= 1
        p = copy.deepcopy(tpl[k])
        for r in p.findall(qn("a:r")) + p.findall(qn("a:br")) + p.findall(qn("a:fld")):
            p.remove(r)
        end = p.find(qn("a:endParaRPr"))
        segs = [(para, None)] if isinstance(para, str) else para
        for j, (text, bold) in enumerate(segs):
            runs = tpl_runs[k] or [r for rs in tpl_runs for r in rs][:1]
            r = copy.deepcopy(runs[min(j, len(runs) - 1)])
            r.find(qn("a:t")).text = text
            rpr = r.find(qn("a:rPr"))
            if bold is not None and rpr is not None:
                rpr.set("b", "1" if bold else "0")
            (end.addprevious(r) if end is not None else p.append(r))
        txb.append(p)


def size(shape, pt):
    for p in shape.text_frame.paragraphs:
        for r in p.runs:
            r.font.size = Pt(pt)


def place(shape, x, y, w, h):
    shape.left, shape.top, shape.width, shape.height = Emu(x), Emu(y), Emu(w), Emu(h)


def remove(shape):
    el = shape._element; el.getparent().remove(el)


def picture(slide, path, x, y, w):
    iw, ih = Image.open(path).size
    return slide.shapes.add_picture(str(path), Emu(x), Emu(y), Emu(w), Emu(int(w * ih / iw)))


def caption(slide, text, x, y, w, pt=11):
    tb = slide.shapes.add_textbox(Emu(x), Emu(y), Emu(w), Emu(300000))
    tb.text_frame.word_wrap = True
    r = tb.text_frame.paragraphs[0].add_run(); r.text = text
    r.font.size = Pt(pt); r.font.italic = True; r.font.color.rgb = RGBColor(0xC8, 0xD2, 0xBE)
    return tb


def note(slide, timing, text=None):
    """Put the time budget at the start of the speaker notes; replace the notes if text is given."""
    ns = slide.notes_slide
    tf = ns.notes_text_frame
    if tf is None:
        donor = next(s.notes_slide.notes_placeholder for s in S if s.has_notes_slide and s.notes_slide.notes_placeholder is not None)
        ns.shapes._spTree.append(copy.deepcopy(donor._element)); tf = ns.notes_text_frame
    old = tf.text if tf.text else ""
    if old.startswith("[TIME"):
        old = old.split("\n", 1)[1] if "\n" in old else ""
    tf.text = f"[TIME {timing}]\n" + (text if text is not None else old)


# ---- 1 Title
note(S[0], "0:15")

# ---- 2 Abstract: the third card says what works and what does not
fill(shp(S[1], "Text 12"), ["91% on standard tests; 19% on our own UWEC photos, so we need more varied photos"])
note(S[1], "0:30")

# ---- 3 Tourism, 4 How AI helps
note(S[2], "0:50")
note(S[3], "0:40")

# ---- 5 Methodology: three sources, shown with a diagram
s = S[4]
fill(shp(s, "Text 1"), [[("Data  ", True), ("NESTLER Safari crops, internet images (images.cv, iNaturalist, other websites) and our own 47 UWEC photos", False)]])
fill(shp(s, "Text 2"), [[("Labels  ", True), ("Source of every image recorded; mislabelled folders fixed; 26 classes", False)]])
for nm in ("Text 1", "Text 2", "Text 3", "Text 4"):
    shp(s, nm).width = Emu(5800000)
shp(s, "Text 2").top = Emu(2950000)
shp(s, "Text 3").top = Emu(4050000)
shp(s, "Text 4").top = Emu(5100000)
picture(s, FIG / "fig_sources_slide.png", 6650000, 1500000, 5100000)
note(s, "0:45", "Three sources feed the model. (1) The NESTLER Safari video dataset: crops of animals from video filmed in Kibale, Queen Elizabeth and Bwindi Impenetrable National Parks, February to June 2025. "
                "(2) Internet images, which means images.cv (ready-made sets of tiger, leopard and fox), iNaturalist (1,016 photos from 603 observations) and 194 pictures saved from other websites. They cover the other species. "
                "(3) Our own 47 phone photos taken at UWEC in Entebbe. The NESTLER and internet images are used for training, "
                "validation and testing. Our own photos are kept as the final real-world test, because they look most like what a "
                "visitor takes. All three help the model, and the next slide shows the numbers.")

# ---- 6 Experimental setup: dataset size, make-up, splits, and what validation is for
s = S[5]
for nm in ("Data split card", "Text 2", "Text 3"):
    remove(shp(s, nm))
picture(s, FIG / "fig_dataset_split.png", 450000, 1380000, 5900000)
place(shp(s, "Models card"), 6500000, 1420000, 5150000, 2020000)
place(shp(s, "Text 5"), 6680000, 1480000, 4800000, 430000)
fill(shp(s, "Text 5"), ["Why validation matters"])
place(shp(s, "Text 6"), 6680000, 1930000, 4800000, 1450000)
fill(shp(s, "Text 6"), ["Picks the best epoch and the best run, and tells training when to stop",
                        "Keeps both test sets untouched, so the scores stay fair",
                        "Limit: it looks like the training data, so it cannot predict the UWEC result"])
size(shp(s, "Text 6"), 14)
place(shp(s, "Metrics card"), 6500000, 3540000, 5150000, 1230000)
place(shp(s, "Text 8"), 6680000, 3580000, 4800000, 400000)
fill(shp(s, "Text 8"), ["Training and metrics"])
place(shp(s, "Text 9"), 6680000, 3980000, 4800000, 780000)
fill(shp(s, "Text 9"), ["YOLOv8n-cls (3 seeds), YOLOv8s-cls, 224 px, AdamW",
                        "Top-1 and top-5; 'not sure' below 0.7; mean ± SD"])
size(shp(s, "Text 9"), 14)
note(s, "0:55", "Total: 4,795 images. Make-up: 2,312 NESTLER Safari crops, 1,284 images.cv, 972 iNaturalist, 180 other websites, "
                "and our own 47 UWEC photos. Splits: 3,636 training (77%), 553 validation (12%), 559 test (12%), plus the 47 UWEC photos "
                "as a separate real-world test. Validation is used to pick the best epoch and run and to stop training, so we never choose "
                "a model by looking at the test sets. That matters because the real-world test has only 47 photos; if we tuned on them the "
                "0.191 result would not be a fair measure. Limit: validation comes from the same sources as training (about 0.90 for every "
                "run), while the UWEC score moved between 0.15 and 0.23, so validation cannot predict real phone-photo accuracy. "
                "Hardware: one NVIDIA RTX 5070 Ti. v2 added two phone-style copies of each training image, planned before seeing results.")

# ---- 7 Results
s = S[6]
fill(shp(s, "Text 13"), ["1 in 5 on real photos", "Zebra and tiger work well",
                         "Chimpanzee, birds, buffalo: never correct; need more varied photos"])
note(s, "0:50")

# ---- 8 Results analysis (new slide, a copy of Methodology)
s = S[7]
fill(shp(s, "Text 0"), ["Results analysis"])
fill(shp(s, "Text 1"), [[("Gap  ", True), ("Test 0.91 vs our UWEC photos 0.19, in every seed and both model sizes", False)]])
fill(shp(s, "Text 2"), [[("Errors  ", True), ("Chimpanzee: monkey or gorilla; birds: frog or fish; buffalo: elephant", False)]])
fill(shp(s, "Text 3"), [[("Confidence  ", True), ("Wrong answers average 0.80 confidence, so a threshold cannot fix it", False)]])
fill(shp(s, "Text 4"), [[("Augmentation  ", True), ("Phone-style training images (v2): 0.170 vs 0.191, no gain", False)]])
for nm in ("Text 1", "Text 2", "Text 3", "Text 4"):
    shp(s, nm).width = Emu(5700000)
for sh in list(s.shapes):
    if sh.shape_type == 13:        # remove any picture copied from the template slide
        remove(sh)
W_ = 4500000
p1 = picture(s, FIG / "../../results/v1/figures/test_vs_uwec.png", 6900000, 1370000, W_)
p2 = picture(s, FIG / "fig_confidence.png", 6900000, 1370000 + p1.height + 70000, W_)
caption(s, "Top: test vs UWEC per run. Bottom: confidence of right and wrong answers", 6900000, p2.top + p2.height + 10000, W_, 10)
note(s, "0:50", "The gap is the same in every run, so it comes from the data. The errors follow the training data: our chimpanzee images "
                "come almost entirely from one video, the NESTLER birds are small egrets while UWEC has owls, parrots and ostriches, and "
                "buffalo had one training image. The bottom chart shows wrong answers are still about 80% confident on phone photos. "
                "Phone-style augmentation did not help: you cannot invent variety the data does not have. Balance: the model does well "
                "where training photos are varied, such as zebra and tiger, and needs more varied photos elsewhere.")

# ---- 9 Discussion, 10 Limitations, 11 Conclusion
note(S[8], "0:35")
note(S[9], "0:30", "Our real-world test is small: 47 photos covering 8 of 26 animals. Most of our images are not visitor-style photos. "
                   "Translations: 44 of 125 machine-translated names passed our automatic check and native speakers still need to confirm them. "
                   "We have not tried the app with visitors or on many phones.")
note(S[10], "0:40")

# ---- 12 Thank you: references, the dataset, and a QR code to try the app
s = S[11]
refs = [p.text for p in shp(s, "Text 3").text_frame.paragraphs if p.text.strip()]
nestler = "NESTLER Wild Animal Recognition Video Dataset (2025). Zenodo, doi:10.5281/zenodo.17036940"
k = next(i for i, t in enumerate(refs) if t.startswith("Jocher"))
refs.insert(k + 1, nestler)
fill(shp(s, "Text 3"), refs)
shp(s, "Text 3").width = Emu(8300000)
size(shp(s, "Text 3"), 14)
picture(s, FIG / "app_qr.png", 9300000, 2150000, 2250000)
caption(s, "Scan to try the app", 9300000, 4450000, 2250000, 14)
note(s, "0:15", "Thank the audience and invite them to scan the QR code to try the app. Then take questions.")

prs.save(out)
print("saved", out)
