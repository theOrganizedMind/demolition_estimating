from tkinter import *
from tkinter import ttk, messagebox

from building_demo import BuildingDemo
from interior_demo import InteriorDemo
from house_demo import HouseDemo


# ============================================================================ #
# ==================================== INFO ================================== #
# ============================================================================ #
# Create the first window where the user selects the project description.
# Based off the desription, the appropriate class will be chosen and the user 
# will be prompted to enter the project details.
# ============================================================================ #
# ==================================== TODO ================================== #
# ============================================================================ #
# TODO: 
# ============================================================================ #


def estimate_project():
    """
    Estimates the project based on the selected description.

    This function retrieves the selected project description from the Tkinter 
    Combobox.
    Based on the selected description, it initializes the appropriate class 
    (InteriorDemo, BuildingDemo, or HouseDemo) and launches the corresponding 
    project window for the user to input specific project details.

    If the selected description is invalid, an error message is displayed.

    Raises:
        ValueError: If the selected description is invalid.

    Calls:
        - InteriorDemo.launch_demo_project_window: Launches the window for 
          interior demolition projects.
        - BuildingDemo.launch_demo_project_window: Launches the window for 
          building demolition projects.
        - HouseDemo.launch_demo_project_window: Launches the window for 
          house demolition projects.
    """
    description_value = description.get()
    if description_value == 'Interior Demolition':
        interior_demo = InteriorDemo(description_value)
        interior_demo.launch_demo_project_window()
    elif description_value == 'Building Demo':
        building_demo = BuildingDemo(description_value)
        building_demo.launch_demo_project_window()
    elif description_value == 'House Demo':
        house_demo = HouseDemo(description_value)
        house_demo.launch_demo_project_window()
    else:
        messagebox.showerror("Invalid Description", 
                             "Please select a valid description.")
        return None


root = Tk()
root.minsize(width=150, height=150)
root.title("Demolition Project Estimating")
root.config(padx=50, pady=50)

description_label = Label(root, text="Description")
description_label.grid(column=0, row=0, padx=5, pady=5)
description = ttk.Combobox(root, state="readonly", 
                           values=[
                               'Interior Demolition', 
                               'Building Demo', 
                               'House Demo',
                               ]
                            )
description.grid(column=1, row=0, padx=5, pady=5)

estimate_equipment_button = Button(root, text="Estimate", 
                                   command=estimate_project)
estimate_equipment_button.grid(column=1, row=5, padx=5, pady=5)

# Set the protocol for window closing
root.protocol("WM_DELETE_WINDOW")

root.mainloop()
