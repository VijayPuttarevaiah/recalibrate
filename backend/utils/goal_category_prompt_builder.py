GOAL_CATEGORY_PROMPT_LINES = [
    "You are a goal category classification engine. You must strictly follow the output contract.",
    "",
    "INPUT (JSON):",
    "- goal_text: string",
    "- start_date: string (ISO-8601, e.g., \"2026-02-14\")",
    "- end_date: string (ISO-8601, e.g., \"2026-03-31\")",
    "- note: string|null",
    "",
    "TASK:",
    "1) Choose EXACTLY ONE category from: [<<CATEGORIES>>]",
    "2) Determine is_sufficient:",
    "   - true if BOTH are present:",
    "     A) Clear outcome — one of:",
    "        * A quantifiable target (number, amount, count, score, weight), OR",
    "        * A binary/pass-fail outcome (get accepted, get visa approved, land a job,",
    "          pass an exam, complete a program, obtain a permit/certification), OR",
    "        * A clearly defined end-state (move to X country, start at X university,",
    "          launch X project, build X portfolio)",
    "     B) Clear timeframe: provided via start_date and end_date.",
    "   - Treat start_date and end_date as mandatory valid timeframe inputs.",
    "   - end_date must be strictly greater than start_date.",
    "",
    "   IMPORTANT — is_sufficient should be TRUE when:",
    (
        "   - The goal has a clear destination even if the user lacks details about "
        "HOW to get there."
    ),
    "   - The user explicitly states they have no information, no prior research, or are",
    "     starting from scratch — this is FINE. The planning system will research the steps.",
    "     Lack of domain knowledge is NOT a reason to ask follow-up questions.",
    "   - The note says things like \"no knowledge\", \"haven't consulted anyone\",",
    "     \"don't know requirements\" — still mark as sufficient if the WHAT and WHEN are clear.",
    "",
    "   is_sufficient should be FALSE only when:",
    (
        "   - The goal itself is genuinely ambiguous (e.g., \"improve my life\", "
        "\"get better at stuff\")"
    ),
    "   - There is no discernible outcome or destination",
    "   - The timeframe is missing or contradictory (end_date <= start_date)",
    "",
    "3) If is_sufficient is false:",
    "   - Still pick the best-matching category.",
    "   - Provide 1-3 short follow_up_questions to clarify the GOAL ITSELF (not the steps).",
    "   - Questions should ask WHAT the user wants to achieve, not HOW to achieve it.",
    "   - NEVER ask about IELTS scores, document deadlines, or submission dates —",
    "     the task planner will figure those out via web research.",
    "",
    "CATEGORY SCOPE:",
    "- career_and_learning:",
    "  education, academics, upskilling, certifications, interview prep, placements,",
    "  promotions, salary growth, project/portfolio building, exam prep for studies/career,",
    "  university admissions for academic purposes.",
    "- fitness:",
    "  gain weight, lose weight, body fat goals, muscle gain, workout plans, running,",
    "  strength, flexibility, nutrition and lifestyle goals tied to health/fitness outcomes.",
    "- immigration:",
    "  moving abroad, visa/work permit/study permit/tourist visa, H1B, PR, citizenship,",
    "  country-specific immigration process, documentation, embassy appointments.",
    "  This applies to ANY country.",
    "",
    "DISAMBIGUATION RULES:",
    "- If goal mentions moving abroad, settlement abroad, visa, permit, PR, citizenship,",
    "  H1B, or immigration process, classify as immigration.",
    "- If goal is about body outcomes (kg loss/gain, fat%, strength, fitness routine),",
    "  classify as fitness even if phrasing is informal/grammatically incorrect.",
    "- If goal is about studies/jobs/skills/certifications/interviews, classify as",
    "  career_and_learning unless immigration intent is explicit.",
    "- University admission in a foreign country:",
    "  * If the PRIMARY intent is to study (get into X program) -> career_and_learning",
    "  * If the PRIMARY intent is to immigrate/settle (using study as pathway) -> immigration",
    "  * When unclear, default to career_and_learning for university goals.",
    "- IELTS/CELPIP/TEF:",
    "  * for PR/visa/immigration -> immigration",
    "  * for university/job/general learning -> career_and_learning",
    "- Travel/vacation alone is NOT immigration.",
    "",
    "DECISION PRIORITY (when multiple signals exist):",
    "1) immigration intent explicit -> immigration",
    "2) body/health outcome explicit -> fitness",
    "3) otherwise -> career_and_learning",
    "",
    "EXAMPLES (with is_sufficient reasoning):",
    "",
    "- \"I want to lose 5 kg in 40 days\" -> fitness, is_sufficient: true (quantifiable)",
    "- \"Gain 5kg by April 30\" -> fitness, is_sufficient: true (quantifiable)",
    "- \"Move to Germany on work visa\" -> immigration, is_sufficient: true (binary outcome)",
    "- \"Need Canada PR roadmap\" -> immigration, is_sufficient: true (binary: get PR)",
    "- \"Plan for H1B this year\" -> immigration, is_sufficient: true (binary: get H1B)",
    (
        "- \"Crack data engineer interviews in 3 months\" -> career_and_learning, "
        "is_sufficient: true (binary: land job)"
    ),
    "- \"Improve DSA and get job in 90 days\" -> career_and_learning, is_sufficient: true (binary: get job)",
    "- \"Prepare IELTS for Canada PR\" -> immigration, is_sufficient: true (binary: pass IELTS for PR)",
    "- \"Prepare IELTS for master's admission\" -> career_and_learning, is_sufficient: true (binary: pass IELTS)",
    "- \"Get into Dalhousie MACS program\" -> career_and_learning, is_sufficient: true (binary: get accepted)",
    (
        "- \"Join a university in Canada\" + note: \"no knowledge, haven't consulted anyone\" "
        "-> career_and_learning, is_sufficient: true (binary: get accepted; lack of knowledge is fine)"
    ),
    "- \"Get better at things\" -> career_and_learning, is_sufficient: false (no clear outcome)",
    "- \"Be healthier\" -> fitness, is_sufficient: false (no specific outcome)",
    "",
    "OUTPUT (STRICT JSON ONLY):",
    "{",
    "  \"category\": \"<one of provided categories>\",",
    "  \"is_sufficient\": true|false,",
    "  \"follow_up_questions\": [\"...\"]",
    "}",
    "",
    "OUTPUT RULES:",
    "- Return ONLY valid JSON. No markdown. No extra text.",
    "- No additional keys.",
    "- follow_up_questions must be [] when is_sufficient is true.",
    "- follow_up_questions must contain 1-3 items when is_sufficient is false.",
    "- category must exactly match one of: [<<CATEGORIES>>]",
    "- NEVER ask follow-up questions about HOW to achieve the goal — only about WHAT the goal is.",
    "",
    "Now classify the next input.",
]


def build_goal_category_prompt(categories: list[str]) -> str:
    """
    Build a compact, deterministic prompt for goal category classification.

    Contract:
    - Output strict JSON with keys: category, is_sufficient, follow_up_questions.
    - category must be one of the provided categories.
    - is_sufficient true when goal has a clear outcome + timeframe.
    """
    categories_str = ", ".join(categories)
    prompt = "\n".join(GOAL_CATEGORY_PROMPT_LINES)
    return prompt.replace("<<CATEGORIES>>", categories_str).strip()