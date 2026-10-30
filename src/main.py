import json
from pathlib import Path
from src.analyzer import analyze_results
def main():
    project_root = Path(__file__).resolve().parent.parent
    input_file = project_root / "examples" / "sample_results.json"

    try:
        with input_file.open("r", encoding="utf-8") as file:
            results = json.load(file)
    except FileNotFoundError:
        print(f"Input file not found: {input_file}")
        return
    except json.JSONDecodeError as error:
        print(f"Invalid JSON: {error}")
        return

    if not isinstance(results, list):
        print("Invalid input: the JSON root must be a list.")
        return

    report = analyze_results(results)
    output_dir = project_root / "reports"
    output_dir.mkdir(exist_ok=True)

    output_file = output_dir / "latest_report.json"

    with output_file.open("w", encoding="utf-8") as file:
        json.dump(report, file, indent=4)

    print(f"Report saved to: {output_file}")

    print("\n=== ProofCheck Report ===")
    print(f"Total results: {report['total']}")
    print(f"Passed: {report['passed']}")
    print(f"Failed: {report['failed']}")
    print(f"Needs review: {report['needs_review']}")
    if report["invalid"] > 0:
        print(
        "WARNING: Invalid results detected. "
        "Review the validation errors."
    )
    if report["pass_rate"] is None:
        print("Pass rate: N/A (no executed checks)")
    else:
        print(f"Pass rate: {report['pass_rate']}%")

    print("Failed requirements:", report["failed_requirements"])
    print("Invalid requirements:", report["invalid_requirements"])
    print("Validation errors:", report["validation_errors"])


if __name__ == "__main__":
    main()
