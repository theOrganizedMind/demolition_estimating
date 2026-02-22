from tkinter import Tk, ttk, Label, Entry, Button
import tkinter as tk
import json
import os


class EquipmentBook:
    def __init__(self):

        self.EQUIPMENT_DATA = "json_files/equipment.json"
        self.filtered_equipment = []
        self.total_equipment_cost = 0
        self.FONT = "Times New Roman"
        self.FONT_SIZE = 13
        self.TITLE_FONT = "Arial"
        self.TITLE_FONT_SIZE = 16


    def open_equipment_book(self, main_equipment_text, update_total_callback=None):
        """
        Open the Equipment Management Window.

        This function creates a new window for managing equipment. It allows the user
        to add, update, remove, search, and select equipment for a project. The equipment
        data is stored in a JSON file, and the user can interact with the data through
        a graphical interface.

        Parameters:
        None

        Returns:
        None
        """

        def load_data(file_path):
            """
            Load data from a JSON file.

            This function checks if the specified JSON file exists. If it does, it reads
            the file and returns the data as a list. If the file does not exist, it returns
            an empty list.

            Parameters:
            file_path (str): The path to the JSON file.

            Returns:
            list: The data loaded from the JSON file, or an empty list if the file does not exist.
            """
            if os.path.exists(file_path):
                with open(file_path, 'r') as file:
                    return json.load(file)
            return []


        # Save data to file
        def save_data(data, file_path):
            """
            Save data to a JSON file.

            This function writes the specified data to a JSON file at the specified file path.

            Parameters:
            data (list): The data to be saved to the JSON file.
            file_path (str): The path to the JSON file.

            Returns:
            None
            """
            with open(file_path, 'w') as file:
                json.dump(data, file, indent=4)


        def clear_fields():
            """
            Clear the input fields.

            This function clears the values in the project type, equipment, and 
            pricing entry widgets.

            Parameters:
            None

            Returns:
            None
            """
            combo_project_type.set('')
            entry_equipment.delete(0, tk.END)
            entry_day_pricing.delete(0, tk.END)
            entry_week_pricing.delete(0, tk.END)
            entry_month_pricing.delete(0, tk.END)
            combo_pricing_type.delete(0, tk.END)
            entry_duration.delete(0, tk.END)


        def add_equipment():
            """
            Add a new equipment entry.

            This function retrieves the project type, equipment name, and pricing details
            from the input fields and adds a new equipment entry to the JSON file. If the
            equipment name is missing, it shows a warning message.

            Parameters:
            None

            Returns:
            None
            """
            project_type = combo_project_type.get()
            equipment = entry_equipment.get()
            day_pricing = entry_day_pricing.get()
            week_pricing = entry_week_pricing.get()
            month_pricing = entry_month_pricing.get()

            if equipment:
                new_equipment = {
                    "Project Type": project_type,
                    "Equipment": equipment, 
                    "Day": day_pricing, 
                    "Week": week_pricing,
                    "Month": month_pricing,
                }

                equipment = load_data(self.EQUIPMENT_DATA)
                equipment.append(new_equipment)
                save_data(equipment, self.EQUIPMENT_DATA)

                # messagebox.showinfo("Success", "Equipment added successfully!")
                show_toast("Equipment added successfully!", "info")
                clear_fields()
                update_equipment_list()
            else:
                # messagebox.showwarning("Input Error", 
                                    # "Equipment and pricing are required fields.")
                show_toast("Equipment and pricing are required fields.", "warning")
                

        def update_equipment():
            """
            Update an existing equipment entry.

            This function retrieves the selected equipment from the equipment list, updates
            its details with the values from the input fields, and saves the updated equipment
            list to the JSON file. If no equipment is selected, it shows a warning message.

            Parameters:
            None

            Returns:
            None
            """
            selected_item = equipment_list.selection()
            if selected_item:
                item_index = int(selected_item[0])
                equipment = load_data(self.EQUIPMENT_DATA)
                
                equipment[item_index] = {
                    "Project Type": combo_project_type.get() if combo_project_type.get() else "N/A",
                    "Equipment": entry_equipment.get(),
                    "Day": entry_day_pricing.get(),
                    "Week": entry_week_pricing.get(),
                    "Month": entry_month_pricing.get(),
                }
                
                save_data(equipment, self.EQUIPMENT_DATA)
                # messagebox.showinfo("Success", "Equipment updated successfully!")
                show_toast("Equipment updated successfully!", "info")
                clear_fields()
                update_equipment_list()
            else:
                # messagebox.showwarning("Selection Error", "No contact selected!")
                show_toast("No equipment selected!", "warning")


        def remove_equipment():
            """
            Remove an equipment entry.

            This function retrieves the selected equipment from the equipment list, removes
            it from the JSON file, and updates the equipment list display. If no equipment
            is selected, it shows a warning message.

            Parameters:
            None

            Returns:
            None
            """
            selected_item = equipment_list.selection()
            if selected_item:
                item_index = int(selected_item[0])
                equipment = load_data(self.EQUIPMENT_DATA)
                del equipment[item_index]
                save_data(equipment, self.EQUIPMENT_DATA)
                # messagebox.showinfo("Success", "Equipment removed successfully!")
                show_toast("Equipment removed successfully!", "info")
                clear_fields()
                update_equipment_list()
            else:
                # messagebox.showwarning("Selection Error", "No equipment selected!")
                show_toast("No equipment selected!", "warning")


        def search_equipment():
            """
            Search for equipment in the equipment list.

            This function filters the equipment list based on the project type or equipment
            name entered in the input fields and updates the equipment list display with
            the filtered results.

            Parameters:
            None

            Returns:
            None
            """
            global filtered_equipment
            project_type = combo_project_type.get().lower()
            equipment_name = entry_equipment.get().lower()

            if not project_type and not equipment_name:
                # messagebox.showwarning("Input Error", "Please enter a project type or equipment name to search.")
                show_toast("Please enter a project type or \n"
                            " equipment name to search.", "warning")
                return

            # Load equipment data from the JSON file
            equipment_data = load_data(self.EQUIPMENT_DATA)

            # Filter the equipment data based on the search criteria
            filtered_equipment = [
                equipment_item for equipment_item in equipment_data
                if (project_type in equipment_item["Project Type"].lower() if project_type else True) and
                (equipment_name in equipment_item["Equipment"].lower() if equipment_name else True)
            ]

            # Update the equipment list display with the filtered results
            update_equipment_list(filtered_equipment)


        def clear_results():
            """
            Clear the search results.

            This function clears the filtered equipment list and displays the complete
            equipment list.

            Parameters:
            None

            Returns:
            None
            """
            global filtered_equipment
            filtered_equipment = []
            update_equipment_list()
            clear_fields()


        # Handle double-click event on contact list
        def on_item_double_click(event):
            """
            Handle the double-click event on the equipment list.

            This function retrieves the selected equipment from the equipment list and 
            populates the input fields (project type, equipment name, and pricing details) 
            with the details of the selected equipment. If the equipment list is filtered, 
            it uses the filtered data; otherwise, it loads the complete equipment data.

            Parameters:
            event (Event): The event object representing the double-click event.

            Returns:
            None
            """
            # global filtered_equipment
            selected_item = equipment_list.selection()
            if selected_item:
                item_index = int(selected_item[0])
                equipment = self.filtered_equipment if self.filtered_equipment else load_data(self.EQUIPMENT_DATA)
                selected_equipment = equipment[item_index]
                combo_project_type.set(selected_equipment["Project Type"])
                entry_equipment.delete(0, tk.END)
                entry_equipment.insert(0, selected_equipment["Equipment"])
                entry_day_pricing.delete(0, tk.END)
                entry_day_pricing.insert(0, selected_equipment["Day"])
                entry_week_pricing.delete(0, tk.END)
                entry_week_pricing.insert(0, selected_equipment["Week"])
                entry_month_pricing.delete(0, tk.END)
                entry_month_pricing.insert(0, selected_equipment["Month"])


        def update_equipment_list(filtered_equipment=None):
            """
            Update the equipment list display.

            This function updates the equipment list display with the equipment data
            from the JSON file. If a filtered equipment list is provided, it displays
            the filtered equipment instead.

            Parameters:
            filtered_equipment (list, optional): A list of filtered equipment to be displayed.
            Defaults to None.

            Returns:
            None
            """
            equipment_data = load_data(self.EQUIPMENT_DATA) if filtered_equipment is None else filtered_equipment
            equipment_list.delete(*equipment_list.get_children())
            for index, equipment_item in enumerate(equipment_data):
                equipment_list.insert("", "end", iid=index, 
                                    values=(equipment_item["Project Type"],
                                        equipment_item["Equipment"], 
                                        equipment_item["Day"], 
                                        equipment_item["Week"], 
                                        equipment_item["Month"]))
                

        def add_equipment_to_project():
            """
            Add selected equipment to the cart.

            This function retrieves the selected equipment from the equipment list,
            calculates the total price based on the selected pricing type and duration,
            and appends the equipment details to the cart.

            Parameters:
            None

            Returns:
            None
            """
            selected_item = equipment_list.selection()
            if selected_item:
                item_index = int(selected_item[0])
                equipment = self.filtered_equipment if self.filtered_equipment else load_data(self.EQUIPMENT_DATA)
                selected_equipment = equipment[item_index]

                # Get the selected pricing type and duration
                pricing_type = combo_pricing_type.get()
                duration = entry_duration.get()

                if not pricing_type or not duration.isdigit():
                    # messagebox.showwarning("Input Error", 
                    #                        "Please select a pricing type and enter a valid duration.")
                    show_toast("Please select a pricing type and enter a valid duration.", "warning")
                    return

                # Calculate the price based on the selected pricing type and duration
                price_per_unit = float(selected_equipment[pricing_type])
                total_price = price_per_unit * int(duration)
                self.total_equipment_cost += total_price

                # Format the equipment details
                equipment_details = (
                    f"Equipment: {selected_equipment['Equipment']}\n"
                    f"Duration: {duration} {pricing_type}\n"
                    f"Price: ${total_price:.2f}\n\n"
                )

                # Append the equipment details to the equipment_text widget
                main_equipment_text.insert("end", equipment_details)

                if update_total_callback:
                    update_total_callback(self.total_equipment_cost)

                # Optionally, clear the fields after adding to the cart
                combo_project_type.set("")
                entry_equipment.delete(0, "end")
                entry_day_pricing.delete(0, "end")
                entry_week_pricing.delete(0, "end")
                entry_month_pricing.delete(0, "end")
                combo_pricing_type.set("")
                entry_duration.delete(0, "end")

                # messagebox.showinfo("Success", "Equipment added to project!")
                show_toast("Equipment added to project!", "info")

            else:
                # messagebox.showwarning("Selection Error", "No equipment selected!")
                show_toast("No equipment selected!", "warning")

        
        def show_toast(message, message_type="info"):
            """
            Show a toast-like notification.

            Parameters:
            message (str): The message to display.
            message_type (str): The type of message ("info", "warning", "error").

            Returns:
            None
            """
            toast = tk.Toplevel(equipment_window)
            toast.overrideredirect(True)  # Remove window decorations
            toast.geometry("300x50+500+300")  # Set size and position
            toast.attributes("-topmost", True)  # Keep on top

            # Set background color based on message type
            bg_color = "green" if message_type == "info" else "orange" if message_type == "warning" else "red"
            # tk.Label(toast, text=message, bg=bg_color, fg="white", font=(FONT, FONT_SIZE)).pack(fill="both", expand=True)

            # fg_color = "green" if message_type == "info" else "orange" if message_type == "warning" else "red"
            tk.Label(toast, text=message, bg=bg_color, fg="black", font=(self.FONT, self.FONT_SIZE)).pack(fill="both", expand=True)

            # Auto-dismiss the toast after 3 seconds
            # toast.after(3000, toast.destroy)

            # Auto-dismiss the toast after 3 seconds, but check if it still exists
            def safe_destroy():
                try:
                    toast.destroy()
                except tk.TclError:
                    pass

            toast.after(3000, safe_destroy)

        # ======================================================================== #
        # =============================== Equipment GUI ========================== #
        # ======================================================================== #
        equipment_window = Tk()
        equipment_window.title("Equipment")
        equipment_window.config(padx=25, pady=25)

        Label(equipment_window, text="Project Type").grid(row=0, column=0, sticky="e",
                                                            padx=10, pady=5)
        combo_project_type = ttk.Combobox(equipment_window, 
                                        values=("Interior Demolition", 
                                                "Building Demo", 
                                                "House Demo",
                                                "Other"), 
                                                width=27)
        combo_project_type.grid(row=0, column=1, padx=10, pady=5)

        Label(equipment_window, text="Equipment").grid(row=1, column=0, sticky="e",
                                                            padx=10, pady=5)
        entry_equipment = Entry(equipment_window, width=30)
        entry_equipment.grid(row=1, column=1, padx=10, pady=5)

        Label(equipment_window, text="Day").grid(row=2, column=0, sticky="e",
                                                            padx=10, pady=5)
        entry_day_pricing = Entry(equipment_window, width=30)
        entry_day_pricing.grid(row=2, column=1, padx=10, pady=5)

        Label(equipment_window, text="Week").grid(row=3, column=0, sticky="e",
                                                    padx=10, pady=5)
        entry_week_pricing = Entry(equipment_window, width=30)
        entry_week_pricing.grid(row=3, column=1, padx=10, pady=5)

        Label(equipment_window, text="Month").grid(row=4, column=0, sticky="e",
                                                    padx=10, pady=5)
        entry_month_pricing = Entry(equipment_window, width=30)
        entry_month_pricing.grid(row=4, column=1, padx=10, pady=5)

        Label(equipment_window, text="Pricing Type").grid(row=5, column=0, sticky="e",
                                                                padx=10, pady=5)
        combo_pricing_type = ttk.Combobox(equipment_window, 
                                        values=("Day", "Week", "Month"), 
                                        width=27)
        combo_pricing_type.grid(row=5, column=1, padx=10, pady=5)

        Label(equipment_window, text="Duration").grid(row=6, column=0, sticky="e",
                                                                padx=10, pady=5)
        entry_duration = Entry(equipment_window, width=30)
        entry_duration.grid(row=6, column=1, padx=10, pady=5)


        Button(equipment_window, width=15, text="Add Equipment", 
                command=add_equipment).grid(row=0, column=2, sticky="w", pady=5)
        Button(equipment_window, width=15, text="Update Equipment", 
                command=update_equipment).grid(row=1, column=2, sticky="w", pady=5)
        Button(equipment_window, width=15, text="Remove Equipment", 
                command=remove_equipment).grid(row=2, column=2, sticky="w", pady=5)
        Button(equipment_window, width=15, text="Search Equipment", 
                command=search_equipment).grid(row=3, column=2, sticky="w", pady=5)
        Button(equipment_window, width=15, text="Clear Fields", 
                command=clear_results).grid(row=4, column=2, sticky="w", pady=5)
        Button(equipment_window, width=15, text="Add to Project",
            command=add_equipment_to_project).grid(row=5, column=2, sticky="w", pady=5)

        equipment_list = ttk.Treeview(equipment_window, columns=("Project Type", "Equipment",
                                                                "Day", "Week", "Month"), 
                                                                show="headings")
        equipment_list.heading("Project Type", text="Project Type")
        equipment_list.heading("Equipment", text="Equipment")
        equipment_list.heading("Day", text="Day")
        equipment_list.heading("Week", text="Week")
        equipment_list.heading("Month", text="Month")
        equipment_list.grid(row=7, column=0, columnspan=3, padx=10, pady=10, sticky="nsew")

        # Bind double-click event to inventory list
        equipment_list.bind("<Double-1>", on_item_double_click)

        update_equipment_list()

        equipment_window.mainloop()


if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()  # Hide the root window
    
    equipment_book = EquipmentBook()
    equipment_book.open_equipment_book(tk.Text())  # Pass a dummy Text widget for testing
