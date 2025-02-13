from tkinter import *
from tkinter import messagebox, scrolledtext, font
from idlelib.tooltip import Hovertip


class BuildingDemo:
    """
    A class to represent a building demolition project and calculate various
    costs associated with it.

    Attributes:
        description (str): A brief description of the project.
        total_sqft (int): The total square footage of the building.
        total_equipment_cost (int): The estimated cost of equipment in dollars.
        total_disposal_cost (int): The estimated cost of disposal in dollars.
        num_days (int): The estimated number of days for the project.
        num_guys (int): The estimated number of workers.
        num_hours (int): The number of work hours per day (default is 10).
        bid_price (float): The calculated bid price for the project (initialized to 0.0).

    Methods: 
        calculate_cost_per_sqft() -> float:
            Calculates and prints the estimated cost per square foot.

        calculate_man_hours() -> float:
            Calculates the total man-hours cost for the project.
        
        calculate_equipment_cost() -> float:
            Calculates the total equipment cost for the project.

        calculate_disposal_cost() -> float:
            Calculates the total disposal cost for the project.

        calculate_job_cost() -> float:
            Calculates and prints the total job cost for the project.

        calculate_bid_price() -> float:
            Calculates and prints the bid price for the project.

        calculate_overhead_cost() -> float:
            Calculates the overhead costs for the project.

        generate_detailed_report() -> str:
            Generates a detailed report of the project.

        validate_input_data() -> bool:
            Validates the input data for the project.

        calculate_profit_margin() -> float:
            Calculates the profit margin for the project.

        calculate_total_cost() -> float:
            Calculates the total cost of the project.

        launch_demo_project_window():
            Launches a new Tkinter window for entering demolition project details.
    """
    
    DAILY_WORK_HOURS = 10
    COST_PER_MAN_HOUR = 30
    PROFIT = 1.35
    OVERHEAD_PERCENTAGE = 0.1

    def __init__(self, description, total_sqft: int = 0, 
                 total_equipment_cost: int = 0, total_disposal_cost: int = 0, 
                 num_days: int = 0, num_guys: int = 0):
        self.description = description
        self.total_sqft = total_sqft
        self.total_equipment_cost = total_equipment_cost      
        self.total_disposal_cost = total_disposal_cost
        self.num_days = num_days
        self.num_guys = num_guys
        self.num_hours = self.DAILY_WORK_HOURS
        self.bid_price = 0.0 # Initialize bid price

    def calculate_cost_per_sqft(self) -> float:
        """
        Calculates and prints the estimated cost per square foot.
        """
        if self.bid_price == 0.0:
            self.calculate_bid_price()
        price_per_sqft = self.bid_price / self.total_sqft
        print(f"The estimated bid price per SqFt is: ${price_per_sqft:.2f}")
        return price_per_sqft

    def calculate_man_hours(self) -> float:
        """
        Calculates the total man-hours cost for the project.
        """
        total_man_hours = self.num_days * self.num_guys * self.num_hours * \
                            self.COST_PER_MAN_HOUR
        return total_man_hours

    def calculate_equipment_cost(self) -> float:
        """
        Calculates the total equipment cost for the project.
        """
        equipment_cost = self.total_equipment_cost
        return equipment_cost

    def calculate_disposal_cost(self) -> float:
        """
        Calculates the total disposal cost for the project. 
        """
        disposal_cost = self.total_disposal_cost
        return disposal_cost

    def calculate_job_cost(self) -> float:
        """
        Calculates the total job cost for the project.
        """
        job_cost = self.calculate_man_hours() + self.calculate_equipment_cost() \
                        + self.calculate_disposal_cost()
        return job_cost

    def calculate_bid_price(self) -> float:
        """
        Calculates and prints the bid price for the project.
        """
        total_cost = self.calculate_total_cost()
        self.bid_price = total_cost * self.PROFIT
        print(f"The estimated bid price is: ${self.bid_price:,.2f}")
        return self.bid_price
    
    def calculate_overhead_cost(self) -> float:
        """
        Calculates the overhead costs for the project.
        """
        overhead_cost = self.calculate_job_cost() * self.OVERHEAD_PERCENTAGE
        return overhead_cost
    
    def on_closing_estimates(self, info):
        if info:
            info.quit()
            info.destroy()

    def generate_detailed_report(self) -> str:
        """
        Generates a detailed report of the project and displays it in a Tkinter window.
        """
        report = (
            f"{self.description} Project Report\n"
            f"-----------------------------------\n"
            f"Total SqFt: {self.total_sqft}\n"
            f"Number of Days: {self.num_days}\n"
            f"Number of Workers: {self.num_guys}\n"
            f"Total Man-Hours Cost: ${self.calculate_man_hours():,.2f}\n"
            f"Total Equipment Cost: ${self.calculate_equipment_cost():,.2f}\n"
            f"Total Disposal Cost: ${self.calculate_disposal_cost():,.2f}\n"
            f"Total Job Cost: ${self.calculate_job_cost():,.2f}\n"
            f"Overhead Cost: ${self.calculate_overhead_cost():,.2f}\n"
            f"Bid Price: ${self.calculate_bid_price():,.2f}\n"
            f"Price Per SqFt: ${self.calculate_cost_per_sqft():.2f}\n"
            f"Profit Margin: {self.calculate_profit_margin():.2f}%\n"
        )

        # Create a new Tkinter window to display the report
        info = Tk()
        info.title("Detailed Report")

        # Customize font and colors
        custom_font = font.Font(family="Times New Roman", size=12)
        text_area = scrolledtext.ScrolledText(info, wrap=WORD, width=60, height=20,
                                            font=custom_font, fg="green")
        text_area.pack(padx=10, pady=10)

        # Insert the report into the text area
        text_area.insert(END, report)

        # Set the protocol for window closing
        info.protocol("WM_DELETE_WINDOW", lambda: self.on_closing_estimates(info))

        info.mainloop()

    def validate_input_data(self) -> bool:
        """
        Validates the input data for the project.
        """
        if self.total_sqft <= 0 or self.total_equipment_cost < 0 or \
           self.total_disposal_cost < 0 or self.num_days <= 0 or \
           self.num_guys <= 0:
            print("Invalid input data. Please check the values.")
            return False
        return True

    def calculate_profit_margin(self) -> float:
        """
        Calculates the profit margin for the project.
        """
        job_cost = self.calculate_job_cost()
        profit_margin = round(((self.bid_price - job_cost) / self.bid_price) * 100, 2)
        return profit_margin

    def calculate_total_cost(self) -> float:
        """
        Calculates the total cost of the project.
        """
        total_cost = self.calculate_job_cost() + self.calculate_overhead_cost()
        return total_cost
    
    def create_tooltip(self, widget, text):
        """Creates tooltips for the tkinter launch_demo_window widgets"""
        Hovertip(widget, text, hover_delay=500)

    def launch_demo_project_window(self):
        """
        Launches a new Tkinter window for entering demolition project details.

        This function creates a new Tkinter TopLevel window for the user to input
        specific details related to a demolition project. It provides entry fields 
        for total square footage, total equipment cost, total disposal cost, number 
        of days, and number of workers. After the user enters the values and clicks 
        the estimate button, the function calculates the estimates and displays them 
        using the generate_detailed_report method.

        Creates:
            - A new Tkinter TopLevel window for entering project details.
            - Entry fields for total square footage, total equipment cost, 
              total disposal cost, number of days, and number of workers.
            - An estimate button to calculate and display the estimates.

        Calls:
            - get_user_input: Retrieves and validates user input.
            - BuildingDemo.calculate_job_cost: Calculates the total job cost.
            - BuildingDemo.calculate_bid_price: Calculates the bid price.
            - BuildingDemo.calculate_cost_per_sqft: Calculates the cost per square foot.
            - BuildingDemo.generate_detailed_report: Displays the calculated estimates.
        """
        demo_project_window = Toplevel()
        demo_project_window.title(f"{self.description} Estimating")
        demo_project_window.config(padx=50, pady=50)

        sqft_label = Label(demo_project_window, text="Total SqFt")
        sqft_label.grid(column=0, row=0, padx=5, pady=5)
        self.create_tooltip(sqft_label, "Enter total square footage.")
        sqft_input = Entry(demo_project_window)
        sqft_input.grid(column=1, row=0, padx=5, pady=5)

        equipment_cost_label = Label(demo_project_window, text="Total Equipment Cost")
        equipment_cost_label.grid(column=0, row=1, padx=5, pady=5)
        self.create_tooltip(equipment_cost_label, 
                    "Enter the total cost of equipment.\nAdds a 35% markup by default.")
        equipment_cost_input = Entry(demo_project_window)
        equipment_cost_input.grid(column=1, row=1, padx=5, pady=5)

        disposal_cost_label = Label(demo_project_window, text="Total Disposal Cost")
        disposal_cost_label.grid(column=0, row=2, padx=5, pady=5)
        self.create_tooltip(disposal_cost_label, "Enter the total disposal cost.\n"
                                            "Adds a 35% markup by default.")
        disposal_cost_input = Entry(demo_project_window)
        disposal_cost_input.grid(column=1, row=2, padx=5, pady=5)

        num_days_label = Label(demo_project_window, text="Total Number of Days")
        num_days_label.grid(column=0, row=3, padx=5, pady=5)
        self.create_tooltip(num_days_label, "Calculates man hours based off number of "
                                        "days entered.")
        num_days_input = Entry(demo_project_window)
        num_days_input.grid(column=1, row=3, padx=5, pady=5)

        num_guys_label = Label(demo_project_window, text="Total Number of Workers")
        num_guys_label.grid(column=0, row=4, padx=5, pady=5)
        self.create_tooltip(num_guys_label, "Calculates man hours based off number of days."
                    "\nHours are set to 10 and hourly rate is set at $30 per hour\n"
                    "plus a 35% markup by default.")
        num_guys_input = Entry(demo_project_window)
        num_guys_input.grid(column=1, row=4, padx=5, pady=5)

        demo_project_window.grab_set() # Make the demo window modal. 

        def get_user_input():
            """
            Prompt the user to input various parameters required for the BuildingDemo class.

            This function collects the following inputs from the user.
            - total_sqft (int): The total square footage of the building.
            - equipment_cost (int): The estimated cost of equipment in dollars.
            - disposal_cost (int): The estimated disposal cost in dollars.
            - num_days (int): The estimated number of days for the project.
            - num_guys (int): The estimated number of workers.

            Returns:
                BuildingDemo: An instance of the BuildingDemo class initialized with the
                user-provided values.
            
            Raises:
                ValueError: If the user inputs a non-integer value.
            """
            try:
                total_sqft = int(sqft_input.get())
                equipment_cost = int(equipment_cost_input.get())
                disposal_cost = int(disposal_cost_input.get())
                num_days = int(num_days_input.get())
                num_guys = int(num_guys_input.get())

                if total_sqft > 0 and equipment_cost >= 0 and disposal_cost >= 0 and \
                   num_days > 0 and num_guys > 0:
                    self.total_sqft = total_sqft
                    self.total_equipment_cost = equipment_cost
                    self.total_disposal_cost = disposal_cost
                    self.num_days = num_days
                    self.num_guys = num_guys
                    self.generate_detailed_report()
                else:
                    messagebox.showerror("Invalid Input", 
                            "Please enter valid positive numbers for all fields.")
            except ValueError:
                messagebox.showerror("Invalid Input", 
                            "Please enter valid integer values for all fields.")

        estimate_button = Button(demo_project_window, text="Estimate",
                                    command=get_user_input)
        estimate_button.grid(column=0, row=5, columnspan=2, pady=10)
    