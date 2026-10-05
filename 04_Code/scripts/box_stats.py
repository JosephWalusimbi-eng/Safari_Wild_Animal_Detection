import glob, os, collections, statistics
root = r"C:\Users\mrjos\Downloads\wildlife-yolo"
names = ["antelope","bird","chimpanzee","elephant","gorilla","hippo","hog"]
areas = collections.defaultdict(list)
vid = collections.defaultdict(lambda: [0, 1.0, 0.0])  # count, min x, max x

for f in glob.glob(root + r"\**\labels\**\*.txt", recursive=True):
    video = os.path.basename(f).split("_frame_")[0]
    for line in open(f):
        c, x, y, w, h = line.split()[:5]
        x, w = float(x), float(w)
        areas[names[int(c)]].append(w * float(h))
        v = vid[video]
        v[0] += 1; v[1] = min(v[1], x - w/2); v[2] = max(v[2], x + w/2)

print("class        n   median area   % under 0.25% of image")
for n in names:
    a = areas[n]
    print(f"{n:11s} {len(a):5d}   {100*statistics.median(a):6.2f}%     {100*sum(t < 0.0025 for t in a)/len(a):5.1f}%")

print("\nvideo          boxes   leftmost-x   rightmost-x   (all boxes inside 0.33-0.67 = pillarboxed)")
for k, v in sorted(vid.items()):
    print(f"{k:14s} {v[0]:5d}     {v[1]:.2f}         {v[2]:.2f}")
