"""build_catalog.py - photos, taxonomy and conservation status for the app's animal guide.

    python build_catalog.py --pwa <pwa folder>

For each species in pwa/model/species.json (except "other"):
  * photo: the lead image of the English Wikipedia article, kept ONLY if its Wikimedia Commons licence
    is CC0, public domain, CC BY or CC BY-SA; resized to 800 px and saved as pwa/images/<class>.jpg,
    with author, licence and source link recorded for the credits page;
  * taxonomy: class, order and family from Wikidata (parent-taxon chain), and IUCN status (P141).
Writes pwa/model/catalog.json. Training images are never used here (they may not be redistributed).
"""
import argparse, io, json, re, time
from pathlib import Path
import requests
from PIL import Image

H = {"User-Agent": "UgaWildVision-catalog/1.0 (student project)"}
TITLES = {"uganda_kob": "Kob", "bird": "Bird", "chimpanzee": "Chimpanzee", "elephant": "African bush elephant",
          "gorilla": "Mountain gorilla", "hippo": "Hippopotamus", "warthog": "Common warthog", "tiger": "Tiger",
          "leopard": "Leopard", "fox": "Fox", "frog": "Frog", "snake": "Snake", "fish": "Fish", "zebra": "Plains zebra",
          "monkey": "Vervet monkey", "crocodile": "Nile crocodile", "tortoise": "Tortoise", "giraffe": "Rothschild's giraffe",
          "rhino": "White rhinoceros", "squirrel": "Squirrel", "lion": "Lion", "buffalo": "African buffalo",
          "cheetah": "Cheetah", "kudu": "Greater kudu", "hyena": "Spotted hyena"}
CATEGORY = {"bird": "Birds", "frog": "Amphibians", "snake": "Reptiles", "crocodile": "Reptiles", "tortoise": "Reptiles",
            "fish": "Fish"}
OK_LICENCE = re.compile(r"^(CC0|Public domain|PD|CC BY(-SA)? \d|CC BY(-SA)?$)", re.I)
MANUAL_TAX = {"fox": {"class": "Mammalia", "order": "Carnivora", "family": "Canidae"},
              "snake": {"class": "Reptilia", "order": "Squamata"}}
RANKS = {"Q37517": "class", "Q36602": "order", "Q35409": "family"}


def get(url, **params):
    for i in range(4):
        try:
            r = requests.get(url, params=params, headers=H, timeout=60)
            if r.status_code == 429:
                time.sleep(15 * (i + 1)); continue
            r.raise_for_status(); return r
        except requests.RequestException:
            time.sleep(3 * (i + 1))
    raise RuntimeError(url)


def strip_html(s):
    return re.sub(r"<[^>]+>", "", s or "").strip()


def wiki_page(title):
    d = get("https://en.wikipedia.org/w/api.php", action="query", titles=title, prop="pageimages|pageprops",
            piprop="original", redirects=1, format="json").json()
    p = next(iter(d["query"]["pages"].values()))
    img = p.get("original", {}).get("source", "")
    return p.get("title"), p.get("pageprops", {}).get("wikibase_item"), img


def commons_info(img_url):
    name = "File:" + requests.utils.unquote(img_url.split("?")[0].split("/")[-1])
    d = get("https://commons.wikimedia.org/w/api.php", action="query", titles=name, prop="imageinfo",
            iiprop="url|extmetadata", iiurlwidth=800, format="json").json()
    p = next(iter(d["query"]["pages"].values()))
    if "imageinfo" not in p:
        return {"licence": "not found on Commons"}
    ii = p["imageinfo"][0]; m = ii.get("extmetadata", {})
    return {"file": name, "thumb": ii.get("thumburl") or ii["url"], "page": ii.get("descriptionurl", ""),
            "licence": strip_html(m.get("LicenseShortName", {}).get("value")),
            "licence_url": m.get("LicenseUrl", {}).get("value", ""),
            "author": strip_html(m.get("Artist", {}).get("value"))[:120]}


def taxonomy(qid):
    q = f"""SELECT ?rank ?label ?status WHERE {{
      OPTIONAL {{ wd:{qid} wdt:P141 ?s . ?s rdfs:label ?status FILTER(LANG(?status)="en") }}
      OPTIONAL {{ wd:{qid} wdt:P171* ?t . ?t wdt:P105 ?rank . ?t wdt:P225 ?label .
                 VALUES ?rank {{ wd:Q37517 wd:Q36602 wd:Q35409 }} }} }}"""
    d = get("https://query.wikidata.org/sparql", query=q, format="json").json()
    out = {}
    for b in d["results"]["bindings"]:
        if "status" in b: out["status"] = b["status"]["value"]
        if "rank" in b:
            out.setdefault(RANKS[b["rank"]["value"].split("/")[-1]], b["label"]["value"])
    return out


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--pwa", required=True); ap.add_argument("--only", default="")
    a = ap.parse_args(); only = set(filter(None, a.only.split(",")))
    pwa = Path(a.pwa); (pwa / "images").mkdir(exist_ok=True)
    species = json.loads((pwa / "model" / "species.json").read_text(encoding="utf-8"))
    cat_path = pwa / "model" / "catalog.json"
    cat = json.loads(cat_path.read_text(encoding="utf-8")) if (only and cat_path.exists()) else {}
    for cls, title in TITLES.items():
        if only and cls not in only:
            continue
        t, qid, img = wiki_page(title)
        entry = {"wikipedia": f"https://en.wikipedia.org/wiki/{t.replace(' ', '_')}", "category": CATEGORY.get(cls, "Mammals")}
        tax = taxonomy(qid) if qid else {}
        if cls == "bird":
            tax["class"] = "Aves"   # Wikidata's parent chain also passes through Reptilia
        for k, v in MANUAL_TAX.get(cls, {}).items():
            tax.setdefault(k, v)
        entry.update({k: tax.get(k, "") for k in ("class", "order", "family", "status")})
        if img and "/wikipedia/commons/" not in img:
            entry["photo"] = None; entry["photo_rejected"] = "local (possibly non-free) Wikipedia file"
        elif img:
            info = commons_info(img)
            if OK_LICENCE.match(info["licence"] or ""):
                raw = get(info["thumb"]).content
                im = Image.open(io.BytesIO(raw)).convert("RGB"); im.thumbnail((800, 800))
                im.save(pwa / "images" / f"{cls}.jpg", quality=82, optimize=True)
                entry["photo"] = {"src": f"images/{cls}.jpg", **{k: info[k] for k in ("author", "licence", "licence_url", "page")}}
            else:
                entry["photo"] = None; entry["photo_rejected"] = info["licence"]
        cat[cls] = entry
        print(f"{cls:11s} {entry['category']:10s} {entry.get('class',''):10s} {entry.get('order',''):14s} "
              f"{entry.get('family',''):16s} {entry.get('status','')[:22]:22s} "
              f"{(entry.get('photo') or {}).get('licence', 'NO PHOTO ' + entry.get('photo_rejected', ''))}")
        time.sleep(2)
    (pwa / "model" / "catalog.json").write_text(json.dumps(cat, ensure_ascii=False, indent=1), encoding="utf-8")
    print("wrote catalog.json")


if __name__ == "__main__":
    main()
