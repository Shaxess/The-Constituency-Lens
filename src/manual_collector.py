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
        political.get('jurisdiction', 'lga'),
    ]
    ws.append_row(row)
    flag = " [FLAGGED FOR REVIEW: " + political['review_reason'] + "]" if political.get('needs_review') else ""
    jur = political.get('jurisdiction', 'lga')
    jur_note = f" [{jur.upper()}]" if jur != "lga" else ""
    print(f"Saved: {political['ward']} | {language} | {political['issues']} | Score {score} ({label}){jur_note} | {text[:50]}...{flag}")

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
        
        ("LASU condemned an alleged assault on a 300-level Nursing student at a private hostel near campus and started a disciplinary process.",
         "LASU Students' Union", "Facebook", "Ward 05 Iba"),

        ("Over 300 diploma graduates protested after LASU raised the CGPA requirement for 200-level admission from 3.0 to 3.5, excluding them; security operatives allegedly brutalized protesters.",
         "Diploma Students (Direct Entry protesters)", "PM News Nigeria", "Ward 05 Iba"),

        ("ASUU declared an indefinite strike across LASU, LASUED and LASUSTECH over an unimplemented December 2025 agreement on staff allowances and welfare.",
         "ASUU Joint Campus Group", "Facebook", "Ward 05 Iba"),

        ("Alleged over 100 LASU final-year students could not graduate due to a lecturer's unuploaded 300-level results; LASU says the matter is under investigation.",
         "Son Of Ayo", "Legit.ng", "Ward 05 Iba"),

        ("LASU English Department students reported a missing-results backlog affecting graduation; LASU later said the issue was resolved and records updated.",
         "English Department Students", "Facebook", "Ward 05 Iba"),

        ("A 300-level LASU student was reportedly killed in a hit-and-run on Igando road while fleeing a police-related disturbance; students demanded justice. Unverified, single-source report.",
         "LASU Students (aggregated)", "Facebook", "Ward 05 Iba"),

        ("LASU banned student content creation on campus after a 'bandits prank' incident; sought student opinions on the policy.",
         "Aanuoluwapo Adeniyi", "Facebook", "Ward 05 Iba"),

        ("LASU Corporate Affairs Unit issued a statement on missing results, assuring no eligible student would be delayed from graduating.",
         "LASU Corporate Affairs Unit", "hola-info247.blogspot.com", "Ward 05 Iba"),

        ("Discussion questioned regional funding equity between federal and state universities, citing LASU as an example of underfunding.",
         "Adedamola Adetayo", "Facebook", "Ward 05 Iba"),

        # --- LASU-related batch (institutional, expect jurisdiction=institutional, not LGA-actionable) ---
        ("LASU condemned an alleged assault on a 300-level Nursing student at a private hostel near campus and started a disciplinary process.",
         "LASU Students' Union", "Facebook", "Ward 05 Iba"),

        ("Over 300 diploma graduates protested after LASU raised the CGPA requirement for 200-level admission from 3.0 to 3.5, excluding them; security operatives allegedly brutalized protesters.",
         "Diploma Students (Direct Entry protesters)", "PM News Nigeria", "Ward 05 Iba"),

        ("ASUU declared an indefinite strike across LASU, LASUED and LASUSTECH over an unimplemented December 2025 agreement on staff allowances and welfare.",
         "ASUU Joint Campus Group", "Facebook", "Ward 05 Iba"),

        ("Alleged over 100 LASU final-year students could not graduate due to a lecturer's unuploaded 300-level results; LASU says the matter is under investigation.",
         "Son Of Ayo", "Legit.ng", "Ward 05 Iba"),

        ("LASU English Department students reported a missing-results backlog affecting graduation; LASU later said the issue was resolved and records updated.",
         "English Department Students", "Facebook", "Ward 05 Iba"),

        ("A 300-level LASU student was reportedly killed in a hit-and-run on Igando road while fleeing a police-related disturbance; students demanded justice. Unverified, single-source report.",
         "LASU Students (aggregated)", "Facebook", "Ward 05 Iba"),

        ("LASU banned student content creation on campus after a 'bandits prank' incident; sought student opinions on the policy.",
         "Aanuoluwapo Adeniyi", "Facebook", "Ward 05 Iba"),

        ("LASU Corporate Affairs Unit issued a statement on missing results, assuring no eligible student would be delayed from graduating.",
         "LASU Corporate Affairs Unit", "hola-info247.blogspot.com", "Ward 05 Iba"),

        ("Discussion questioned regional funding equity between federal and state universities, citing LASU as an example of underfunding.",
         "Adedamola Adetayo", "Facebook", "Ward 05 Iba"),
    ]

    for text, author, source, ward in samples:
        add_post(text, author, source, ward)

    print(f"\nDone - Added {len(samples)} posts to sheet")