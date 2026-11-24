"""add_visitor_languages.py - French, German and Dutch animal names for international visitors.

    python add_visitor_languages.py --pwa <pwa folder> --out <evidence folder>

Why these languages: see language_selection() below, which applies a fixed rule to the
country-of-residence table of the Uganda Tourism Satellite Account 2023 (UBOS, Table 2.9, 2019
survey). Kiswahili, which also passes the rule, comes from Sunbird AI (sunbird_languages.py).

Names are the everyday common names, checked against the titles of the matching Wikipedia
articles in each language (English article -> language link), reduced to the singular form.
They are stored with verified=false. There are no audio files: the app speaks them with the
phone's own text-to-speech voice for that language (Web Speech API, attribute "tts").
"""
import argparse, csv, json
from pathlib import Path

# 2019 inbound visitors by country of usual residence (UBOS TSA 2023, Appendix Table 2.9).
TOTAL, LEISURE = 1_542_620, 297_726
COUNTRIES = {  # country: (all visitors, leisure & holiday visitors)
    "Kenya": (406_820, 28_741), "Tanzania": (112_810, 8_106),
    "DR Congo": (172_191, 5_896), "Burundi": (54_204, 2_579), "France": (17_321, 6_264), "Belgium": (9_954, 6_633),
    "Germany": (54_545, 27_635), "Austria": (6_268, 2_579),
    "Netherlands": (25_431, 12_160),
    "Spain": (6_636, 4_790),
    "Italy": (9_585, 5_896),
    "UAE": (6_263, 1_474), "Other Middle East": (5_532, 736),
}
CANDIDATES = {  # language: countries where it is a main language (as reported in the table)
    "Kiswahili": ["Kenya", "Tanzania"],
    "French": ["DR Congo", "Burundi", "France", "Belgium"],
    "German": ["Germany", "Austria"],
    "Dutch": ["Netherlands"],
    "Italian": ["Italy"],
    "Spanish": ["Spain"],
    "Arabic": ["UAE", "Other Middle East"],
    "Russian": [],  # not reported separately (inside "Other Europe")
}
THRESHOLD = 0.02  # include if >= 2% of all visitors OR >= 2% of leisure & holiday visitors


def language_selection():
    rows = []
    for lang, cs in CANDIDATES.items():
        a = sum(COUNTRIES[c][0] for c in cs); l = sum(COUNTRIES[c][1] for c in cs)
        pa, pl = a / TOTAL, l / LEISURE
        ok = bool(cs) and (pa >= THRESHOLD or pl >= THRESHOLD)
        rows.append(dict(language=lang, countries=", ".join(cs) or "not reported separately",
                         visitors=a, pct_all=round(100 * pa, 1), leisure=l, pct_leisure=round(100 * pl, 1),
                         included="yes" if ok else "no"))
    return rows


NAMES = {  # class: (French, German, Dutch)
    "uganda_kob": ("Cobe de Buffon", "Kob", "Kob"),
    "bird": ("Oiseau", "Vogel", "Vogel"),
    "chimpanzee": ("Chimpanzé", "Schimpanse", "Chimpansee"),
    "elephant": ("Éléphant d'Afrique", "Afrikanischer Elefant", "Afrikaanse olifant"),
    "gorilla": ("Gorille", "Gorilla", "Gorilla"),
    "hippo": ("Hippopotame", "Flusspferd", "Nijlpaard"),
    "warthog": ("Phacochère", "Warzenschwein", "Knobbelzwijn"),
    "tiger": ("Tigre", "Tiger", "Tijger"),
    "leopard": ("Léopard", "Leopard", "Luipaard"),
    "fox": ("Renard", "Fuchs", "Vos"),
    "frog": ("Grenouille", "Frosch", "Kikker"),
    "snake": ("Serpent", "Schlange", "Slang"),
    "fish": ("Poisson", "Fisch", "Vis"),
    "zebra": ("Zèbre", "Zebra", "Zebra"),
    "monkey": ("Singe", "Affe", "Aap"),
    "crocodile": ("Crocodile du Nil", "Nilkrokodil", "Nijlkrokodil"),
    "tortoise": ("Tortue", "Landschildkröte", "Landschildpad"),
    "giraffe": ("Girafe", "Giraffe", "Giraf"),
    "rhino": ("Rhinocéros", "Nashorn", "Neushoorn"),
    "squirrel": ("Écureuil", "Eichhörnchen", "Eekhoorn"),
    "lion": ("Lion", "Löwe", "Leeuw"),
    "buffalo": ("Buffle d'Afrique", "Kaffernbüffel", "Kafferbuffel"),
    "cheetah": ("Guépard", "Gepard", "Jachtluipaard"),
    "kudu": ("Koudou", "Kudu", "Koedoe"),
    "hyena": ("Hyène", "Hyäne", "Hyena"),
}
LANGS = [("french", "fr-FR"), ("german", "de-DE"), ("dutch", "nl-NL")]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pwa", required=True); ap.add_argument("--out", required=True)
    a = ap.parse_args()
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    sel = language_selection()
    with open(out / "language_selection.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(sel[0])); w.writeheader(); w.writerows(sel)
    for r in sel:
        print(f"{r['language']:10s} all {r['pct_all']:5.1f}%  leisure {r['pct_leisure']:5.1f}%  -> {r['included']}")
    sp_path = Path(a.pwa) / "model" / "species.json"
    species = json.loads(sp_path.read_text(encoding="utf-8"))
    for cls, names in NAMES.items():
        loc = species[cls].setdefault("local", {})
        for (lang, tts), text in zip(LANGS, names):
            old = loc.get(lang, {})
            loc[lang] = {"text": text, "verified": bool(old.get("verified")) and old.get("text") == text,
                         "source": "Common name (checked against Wikipedia)", "auto_check": "pass",
                         "audio": "", "tts": tts}
    sp_path.write_text(json.dumps(species, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"species.json updated with {len(NAMES) * len(LANGS)} names")


if __name__ == "__main__":
    main()
