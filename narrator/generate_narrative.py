"""
Mamaearth Returns & Growth Intelligence Pipeline
Part 3: GenAI-Powered Insight Narrator

Run this script from the repository root: python narrator/generate_narrative.py

Set GEMINI_API_KEY as an environment variable to use the live Gemini API path.
Free-tier key: generate one at https://aistudio.google.com (never a paid-only key).
If no key is set, or the API call fails for any reason (network, rate limit,
server error), this automatically falls back to generate_scr_narrative_offline,
which builds the identical SCR structure from the same findings dict with zero
network access and zero environment setup required.
"""

import os
import json

from google import genai
from google.genai import types


def generate_scr_narrative(findings: dict) -> dict:
    """
    Builds an SCR (Situation-Complication-Resolution) business narrative from
    the verified findings dict, using the Gemini API. Falls back to the
    offline template path if no API key is configured or the call fails.
    """
    api_key = os.environ.get('GEMINI_API_KEY')

    if not api_key:
        return generate_scr_narrative_offline(findings)

    client = genai.Client(api_key=api_key)

    system_instruction = (
        "You are a senior data analyst writing for Mamaearth's regional ops and finance heads. "
        "Structure your response into exactly three labeled sections: Situation, Complication, "
        "Resolution. Every number you state in the output must come from the supplied findings "
        "and appear with the same value — do not invent, round differently, or estimate any statistic."
    )

    user_prompt = (
        f"Here are the verified findings from our returns and revenue analysis:\n\n"
        f"Cleaned total revenue: INR {findings['cleaned_total_revenue_inr']}\n"
        f"Raw total revenue before cleaning: INR {findings['raw_total_revenue_inr']}\n"
        f"Reconciliation delta (due to duplicate removal): INR {findings['duplicate_reconciliation_delta_inr']}\n"
        f"Return rate by payment method: {findings['return_rate_by_payment']}\n"
        f"Highest-risk segment: {findings['highest_risk_segment']}\n"
        f"True peak revenue month: {findings['true_peak_month']}\n"
        f"Outlier-inflated month (before correction): {findings['outlier_inflated_month']}\n\n"
        f"Write the SCR business narrative now."
    )

    try:
        response = client.models.generate_content(
            model="gemini-3.8-flash",
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.0,  # deterministic output: this is a factual business report, not creative writing
                max_output_tokens=1024,
                # Gemini 3-series models consume max_output_tokens on internal "thinking" before
                # producing visible text. thinking_level="low" keeps reasoning minimal for this
                # straightforward formatting task, leaving enough budget for the full narrative
                # instead of truncating mid-sentence.
                thinking_config=types.ThinkingConfig(thinking_level="low"),
                http_options=types.HttpOptions(timeout=10000)  # milliseconds, per taught Gemini minimum
            )
        )
        return {
            "status": "success",
            "narrative": response.text,
            "tokens": response.usage_metadata.total_token_count,
            "source": "online"
        }
    except Exception as e:
        print(f"Online call failed ({e}); falling back to offline narrative.")
        return generate_scr_narrative_offline(findings)


def generate_scr_narrative_offline(findings: dict) -> dict:
    """
    Deterministic, fully offline SCR narrative built directly from the findings
    dict via string templates. No network call, no API key, same return-dict
    shape as generate_scr_narrative. Runs with zero environment configuration.
    """
    situation = (
        f"Mamaearth's revenue reconciliation establishes a cleaned total revenue of "
        f"INR {findings['cleaned_total_revenue_inr']}, adjusted from a raw total revenue "
        f"before cleaning of INR {findings['raw_total_revenue_inr']} following a "
        f"reconciliation delta of INR {findings['duplicate_reconciliation_delta_inr']} "
        f"due to duplicate removal. The true peak revenue month is "
        f"{findings['true_peak_month']['month']}, delivering revenue of "
        f"INR {findings['true_peak_month']['revenue_inr']}."
    )

    complication = (
        f"Return rates vary sharply by payment method: COD stands at "
        f"{findings['return_rate_by_payment']['COD']}%, versus CARD at "
        f"{findings['return_rate_by_payment']['CARD']}% and UPI at "
        f"{findings['return_rate_by_payment']['UPI']}%. The highest-risk segment is "
        f"{findings['highest_risk_segment']['payment_method']} orders in city tier "
        f"{findings['highest_risk_segment']['city_tier']}, with a return rate of "
        f"{findings['highest_risk_segment']['return_rate_pct']}%. Additionally, "
        f"{findings['outlier_inflated_month']['month']} showed an outlier-inflated "
        f"apparent revenue of INR {findings['outlier_inflated_month']['apparent_revenue_inr']}, "
        f"corrected down to INR {findings['outlier_inflated_month']['corrected_revenue_inr']}."
    )

    resolution = (
        f"Finance and regional operations should prioritize tightening COD controls in "
        f"city tier {findings['highest_risk_segment']['city_tier']} to address the "
        f"{findings['highest_risk_segment']['return_rate_pct']}% return rate there, while "
        f"encouraging migration toward lower-risk CARD and UPI channels. Forecasting and "
        f"capacity planning should be anchored to the verified "
        f"{findings['true_peak_month']['month']} baseline of "
        f"INR {findings['true_peak_month']['revenue_inr']}, and duplicate-detection checks "
        f"should be made permanent to prevent the INR "
        f"{findings['duplicate_reconciliation_delta_inr']} leakage seen this cycle."
    )

    narrative = (
        f"### Situation\n{situation}\n\n"
        f"### Complication\n{complication}\n\n"
        f"### Resolution\n{resolution}"
    )

    return {"status": "success", "narrative": narrative, "tokens": None, "source": "offline"}


def check_numeric_accuracy(narrative: str, findings: dict) -> bool:
    """
    Confirms five key verified figures (plus the peak month name) are present
    in the narrative text as substrings, after normalizing commas. Prints a
    pass/fail line per figure. Returns True only if every check passes.
    """
    normalized = narrative.replace(',', '')

    checks = [
        ("Cleaned total revenue", str(findings['cleaned_total_revenue_inr'])),
        ("COD return rate", str(findings['return_rate_by_payment']['COD'])),
        ("Highest-risk segment return rate", str(findings['highest_risk_segment']['return_rate_pct'])),
        ("Reconciliation delta", str(findings['duplicate_reconciliation_delta_inr'])),
        ("True peak month revenue", str(findings['true_peak_month']['revenue_inr'])),
    ]

    all_passed = True
    for label, value in checks:
        passed = value in normalized
        all_passed = all_passed and passed
        print(f"{'PASS' if passed else 'FAIL'}: {label} ({value})")

    month_num = findings['true_peak_month']['month']  # e.g. "2026-03"
    month_names = {"01": "January", "02": "February", "03": "March", "04": "April",
                   "05": "May", "06": "June", "07": "July", "08": "August",
                   "09": "September", "10": "October", "11": "November", "12": "December"}
    month_name = month_names.get(month_num.split('-')[1], month_num)
    month_passed = (month_name in normalized) or (month_num in normalized)
    all_passed = all_passed and month_passed
    print(f"{'PASS' if month_passed else 'FAIL'}: True peak month name ({month_name} or {month_num})")

    print(f"\nOverall: {'ALL CHECKS PASSED' if all_passed else 'SOME CHECKS FAILED'}")
    return all_passed


if __name__ == "__main__":
    with open('narrator/findings.json', 'r') as f:
        findings = json.load(f)

    result = generate_scr_narrative(findings)
    print(f"Status: {result['status']}")
    print(f"Tokens: {result.get('tokens')}")
    print(result['narrative'])
    print()

    # Save the online path's actual output once, per the brief, so the
    # checker and grader can verify against a saved sample without needing
    # a live API call or key at grading time. Only overwrite sample_output.txt
    # when the narrative genuinely came from the live Gemini call — never
    # overwrite a real saved sample with an offline-fallback result.
    if result.get('source') == 'online':
        with open('narrator/sample_output.txt', 'w') as f:
            f.write(result['narrative'])
        print("Saved narrator/sample_output.txt (genuine online output)\n")
    else:
        print("Narrative came from the offline fallback this run — "
              "narrator/sample_output.txt was left untouched.\n")

    check_numeric_accuracy(result['narrative'], findings)
