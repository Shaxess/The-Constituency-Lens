# language_detect.py - Lightweight keyword-marker language detection.
# Deliberately NOT using a heavy NLP library (langdetect/fasttext) - after
# today's torch/tiktoken/sentencepiece chain, a new dependency is the last
# thing this pipeline needs right now. This is honest about being a
# heuristic, not a trained classifier - upgrade later if it proves too rough.

# Common markers per language, drawn from real Ojo complaint text seen so far.
# Extend these lists as more real data comes in - that's how this improves.

PIDGIN_MARKERS = [
    "dey", "don", "wetin", "abeg", "sef", "wahala", "na", "dem",
    "wey", "fit", "una", "make", "oga", "wan", "waka",
]

IGBO_MARKERS = [
    "mmiri", "anyi", "ahuhu", "biko", "oke onu", "onweghi",
    "okporo uzo", "uzo", "ona buruku", "ọkụ", "oku",
]

YORUBA_MARKERS = [
    "omi", "owo oja", "ego ahia", "ile", "won", "mo", "yio",
]


def detect_language(text):
    """
    Returns a language code: 'en', 'pcm', 'ig', 'yo', or a combination
    like 'en-pcm-ig' when multiple languages' markers are both present
    (common in code-switched Nigerian social media text).

    This is a heuristic on keyword presence, not a trained model - it will
    miss vernacular terms not yet in the marker lists above, and won't
    catch language used without any of these specific words. Good enough
    for a first pass; tune the marker lists as real data reveals gaps.
    """
    text_lower = text.lower()

    detected = []
    if any(m in text_lower for m in PIDGIN_MARKERS):
        detected.append("pcm")
    if any(m in text_lower for m in IGBO_MARKERS):
        detected.append("ig")
    if any(m in text_lower for m in YORUBA_MARKERS):
        detected.append("yo")

    if not detected:
        return "en"

    # English is the base/matrix language in almost all code-switched posts
    # seen so far, so it's included alongside any detected vernacular.
    return "en-" + "-".join(detected)


if __name__ == "__main__":
    tests = [
        "the bad portion of the road that lead to the market, always jam-packed with people",
        "Alaba market for Ojo, levy too much, oke onu, onweghi light for 3 days, anyi na-ata ahuhu",
        "Road from Okokomaiko to Iba don bad, okporo uzo ojoo, chairman no do anything",
        "those boys the pass police checked point everyday ooo, them dey even follow ajangbandi police station self",
    ]
    for t in tests:
        print(f"{detect_language(t):15} | {t[:60]}...")
