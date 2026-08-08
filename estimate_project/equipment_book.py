from tkinter import Tk, ttk, Label, Entry, Button, scrolledtext, font
import tkinter as tk
from tkinter import *

from postgresql import get_db_connection

# ========================================================================== #
# ================================== INFO ================================== #
# ========================================================================== #
# 
# ========================================================================== #
# ================================== TODO ================================== #
# ========================================================================== #
# TODO: 
# Add PostgreSQL variables to .env before running program. 
# See postgresql.py for required parameters.
# ========================================================================== #

def _format_rate(value):
    """Format numeric rates for display in the UI."""
    if value is None:
        return ""

    value = float(value)
    if value.is_integer():
        return str(int(value))
    return f"{value:.2f}".rstrip("0").rstrip(".")


def fetch_equipment_from_postgresql(project_type=None, equipment_name=None):
    """Fetch equipment rows and normalize them to GUI-friendly dictionaries."""
    query = """
        SELECT
            project_type,
            equipment_name,
            day_rate,
            week_rate,
            month_rate
        FROM equipment
    """
    params = []
    conditions = []

    if project_type:
        conditions.append("project_type ILIKE %s")
        params.append(f"%{project_type}%")
    if equipment_name:
        conditions.append("equipment_name ILIKE %s")
        params.append(f"%{equipment_name}%")

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    query += " ORDER BY project_type, equipment_name;"

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, params)
            rows = cur.fetchall()

    return [
        {
            "Project Type": row[0] or "N/A",
            "Equipment": row[1] or "",
            "Day": _format_rate(row[2]),
            "Week": _format_rate(row[3]),
            "Month": _format_rate(row[4]),
        }
        for row in rows
    ]


def insert_equipment_to_postgresql(project_type, 
                                   equipment_name, 
                                   day_rate, 
                                   week_rate, 
                                   month_rate):
    """Insert a new equipment row into PostgreSQL."""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO equipment (project_type, equipment_name, day_rate, week_rate, month_rate)
                VALUES (%s, %s, %s, %s, %s);
                """,
                (project_type, equipment_name, day_rate, week_rate, month_rate),
            )
        conn.commit()


def update_equipment_in_postgresql(original_equipment, updated_equipment):
    """Update an equipment row by matching its original values."""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE equipment
                SET
                    project_type = %s,
                    equipment_name = %s,
                    day_rate = %s,
                    week_rate = %s,
                    month_rate = %s
                WHERE
                    project_type IS NOT DISTINCT FROM %s
                    AND equipment_name IS NOT DISTINCT FROM %s
                    AND day_rate IS NOT DISTINCT FROM %s
                    AND week_rate IS NOT DISTINCT FROM %s
                    AND month_rate IS NOT DISTINCT FROM %s;
                """,
                (
                    updated_equipment["Project Type"],
                    updated_equipment["Equipment"],
                    updated_equipment["Day"],
                    updated_equipment["Week"],
                    updated_equipment["Month"],
                    original_equipment["Project Type"],
                    original_equipment["Equipment"],
                    original_equipment["Day"],
                    original_equipment["Week"],
                    original_equipment["Month"],
                ),
            )
            updated_rows = cur.rowcount
        conn.commit()

    return updated_rows


def delete_equipment_from_postgresql(equipment_item):
    """Delete an equipment row by matching all visible values."""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                DELETE FROM equipment
                WHERE
                    project_type IS NOT DISTINCT FROM %s
                    AND equipment_name IS NOT DISTINCT FROM %s
                    AND day_rate IS NOT DISTINCT FROM %s
                    AND week_rate IS NOT DISTINCT FROM %s
                    AND month_rate IS NOT DISTINCT FROM %s;
                """,
                (
                    equipment_item["Project Type"],
                    equipment_item["Equipment"],
                    equipment_item["Day"],
                    equipment_item["Week"],
                    equipment_item["Month"],
                ),
            )
            deleted_rows = cur.rowcount
        conn.commit()

    return deleted_rows


class EquipmentBook:
    def __init__(self):
        self.filtered_equipment = []
        self.total_equipment_cost = 0
        self.FONT = "Times New Roman"
        self.FONT_SIZE = 13
        self.TITLE_FONT = "Arial"
        self.TITLE_FONT_SIZE = 16


    def open_equipment_book(self, main_equipment_text, 
                            update_total_callback=None, 
                            standalone_mode=False):
        """
        Open the Equipment Management Window.

        This function creates a new window for managing equipment. It allows the user
        to add, update, remove, search, and select equipment for a project. The equipment
        data is stored in PostgreSQL, and the user can interact with the data through
        a graphical interface.

        Parameters:
        None

        Returns:
        None
        """

        selected_project_equipment = []

        def get_selected_equipment():
            """Return selected equipment index and record from current view."""
            selected_item = equipment_list.selection()
            if not selected_item:
                return None, None

            item_index = int(selected_item[0])
            equipment_data = self.filtered_equipment if self.filtered_equipment else fetch_equipment_from_postgresql()
            if item_index >= len(equipment_data):
                return None, None

            return item_index, equipment_data[item_index]


        def parse_rate_values(day_value, week_value, month_value):
            """Parse rate strings from the UI into floats for DB operations."""
            try:
                return float(day_value), float(week_value), float(month_value)
            except ValueError:
                return None


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
            from the input fields and adds a new equipment entry to PostgreSQL. If the
            equipment name is missing, it shows a warning message.

            Parameters:
            None

            Returns:
            None
            """
            project_type = combo_project_type.get()
            equipment_name = entry_equipment.get().strip()
            day_pricing = entry_day_pricing.get()
            week_pricing = entry_week_pricing.get()
            month_pricing = entry_month_pricing.get()
            rates = parse_rate_values(day_pricing, week_pricing, month_pricing)

            if equipment_name and rates:
                day_rate, week_rate, month_rate = rates
                insert_equipment_to_postgresql(
                    project_type if project_type else "N/A",
                    equipment_name,
                    day_rate,
                    week_rate,
                    month_rate,
                )

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
            row to PostgreSQL. If no equipment is selected, it shows a warning message.

            Parameters:
            None

            Returns:
            None
            """
            _, selected_equipment = get_selected_equipment()
            day_pricing = entry_day_pricing.get()
            week_pricing = entry_week_pricing.get()
            month_pricing = entry_month_pricing.get()
            rates = parse_rate_values(day_pricing, week_pricing, month_pricing)

            if selected_equipment and rates:
                day_rate, week_rate, month_rate = rates
                updated_equipment = {
                    "Project Type": combo_project_type.get() if combo_project_type.get() else "N/A",
                    "Equipment": entry_equipment.get().strip(),
                    "Day": day_rate,
                    "Week": week_rate,
                    "Month": month_rate,
                }

                original_equipment = {
                    "Project Type": selected_equipment["Project Type"],
                    "Equipment": selected_equipment["Equipment"],
                    "Day": float(selected_equipment["Day"]),
                    "Week": float(selected_equipment["Week"]),
                    "Month": float(selected_equipment["Month"]),
                }

                updated_rows = update_equipment_in_postgresql(original_equipment, updated_equipment)
                if updated_rows == 0:
                    show_toast("No matching equipment found to update.", "warning")
                    return

                # messagebox.showinfo("Success", "Equipment updated successfully!")
                show_toast("Equipment updated successfully!", "info")
                clear_fields()
                update_equipment_list()
            else:
                # messagebox.showwarning("Selection Error", "No contact selected!")
                show_toast("Select equipment and enter valid pricing values.", "warning")


        def remove_equipment():
            """
            Remove an equipment entry.

            This function retrieves the selected equipment from the equipment list, removes
            it from PostgreSQL, and updates the equipment list display. If no equipment
            is selected, it shows a warning message.

            Parameters:
            None

            Returns:
            None
            """
            _, selected_equipment = get_selected_equipment()
            if selected_equipment:
                equipment_to_delete = {
                    "Project Type": selected_equipment["Project Type"],
                    "Equipment": selected_equipment["Equipment"],
                    "Day": float(selected_equipment["Day"]),
                    "Week": float(selected_equipment["Week"]),
                    "Month": float(selected_equipment["Month"]),
                }
                deleted_rows = delete_equipment_from_postgresql(equipment_to_delete)
                if deleted_rows == 0:
                    show_toast("No matching equipment found to remove.", "warning")
                    return

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
            project_type = combo_project_type.get().lower()
            equipment_name = entry_equipment.get().lower()

            if not project_type and not equipment_name:
                # messagebox.showwarning("Input Error", "Please enter a project type or equipment name to search.")
                show_toast("Please enter a project type or \n"
                            " equipment name to search.", "warning")
                return

            self.filtered_equipment = fetch_equipment_from_postgresql(project_type, equipment_name)

            # Update the equipment list display with the filtered results
            update_equipment_list(self.filtered_equipment)


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
            self.filtered_equipment = []
            update_equipment_list()
            clear_fields()


        # Handle double-click event on equipment list
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
            _, selected_equipment = get_selected_equipment()
            if selected_equipment:
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
            from PostgreSQL. If a filtered equipment list is provided, it displays
            the filtered equipment instead.

            Parameters:
            filtered_equipment (list, optional): A list of filtered equipment to be displayed.
            Defaults to None.

            Returns:
            None
            """
            equipment_data = fetch_equipment_from_postgresql() if filtered_equipment is None else filtered_equipment
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
            _, selected_equipment = get_selected_equipment()
            if selected_equipment:

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

                selected_project_equipment.append(
                    {
                        "equipment": selected_equipment["Equipment"],
                        "duration": int(duration),
                        "pricing_type": pricing_type,
                        "total_price": total_price,
                    }
                )

                # Append the equipment details to the equipment_text widget
                if main_equipment_text is not None:
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

            tk.Label(toast, text=message, bg=bg_color, fg="black", 
                     font=(self.FONT, self.FONT_SIZE)).pack(fill="both", expand=True)

            # Use a Tcl-level `after` script so teardown does not try to invoke
            # a deleted Python callback command during window shutdown.
            toast.tk.call("after", 3000, f"catch {{destroy {toast._w}}}")

        def finish_button():
            """Close the equipment picker and show standalone summary results."""
            if not standalone_mode:
                return

            if not selected_project_equipment:
                show_toast("No equipment added to project.", "warning")
                return

            result_lines = []
            for item in selected_project_equipment:
                result_lines.append(
                    f"Equipment: {item['equipment']}\n"
                    f"Duration: {item['duration']} {item['pricing_type']}\n"
                    f"Price: ${item['total_price']:.2f}\n"
                )

            result = "\n".join(result_lines)
            result += f"\n\nTotal Equipment Cost: ${self.total_equipment_cost:,.2f}"

            equipment_window.destroy()

            summary_window = tk.Tk()
            summary_window.title("Equipment Summary")
            summary_window.geometry("450x350")
            summary_window.config(padx=10, pady=10)

            custom_font = font.Font(family="Times New Roman", size=12)
            result_box = scrolledtext.ScrolledText(
                summary_window,
                width=50,
                height=16,
                font=custom_font,
                fg="green",
            )
            result_box.insert("1.0", result)
            result_box.config(state="disabled")
            result_box.pack(fill="both", expand=True)

            summary_window.mainloop()

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
        if standalone_mode:
            Button(equipment_window, width=15, text="Finish",
                   command=finish_button).grid(row=6, column=2, sticky="w", pady=5)

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
    equipment_book.open_equipment_book(tk.Text(), standalone_mode=True)
