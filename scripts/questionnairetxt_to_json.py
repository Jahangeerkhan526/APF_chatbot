# -*- coding: utf-8 -*-
"""
questionnaire_to_json.py
========================
APF Nancy Chatbot - Extract GAQ-P and GAQ-PP questions to JSON

What it does:
  - Reads extracted txt files from data/processed/questionnaires/text/
  - Parses ORIGINAL questions exactly as written in the PDFs
  - Saves structured JSON to data/processed/questionnaires/questions.json
  - NO warm versions hardcoded - LLM will rephrase at runtime

Usage:
    python scripts/questionnaire_to_json.py

Input:  data/processed/questionnaires/text/*.txt
Output: data/processed/questionnaires/questions.json
"""

import re
import json
from pathlib import Path
from datetime import datetime

# ── CONFIG ────────────────────────────────────────────────────────────────────
INPUT_DIR   = "data/processed/questionnaires/text"
OUTPUT_DIR  = "data/processed/questionnaires"
OUTPUT_FILE = "questions.json"

# ── FILE MAPPING ──────────────────────────────────────────────────────────────
FILES = {
    "pregnancy" : "CSEP-PATH_GAQ_P_UK version.txt",
    "postnatal" : "CSEP-PATH_GAQ_PP_Guidelines.txt",
}

# ── HELPERS ───────────────────────────────────────────────────────────────────

def parse_questions(text: str, questionnaire: str, for_user: str) -> list:
    """
    Parse questions from extracted txt file.
    Looks for patterns like:
    a.  Question text
    b.  Question text
    """
    questions = []
    
    # Find all question lines — pattern: letter + dot + text
    pattern = r'([a-p])\.\s+(.*?)(?=\n[a-p]\.|$)'
    matches  = re.findall(pattern, text, re.DOTALL)

    # Also find numbered sections (1. 2. 3.)
    section  = "main"
    lines    = text.split('\n')
    
    current_section = "main"
    q_number        = 0

    for line in lines:
        line = line.strip()

        # Detect section headers
        if line.startswith('1.') and 'pregnancy' in line.lower():
            current_section = "current_pregnancy"
        elif line.startswith('1.') and 'childbirth' in line.lower():
            current_section = "first_year_postpartum"
        elif line.startswith('2.') and 'previous' in line.lower():
            current_section = "previous_pregnancies"
        elif line.startswith('2.') and 'other medical' in line.lower():
            current_section = "other_conditions"

        # Detect question lines: a. b. c. etc
        q_match = re.match(r'^([a-p])\.\s+(.+)', line)
        if q_match:
            letter   = q_match.group(1)
            q_text   = q_match.group(2).strip()
            q_number += 1

            # Determine section number
            sec_num = "1" if current_section in [
                "current_pregnancy", 
                "first_year_postpartum",
                "main"
            ] else "2"

            questions.append({
                "question_id"      : f"{questionnaire.lower().replace('-','').replace('pp','pp')}_{sec_num}{letter}",
                "questionnaire"    : questionnaire,
                "for"              : for_user,
                "section"          : current_section,
                "question_number"  : f"{sec_num}{letter}",
                "question_original": q_text,
                "answer_type"      : "yes_no",
                "if_yes"           : "refer_to_gp",
                "source_type"      : "screening_question",
            })

    return questions


def main():
    print("\n" + "="*60)
    print("  APF Questionnaire → JSON")
    print("="*60)
    print(f"  Input : {INPUT_DIR}")
    print(f"  Output: {OUTPUT_DIR}/{OUTPUT_FILE}")

    # Check input directory
    if not Path(INPUT_DIR).exists():
        print(f"\n[ERROR] {INPUT_DIR} not found!")
        print(f"  Run first: python scripts/questionnaire_to_text.py")
        return

    # Create output directory
    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)

    all_questions = {
        "gaqp_questions" : [],
        "gaqpp_questions": [],
    }

    print(f"\n  {'File':<45} {'Questions':>10}")
    print(f"  {'-'*57}")

    # Process each file
    for user_type, filename in FILES.items():
        filepath = Path(INPUT_DIR) / filename

        if not filepath.exists():
            # Try to find file with similar name
            txt_files = list(Path(INPUT_DIR).glob("*.txt"))
            found     = None
            for f in txt_files:
                if "GAQ_PP" in f.name and user_type == "postnatal":
                    found = f
                elif "GAQ_P_UK" in f.name and user_type == "pregnancy":
                    found = f
            if found:
                filepath = found
            else:
                print(f"  ❌ {filename:<45} NOT FOUND")
                continue

        # Read txt file
        with open(filepath, "r", encoding="utf-8") as f:
            text = f.read()

        # Set questionnaire name
        questionnaire = "GAQ-P" if user_type == "pregnancy" else "GAQ-PP"

        # Parse questions
        questions = parse_questions(text, questionnaire, user_type)

        if user_type == "pregnancy":
            all_questions["gaqp_questions"] = questions
        else:
            all_questions["gaqpp_questions"] = questions

        print(f"  ✅ {filepath.name:<45} {len(questions):>10}")

        # Print parsed questions
        print(f"\n  Sample questions from {questionnaire}:")
        for q in questions[:3]:
            print(f"    [{q['question_number']}] {q['question_original'][:70]}...")
        print(f"    ... {len(questions)} total\n")

    # Add pelvic symptoms from Marlize email
    # These are NOT contraindications but require pelvic physio referral
    pelvic_symptoms = [
        {"symptom_id": "pelvic_1", "for": "postnatal", "original": "Urinary and/or faecal incontinence", "action": "refer_to_pelvic_physio", "signpost": "thepogp.co.uk/resources/booklets"},
        {"symptom_id": "pelvic_2", "for": "postnatal", "original": "Urinary and/or faecal urgency that is difficult to defer", "action": "refer_to_pelvic_physio", "signpost": "thepogp.co.uk/resources/booklets"},
        {"symptom_id": "pelvic_3", "for": "postnatal", "original": "Heaviness/pressure/bulge/dragging in the pelvic area", "action": "refer_to_pelvic_physio", "signpost": "thepogp.co.uk/resources/booklets"},
        {"symptom_id": "pelvic_4", "for": "postnatal", "original": "Pain with intercourse", "action": "refer_to_pelvic_physio", "signpost": "thepogp.co.uk/resources/booklets"},
        {"symptom_id": "pelvic_5", "for": "postnatal", "original": "Obstructive defecation", "action": "refer_to_pelvic_physio", "signpost": "thepogp.co.uk/resources/booklets"},
        {"symptom_id": "pelvic_6", "for": "postnatal", "original": "Pendular abdomen, separated abdominal muscles and/or decreased abdominal strength and function", "action": "refer_to_pelvic_physio", "signpost": "thepogp.co.uk/resources/booklets"},
        {"symptom_id": "pelvic_7", "for": "postnatal", "original": "Musculoskeletal lumbopelvic pain", "action": "refer_to_pelvic_physio", "signpost": "thepogp.co.uk/resources/booklets"},
    ]

    # Build final output
    output = {
        "metadata": {
            "created_at"   : datetime.now().isoformat(),
            "total_gaqp"   : len(all_questions["gaqp_questions"]),
            "total_gaqpp"  : len(all_questions["gaqpp_questions"]),
            "total_pelvic" : len(pelvic_symptoms),
            "source_gaqp"  : "CSEP-PATH_GAQ_P_UK_version.pdf",
            "source_gaqpp" : "CSEP-PATH_GAQ_PP_Guidelines.pdf",
            "source_pelvic": "Marlize email APF recommendation",
            "note"         : "Original questions only. LLM rephrases warmly at runtime.",
        },
        "gaqp_questions" : all_questions["gaqp_questions"],
        "gaqpp_questions": all_questions["gaqpp_questions"],
        "pelvic_symptoms": pelvic_symptoms,
    }

    # Save JSON
    output_path = Path(OUTPUT_DIR) / OUTPUT_FILE
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\n{'='*60}")
    print(f"  ✅ DONE!")
    print(f"{'='*60}")
    print(f"  GAQ-P questions  : {len(all_questions['gaqp_questions'])}")
    print(f"  GAQ-PP questions : {len(all_questions['gaqpp_questions'])}")
    print(f"  Pelvic symptoms  : {len(pelvic_symptoms)}")
    print(f"  Saved to         : {output_path}")
    print(f"\n  Next step → run:")
    print(f"  python scripts/embed_questionnaires.py")


if __name__ == "__main__":
    main()