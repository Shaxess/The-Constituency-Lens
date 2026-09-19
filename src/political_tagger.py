# TCL Political Tagger - Ojo LGA Edition
# Turns raw complaint into political intelligence

import re

# --- OJO LGA POLITICAL STRUCTURE ---
# I will update these names after I confirm current office holders

OJO_POLITICIANS = {
    # LGA Level
    "lga_chairman": ["ojo chairman", "ojo lg chairman", "chairman ojo", "executive chairman ojo", "hon ojo chairman", "Ege"],
    "vice_chairman": ["vice chairman ojo", "ojo vice chairman"],
    "councillor": [f"ward {i} councillor" for i in range(1, 11)] + [f"ward {i} councilor" for i in range(1, 11)] + ["councillor", "councilor", "kounsila"],

    # State House of Assembly - Ojo has 2 seats
    "house_assembly_ojo1": ["ojo constituency 1", "ojo 1 assembly", "hon ojo 1", "house of assembly ojo 1"],
    "house_assembly_ojo2": ["ojo constituency 2", "ojo 2 assembly", "hon ojo 2", "house of assembly ojo 2"],

    # Federal - House of Reps
    "house_reps_ojo": ["ojo federal", "house of reps ojo", "ojo rep", "hon ojo rep", "ojo federal constituency"],

    # LCDA Chairmen inside Ojo LGA (very important - grassroots)
    "iba_lcda": ["iba lcda", "iba chairman", "chairman iba"],
    "oto_awori_lcda": ["oto awori", "oto-awori lcda", "oto chairman"],

    # General political keywords
    "governor": ["sanwo olu", "governor lagos", "lasg"],
    "president": ["tinubu", "president", "fg"],
}

# Generic role words with no LGA/LCDA name attached - used ONLY as a fallback
# when nothing specific matched above, so we don't miss the very common
# pattern of people just saying "chairman" with no qualifier.
GENERIC_ROLE_FALLBACK = {
    "lga_chairman": ["chairman"],
}

# Ojo Issues - what people complain about (maps to LGA responsibility)
OJO_ISSUES = {
    "road": ["road", "okporo uzo", "uzo ojoo", "ona buruku", "pothole", "badagry road", "okokomaiko road", "alaba road"],
    "light": ["light", "nepa", "oku", "ọkụ", "electricity", "ekedc"],
    "water": ["water", "mmiri", "omi", "borehole"],
    "waste": ["waste", "dirt", "refuse", "lawma", "dirty", "ekiti", "idoti"],
    "security": ["robbery", "thief", "ohi", "ole", "cult", "security", "police"],
    "market_levy": ["levy", "owo oja", "ego ahia", "alaba levy", "agbero", "ticket", "oke onu"],
    "education": ["school", "lasu", "teacher", "classroom"],
    "health": ["hospital", "clinic", "health center", "maternity", "drug"],
    "flood": ["flood", "water enter", "erosion", "drainage"],
}

# --- REVIEW QUEUE TRIAGE ---
# Posts that accuse a named person or group of a violent act carry real
# defamation and retaliation risk if the accusation is wrong. These get
# flagged for human verification and are held out of aggregated/public
# output until cleared. Generic complaints ("robbery at Lasu gate") are
# NOT flagged - only ones that appear to name who did it.

VIOLENT_ACT_KEYWORDS = [
    "killed", "killing", "kill", "murdered", "murder", "shot", "shooting",
    "stabbed", "stabbing", "beat to death", "lynched", "burnt", "burned",
    "assassinated", "gunned down", "hacked", "died after", "beheaded",
]

# Known cult/group names that commonly appear in accusations.
# Extend this as you encounter more in real data.
KNOWN_GROUP_NAMES = [
    "aye", "nbm", "black axe", "vikings", "dnki", "eiye", "buccaneer",
    "confraternity", "confra", "maphite", "kkk",
]

# Ojo Wards - map keywords to ward
OJO_WARDS = {
    "Ward 01 Ojo Town": ["ojo town", "ojo market"],
    "Ward 02 Okokomaiko": ["okokomaiko", "okoko", "alaba market", "alaba road", "badagry expressway junction"],
    "Ward 03 Ajangbadi": ["ajangbadi", "ajangbandi"],
    "Ward 04 Ijanikin": ["ijanikin"],
    "Ward 05 Iba": ["iba", "iba housing estate", "lasu gate", "lasu"],
    "Ward 06 Ilogbo": ["ilogbo"],
    "Ward 07 Irewe": ["irewe"],
    "Ward 08 Tafi": ["tafi", "taffi"],
    "Ward 09 Etegbin": ["etegbin"],
    "Ward 10 Idoluwo": ["idoluwo"],
    "Ward 11 Sabo": ["sabo", "alaba international", "alaba international market", "calabosa", "ilufe", "alaba rago"],
}


def _looks_like_named_accusation(text, text_lower):
    """
    Heuristic: does this post appear to name WHO committed a violent act?

    Returns (needs_review: bool, reason: str).

    Deliberately conservative - it's better to flag a few harmless posts
    for a human glance than to auto-publish an unverified accusation
    naming a real person or group.

    LIMITATION: without a proper NER model this uses capitalisation and a
    known-group list, so it will miss some names and false-positive on
    place names and sentence starts. Tune the lists as real data comes in.
    """
    has_violent_act = any(
        re.search(r"\b" + re.escape(kw) + r"\b", text_lower)
        for kw in VIOLENT_ACT_KEYWORDS
    )
    if not has_violent_act:
        return False, ""

    # 1. Named group explicitly mentioned
    for group in KNOWN_GROUP_NAMES:
        if group in text_lower:
            return True, f"violent act + named group ('{group}')"

    # 2. Nickname in quotes - e.g. Ibrahim, alias "Malo"
    if re.search(r"""["'\u2018\u2019\u201c\u201d]\s*\w+\s*["'\u2018\u2019\u201c\u201d]""", text):
        return True, "violent act + quoted alias/nickname"

    # 3. Capitalised word that isn't at the start of a sentence and isn't a
    #    known place/organisation - a rough proxy for a personal name.
    known_non_names = set()
    for phrase_list in list(OJO_WARDS.values()) + list(OJO_ISSUES.values()):
        for phrase in phrase_list:
            known_non_names.add(phrase.lower())
            # also add each individual word from multi-word phrases
            # (e.g. "health center" -> "health", "center") so a
            # capitalised word inside a known phrase isn't flagged alone.
            for word in phrase.lower().split():
                known_non_names.add(word)
    known_non_names.update({
        "ojo", "lagos", "nigeria", "lga", "lcda", "ward", "road", "street",
        "market", "police", "god", "state", "federal", "government",
        "ecowas", "primary", "junction", "estate", "housing", "area",
        "community", "residents", "chairman", "hon", "governor", "fg",
    })

    words = text.split()
    for i, word in enumerate(words):
        clean = re.sub(r"[^\w]", "", word)
        if not clean or len(clean) < 3:
            continue
        if i == 0:  # sentence-start capitalisation isn't a signal
            continue
        prev = re.sub(r"[^\w]", "", words[i - 1])
        if prev and prev[-1] in ".!?":  # also sentence start
            continue
        if clean[0].isupper() and clean.lower() not in known_non_names:
            return True, f"violent act + possible personal name ('{clean}')"

    # Violent act mentioned but nobody appears to be named - safe to pass
    return False, ""


def tag_political_entities(text):
    text_lower = text.lower()
    found_politicians = []
    found_issues = []
    found_ward = "Unknown"

    # 1. Find who is mentioned (specific/qualified matches first)
    for role, keywords in OJO_POLITICIANS.items():
        for kw in keywords:
            if kw.lower() in text_lower:
                found_politicians.append(role)
                break

    # 1b. Fallback: only fire generic role words (e.g. bare "chairman")
    # if nothing specific was already matched, so a specific "iba chairman"
    # mention doesn't get double-counted as the generic LGA chairman too.
    if not found_politicians:
        for role, keywords in GENERIC_ROLE_FALLBACK.items():
            for kw in keywords:
                if kw in text_lower:
                    found_politicians.append(role)
                    break

    # 2. Find what issue
    for issue, keywords in OJO_ISSUES.items():
        for kw in keywords:
            if kw in text_lower:
                found_issues.append(issue)
                break

    # 3. Find which ward (most specific first)
    for ward, keywords in OJO_WARDS.items():
        for kw in keywords:
            if kw in text_lower:
                found_ward = ward
                break
        if found_ward != "Unknown":
            break

    # 4. Political blame score
    is_blame = len(found_politicians) > 0 and len(found_issues) > 0

    # 5. Review-queue triage - flag unverified named accusations of violence
    needs_review, review_reason = _looks_like_named_accusation(text, text_lower)

    return {
        "politicians": list(set(found_politicians)),
        "issues": list(set(found_issues)),
        "ward": found_ward,
        "is_political": len(found_politicians) > 0 or "ward" in text_lower or "councillor" in text_lower,
        "is_blame_game": is_blame,
        "value": "HIGH" if is_blame else "MEDIUM" if len(found_issues) > 0 else "LOW",
        "needs_review": needs_review,
        "review_reason": review_reason,
    }


# Test
if __name__ == "__main__":
    tests = [
        "Ojo chairman no do anything for Ward 4 road, okporo uzo ojoo, onweghi mmiri",
        "Alaba market leader say levy too much, oke onu, biko chairman help us",
        "LASU students for Iba dey suffer, no light for 3 days",
        "NEPA don take light for Okokomaiko again, no be chairman fault but LASG",
        "chairman no do anything",  # bare mention - should now tag lga_chairman via fallback
        # --- review-queue cases ---
        "afternoon robbery at Lasu gate, Alaba businessmen",  # should NOT flag - no named accused
        "Ibrahim, alias Malo, was killed by the Aye cult group on Ogidan Street",  # SHOULD flag
        "Bomber was shot dead near ECOWAS Road, residents say fifth killing on the street",  # SHOULD flag
    ]

    for t in tests:
        result = tag_political_entities(t)
        print(f"\nText: {t}")
        print(f" -> {result}")