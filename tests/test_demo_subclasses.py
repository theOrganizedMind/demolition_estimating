from estimate_project.building_demo import BuildingDemo
from estimate_project.house_demo import HouseDemo
from estimate_project.interior_demo import InteriorDemo


def test_house_demo_is_building_demo():
    demo = HouseDemo(
        description="House Demo",
        total_sqft=1200,
        total_equipment_cost=500,
        total_disposal_cost=300,
        num_days=2,
        num_guys=3,
    )

    assert isinstance(demo, BuildingDemo)
    assert demo.description == "House Demo"
    assert demo.num_hours == BuildingDemo.DAILY_WORK_HOURS


def test_interior_demo_is_building_demo():
    demo = InteriorDemo(
        description="Interior Demolition",
        total_sqft=800,
        total_equipment_cost=400,
        total_disposal_cost=200,
        num_days=1,
        num_guys=2,
    )

    assert isinstance(demo, BuildingDemo)
    assert demo.description == "Interior Demolition"
    assert demo.num_hours == BuildingDemo.DAILY_WORK_HOURS
