from tkinter import *
from tkinter import ttk, messagebox, scrolledtext, font

from equipment_dict import equipment_dict


def launch_equipment_cost_window():
    """
    Launches the Equipment Cost window application.

    This function creates a GUI application using Tkinter that allows users to
    select a project type, choose equipment, specify the rental duration and 
    quantity, and calculate the total cost of the selected equipment. 
    The application includes the following features:

    - A dropdown menu to select the project type (Interior Demolition, 
      Building Demo, House Demo).
    - A dynamically updated dropdown menu to select equipment based on the chosen
      project type.
    - Input fields to specify the rental duration (Day, Week, Month) and quantity.
    - An 'Add' button to add the selected equipment and its details to the project.
    - A 'Finish' button to display a summary of the selected equipment and
      their total cost in a new pop-up window.
    - The summary window includes a scrolled text widget to display the details
      and a function to clear the project equipment dictionary when the window
      is closed.

    The function initializes the main application window, sets up the layout and
    widgets, and binds events to update the equipment list based on the selected
    project type.
    """
    project_equipment = {}


    def update_equipment_list(event):
        """
        Updates the equipment list dropdown menu based on the selected project type.

        This function is called when the user selects a project type from the 
        project description dropdown menu. It updates the values of the equipment 
        description dropdown menu to display the equipment available for the 
        selected project type.

        Parameters:
        event (Event): The event object containing information about the 
        combobox selection change.

        Returns:
        None
        """
        selected_project = project_description.get()
        if selected_project:
            equipment_description['values'] = list(equipment_dict[selected_project].keys())


    def add_button():
        """
        Adds equipment details to the project equipment dictionary.

        This function retrieves the equipment description, duration, and duration
        quantity from the input fields.
        It then calculates the total price based on the equipment and duration, and
        updates the project equipment dictionary with the duration quantity and
        total price. If the equipment alreadys exists in the dictionary, it
        updates the existing entry; otherwise it creates a new entry.
        The input fields are cleared after the operation.

        Raises a warning if any input fields are empty.

        Parameters:
        None

        Returns:
        None
        """
        equipment = equipment_description.get()
        duration = duration_description.get()
        duration_qty = duration_quantity.get()

        if equipment and duration and duration_qty:
            duration_qty = int(duration_qty)
            price = equipment_dict[project_description.get()][equipment][duration] * duration_qty
            if equipment in project_equipment:
                project_equipment[equipment]['Duration Quantity'] += duration_qty
                project_equipment[equipment]['Total Price'] += price
            else:
                project_equipment[equipment] = {
                                                'Duration': duration, 
                                                'Duration Quantity': duration_qty,
                                                'Total Price': price
                                                }

            # Clear input fields
            equipment_description.set('')
            duration_description.set('')
            duration_quantity.delete(0, END)
        else:
            messagebox.showwarning("Input Error", "Please fill all fields")


    def finish_button():
        """
        Displays a summary of the project equipment and their total cost in a pop-up
        window.
        This function iterates through the project equipment dictionary, compiling
        a summary of each equipment's duration, duration quantity, and total price.
        It calculates the total cost of all equipment and displays the information
        in a new pop-up window with a scrolled text widget. When the pop-up window
        is closed, the project equipment dictionary is cleared.

        Parameters:
        None

        Returns:
        None
        """
        result = ""
        total_cost = 0
        for equipment, details in project_equipment.items():
            result += f"{equipment}:\nDuration: {details['Duration Quantity']} \
{details['Duration']},\n\
Total Price: ${details['Total Price']}\n\n"
            total_cost += details['Total Price']
        result += f"\nTotal Equipment Cost: ${total_cost:,.2f}"

        # Create a new pop-up window
        popup = Toplevel(root)
        popup.title("Equipment Summary")
        popup.geometry("400x350")

        # Add a scrolled text widget to the pop-up window
        custom_font = font.Font(family="Times New Roman", size=12)
        scrolled_text = scrolledtext.ScrolledText(popup, width=40, height=15,
                                                    font=custom_font, fg="green")
        scrolled_text.insert(INSERT, result)
        scrolled_text.pack(padx=10, pady=10)

        # Function to clear the project_equipment dictionary when the window is closed.
        def on_close():
            project_equipment.clear()
            popup.destroy()

        # Bind the close event to the on_close function
        popup.protocol("WM_DELETE_WINDOW", on_close)

    # ======================================================================== #
    # =============================== Main GUI =============================== #
    # ======================================================================== #
    root = Tk()
    root.minsize(width=150, height=150)
    root.title("Equipment Cost")
    root.config(padx=50, pady=50)

    project_description_label = Label(root, text="Project Description")
    project_description_label.grid(column=0, row=0, padx=5, pady=5)
    project_description = ttk.Combobox(root, state="readonly", 
                           values=[
                               'Interior Demolition', 
                               'Building Demo', 
                               'House Demo',
                               ]
                            )
    project_description.grid(column=0, row=1, padx=5, pady=5)
    project_description.bind("<<ComboboxSelected>>", update_equipment_list)

    equipment_description_label = Label(root, text="Equipment List")
    equipment_description_label.grid(column=0, row=2, padx=5, pady=5)
    equipment_description = ttk.Combobox(root, state="readonly",
                                        values=list(equipment_dict.keys()))
    equipment_description.grid(column=0, row=3, padx=5, pady=5)

    duration_label = Label(root, text="Duration")
    duration_label.grid(column=0, row=4, padx=5, pady=5)
    duration_description = ttk.Combobox(root, state="readonly",
                                        values=["Day", "Week", "Month"])
    duration_description.grid(column=0, row=5, padx=5, pady=5)

    duration_quantity_label = Label(root, text="Duration Quantity")
    duration_quantity_label.grid(column=0, row=6, padx=5, pady=5)
    duration_quantity = Entry(root)
    duration_quantity.grid(column=0, row=7, padx=5, pady=5)

    add_button_label = Button(root, text="Add", command=add_button)
    add_button_label.grid(column=0, row=8, padx=5, pady=5)

    finish_button_label = Button(root, text="Finish", command=finish_button)
    finish_button_label.grid(column=1, row=8, padx=5, pady=5)


    root.mainloop()


launch_equipment_cost_window()
