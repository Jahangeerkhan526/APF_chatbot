# -*- coding: utf-8 -*-
"""
questionnaire_to_json.py
========================
APF Nancy Chatbot - Convert GAQ-P and GAQ-PP questions to JSON

What it does:
  - Contains all questions extracted from GAQ-P and GAQ-PP PDFs
  - Original question text preserved exactly from PDFs
  - Warm friendly versions for Nancy to ask conversationally
  - Includes pelvic floor symptoms from Marlize email
  - Saves structured JSON to data/processed/questionnaires/questions.json

Usage:
    python scripts/questionnaire_to_json.py

Output: data/processed/questionnaires/questions.json
"""

import json
from pathlib import Path
from datetime import datetime

# ── CONFIG ────────────────────────────────────────────────────────────────────
OUTPUT_DIR  = "data/processed/questionnaires"
OUTPUT_FILE = "questions.json"

# ── GAQ-P QUESTIONS (Pregnancy) ───────────────────────────────────────────────
# Source: CSEP-PATH_GAQ_P_UK_version.pdf
# Original text preserved exactly from PDF

GAQP_QUESTIONS = [
    {
        "question_id"      : "gaqp_1a",
        "questionnaire"    : "GAQ-P",
        "for"              : "pregnancy",
        "section"          : "current_pregnancy",
        "question_number"  : "1a",
        "question_original": "Mild, moderate or severe respiratory or cardiovascular diseases (e.g., chronic bronchitis)?",
        "question_warm"    : "Have you been told you have any heart or breathing conditions, such as asthma, chronic bronchitis, or a heart problem?",
        "answer_type"      : "yes_no",
        "if_yes"           : "refer_to_gp",
    },
    {
        "question_id"      : "gaqp_1b",
        "questionnaire"    : "GAQ-P",
        "for"              : "pregnancy",
        "section"          : "current_pregnancy",
        "question_number"  : "1b",
        "question_original": "Epilepsy that is not stable?",
        "question_warm"    : "Do you have epilepsy that is currently not well controlled or stable?",
        "answer_type"      : "yes_no",
        "if_yes"           : "refer_to_gp",
    },
    {
        "question_id"      : "gaqp_1c",
        "questionnaire"    : "GAQ-P",
        "for"              : "pregnancy",
        "section"          : "current_pregnancy",
        "question_number"  : "1c",
        "question_original": "Type 1 diabetes that is not stable or your blood sugar is outside of target ranges?",
        "question_warm"    : "Do you have Type 1 diabetes that is not currently well controlled, or is your blood sugar often outside the target range?",
        "answer_type"      : "yes_no",
        "if_yes"           : "refer_to_gp",
    },
    {
        "question_id"      : "gaqp_1d",
        "questionnaire"    : "GAQ-P",
        "for"              : "pregnancy",
        "section"          : "current_pregnancy",
        "question_number"  : "1d",
        "question_original": "Thyroid disease that is not stable or your thyroid function is outside of target ranges?",
        "question_warm"    : "Have you been told you have a thyroid condition that is not currently stable or well controlled?",
        "answer_type"      : "yes_no",
        "if_yes"           : "refer_to_gp",
    },
    {
        "question_id"      : "gaqp_1e",
        "questionnaire"    : "GAQ-P",
        "for"              : "pregnancy",
        "section"          : "current_pregnancy",
        "question_number"  : "1e",
        "question_original": "An eating disorder(s) or malnutrition?",
        "question_warm"    : "Are you currently experiencing or being treated for an eating disorder, or are you struggling to get enough nutrition?",
        "answer_type"      : "yes_no",
        "if_yes"           : "refer_to_gp",
    },
    {
        "question_id"      : "gaqp_1f",
        "questionnaire"    : "GAQ-P",
        "for"              : "pregnancy",
        "section"          : "current_pregnancy",
        "question_number"  : "1f",
        "question_original": "Twins (28 weeks pregnant or later)? Or are you expecting triplets or higher multiple births?",
        "question_warm"    : "Are you expecting twins and are 28 weeks or more pregnant, or are you expecting triplets or more babies?",
        "answer_type"      : "yes_no",
        "if_yes"           : "refer_to_gp",
    },
    {
        "question_id"      : "gaqp_1g",
        "questionnaire"    : "GAQ-P",
        "for"              : "pregnancy",
        "section"          : "current_pregnancy",
        "question_number"  : "1g",
        "question_original": "Low red blood cell number (anemia) with high levels of fatigue and/or light-headedness?",
        "question_warm"    : "Have you been told you have anaemia and are you feeling very tired or dizzy because of it?",
        "answer_type"      : "yes_no",
        "if_yes"           : "refer_to_gp",
    },
    {
        "question_id"      : "gaqp_1h",
        "questionnaire"    : "GAQ-P",
        "for"              : "pregnancy",
        "section"          : "current_pregnancy",
        "question_number"  : "1h",
        "question_original": "High blood pressure (preeclampsia, gestational hypertension, or chronic hypertension that is not stable)?",
        "question_warm"    : "Have you been told you have high blood pressure during this pregnancy, such as pre-eclampsia or gestational hypertension?",
        "answer_type"      : "yes_no",
        "if_yes"           : "refer_to_gp",
    },
    {
        "question_id"      : "gaqp_1i",
        "questionnaire"    : "GAQ-P",
        "for"              : "pregnancy",
        "section"          : "current_pregnancy",
        "question_number"  : "1i",
        "question_original": "A baby that is growing slowly (intrauterine growth restriction)?",
        "question_warm"    : "Has your midwife or doctor mentioned that your baby is not growing as expected or growing more slowly than usual?",
        "answer_type"      : "yes_no",
        "if_yes"           : "refer_to_gp",
    },
    {
        "question_id"      : "gaqp_1j",
        "questionnaire"    : "GAQ-P",
        "for"              : "pregnancy",
        "section"          : "current_pregnancy",
        "question_number"  : "1j",
        "question_original": "Unexplained bleeding, ruptured membranes or labour before 37 weeks?",
        "question_warm"    : "Have you had any unexplained bleeding, has your waters broken, or have you had any signs of early labour before 37 weeks?",
        "answer_type"      : "yes_no",
        "if_yes"           : "refer_to_gp",
    },
    {
        "question_id"      : "gaqp_1k",
        "questionnaire"    : "GAQ-P",
        "for"              : "pregnancy",
        "section"          : "current_pregnancy",
        "question_number"  : "1k",
        "question_original": "A placenta that is partially or completely covering the cervix (placenta previa)?",
        "question_warm"    : "Have you been told that your placenta is low-lying or covering your cervix, sometimes called placenta praevia?",
        "answer_type"      : "yes_no",
        "if_yes"           : "refer_to_gp",
    },
    {
        "question_id"      : "gaqp_1l",
        "questionnaire"    : "GAQ-P",
        "for"              : "pregnancy",
        "section"          : "current_pregnancy",
        "question_number"  : "1l",
        "question_original": "Weak cervical tissue (incompetent cervix)?",
        "question_warm"    : "Has your doctor ever mentioned that your cervix is weak or may need extra support during this pregnancy?",
        "answer_type"      : "yes_no",
        "if_yes"           : "refer_to_gp",
    },
    {
        "question_id"      : "gaqp_1m",
        "questionnaire"    : "GAQ-P",
        "for"              : "pregnancy",
        "section"          : "current_pregnancy",
        "question_number"  : "1m",
        "question_original": "A stitch or tape to reinforce your cervix (cerclage)?",
        "question_warm"    : "Have you had a stitch or tape placed in your cervix to help support it during this pregnancy?",
        "answer_type"      : "yes_no",
        "if_yes"           : "refer_to_gp",
    },
    {
        "question_id"      : "gaqp_2a",
        "questionnaire"    : "GAQ-P",
        "for"              : "pregnancy",
        "section"          : "previous_pregnancies",
        "question_number"  : "2a",
        "question_original": "Recurrent miscarriages (loss of your baby before 20 weeks gestation two or more times)?",
        "question_warm"    : "Have you experienced two or more miscarriages in previous pregnancies before 20 weeks?",
        "answer_type"      : "yes_no",
        "if_yes"           : "refer_to_gp",
    },
    {
        "question_id"      : "gaqp_2b",
        "questionnaire"    : "GAQ-P",
        "for"              : "pregnancy",
        "section"          : "previous_pregnancies",
        "question_number"  : "2b",
        "question_original": "Early delivery (before 37 weeks gestation)?",
        "question_warm"    : "Have you had a premature birth in a previous pregnancy where your baby arrived before 37 weeks?",
        "answer_type"      : "yes_no",
        "if_yes"           : "refer_to_gp",
    },
]

# ── GAQ-PP QUESTIONS (Postpartum) ─────────────────────────────────────────────
# Source: CSEP-PATH_GAQ_PP_Guidelines.pdf
# Original text preserved exactly from PDF

GAQPP_QUESTIONS = [
    {
        "question_id"      : "gaqpp_1a",
        "questionnaire"    : "GAQ-PP",
        "for"              : "postnatal",
        "section"          : "first_year_postpartum",
        "question_number"  : "1a",
        "question_original": "Loss of consciousness for any reason?",
        "question_warm"    : "Have you fainted or lost consciousness for any reason since having your baby?",
        "answer_type"      : "yes_no",
        "if_yes"           : "refer_to_gp",
    },
    {
        "question_id"      : "gaqpp_1b",
        "questionnaire"    : "GAQ-PP",
        "for"              : "postnatal",
        "section"          : "first_year_postpartum",
        "question_number"  : "1b",
        "question_original": "Neurological symptoms such as poor coordination or muscle weakness affecting balance?",
        "question_warm"    : "Have you noticed any problems with your balance, coordination or muscle weakness since having your baby?",
        "answer_type"      : "yes_no",
        "if_yes"           : "refer_to_gp",
    },
    {
        "question_id"      : "gaqpp_1c",
        "questionnaire"    : "GAQ-PP",
        "for"              : "postnatal",
        "section"          : "first_year_postpartum",
        "question_number"  : "1c",
        "question_original": "Deep vein thrombosis (blood clot in legs) or pulmonary emboli (blood clot in lungs)?",
        "question_warm"    : "Have you experienced any leg pain, swelling or redness that could suggest a blood clot, or have you felt unusually short of breath or dizzy?",
        "answer_type"      : "yes_no",
        "if_yes"           : "refer_to_gp",
    },
    {
        "question_id"      : "gaqpp_1d",
        "questionnaire"    : "GAQ-PP",
        "for"              : "postnatal",
        "section"          : "first_year_postpartum",
        "question_number"  : "1d",
        "question_original": "High blood pressure (>140/90mmHg) that is not stable?",
        "question_warm"    : "Have you been told you have high blood pressure since having your baby that is not currently stable?",
        "answer_type"      : "yes_no",
        "if_yes"           : "refer_to_gp",
    },
    {
        "question_id"      : "gaqpp_1e",
        "questionnaire"    : "GAQ-PP",
        "for"              : "postnatal",
        "section"          : "first_year_postpartum",
        "question_number"  : "1e",
        "question_original": "An eating disorder(s) or malnutrition?",
        "question_warm"    : "Are you currently experiencing or being treated for an eating disorder, or struggling to eat enough to nourish yourself and your baby?",
        "answer_type"      : "yes_no",
        "if_yes"           : "refer_to_gp",
    },
    {
        "question_id"      : "gaqpp_1f",
        "questionnaire"    : "GAQ-PP",
        "for"              : "postnatal",
        "section"          : "first_year_postpartum",
        "question_number"  : "1f",
        "question_original": "Postpartum cardiomyopathy (heart disease after childbirth)?",
        "question_warm"    : "Have you been diagnosed with any heart condition since having your baby?",
        "answer_type"      : "yes_no",
        "if_yes"           : "refer_to_gp",
    },
    {
        "question_id"      : "gaqpp_1g",
        "questionnaire"    : "GAQ-PP",
        "for"              : "postnatal",
        "section"          : "first_year_postpartum",
        "question_number"  : "1g",
        "question_original": "New symptoms of heart disease (e.g., chest pain or discomfort) or stroke (e.g., face drooping, slurred speech) during activities of daily living or at rest?",
        "question_warm"    : "Have you experienced any chest pain, or any symptoms like face drooping or slurred speech during everyday activities or at rest?",
        "answer_type"      : "yes_no",
        "if_yes"           : "refer_to_gp",
    },
    {
        "question_id"      : "gaqpp_1h",
        "questionnaire"    : "GAQ-PP",
        "for"              : "postnatal",
        "section"          : "first_year_postpartum",
        "question_number"  : "1h",
        "question_original": "Severe abdominal pain?",
        "question_warm"    : "Have you been experiencing any severe or persistent abdominal pain since having your baby?",
        "answer_type"      : "yes_no",
        "if_yes"           : "refer_to_gp",
    },
    {
        "question_id"      : "gaqpp_1i",
        "questionnaire"    : "GAQ-PP",
        "for"              : "postnatal",
        "section"          : "first_year_postpartum",
        "question_number"  : "1i",
        "question_original": "Chest pain/discomfort, dizziness or lightheadedness during exercise?",
        "question_warm"    : "Do you get chest pain, discomfort, dizziness or feel lightheaded when you try to do any physical activity?",
        "answer_type"      : "yes_no",
        "if_yes"           : "refer_to_gp",
    },
    {
        "question_id"      : "gaqpp_1j",
        "questionnaire"    : "GAQ-PP",
        "for"              : "postnatal",
        "section"          : "first_year_postpartum",
        "question_number"  : "1j",
        "question_original": "Breathing difficulties such as shortness of breath at rest that does not improve with medications?",
        "question_warm"    : "Are you experiencing any breathing difficulties or shortness of breath even when resting that does not improve with medication?",
        "answer_type"      : "yes_no",
        "if_yes"           : "refer_to_gp",
    },
    {
        "question_id"      : "gaqpp_1k",
        "questionnaire"    : "GAQ-PP",
        "for"              : "postnatal",
        "section"          : "first_year_postpartum",
        "question_number"  : "1k",
        "question_original": "Kidney disease?",
        "question_warm"    : "Have you been diagnosed with any kidney problems since having your baby?",
        "answer_type"      : "yes_no",
        "if_yes"           : "refer_to_gp",
    },
    {
        "question_id"      : "gaqpp_1l",
        "questionnaire"    : "GAQ-PP",
        "for"              : "postnatal",
        "section"          : "first_year_postpartum",
        "question_number"  : "1l",
        "question_original": "Excessive fatigue (e.g., beyond tiredness, does not improve with rest)?",
        "question_warm"    : "Are you experiencing extreme fatigue that goes beyond normal tiredness and does not get better even when you rest?",
        "answer_type"      : "yes_no",
        "if_yes"           : "refer_to_gp",
    },
    {
        "question_id"      : "gaqpp_1m",
        "questionnaire"    : "GAQ-PP",
        "for"              : "postnatal",
        "section"          : "first_year_postpartum",
        "question_number"  : "1m",
        "question_original": "Severe infection accompanied by fever, body aches, or swollen lymph glands?",
        "question_warm"    : "Have you had a severe infection with symptoms like high fever, body aches or swollen glands since having your baby?",
        "answer_type"      : "yes_no",
        "if_yes"           : "refer_to_gp",
    },
    {
        "question_id"      : "gaqpp_1n",
        "questionnaire"    : "GAQ-PP",
        "for"              : "postnatal",
        "section"          : "first_year_postpartum",
        "question_number"  : "1n",
        "question_original": "Broken bone(s) or another significant injury?",
        "question_warm"    : "Have you had any broken bones or a significant injury since having your baby?",
        "answer_type"      : "yes_no",
        "if_yes"           : "refer_to_gp",
    },
    {
        "question_id"      : "gaqpp_1o",
        "questionnaire"    : "GAQ-PP",
        "for"              : "postnatal",
        "section"          : "first_year_postpartum",
        "question_number"  : "1o",
        "question_original": "Caesarean section pain that worsens with exercise (e.g., surgical incision pain)?",
        "question_warm"    : "If you had a caesarean, do you experience pain around your scar that gets worse when you try to be active?",
        "answer_type"      : "yes_no",
        "if_yes"           : "refer_to_gp",
    },
    {
        "question_id"      : "gaqpp_1p",
        "questionnaire"    : "GAQ-PP",
        "for"              : "postnatal",
        "section"          : "first_year_postpartum",
        "question_number"  : "1p",
        "question_original": "Vaginal bleeding not associated with menses?",
        "question_warm"    : "Have you experienced any unexpected vaginal bleeding that is not your normal period since having your baby?",
        "answer_type"      : "yes_no",
        "if_yes"           : "refer_to_gp",
    },
]

# ── PELVIC FLOOR SYMPTOMS ─────────────────────────────────────────────────────
# Source: Marlize email — not contraindications but require pelvic physio referral

PELVIC_SYMPTOMS = [
    {
        "symptom_id": "pelvic_1",
        "for"       : "postnatal",
        "original"  : "Urinary and/or faecal incontinence",
        "warm"      : "Are you experiencing any leaking of wee or poo that you cannot control?",
        "action"    : "refer_to_pelvic_physio",
        "signpost"  : "thepogp.co.uk/resources/booklets",
    },
    {
        "symptom_id": "pelvic_2",
        "for"       : "postnatal",
        "original"  : "Urinary and/or faecal urgency that is difficult to defer",
        "warm"      : "Do you feel a sudden urgent need to go to the toilet that is very difficult to hold?",
        "action"    : "refer_to_pelvic_physio",
        "signpost"  : "thepogp.co.uk/resources/booklets",
    },
    {
        "symptom_id": "pelvic_3",
        "for"       : "postnatal",
        "original"  : "Heaviness/pressure/bulge/dragging in the pelvic area",
        "warm"      : "Do you feel any heaviness, pressure or a dragging sensation in your pelvic area or down below?",
        "action"    : "refer_to_pelvic_physio",
        "signpost"  : "thepogp.co.uk/resources/booklets",
    },
    {
        "symptom_id": "pelvic_4",
        "for"       : "postnatal",
        "original"  : "Pain with intercourse",
        "warm"      : "Are you experiencing any pain during sex since having your baby?",
        "action"    : "refer_to_pelvic_physio",
        "signpost"  : "thepogp.co.uk/resources/booklets",
    },
    {
        "symptom_id": "pelvic_5",
        "for"       : "postnatal",
        "original"  : "Obstructive defecation",
        "warm"      : "Are you having difficulty passing stools or feeling like something is blocking you when trying to go to the toilet?",
        "action"    : "refer_to_pelvic_physio",
        "signpost"  : "thepogp.co.uk/resources/booklets",
    },
    {
        "symptom_id": "pelvic_6",
        "for"       : "postnatal",
        "original"  : "Pendular abdomen, separated abdominal muscles and/or decreased abdominal strength",
        "warm"      : "Have you noticed a gap or separation down the middle of your tummy, or do you feel your tummy muscles are very weak?",
        "action"    : "refer_to_pelvic_physio",
        "signpost"  : "thepogp.co.uk/resources/booklets",
    },
    {
        "symptom_id": "pelvic_7",
        "for"       : "postnatal",
        "original"  : "Musculoskeletal lumbopelvic pain",
        "warm"      : "Are you experiencing any ongoing back or pelvic pain since having your baby?",
        "action"    : "refer_to_pelvic_physio",
        "signpost"  : "thepogp.co.uk/resources/booklets",
    },
]


# ── MAIN ──────────────────────────────────────────────────────────────────────

def main():
    print("\n" + "="*60)
    print("  APF Questionnaire → JSON Converter")
    print("="*60)

    # Create output directory
    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)

    # Build output
    output = {
        "metadata": {
            "created_at"  : datetime.now().isoformat(),
            "total_gaqp"  : len(GAQP_QUESTIONS),
            "total_gaqpp" : len(GAQPP_QUESTIONS),
            "total_pelvic": len(PELVIC_SYMPTOMS),
            "source_gaqp" : "CSEP-PATH_GAQ_P_UK_version.pdf",
            "source_gaqpp": "CSEP-PATH_GAQ_PP_Guidelines.pdf",
            "source_pelvic": "Marlize email - APF recommendation",
            "note"        : "Original questions from PDFs. Warm versions rephrased for friendly conversation.",
        },
        "gaqp_questions" : GAQP_QUESTIONS,
        "gaqpp_questions": GAQPP_QUESTIONS,
        "pelvic_symptoms": PELVIC_SYMPTOMS,
    }

    # Save JSON
    output_path = Path(OUTPUT_DIR) / OUTPUT_FILE
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\n  GAQ-P questions  : {len(GAQP_QUESTIONS)}")
    print(f"  GAQ-PP questions : {len(GAQPP_QUESTIONS)}")
    print(f"  Pelvic symptoms  : {len(PELVIC_SYMPTOMS)}")
    print(f"\n  Sample warm questions:")
    print(f"  {'-'*56}")
    for q in GAQP_QUESTIONS[:3]:
        print(f"\n  [{q['question_id']}] {q['question_warm']}")
    print(f"\n  ...")
    for q in GAQPP_QUESTIONS[:3]:
        print(f"\n  [{q['question_id']}] {q['question_warm']}")

    print(f"\n{'='*60}")
    print(f"  ✅ DONE!")
    print(f"{'='*60}")
    print(f"  Saved to: {output_path}")
    print(f"\n  Next step → run:")
    print(f"  python scripts/embed_questionnaires.py")


if __name__ == "__main__":
    main()
