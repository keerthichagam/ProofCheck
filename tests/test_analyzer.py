import pytest
from src.analyzer import analyze_results


def test_analyze_results_counts_statuses():
    results = [
        {
            "requirement": "Login works",
            "status": "pass",
            "evidence": {
                "type": "automated_test",
                "execution_id": "run-101",
                "result": "passed",
            },
        },
        {"requirement": "Checkout works", "status": "unknown"},
        {"requirement": "Payment works", "status": "fail"},
    ]

    report = analyze_results(
        results,
        trusted_runs=[
            {"execution_id": "run-101", "result": "passed"}
        ],
    )

    assert report["passed"] == 1
    assert report["failed"] == 1
    assert report["invalid"] == 1
    assert report["invalid_requirements"] == ["Checkout works"]
    assert report["total"] == 3


def test_analyze_results_with_empty_list():
    report = analyze_results([])

    assert report["passed"] == 0
    assert report["failed"] == 0
    assert report["needs_review"] == 0
    assert report["invalid"] == 0
    assert report["unverified"] == 0
    assert report["total"] == 0
    assert report["failed_requirements"] == []
    assert report["invalid_requirements"] == []
    assert report["unverified_requirements"] == []


def test_missing_requirement_is_invalid_not_passed():
    report = analyze_results([
        {"requirement": "", "status": "pass"}
    ])

    assert report["passed"] == 0
    assert report["invalid"] == 1
    assert report["invalid_requirements"] == ["Unknown requirement"]
    assert report["validation_errors"] == [
        "Requirement name is missing or invalid"
    ]
    assert report["total"] == 1


def test_malformed_result_is_invalid():
    report = analyze_results([None])

    assert report["passed"] == 0
    assert report["invalid"] == 1
    assert report["total"] == 1


def test_pass_rate_uses_only_executed_checks():
    results = [
        {
            "requirement": "Login works",
            "status": "pass",
            "evidence": {
                "type": "automated_test",
                "execution_id": "run-201",
                "result": "passed",
            },
        },
        {
            "requirement": "Checkout works",
            "status": "pass",
            "evidence": {
                "type": "automated_test",
                "execution_id": "run-202",
                "result": "passed",
            },
        },
        {"requirement": "Payment works", "status": "fail"},
        {"requirement": "Unknown check", "status": "unknown"},
        {"requirement": "Manual review", "status": "needs_review"},
    ]

    report = analyze_results(
        results,
        trusted_runs=[
            {"execution_id": "run-201", "result": "passed"},
            {"execution_id": "run-202", "result": "passed"},
        ],
    )

    assert report["passed"] == 2
    assert report["failed"] == 1
    assert report["unverified"] == 0
    assert report["pass_rate"] == 66.67


def test_missing_status_is_invalid():
    report = analyze_results([
        {"requirement": "Login works"}
    ])

    assert report["invalid"] == 1
    assert report["invalid_requirements"] == ["Login works"]
    assert report["validation_errors"] == [
        "Login works: Invalid or missing status"
    ]


def test_non_string_status_is_invalid():
    report = analyze_results([
        {"requirement": "Payment works", "status": 123}
    ])

    assert report["invalid"] == 1
    assert report["invalid_requirements"] == ["Payment works"]
    assert report["validation_errors"] == [
        "Payment works: Invalid or missing status"
    ]


def test_unverified_result_is_counted_separately():
    results = [
        {
            "requirement": "Password reset works",
            "status": "unverified",
        }
    ]

    report = analyze_results(results)
    assert report["unverified_requirements"] == [
    "Password reset works"
]
    assert report["unverified"] == 1
    assert report["passed"] == 0
    assert report["failed"] == 0
    assert report["invalid"] == 0
    assert report["total"] == 1
    assert report["pass_rate"] is None


def test_pass_with_incomplete_evidence_is_unverified():
    results = [
        {
            "requirement": "Password reset works",
            "status": "pass",
            "evidence": {
                "type": "automated_test",
                "result": "passed",
            },
        }
    ]

    report = analyze_results(results)

    assert report["passed"] == 0
    assert report["unverified"] == 1
    assert report["unverified_requirements"] == [
        "Password reset works"
    ]
    assert report["pass_rate"] is None

def test_pass_without_evidence_is_unverified():
    results = [
        {
            "requirement": "Login works",
            "status": "pass",
        }
    ]

    report = analyze_results(results)

    assert report["passed"] == 0
    assert report["unverified"] == 1
    assert report["unverified_requirements"] == [
        "Login works"
    ]
    assert report["pass_rate"] is None

def test_duplicate_trusted_runs_are_unverified():
    results = [
        {
            "requirement": "Login works",
            "status": "pass",
            "evidence": {
                "type": "automated_test",
                "execution_id": "run-101",
                "result": "passed",
            },
        }
    ]

    trusted_runs = [
        {"execution_id": "run-101", "result": "passed"},
        {"execution_id": "run-101", "result": "passed"},
    ]

    report = analyze_results(results, trusted_runs=trusted_runs)

    assert report["passed"] == 0
    assert report["unverified"] == 1
    assert report["unverified_requirements"] == ["Login works"]
    assert report["pass_rate"] is None


def test_pass_with_required_evidence_fields():
    results = [
        {
            "requirement": "Password reset works",
            "status": "pass",
            "evidence": {
                "type": "automated_test",
                "execution_id": "run-104",
                "result": "passed",
            },
        }
    ]

    report = analyze_results(
        results,
        trusted_runs=[
            {"execution_id": "run-104", "result": "passed"}
        ],
    )

    assert report["passed"] == 1
    assert report["unverified"] == 0
    assert report["pass_rate"] == 100.0


def test_unknown_execution_id_is_unverified():
    results = [
        {
            "requirement": "Password reset works",
            "status": "pass",
            "evidence": {
                "type": "automated_test",
                "execution_id": "run-missing",
                "result": "passed",
            },
        }
    ]

    trusted_runs = [
        {"execution_id": "run-104", "result": "passed"}
    ]

    report = analyze_results(results, trusted_runs=trusted_runs)

    assert report["passed"] == 0
    assert report["unverified"] == 1
    assert report["unverified_requirements"] == [
        "Password reset works"
    ]
    assert report["pass_rate"] is None

def test_conflicting_execution_result_is_unverified():
    results = [
        {
            "requirement": "Login works",
            "status": "pass",
            "evidence": {
                "type": "automated_test",
                "execution_id": "run-105",
                "result": "passed",
            },
        }
    ]

    trusted_runs = [
        {"execution_id": "run-105", "result": "failed"}
    ]

    report = analyze_results(results, trusted_runs=trusted_runs)

    assert report["passed"] == 0
    assert report["unverified"] == 1
    assert report["unverified_requirements"] == ["Login works"]
    assert report["pass_rate"] is None

def test_conflicting_trusted_runs_are_unverified():
    results = [
        {
            "requirement": "Login works",
            "status": "pass",
            "evidence": {
                "type": "automated_test",
                "execution_id": "run-106",
                "result": "passed",
            },
        }
    ]

    trusted_runs = [
        {"execution_id": "run-106", "result": "passed"},
        {"execution_id": "run-106", "result": "failed"},
    ]

    report = analyze_results(results, trusted_runs=trusted_runs)

    assert report["passed"] == 0
    assert report["unverified"] == 1
    assert report["unverified_requirements"] == ["Login works"]
    assert report["pass_rate"] is None
    
def test_trusted_runs_must_be_a_list():
    with pytest.raises(
        TypeError,
        match="trusted_runs must be a list",
    ):
        analyze_results([], trusted_runs="not-a-list")

def test_results_must_be_a_list():
    with pytest.raises(
        TypeError,
        match="results must be a list",
    ):
        analyze_results(None)

def test_malformed_trusted_run_is_ignored():
    results = [
        {
            "requirement": "Login works",
            "status": "pass",
            "evidence": {
                "type": "automated_test",
                "execution_id": "run-201",
                "result": "passed",
            },
        }
    ]

    trusted_runs = [
        None,
        {"execution_id": "", "result": "passed"},
        {"execution_id": "run-201", "result": "passed"},
    ]

    report = analyze_results(results, trusted_runs=trusted_runs)

    assert report["passed"] == 1
    assert report["unverified"] == 0
def test_malformed_result_type_is_ignored():
    results = [
        {
            "requirement": "Login works",
            "status": "pass",
            "evidence": {
                "type": "automated_test",
                "execution_id": "run-301",
                "result": "passed",
            },
        }
    ]

    trusted_runs = [
        {"execution_id": "run-301", "result": 123},
        {"execution_id": "run-301", "result": None},
        {"execution_id": "run-301", "result": "passed"},
        {"execution_id": [], "result": "passed"},
    ]

    report = analyze_results(results, trusted_runs=trusted_runs)

    assert report["passed"] == 1
    assert report["unverified"] == 0
