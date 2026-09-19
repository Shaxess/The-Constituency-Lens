# TCL Low-Data Collector - Ojo Edition
# When Twitter blocks you, you manually copy 20 posts in 15 mins - still works!
from sheets_client import get_client, get_sheet
from political_tagger import tag_political_entities
from sentiment import analyze
from language_detect import detect_language
from datetime import datetime

def add_post(text, author, source, ward_hint=""):
    political = tag_political_entities(text + " " + ward_hint)
    sentiment = analyze(text)  # returns a dict: {"label", "score", "method", "matched_terms"}
    label = sentiment["label"]
    score = sentiment["score"]
    matched_terms = sentiment.get("matched_terms", [])
    language = detect_language(text)

    client = get_client()
    ws = get_sheet(client)
    row = [
        datetime.now().strftime("%Y-%m-%d"),
        "Ojo",
        political['ward'],
        source,
        text[:400],
        author,
        "manual link",
        language,
        ",".join(political['issues']),
        ",".join(political['politicians']),
        political['value'],
        str(score),
        "REVIEW" if political.get('needs_review') else "",
        political.get('review_reason', ""),
        ",".join(matched_terms) if matched_terms else label,
    ]
    ws.append_row(row)
    flag = " [FLAGGED FOR REVIEW: " + political['review_reason'] + "]" if political.get('needs_review') else ""
    print(f"Saved: {political['ward']} | {language} | {political['issues']} | Score {score} ({label}) | {text[:50]}...{flag}")

if __name__ == "__main__":
    # ward_hint uses official INEC ward names to help the tagger resolve
    # ambiguous landmarks (Alaba spans two wards - see notes below).
    samples = [
        ("Alaba market for Ojo, levy too much, oke onu, onweghi light for 3 days, anyi na-ata ahuhu",
         "Alaba Trader", "Facebook Alaba Page", "Ward 02 Okokomaiko"),  # Alaba Market Axis

        ("Road from Okokomaiko to Iba don bad, okporo uzo ojoo, chairman no do anything",
         "Ojo Youth", "Facebook Ojo LGA", "Ward 02 Okokomaiko"),

        ("NEPA don take light for Iba LCDA, LASU students dey suffer for hostel",
         "LASU Comrade", "Facebook LASU", "Ward 05 Iba"),  # LASU/hostel context -> Iba, distinct from Alaba-side LASU gate mentions

        ("Waste full for Ojo Ward 5, LAWMA no come, dirty everywhere, biko help us",
         "Mama Nkechi Ojo", "Facebook Ojo Community", "Ward 05 Iba"),

        ("the bad portion of the road that lead to the market, always jam-packed with people",
         "Alaba Resident", "Facebook Alaba Page", "Ward 02 Okokomaiko"),  # Alaba Market Axis road

        ("afternoon robbery at Lasu gate, Alaba businessmen",
         "Alaba Trader", "Facebook Alaba Page", "Ward 05 Iba"),  # confirmed - LASU gate is closer to Iba

        ("confrata Naija stop the Vikings (DNKI) cultists terrorizing the Alaba International Market area and other parts of Ojo axis",
         "Ojo Concerned Citizen", "Facebook Ojo Community", "Ward 11 Sabo"),  # Alaba International Market

        ("Imagine it was the anti cult group of law enforcement recording and monitoring them like this, they would have been arrested easily",
         "Ojo Concerned Citizen", "Facebook Ojo Community", "Ward 11 Sabo"),

        ("Man alleges his infant twin boys died at home on 25 Dec, a day after receiving immunization shots at Ajangbadi Primary Health Center, Ojo (24 Dec). Says twins became weak with high fever post-injection; nurse advised paracetamol at home. Family is demanding answers on what was administered.",
         "Sound Mind", "Facebook", "Ward 03 Ajangbadi"),

        ("Residents in Okokomaiko report recurring violent incidents, including killings, along ECOWAS Road and surrounding streets over the past year; specific perpetrators remain unconfirmed. Community members are calling for increased police presence and investigation.",
         "Okokomaiko Residents (aggregated)", "Facebook (multiple posts)", "Ward 02 Okokomaiko"),

        ("those boys the pass police checked point everyday ooo, them dey even follow ajangbandi police station self",
         "Ojo Concerned Citizen", "Facebook Ojo Community", "Ward 03 Ajangbadi"),  # confirmed - "ajangbandi" is local spelling of Ajangbadi
    ]

    for text, author, source, ward in samples:
        add_post(text, author, source, ward)

    print(f"\nDone - Added {len(samples)} posts to sheet")