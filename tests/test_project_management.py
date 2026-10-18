from estimate_project import project_management
import pytest


def _build_app_with_projects(*bid_numbers: str):
    app = project_management.ProjectManagementApp.__new__(project_management.ProjectManagementApp)
    app.data = {
        "projects": [{"bid_number": bid_number} for bid_number in bid_numbers],
        "tasks": [],
    }
    return app


def test_normalize_task_record_defaults_cost_code_and_value():
    app = _build_app_with_projects()

    normalized = app._normalize_task_record(
        {
            "cost_code": "9999",
            "cost_code_value": -250.0,
            "job_number": "2026-0001",
            "status": "Unsupported",
        }
    )

    assert normalized["cost_code"] == "0100"
    assert normalized["description"] == "Labor"
    assert normalized["cost_code_value"] == 0.0
    assert normalized["bid_number"] == "2026-0001"
    assert normalized["status"] == "Bidding"


def test_validate_import_task_accepts_and_converts_cost_code_value():
    app = _build_app_with_projects("2026-0001")
    candidate = {
        "cost_code": "0200",
        "description": "",
        "cost_code_value": "1800",
        "bid_number": "2026-0001",
        "start_date": "2026-01-08",
        "end_date": "2026-01-09",
        "status": "Bidding",
    }

    app._validate_import_task(candidate)

    assert candidate["description"] == "Misc"
    assert candidate["cost_code_value"] == 1800.0


def test_validate_import_task_rejects_negative_cost_code_value():
    app = _build_app_with_projects("2026-0001")
    candidate = {
        "cost_code": "0100",
        "description": "",
        "cost_code_value": "-1",
        "bid_number": "2026-0001",
        "start_date": "2026-01-08",
        "end_date": "2026-01-09",
        "status": "Bidding",
    }

    with pytest.raises(ValueError, match="cannot be negative"):
        app._validate_import_task(candidate)
