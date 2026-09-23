import json
from pathlib import Path

import requests


API_URL = "http://localhost:8000/extract"
EVAL_FILE = Path(__file__).parent / "intent-extraction-v1.json"

STRICT_FIELDS = [
    "category",
    "urgency",
    "needs_review",
]


def main():
    with EVAL_FILE.open("r", encoding="utf-8") as file:
        cases = json.load(file)

    passed = 0

    for index, case in enumerate(cases, start=1):
        response = requests.post(
            API_URL,
            json={"text": case["input"]},
            timeout=60,
        )

        if response.status_code != 200:
            print(f"Case {index}: FAIL — HTTP {response.status_code}")
            continue

        actual = response.json()
        expected = case["expected"]

        strict_fields_match = all(
            actual.get(field) == expected.get(field)
            for field in STRICT_FIELDS
        )

        confidence_ok = True

        if expected["needs_review"]:
            confidence_ok = actual.get("confidence", 1.0) < 0.5

        case_passed = strict_fields_match and confidence_ok

        if case_passed:
            passed += 1
            print(f"Case {index}: PASS")
        else:
            print(f"Case {index}: FAIL")

        print(f"  Input:    {case['input']}")
        print(f"  Action:   {actual.get('action')}")
        print(f"  Subject:  {actual.get('subject')}")
        print(f"  Category: {actual.get('category')}")
        print(f"  Urgency:  {actual.get('urgency')}")
        print(f"  Review:   {actual.get('needs_review')}")
        print(f"  Confidence: {actual.get('confidence')}")

        if not case_passed:
            print(f"  Expected closed fields: {expected}")

        print()

    total = len(cases)
    percentage = (passed / total) * 100

    print(f"Result: {passed}/{total} passed ({percentage:.1f}%)")


if __name__ == "__main__":
    main()