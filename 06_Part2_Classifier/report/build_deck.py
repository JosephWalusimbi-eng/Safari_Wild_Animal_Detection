"""build_deck.py - fills the 12-slide presentation from the old template (Walusimbi_Namuyiga.pptx).

    python build_deck.py <stage1.pptx (template with slides duplicated and ordered)> <img folder> <out.pptx>

Text is written into the template's own runs so its fonts, sizes and colours are kept.
"""
import copy, sys
from pathlib import Path
from PIL import Image
from pptx import Presentation
from pptx.chart.data import CategoryChartData
from pptx.oxml.ns import qn
from pptx.util import Emu

src, IMG, out = sys.argv[1], Path(sys.argv[2]), sys.argv[3]
prs = Presentation(src)
S = list(prs.slides)


def shp(slide, name):
    for s in slide.shapes:
        if s.name == name:
            return s
    raise KeyError(name)


def fill(shape, paras):
    """paras: list of paragraphs; each is a str or a list of (text, bold) segments.
    Paragraph i copies the formatting of template paragraph min(i, n-1); segment j copies run j."""
    txb = shape.text_frame._txBody
    tpl = [p for p in txb.findall(qn("a:p"))]
    tpl_runs = [p.findall(qn("a:r")) for p in tpl]
    for p in tpl:
        txb.remove(p)
    for i, para in enumerate(paras):
        k = min(i, len(tpl) - 1)
        # prefer a template paragraph that actually has runs
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
            if end is not None:
                end.addprevious(r)
            else:
                p.append(r)
        txb.append(p)


def put_image(slide, pic_name, path, mode="fit", frame_name=None):
    """Replace a picture's image. mode='fill' crops to the frame; 'fit' keeps the whole image and
    shrinks the frame (and its decorative border shape) to the image's aspect, centred."""
    pic = shp(slide, pic_name)
    part, rid = slide.part.get_or_add_image_part(str(path))
    pic._element.blipFill.find(qn("a:blip")).set(qn("r:embed"), rid)
    iw, ih = Image.open(path).size
    L, T, W, H = pic.left, pic.top, pic.width, pic.height
    pic.crop_left = pic.crop_right = pic.crop_top = pic.crop_bottom = 0
    if mode == "fill":
        a_img, a_box = iw / ih, W / H
        if a_img > a_box:
            c = (1 - a_box / a_img) / 2; pic.crop_left = pic.crop_right = c
        else:
            c = (1 - a_img / a_box) / 2; pic.crop_top = pic.crop_bottom = c
        return
    if iw / ih > W / H:
        nw, nh = W, int(W * ih / iw)
    else:
        nw, nh = int(H * iw / ih), H
    pic.left, pic.top, pic.width, pic.height = Emu(L + (W - nw) // 2), Emu(T + (H - nh) // 2), Emu(nw), Emu(nh)
    if frame_name:
        f = shp(slide, frame_name)
        f.left, f.top, f.width, f.height = pic.left, pic.top, pic.width, pic.height


def add_picture_like(slide, pic_name, path, top, height):
    """Second picture under an existing one, same width, fitted."""
    ref = shp(slide, pic_name)
    iw, ih = Image.open(path).size
    w = ref.width; h = int(w * ih / iw)
    if h > height:
        h = height; w = int(h * iw / ih)
    return slide.shapes.add_picture(str(path), Emu(ref.left + (ref.width - w) // 2), Emu(top), Emu(w), Emu(h))


def chart(slide, cats, vals, fmt="0", vmax=None):
    ch = shp(slide, "Chart 0").chart
    cd = CategoryChartData(number_format=fmt)
    cd.categories = cats
    cd.add_series("Value", vals)
    ch.replace_data(cd)
    ax = ch.value_axis
    ax.maximum_scale = vmax; ax.minimum_scale = 0
    dl = ch.plots[0].data_labels
    dl.number_format = fmt; dl.number_format_is_linked = False
    for ser in ch.plots[0].series:          # the template also formats labels on the series itself
        sdl = ser._element.find(qn("c:dLbls"))
        if sdl is not None:
            nf = sdl.find(qn("c:numFmt"))
            if nf is not None:
                nf.set("formatCode", fmt); nf.set("sourceLinked", "0")


def notes(slide, text):
    tf = slide.notes_slide.notes_text_frame
    if tf is None:   # this notes page has no body placeholder: copy one from a slide whose notes work
        donor = next(sl.notes_slide.notes_placeholder for sl in S
                     if sl.has_notes_slide and sl.notes_slide.notes_placeholder is not None)
        slide.notes_slide.shapes._spTree.append(copy.deepcopy(donor._element))
        tf = slide.notes_slide.notes_text_frame
    tf.text = text


# ---------------- 1 Title
s = S[0]
fill(shp(s, "Text 3"), ["UGAWILDVISION · PART 2"])
fill(shp(s, "Text 4"), ["AI for Advancing Wildlife Tourism in Uganda"])
fill(shp(s, "Text 5"), ["An offline smartphone field guide that identifies animals and speaks their names"])
shp(s, "Text 5").top = Emu(2926080)
fill(shp(s, "Text 6"), [[("Joseph Walusimbi ", True), ("2401600068", False)], "",
                        [("Joanita Namuyiga", True)], [("2401600382", False)]])
put_image(s, "Image 0", IMG / "uwec_tiger.jpg", "fill")
put_image(s, "Image 1", IMG / "uwec_cheetah.jpg", "fill")
notes(s, "Our project uses artificial intelligence to support wildlife tourism in Uganda. UgaWildVision is a free "
         "phone app: a visitor photographs an animal and the app names it, gives facts and safety notes, and says "
         "its name in Ugandan and visitor languages, all offline. The photos on this slide were taken by our team "
         "at the Uganda Wildlife Conservation Education Centre (UWEC), Entebbe.")

# ---------------- 2 Abstract
s = S[1]
fill(shp(s, "Text 0"), ["Abstract"])
fill(shp(s, "Text 3"), ["The need"])
fill(shp(s, "Text 4"), ["Tourism earned US$1.28 bn in 2024; visitors lack guides and local-language information"])
fill(shp(s, "Text 7"), ["What we built"])
fill(shp(s, "Text 8"), ["A 5.9 MB AI model in an offline phone app: 25 animals, facts, names in 9 languages"])
fill(shp(s, "Text 11"), ["What we found"])
fill(shp(s, "Text 12"), ["91% correct on standard tests, 19% on real visitor photos: real photos are the gap"])
put_image(s, "Annotated antelope frame", IMG / "app_grid_crop.png", "fit", "Annotated antelope frame frame")
fill(shp(s, "Text 15"), [[("Why it matters", True)],
                         [("A free digital guide for 1.37 million yearly visitors, even without a network", None)]])
notes(s, "In one minute: Uganda's tourism depends on wildlife, but visitors often have no guide and no information "
         "in their language. We built an AI field guide that runs on the phone. It works well on standard test images "
         "but only about one time in five on real visitor photos, and we show why and how to fix it.")

# ---------------- 3 Tourism in Uganda (introduction)
s = S[2]
fill(shp(s, "Text 0"), ["Tourism in Uganda"])
for (big, small, b, t) in [("1.37M", "visitors in 2024", "Text 2", "Text 3"), ("$1.28B", "earned in 2024", "Text 5", "Text 6"),
                           ("876,512", "direct jobs", "Text 8", "Text 9"), ("28%", "use the internet", "Text 11", "Text 12")]:
    fill(shp(s, b), [big]); fill(shp(s, t), [small])
chart(s, ["Kiswahili", "French", "German", "Dutch", "Arabic", "Italian", "Spanish"],
      [33.7, 16.4, 3.9, 1.6, 0.8, 0.6, 0.4], "0.0", 40)
fill(shp(s, "Text 13"), [[("The problem", True)], "Guiding is uneven and few guides know local animal names",
                         "Weak network in parks: a tool must work offline"])
fill(shp(s, "Text 14"), ["Visitors by language of home country, % of 2019 arrivals (UBOS)"])
notes(s, "Sources: Ministry of Tourism 2024 figures (1,371,895 visitors, USD 1.28 billion); Tourism Satellite Account "
         "(876,512 direct jobs); DataReportal 2025 (28% internet use). The chart is how we chose the visitor languages: "
         "a language is included if its countries send at least 2% of all visitors or of holiday visitors. Kiswahili, "
         "French, German and Dutch pass; Arabic, Italian and Spanish do not; Russia is not reported separately.")

# ---------------- 4 How AI helps
s = S[3]
fill(shp(s, "Text 0"), ["How AI helps"])
fill(shp(s, "Text 2"), ["What UgaWildVision does"])
fill(shp(s, "Text 3"), ["Photo in, species name out, in under a second on the phone",
                        "Facts, safety notes and conservation status for 25 animals",
                        "Works offline; photos never leave the phone",
                        "Install from a QR code; keep a log of sightings"])
fill(shp(s, "Text 5"), ["Names in 9 languages"])
fill(shp(s, "Text 6"), ["Chosen from visitor statistics; audio from Sunbird AI or the phone's own voice"])
langs = ["English", "Luganda", "Runyankole", "Rutooro", "Ateso", "Kiswahili", "French", "German", "Dutch"]
pill_pairs = [("Class pill gorilla", "Text 8"), ("Class pill chimpanzee", "Text 10"), ("Class pill hippo", "Text 12"),
              ("Class pill hog", "Text 14"), ("Class pill bird", "Text 16"), ("Class pill antelope", "Text 18"),
              ("Class pill elephant", "Text 20")]
spTree = s.shapes._spTree
pairs = [(shp(s, a), shp(s, b)) for a, b in pill_pairs]
while len(pairs) < len(langs):           # clone the last pill for the extra languages
    a, b = pairs[-1]
    na, nb = copy.deepcopy(a._element), copy.deepcopy(b._element)
    spTree.append(na); spTree.append(nb)
    pairs.append((s.shapes[-2], s.shapes[-1]))
x0, xmax, y, gap = 6583680, 11430000, 3794760, 137160
x = x0
for (pill, txt), lang in zip(pairs, langs):
    w = int(len(lang) * 128016 + 420000)
    if x + w > xmax:
        x = x0; y += 640080
    for e in (pill, txt):
        e.left, e.top, e.width, e.height = Emu(x), Emu(y), Emu(w), Emu(548640)
    fill(txt, [lang])
    x += w + gap
notes(s, "AI here means an image-classification model that runs inside the browser on the phone. The app adds a field "
         "guide around it: photos, facts, IUCN status, safety notes and names in Ugandan and visitor languages.")

# ---------------- 5 Methodology
s = S[4]
fill(shp(s, "Text 0"), ["Methodology"])
fill(shp(s, "Text 1"), [[("Data  ", True), ("Part 1 park video crops plus 5,187 Entebbe images; source of every image recorded", False)]])
fill(shp(s, "Text 2"), [[("Labels  ", True), ("Mislabelled folders fixed; 26 classes; split by session or photo group", False)]])
fill(shp(s, "Text 3"), [[("Model  ", True), ("YOLOv8n-cls, 1.47 M parameters, ImageNet-pretrained, fine-tuned", False)]])
fill(shp(s, "Text 4"), [[("App  ", True), ("ONNX model in an offline web app; names from Sunbird AI; facts and photos", False)]])
for nm in ("Text 1", "Text 2", "Text 3", "Text 4"):
    shp(s, nm).width = Emu(5943600)
pic = shp(s, "Annotated chimpanzee frame")
pic.left, pic.top, pic.width, pic.height = Emu(6675120), Emu(1417320), Emu(5212080), Emu(3657600)
put_image(s, "Annotated chimpanzee frame", IMG / "fig_pipeline.png", "fit", "Annotated chimpanzee frame frame")
cap = shp(s, "Text 6"); cap.left, cap.width = Emu(6675120), Emu(5212080); cap.top = Emu(pic.top + pic.height + 91440)
fill(shp(s, "Text 6"), ["From data sources to the phone app"])
notes(s, "Only 47 of the Entebbe images are our own phone photos from UWEC; the rest come from public image "
         "collections, so we used them for training only and kept our own 47 photos as the real-world test.")

# ---------------- 6 Experimental setup
s = S[5]
fill(shp(s, "Text 0"), ["Experimental setup"])
fill(shp(s, "Text 2"), ["Data"])
fill(shp(s, "Text 3"), ["3,636 train, 553 val, 559 test", "47 UWEC visitor photos, never trained on", "Max 400 / 60 / 60 per class"])
fill(shp(s, "Text 5"), ["Training"])
fill(shp(s, "Text 6"), ["YOLOv8n-cls (3 seeds), YOLOv8s-cls (1)", "224 px, batch 64, up to 60 epochs", "AdamW, lr 0.001, cosine"])
fill(shp(s, "Text 8"), ["Metrics"])
fill(shp(s, "Text 9"), ["Top-1, top-5 and per-class accuracy", "\"Not sure\" below 0.7 confidence", "Mean ± SD over seeds"])
fill(shp(s, "Text 10"), ["Experiments, in order"])
for (t, a, b) in [("Text 12", "E1", "Train v1"), ("Text 14", "E2", "Pick on val"), ("Text 16", "E3", "Test + UWEC"),
                  ("Text 18", "E4", "v2 phone aug."), ("Text 20", "E5", "Export + app")]:
    fill(shp(s, t), [a, b])
notes(s, "Hardware: one NVIDIA RTX 5070 Ti; Ultralytics 8.4.171. v2 added two phone-style copies of each training image "
         "(fences, compression, blur, wider context), fixed before seeing any v2 result.")

# ---------------- 7 Results
s = S[6]
fill(shp(s, "Text 0"), ["Results"])
for (big, small, b, t) in [("0.909", "standard test accuracy", "Text 2", "Text 3"), ("0.191", "UWEC visitor photos", "Text 5", "Text 6"),
                           ("5.9 MB", "model on the phone", "Text 8", "Text 9"), ("~45 ms", "per photo, offline", "Text 11", "Text 12")]:
    fill(shp(s, b), [big]); fill(shp(s, t), [small])
chart(s, ["Zebra", "Tiger", "Crocodile", "Cheetah", "Lion", "Bird", "Chimpanzee", "Buffalo"],
      [93, 78, 33, 13, 11, 0, 0, 0], "0", 100)
fill(shp(s, "Text 13"), [[("1 in 5 on real photos", True)], "Zebra and tiger transfer well",
                         "Chimpanzee, birds and buffalo: never correct"])
fill(shp(s, "Text 14"), ["UWEC photos named correctly, % (v1, mean of 3 seeds)"])
notes(s, "Test accuracy 0.909 ± 0.007 and UWEC 0.191 ± 0.030 over three seeds. The ONNX model agrees with "
         "PyTorch on 606 of 606 images. 44 of 125 machine-translated names passed our automatic checks.")

# ---------------- 8 Results analysis
s = S[7]
fill(shp(s, "Text 0"), ["Results analysis"])
fill(shp(s, "Text 1"), [[("Gap  ", True), ("Test 0.91 vs phone photos 0.19, in every seed and both model sizes", False)]])
fill(shp(s, "Text 2"), [[("Errors  ", True), ("Chimp → monkey or gorilla; birds → frog or fish; buffalo → elephant", False)]])
fill(shp(s, "Text 3"), [[("Confidence  ", True), ("Wrong answers average 0.80 confidence, so a threshold cannot fix it", False)]])
fill(shp(s, "Text 4"), [[("Augmentation  ", True), ("Phone-style training images (v2): 0.170 vs 0.191, no gain", False)]])
for nm in ("Text 1", "Text 2", "Text 3", "Text 4"):
    shp(s, nm).width = Emu(5669280)
pic = shp(s, "Annotated chimpanzee frame")
pic.left, pic.top, pic.width, pic.height = Emu(6400800), Emu(1371600), Emu(5486400), Emu(2560320)
put_image(s, "Annotated chimpanzee frame", IMG / "test_vs_uwec.png", "fit", "Annotated chimpanzee frame frame")
second = add_picture_like(s, "Annotated chimpanzee frame", IMG / "fig_confidence.png", pic.top + pic.height + 91440, 2100000)
second.left = Emu(6400800); second.width = Emu(5486400); second.height = Emu(int(5486400 * 740 / 2000))
cap = shp(s, "Text 6"); cap.left, cap.width = Emu(6400800), Emu(5486400); cap.top = Emu(second.top + second.height + 45720)
fill(cap, ["Top: test vs UWEC per run. Bottom: confidence of right and wrong answers"])
notes(s, "The errors follow the training data: chimpanzee images come from one Part 1 video, and Part 1 birds are small "
         "egrets, unlike the owls, parrots and ostriches at UWEC.")

# ---------------- 9 Discussion
s = S[8]
fill(shp(s, "Text 0"), ["Discussion"])
fill(shp(s, "Text 3"), ["Delivery is ready"])
fill(shp(s, "Text 4"), ["Small, offline, private and free; installs from a QR code at the gate"])
fill(shp(s, "Text 7"), ["Recognition needs local photos"])
fill(shp(s, "Text 8"), ["Trained mostly on web images; visitors' phone photos look different"])
fill(shp(s, "Text 11"), ["Tourism sites can close the gap"])
fill(shp(s, "Text 12"), ["About 30 photos per animal from guides and staff would fix the main gap"])
put_image(s, "Annotated antelope frame", IMG / "app_detail_crop.png", "fit", "Annotated antelope frame frame")
fill(shp(s, "Text 15"), [[("Best use now", True)],
                         [("A guide's assistant at UWEC: facts, safety and names in 9 languages", None)]])
notes(s, "The same lesson appeared in Part 1: a normal test set overstates real-world accuracy. Because the animals at "
         "a site are the same every day, staff can collect exactly the photos the model is missing.")

# ---------------- 10 Limitations
s = S[9]
fill(shp(s, "Text 0"), ["Limitations"])
fill(shp(s, "Text 3"), ["Small real-world test"])
fill(shp(s, "Text 4"), ["47 UWEC photos covering 8 of 26 classes; 1 to 9 photos per animal"])
fill(shp(s, "Text 7"), ["Few own photos"])
fill(shp(s, "Text 8"), ["Most images came from the web and cannot be shared or published"])
fill(shp(s, "Text 11"), ["Names not yet checked"])
fill(shp(s, "Text 12"), ["Machine translation: 44 of 125 names pass our checks; speakers must verify"])
put_image(s, "Annotated antelope frame", IMG / "fig_lang_check.png", "fit", "Annotated antelope frame frame")
fill(shp(s, "Text 15"), [[("Not yet done", True)],
                         [("Trials on visitors' phones; timing on field devices", None)]])
notes(s, "Issues met during the work: a one-pixel preprocessing mismatch (fixed, now 606/606), a browser path bug, a "
         "dataset upload that timed out (rebuilt on the GPU machine), and mislabelled folders (fixed by eye).")

# ---------------- 11 Conclusion and future work
s = S[10]
fill(shp(s, "Text 0"), ["Conclusion and future work"])
fill(shp(s, "Text 2"), ["Conclusion"])
fill(shp(s, "Text 3"), ["AI can give visitors a free, offline guide", "The app works: 5.9 MB, ~45 ms, 9 languages",
                        "Real-photo accuracy (0.19) is the gap"])
fill(shp(s, "Text 5"), ["Future work"])
fill(shp(s, "Text 6"), ["30+ phone photos per animal", "Native speakers check names", "Pilot with UWEC visitors"])
fill(shp(s, "Text 8"), ["Impact"])
fill(shp(s, "Text 9"), ["Better visitor experience", "Local languages for domestic tourists", "Support for guides"])
fill(shp(s, "Text 10"), ["Roadmap"])
for (t, a, b) in [("Text 12", "1", "Collect photos"), ("Text 14", "2", "Retrain"), ("Text 16", "3", "Verify names"),
                  ("Text 18", "4", "Pilot at UWEC"), ("Text 20", "5", "National parks")]:
    fill(shp(s, t), [a, b])
notes(s, "Close on the main message: the platform is ready; the next step is data from tourism sites.")

# ---------------- 12 Thank you and references
s = S[11]
fill(shp(s, "Text 3"), [
    "Ministry of Tourism, Wildlife and Antiquities (2025). Uganda's tourism sector hits record US$1.28 billion in 2024.",
    "UBOS (2023). Uganda Tourism Satellite Account 2023.",
    "Gretzel, U., et al. (2015). Smart tourism: foundations and developments. Electronic Markets.",
    "Beery, S., Van Horn, G., & Perona, P. (2018). Recognition in Terra Incognita. ECCV.",
    "Jocher, G., Chaurasia, A., & Qiu, J. (2023). Ultralytics YOLOv8.",
    "Sunbird AI (2026). Translation and speech API for Ugandan languages. sunbird.ai",
    "Walusimbi, J., Babirye, A., & Sserwadda, A. (2026). UgaWildlifeVision Dataset. Zenodo, doi:10.5281/zenodo.23171670",
    "Photos: our team at UWEC; app photos from Wikimedia Commons (credited in the app).",
])
notes(s, "Thank the audience and invite them to scan the QR code on the app's install page.")

prs.save(out)
print("saved", out)
