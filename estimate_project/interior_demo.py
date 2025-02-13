from building_demo import BuildingDemo


class InteriorDemo(BuildingDemo):
    """
    A class to represent a interior demolition project, inheriting from BuildingDemo.

    This class inherits all attributes and methods from the BuildingDemo class
    and can be used to calculate various costs associated with a interior demolition
    project.

    Attributes:
        description (str): A brief description of the project.
        total_sqft (int): The total square footage of the building.
        total_equipment_cost (int): The estimated cost of equipment in dollars.
        total_disposal_cost (int): The estimated cost of disposal in dollars.
        num_days (int): The estimated number of days for the project.
        num_guys (int): The estimated number of workers.
        num_hours (int): The number of work hours per day (default is 10).
        bid_price (float): The calculated bid price for the project (initialized to 0.0).
    """

    def __init__(self, description, total_sqft: int = 0, 
                 total_equipment_cost: int = 0, total_disposal_cost: int = 0, 
                 num_days: int = 0, num_guys: int = 0):
        super().__init__(description, total_sqft, total_equipment_cost, 
                         total_disposal_cost, num_days, num_guys)
