import glob, os, collections, statistics, cv2
root = r"C:\Users\mrjos\Downloads\wildlife-yolo"
stats = collections.defaultdict(lambda: {"imgs":0, "pillar":0, "chimp":[], })

def sharp(g):  # mean absolute gradient
    return (abs(cv2.Sobel(g, cv2.CV_32F, 1, 0)).mean() + abs(cv2.Sobel(g, cv2.CV_32F, 0, 1)).mean())

for img in glob.glob(root + r"\images\**\*.*", recursive=True):
    if not img.lower().endswith((".jpg", ".jpeg", ".png")): continue
    parts = img.split(os.sep)
    split = parts[parts.index("images") + 1]
    video = os.path.basename(img).split("_frame_")[0]
    g = cv2.imread(img, cv2.IMREAD_GRAYSCALE)
    if g is None: continue
    g = cv2.resize(g, (480, 270))
    left, mid = g[:, :int(480*0.28)], g[:, int(480*0.40):int(480*0.60)]
    pillar = sharp(left) < 0.35 * sharp(mid)
    s = stats[(video, split)]
    s["imgs"] += 1; s["pillar"] += pillar
    lbl = img.replace(os.sep + "images" + os.sep, os.sep + "labels" + os.sep).rsplit(".", 1)[0] + ".txt"
    if os.path.exists(lbl):
        for line in open(lbl):
            c, x, y, w, h = line.split()[:5]
            if c == "2": s["chimp"].append(float(w) * float(h))

print("video          split   imgs  %pillarboxed  chimp_boxes  chimp_median_area")
for (v, sp), s in sorted(stats.items()):
    med = f"{100*statistics.median(s['chimp']):.2f}%" if s["chimp"] else "-"
    print(f"{v:14s} {sp:6s} {s['imgs']:5d}  {100*s['pillar']/s['imgs']:8.0f}%  {len(s['chimp']):10d}  {med:>10s}")
