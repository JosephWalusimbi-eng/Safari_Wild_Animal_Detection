# Next steps (not done yet)

## 1. Local-language species-name table (stretch goal from the proposal, Section 6.6)

**Goal.** Show each detected animal's name in a Ugandan language, so rangers and
community members can read the output. This is a lookup, not a translation model:
the detector outputs one of seven class names, and a small static table maps it
to the name in the chosen language.

**Status: not started. It is blocked on two things only you can provide:**
1. **A Sunbird AI API key.** Sign up at https://sunbird.ai (as the proposal says)
   and create a key. Keep it out of the code and out of the report: store it in an
   environment variable (for example `SUNBIRD_API_KEY`). Check the current API
   documentation for the exact endpoint and request format before writing the
   script; the proposal names a translate endpoint (`/tasks/translate`), but I have
   not verified it against the live documentation.
2. **People who speak the languages,** to check the terms. The proposal asks for
   native or fluent speakers for Luganda and for the languages spoken around the
   source parks: Runyankole, Rukiga, Rutooro and Runyoro.

**Plan (about half a day of work once the key is available):**
1. Languages: English plus Luganda and the four western languages above as the
   minimum; the proposal's full target is every Ugandan language the service
   supports (30 listed there).
2. Generate: one request per (class, language). Seven classes by 5 languages is
   35 requests for the minimum set; 7 by 30 = 210 for the full set. Class names
   to translate: antelope (the animal is the Uganda kob, so also try "kob"),
   bird, chimpanzee, elephant, gorilla, hippo (hippopotamus), hog (warthog).
3. Store as CSV or JSON with columns `class_name, language_code, translated_term,
   source, verified` (verified = false until a speaker confirms it).
4. Automatic sanity check: translate each result back to English and flag any entry
   that does not return the original word. Single words out of context often go wrong
   (a language with no word for "gorilla" may return a general word for ape).
5. Human check: a native or fluent speaker confirms each term for Luganda and the four
   western languages. Anything unconfirmed stays labelled "machine-translated" in any
   output shown to people.
6. Use: add a `--language lg` option to `predict.py` that prints and draws the
   translated name (with the English name kept alongside), reading the CSV.
   No translation service is needed at run time.

**Honest limits to state when this is built:** machine translation of single animal
words can be wrong or too general; unverified terms must not be presented as correct;
the table covers the seven classes only.

## 2. Ways to improve the weak points (see the report, Section 5)

| Weak point | Cheap thing to try next | Needs |
|---|---|---|
| Bird (almost never found) | Higher input size (a 1280-pixel run is in progress), tiled inference, many more bird examples | More bird footage for a real fix |
| Antelope / small animals | Same; interleaved antelope split to separate "unseen footage" from "late footage" | Compute only |
| Unseen sessions and new cameras | Nothing cheap fixes this | More varied footage from more places |
| Field speed | Time `predict.py` with the ONNX model on the target device | The device |
