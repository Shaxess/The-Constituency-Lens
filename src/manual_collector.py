# TCL Low-Data Collector - Ojo Edition
# When Twitter blocks you, you manually copy 20 posts in 15 mins - still works!
from sheets_client import get_client, get_sheet
from political_tagger import tag_political_entities
from sentiment import analyze
from datetime import datetime

def add_post(text, author, source, ward_hint=""):
    political = tag_political_entities(text + " " + ward_hint)
    sentiment = analyze(text)  # returns a dict: {"label", "score", "method", "phrase"?}
    label = sentiment["label"]
    score = sentiment["score"]
    matched_phrase = sentiment.get("phrase", "")  # only present for dictionary-matched entries

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
        matched_phrase if matched_phrase else label,
        ",".join(political['issues']),
        ",".join(political['politicians']),
        political['value'],
        str(score)
    ]
    ws.append_row(row)
    print(f"Saved: {political['ward']} | {political['issues']} | Score {score} ({label}) | {text[:50]}...")

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

        ("those boys the pass police checked point everyday ooo, them dey even follow ajangbandi police station self",
         "Ojo Concerned Citizen", "Facebook Ojo Community", "Ward 03 Ajangbadi"),  # confirmed - "ajangbandi" is local spelling of Ajangbadi
    ]

    for text, author, source, ward in samples:
        add_post(text, author, source, ward)

    print(f"\nDone - Added {len(samples)} posts to sheet")