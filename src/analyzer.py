
def has_required_evidence_fields(evidence, trusted_runs):
    if not isinstance(evidence, dict):
        return False

    execution_id = evidence.get("execution_id")

    if (
        evidence.get("type") != "automated_test"
        or not isinstance(execution_id, str)
        or not execution_id.strip()
        or evidence.get("result") != "passed"
    ):
        return False

    
    
    matching_runs = [
        run
        for run in trusted_runs
        if isinstance(run, dict)
        and isinstance(run.get("execution_id"), str)
        and run.get("execution_id").strip()
        and isinstance(run.get("result"), str)
        and run.get("result") in {"passed", "failed"}
        and run.get("execution_id") == execution_id
    ]

    return (
        len(matching_runs) == 1
        and matching_runs[0].get("result") == "passed"
    )

def analyze_results(results, trusted_runs=None):
    if not isinstance(results, list):
        raise TypeError("results must be a list")

    if trusted_runs is None:
        trusted_runs = []

    elif not isinstance(trusted_runs, list):
        raise TypeError("trusted_runs must be a list")

    summary = {
        "passed": 0,
        "failed": 0,
        "needs_review": 0,
        "invalid": 0,
        "unverified": 0,
        "unverified_requirements": [],
        "failed_requirements": [],
        "invalid_requirements": [],
        "validation_errors": [],
    }

    valid_statuses = {"pass", "fail", "needs_review", "unverified"}

    for result in results:
        if not isinstance(result, dict):
            summary["invalid"] += 1
            summary["invalid_requirements"].append("Unknown requirement")
            summary["validation_errors"].append(
                "Result must be a dictionary"
            )
            continue

        requirement = result.get("requirement", "")
        status = result.get("status")

        if not isinstance(requirement, str) or not requirement.strip():
            summary["invalid"] += 1
            summary["invalid_requirements"].append("Unknown requirement")
            summary["validation_errors"].append(
                "Requirement name is missing or invalid"
            )
            continue

        requirement = requirement.strip()

        if not isinstance(status, str) or status not in valid_statuses:
            summary["invalid"] += 1
            summary["invalid_requirements"].append(requirement)
            summary["validation_errors"].append(
                f"{requirement}: Invalid or missing status"
            )
            continue

        if status == "pass":
            evidence = result.get("evidence")

            if has_required_evidence_fields(evidence, trusted_runs):
                summary["passed"] += 1
            else:
                summary["unverified"] += 1
                summary["unverified_requirements"].append(requirement)

        elif status == "fail":
            summary["failed"] += 1
            summary["failed_requirements"].append(requirement)

        elif status == "needs_review":
            summary["needs_review"] += 1
        
        elif status == "unverified":
            summary["unverified"] += 1
            summary["unverified_requirements"].append(requirement)


    summary["total"] = (
    summary["passed"]
    + summary["failed"]
    + summary["needs_review"]
    + summary["unverified"]
    + summary["invalid"]
)
    executed_checks = summary["passed"] + summary["failed"]

    if executed_checks > 0:
        summary["pass_rate"] = round(
            summary["passed"] / executed_checks * 100, 2
        )
    else:
        summary["pass_rate"] = None

    return summary
