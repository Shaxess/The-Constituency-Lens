# sentiment.py - Ojo Safe Version - Weighted dictionary first, xlm-roberta optional
import logging
logger = logging.getLogger("TCL-Sentiment")

# Weighted lexicon - English/Pidgin/Igbo/Yoruba terms and phrases.
# Score is per-match; total is summed across all matches found in the text,
# so a post with multiple negative cues scores more negative than one with
# a single mild cue. This is the PRIMARY scoring method right now since
# the transformer is unavailable - keep this list growing as real data
# comes in and you spot terms it's missing.
WEIGHTED_LEXICON = {
    # Strong negative - suffering/anger phrases
    "onweghi mmiri": -3,
    "anyi na-ata ahuhu": -3,
    "oke onu": -2,
    "dey suffer": -2,
    "suffer": -2,
    "no do anything": -2,
    "terrorizing": -3,
    "cultist": -2,
    "robbery": -2,
    "jam-packed": -1,
    "bad road": -2,
    "okporo uzo ojoo": -2,
    "don bad": -2,
    "no light": -2,
    "dirty everywhere": -2,
    "waste full": -1,
    "biko help us": -1,  # plea/distress marker

    # Mild negative
    "too much": -1,
    "no come": -1,
    "checked point everyday": -1,  # weariness/complaint about repeated harassment

    # Positive
    "good work": 2,
    "well done": 2,
    "kudos": 2,
    "fixed": 2,
    "improved": 1,
}

# Lazy load transformer - don't import on startup
_transformer_model = None


def _load_transformer_safely():
    global _transformer_model
    if _transformer_model is not None:
        return _transformer_model
    try:
        from transformers import pipeline
        logger.info("Loading xlm-roberta...")
        _transformer_model = pipeline("sentiment-analysis", model="cardiffnlp/twitter-xlm-roberta-base-sentiment", use_fast=False)
        return _transformer_model
    except Exception as e:
        logger.warning(f"Transformer not available (torch broken): {e} - using dictionary only")
        return None


def analyze(text: str):
    text_lower = text.lower()

    # 1. Weighted dictionary scoring - sums every matched term/phrase
    matched_terms = []
    total_score = 0
    for phrase, weight in WEIGHTED_LEXICON.items():
        if phrase in text_lower:
            total_score += weight
            matched_terms.append(phrase)

    if matched_terms:
        label = "NEGATIVE" if total_score < 0 else "POSITIVE" if total_score > 0 else "NEUTRAL"
        return {
            "label": label,
            "score": total_score,
            "method": "dictionary",
            "matched_terms": matched_terms,
        }

    # 2. Try transformer only if available and dictionary found nothing
    model = _load_transformer_safely()
    if model:
        try:
            result = model(text[:512])[0]
            raw_label = result["label"].lower()
            confidence = result["score"]
            # Sign the confidence to match the lexicon's signed scale
            # (-N to +N). Without this, a 0.87 "negative" confidence and
            # a 0.87 "positive" confidence would average as identical,
            # which silently corrupts every ward/issue aggregate.
            if "neg" in raw_label:
                signed_score = -confidence
            elif "pos" in raw_label:
                signed_score = confidence
            else:
                signed_score = 0
            return {"label": result["label"], "score": round(signed_score, 3), "method": "xlm-roberta", "matched_terms": []}
        except Exception as e:
            logger.error(f"Transformer inference failed: {e}")

    # 3. Fallback neutral - genuinely nothing matched
    return {"label": "NEUTRAL", "score": 0, "method": "fallback", "matched_terms": []}


# Test
if __name__ == "__main__":
    tests = [
        "Alaba market for Ojo, levy too much, oke onu, onweghi light for 3 days, anyi na-ata ahuhu",
        "Road from Okokomaiko to Iba don bad, okporo uzo ojoo, chairman no do anything",
        "the bad portion of the road that lead to the market, always jam-packed with people",
        "confrata Naija stop the Vikings (DNKI) cultists terrorizing the Alaba International Market area",
        "Chairman finally fixed the road, well done",
    ]
    for t in tests:
        print(f"\n{t}\n -> {analyze(t)}")