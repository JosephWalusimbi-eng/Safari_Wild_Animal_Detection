"""make_species_json.py - build pwa/model/species.json: what the app shows for each class.

English facts for the 7 Part 1 classes and any local-language names come from the
species_language_table_<lang>.csv files in the working archive. A local name is shown in the
app as verified only when its row has `verified_by` filled in; otherwise it is labelled
"machine/unverified" (or "translation pending" if empty). Re-run after editing the tables.

    python make_species_json.py --tables D:\\Safari_Wild_Animal_Detection_working_archive
        --classes ..\\cls_v1\\classes.txt --out ..\\pwa\\model\\species.json
"""
import argparse, csv, json
from pathlib import Path

LANGS = ["luganda", "runyankole", "rutooro", "ateso"]
PART1_NAME = {"uganda_kob": "antelope", "warthog": "hog"}   # class -> english_class in tables
LOW_DATA = {"lion", "buffalo", "cheetah", "kudu", "hyena"}

# display name, scientific name (or group), safety note ("" if none)
INFO = {
    "uganda_kob": ("Uganda kob", "Kobus kob thomasi", ""),
    "bird": ("Bird", "Aves (many species)", ""),
    "chimpanzee": ("Chimpanzee", "Pan troglodytes", "Wild animal: keep your distance."),
    "elephant": ("African elephant", "Loxodonta africana", "Dangerous: keep a wide distance."),
    "gorilla": ("Gorilla", "Gorilla beringei (in Uganda)", "Wild animal: keep your distance."),
    "hippo": ("Hippopotamus", "Hippopotamus amphibius", "Dangerous: keep a wide distance."),
    "warthog": ("Warthog", "Phacochoerus africanus", ""),
    "tiger": ("Tiger", "Panthera tigris", "Dangerous big cat."),
    "leopard": ("Leopard", "Panthera pardus", "Dangerous big cat."),
    "fox": ("Fox", "Vulpes and related genera", ""),
    "frog": ("Frog or toad", "Anura (many species)", ""),
    "snake": ("Snake", "Serpentes (cobras, pythons, vipers)", "Do not approach: some snakes are venomous."),
    "fish": ("Fish", "many species", ""),
    "zebra": ("Zebra", "Equus quagga", ""),
    "monkey": ("Monkey", "Cercopithecidae (many species)", ""),
    "crocodile": ("Crocodile", "Crocodylus niloticus (Nile crocodile)", "Dangerous: stay away from the water's edge."),
    "tortoise": ("Tortoise", "Testudinidae", ""),
    "giraffe": ("Giraffe", "Giraffa camelopardalis", ""),
    "rhino": ("Rhinoceros", "Ceratotherium simum / Diceros bicornis", "Dangerous: keep a wide distance."),
    "squirrel": ("Squirrel", "Sciuridae (many species)", ""),
    "lion": ("Lion", "Panthera leo", "Dangerous big cat."),
    "buffalo": ("African buffalo", "Syncerus caffer", "Dangerous: keep a wide distance."),
    "cheetah": ("Cheetah", "Acinonyx jubatus", "Wild big cat."),
    "kudu": ("Kudu", "Tragelaphus spp.", ""),
    "hyena": ("Hyena", "Hyaenidae (e.g. Crocuta crocuta)", "Wild animal: keep your distance."),
    "other": ("Not one of the species I know", "", ""),
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tables", required=True); ap.add_argument("--classes", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    classes = [c.strip() for c in Path(a.classes).read_text(encoding="utf-8").split() if c.strip()]
    rows = {}
    for lang in LANGS:
        p = Path(a.tables) / f"species_language_table_{lang}.csv"
        if p.exists():
            with open(p, encoding="utf-8") as fh:
                rows[lang] = list(csv.DictReader(fh))
    out = {}
    for c in classes:
        name, sci, safety = INFO[c]
        key = PART1_NAME.get(c, c)
        facts, local = [], {}
        for lang, rs in rows.items():
            for r in rs:
                if r["english_class"] != key:
                    continue
                if r["content_type"].startswith("fact") and lang == LANGS[0]:
                    facts.append(r["english_source"])
                if r["content_type"] == "name":
                    local[lang] = dict(text=r["translated_text"].strip(),
                                       verified=bool(r["verified_by"].strip()))
        out[c] = dict(name=name, scientific=sci, safety=safety, low_data=c in LOW_DATA,
                      facts=facts, local=local)
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"wrote {a.out}: {len(out)} classes, facts for {sum(bool(v['facts']) for v in out.values())}")


if __name__ == "__main__":
    main()
