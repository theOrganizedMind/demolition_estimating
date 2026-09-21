from unittest.mock import Mock

import pytest

from estimate_project import building_demo
from estimate_project.building_demo import BuildingDemo


@pytest.fixture
def demo():
    return BuildingDemo(
        description="Building Demo",
        structure_type="Wood",
        total_sqft=1000,
        total_equipment_cost=5000,
        total_disposal_cost=2500,
        num_days=5,
        num_guys=4,
    )


def test_cost_calculations(demo):
    assert demo.calculate_man_hours() == 6000
    assert demo.calculate_equipment_cost() == 5000
    assert demo.calculate_disposal_cost() == 2500
    assert demo.calculate_job_cost() == 13500
    assert demo.calculate_overhead_cost() == 1350
    assert demo.calculate_total_cost() == 14850


def test_bid_and_profit_calculations(demo):
    bid_price = demo.calculate_bid_price()
    assert bid_price == pytest.approx(20047.5)
    assert demo.calculate_cost_per_sqft() == pytest.approx(20.0475)
    assert demo.calculate_profit_margin() == pytest.approx(32.66)


def test_validate_input_data_true_for_valid_values(demo):
    assert demo.validate_input_data() is True


@pytest.mark.parametrize(
    "kwargs",
    [
        {"total_sqft": 0},
        {"total_equipment_cost": -1},
        {"total_disposal_cost": -1},
        {"num_days": 0},
        {"num_guys": 0},
    ],
)
def test_validate_input_data_false_for_invalid_values(demo, kwargs):
    for key, value in kwargs.items():
        setattr(demo, key, value)
    assert demo.validate_input_data() is False


def test_generate_detailed_report_contains_key_sections(demo):
    report = demo.generate_detailed_report()

    assert "Building Demo Project Report" in report
    assert "Structure Type: Wood" in report
    assert "Total Job Cost:" in report
    assert "Bid Price:" in report
    assert "Profit Margin:" in report


def test_on_closing_estimates_calls_quit_and_destroy(demo):
    info = Mock()
    demo.on_closing_estimates(info)
    info.quit.assert_called_once_with()
    info.destroy.assert_called_once_with()


def test_create_tooltip_uses_hovertip(monkeypatch, demo):
    fake_widget = object()
    calls = []

    def fake_hovertip(widget, text, hover_delay):
        calls.append((widget, text, hover_delay))

    monkeypatch.setattr(building_demo, "Hovertip", fake_hovertip)
    demo.create_tooltip(fake_widget, "tooltip text")

    assert calls == [(fake_widget, "tooltip text", 500)]
