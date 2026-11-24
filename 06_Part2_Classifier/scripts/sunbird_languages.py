"""sunbird_languages.py - local-language animal names (text + audio) for the PWA, via the Sunbird AI API.

    set SUNBIRD_API_KEY=...          (optional fallbacks: SUNBIRD_API_KEY_2, SUNBIRD_API_KEY_3)
    python sunbird_languages.py --pwa <pwa folder> --out <evidence folder> [--only lion,zebra] [--no-audio]

For every species in pwa/model/species.json (except "other") and every language slot
(luganda, runyankole, rutooro, ateso, kiswahili):
  1. translate the English name with POST /tasks/translate (Sunflower model),
  2. translate the result back to English (a check, stored for the native-speaker review),
  3. synthesise the name with POST /tasks/audio/speech where Sunbird has a voice
     (Luganda lug, Runyankole nyn, Ateso teo, Kiswahili swa; Rutooro has no TTS voice yet) and save the audio
     to pwa/model/audio/<class>_<language>.<ext>.
Results go into species.json "local" with verified=false (the app shows "unverified" until a
speaker checks them) and into <out>/sunbird_names.csv. Every API answer is cached in
<out>/sunbird_cache.json, so a re-run only calls the API for what is missing.
API keys are read from the environment only and are never written to any file.
"""
import argparse, csv, json, os, re, sys, time
from pathlib import Path
import requests

BASE = "https://api.sunbird.ai"
LANGS = {"luganda": "lug", "runyankole": "nyn", "rutooro": "ttj", "ateso": "teo", "kiswahili": "swa"}
TTS_LANGS = {"lug", "nyn", "teo", "swa"}
# Automatic check: the back-translation must name the same animal (a word below), and the
# "translation" must not just be the English name again. Names that fail are kept in the CSV for
# the speaker review but are not shown in the app.
SYNONYMS = {"uganda_kob": ["kob", "antelope"], "hippo": ["hippo"], "warthog": ["warthog", "pig", "hog"],
            "tortoise": ["tortoise", "turtle"], "rhino": ["rhino"], "snake": ["snake", "serpent"],
            "kudu": ["kudu", "antelope"], "bird": ["bird"], "chimpanzee": ["chimp"], "crocodile": ["crocodile"],
            "monkey": ["monkey"], "fish": ["fish"], "frog": ["frog", "toad"]}


WIKI = {}   # class -> {wiki language code: article title}, from results/wikipedia_names.json
WIKI_LANG = {"swa": "sw", "lug": "lg"}


def norm(t):
    return re.sub(r"\s*\(.*?\)", "", t or "").strip().lower()


def auto_check(cls, english, text, back, code=""):
    words = SYNONYMS.get(cls, [w for w in english.lower().split() if w != "uganda"])
    if len(text.split()) > 4:
        return "fail: a sentence, not a name"
    if text.strip().lower() == english.strip().lower():
        return "fail: returned the English name"
    title = norm(WIKI.get(cls, {}).get(WIKI_LANG.get(code, ""), ""))
    if title and norm(text) == title:
        return "pass (matches Wikipedia article title)"
    if not any(w in back.lower() for w in words):
        return "fail: back-translation names another thing"
    return "pass"


class Client:
    def __init__(self):
        self.keys = [k for k in (os.environ.get("SUNBIRD_API_KEY"), os.environ.get("SUNBIRD_API_KEY_2"), os.environ.get("SUNBIRD_API_KEY_3")) if k]
        if not self.keys:
            sys.exit("Set SUNBIRD_API_KEY (and optionally SUNBIRD_API_KEY_2) in the environment.")
        self.i = 0

    def post(self, path, body, timeout=180):
        last = None
        for attempt in range(6):
            key = self.keys[self.i]
            try:
                r = requests.post(BASE + path, json=body, timeout=timeout,
                                  headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
            except requests.RequestException as e:
                last = str(e); time.sleep(5 * (attempt + 1)); continue
            if r.status_code in (401, 402, 403, 429) and self.i + 1 < len(self.keys):
                print(f"  key {self.i + 1} refused ({r.status_code}); switching to key {self.i + 2}")
                self.i += 1; continue
            if r.status_code == 429 or r.status_code >= 500:
                last = f"{r.status_code} {r.text[:200]}"; time.sleep(10 * (attempt + 1)); continue
            if r.status_code != 200:
                raise RuntimeError(f"{path} -> {r.status_code}: {r.text[:300]}")
            return r.json()
        raise RuntimeError(f"{path} failed after retries: {last}")


def translate(cl, text, src, tgt):
    d = cl.post("/tasks/translate", {"source_language": src, "target_language": tgt, "text": text})
    out = d.get("output") or {}
    t = out.get("translated_text") or out.get("text")
    if not t:
        raise RuntimeError(f"no translation in answer: {json.dumps(d)[:300]}")
    return t.strip().strip(".").strip()


def speech(cl, text, lang):
    d = cl.post("/tasks/audio/speech", {"text": text, "language": lang, "response_mode": "url"})
    return d["audio_url"], d.get("voice"), d.get("duration_seconds")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pwa", required=True); ap.add_argument("--out", required=True)
    ap.add_argument("--only", default=""); ap.add_argument("--no-audio", action="store_true")
    ap.add_argument("--wiki", default=str(Path(__file__).resolve().parent.parent / "results" / "wikipedia_names.json"))
    a = ap.parse_args()
    if Path(a.wiki).exists():
        WIKI.update(json.loads(Path(a.wiki).read_text(encoding="utf-8")))
    pwa, out = Path(a.pwa), Path(a.out); out.mkdir(parents=True, exist_ok=True)
    sp_path = pwa / "model" / "species.json"
    species = json.loads(sp_path.read_text(encoding="utf-8"))
    audio_dir = pwa / "model" / "audio"; audio_dir.mkdir(exist_ok=True)
    cache_path = out / "sunbird_cache.json"
    cache = json.loads(cache_path.read_text(encoding="utf-8")) if cache_path.exists() else {}
    only = set(filter(None, a.only.split(",")))
    cl = Client()

    def save_cache():
        cache_path.write_text(json.dumps(cache, ensure_ascii=False, indent=1), encoding="utf-8")

    rows = []
    for cls, info in species.items():
        if cls == "other" or (only and cls not in only):
            continue
        name = info["name"]
        info.setdefault("local", {})
        for lang, code in LANGS.items():
            key = f"{cls}|{code}"
            c = cache.get(key, {})
            if "text" not in c:
                c["text"] = translate(cl, name, "eng", code); cache[key] = c; save_cache()
            if "back" not in c:
                c["back"] = translate(cl, c["text"], code, "eng"); cache[key] = c; save_cache()
            check = auto_check(cls, name, c["text"], c["back"], code)
            audio_file = ""
            if code in TTS_LANGS and not a.no_audio and check.startswith("pass"):
                if "audio_file" not in c:
                    url, voice, dur = speech(cl, c["text"], code)
                    r = requests.get(url, timeout=120); r.raise_for_status()
                    ext = ".wav" if "wav" in r.headers.get("Content-Type", "") or url.split("?")[0].endswith(".wav") else ".mp3"
                    if url.split("?")[0].endswith(".ogg"): ext = ".ogg"
                    fn = f"{cls}_{lang}{ext}"
                    (audio_dir / fn).write_bytes(r.content)
                    c.update(audio_file=fn, voice=voice, duration=dur); cache[key] = c; save_cache()
                audio_file = c["audio_file"]
            old = info["local"].get(lang, {})
            info["local"][lang] = {
                "text": c["text"],
                "verified": bool(old.get("verified")) and old.get("text") == c["text"],
                "auto_check": check,
                "source": "Sunbird AI (machine translation)",
                "back_translation": c["back"],
                "audio": f"model/audio/{audio_file}" if audio_file else "",
            }
            rows.append([cls, name, lang, code, c["text"], c["back"], check, audio_file, c.get("voice", ""), "no"])
            print(f"{cls:12s} {lang:11s} {c['text']!r:30s} back: {c['back']!r}{'  [audio]' if audio_file else ''}  {check}")
        sp_path.write_text(json.dumps(species, ensure_ascii=False, indent=1), encoding="utf-8")

    with open(out / "sunbird_names.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["class", "english", "language", "iso", "translated", "back_translation", "auto_check", "audio_file", "voice", "verified_by_speaker"])
        w.writerows(rows)
    print(f"done: {len(rows)} names; species.json updated; audio in {audio_dir}")


if __name__ == "__main__":
    main()
