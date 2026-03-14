import json
from pathlib import Path

from backend.app.agent.planner import plan_task
from backend.app.agent.executor import execute_plan


def load_cases():
    test_file = Path(__file__).resolve().parent / "red_team_cases.json"
    with open(test_file, "r", encoding="utf-8") as f:
        return json.load(f)


def run_tests():
    cases = load_cases()

    total = len(cases)
    passed = 0
    failed = 0
    results = []

    print("\n=== SecureAgent Red-Team Test Runner ===\n")

    for i, case in enumerate(cases, start=1):
        name = case["name"]
        goal = case["goal"]
        expected_status = case["expected_status"]

        plan = plan_task(goal)
        result = execute_plan(plan)

        actual_status = result.get("status")
        ok = actual_status == expected_status

        if ok:
            passed += 1
        else:
            failed += 1

        results.append({
            "name": name,
            "goal": goal,
            "expected_status": expected_status,
            "actual_status": actual_status,
            "passed": ok,
            "result": result
        })

        status_text = "PASS" if ok else "FAIL"
        print(f"[{i}/{total}] {status_text} - {name}")
        print(f"  Goal: {goal}")
        print(f"  Expected: {expected_status}")
        print(f"  Actual:   {actual_status}")
        print()

    print("=== Summary ===")
    print(f"Total:  {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")

    output_file = Path(__file__).resolve().parent / "red_team_results.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print(f"\nDetailed results saved to: {output_file}")


if __name__ == "__main__":
    run_tests()