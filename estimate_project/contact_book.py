from tkinter import Tk, Label, Entry, Button, ttk
import tkinter as tk
import json
import os


class ContactBook:
    """
    ContactBook class for managing contacts in a JSON file.

    This class provides methods to add, update, remove, search, and select 
    contacts. The contact data is stored in a JSON file, and the user can 
    interact with the data through a graphical interface.

    Attributes:
    - CONTACTS_DATA (str): Path to the JSON file where contacts are stored.
    - filtered_contacts (list): List of contacts filtered by search criteria.
    """
    def __init__(self):
        """
        Initialize the ContactBook class.

        This method sets up the initial state of the ContactBook class, including
        the path to the contacts data file and an empty list for filtered contacts.
        """
        self.CONTACTS_DATA = "json_files/contacts.json"
        self.filtered_contacts = []

        self.FONT = "Times New Roman"
        self.FONT_SIZE = 13
        self.TITLE_FONT = "Arial"
        self.TITLE_FONT_SIZE = 16

    def open_contact_book(self, company_var, billing_address_var, 
                          contact_name_var, phone_var, email_var):
        """
        Open the Contact Book Window.

        This function creates a new window for managing contacts. It allows the user
        to add, update, remove, search, and select contacts. The contact data is stored
        in a JSON file, and the user can interact with the data through a graphical
        interface.

        Features:
        - Add a new contact with company name, client name, phone number, and email.
        - Update an existing contact's details.
        - Remove a contact from the contact book.
        - Search for contacts by company name or client name.
        - Select a contact to populate fields in the main GUI.

        Parameters:
        None

        Returns:
        None
        """

        def load_data(file_path):
            """
            Load data from a JSON file.

            This function checks if the specified JSON file exists. If it does, it 
            reads the file and returns the data as a list. If the file does not 
            exist, it returns an empty list.

            Parameters:
            file_path (str): The path to the JSON file.

            Returns:
            list: The data loaded from the JSON file, or an empty list if the file 
            does not exist.
            """
            if os.path.exists(file_path):
                with open(file_path, 'r') as file:
                    return json.load(file)
            return []


        # Save data to file
        def save_data(data, file_path):
            """
            Save data to a JSON file.

            This function writes the specified data to a JSON file at the specified 
            file path.

            Parameters:
            data (list): The data to be saved to the JSON file.
            file_path (str): The path to the JSON file.

            Returns:
            None
            """
            with open(file_path, 'w') as file:
                json.dump(data, file, indent=4)

        def show_toast(message, message_type="info"):
            """
            Show a toast-like notification.

            Parameters:
            message (str): The message to display.
            message_type (str): The type of message ("info", "warning", "error").

            Returns:
            None
            """
            toast = tk.Toplevel(contact_book_window)
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


        def clear_fields():
            """
            Clear the input fields.

            This function clears the values in the company, client, phone, and email 
            entry widgets.

            Parameters:
            None

            Returns:
            None
            """
            combo_company.set('')
            entry_billing_address.delete(0, tk.END)
            entry_client.delete(0, tk.END)
            entry_phone.delete(0, tk.END)
            entry_email.delete(0, tk.END)


        def add_contact():
            """
            Add a new contact to the contact book.

            This function retrieves the company name, client name, phone number, 
            and email address from the respective Tkinter entry widgets. It then 
            creates a new contact dictionary with these details and appends it to 
            the contacts list stored in a JSON file. If the JSON file does not 
            exist, it creates a new one. After successfully adding the contact, 
            it clears the entry fields and shows a success message. If the client 
            name or phone number is missing, it shows a warning message.

            Parameters:
            None

            Returns:
            None
            """
            company = combo_company.get()
            billing_address = entry_billing_address.get()
            client = entry_client.get()
            phone = entry_phone.get()
            email = entry_email.get()

            if client and phone:
                new_contact = {
                    "company": company if company else "N/A", 
                    "billing address": billing_address if billing_address else "N/A",
                    "client": client, 
                    "phone": phone,
                    "email": email if email else "N/A",
                }

                contacts = load_data(self.CONTACTS_DATA)
                contacts.append(new_contact)
                save_data(contacts, self.CONTACTS_DATA)

                # messagebox.showinfo("Success", "Contact added successfully!")
                # update_status("Contact added successfully!", "info")
                show_toast("Contact added successfully!", "info")
                clear_fields()
                update_contact_list()
                update_company_list()
            else:
                # messagebox.showwarning("Input Error", 
                #                     "Client name and phone number are required!")
                # update_status("Client name and phone number are required!", "warning")
                show_toast("Client name and phone number are required!", "warning")
                

        def update_contact():
            """
            Update an existing contact in the contact book.

            This function retrieves the selected contact from the contact list, 
            updates its details with the values from the Tkinter entry widgets, 
            and saves the updated contacts list to the JSON file. After 
            successfully updating the contact, it clears the entry fields and 
            shows a success message. If no contact is selected, it shows a warning 
            message.

            Parameters:
            None

            Returns:
            None
            """
            selected_item = contact_list.selection()
            if selected_item:
                item_index = int(selected_item[0])
                contacts = load_data(self.CONTACTS_DATA)
                
                contacts[item_index] = {
                    "company": combo_company.get() if combo_company.get() else "N/A",
                    "billing address": entry_billing_address.get() if entry_billing_address.get() else "N/A",
                    "client": entry_client.get(),
                    "phone": entry_phone.get(),
                    "email": entry_email.get() if entry_email.get() else "N/A",
                }
                
                save_data(contacts, self.CONTACTS_DATA)
                # messagebox.showinfo("Success", "Contact updated successfully!")
                show_toast("Contact updated successfully!", "info")
                clear_fields()
                update_contact_list()
                update_company_list()
            else:
                # messagebox.showwarning("Selection Error", "No contact selected!")
                show_toast("No contact selected!", "warning")


        def remove_contact():
            """
            Remove a contact from the contact book.

            This function retrieves the selected contact from the contact list, 
            removes it from the contacts list, and saves the updated contacts list 
            to the JSON file. After successfully removing the contact, it clears 
            the entry fields and shows a success message. If no contact is 
            selected, it shows a warning message.

            Parameters:
            None

            Returns:
            None
            """
            selected_item = contact_list.selection()
            if selected_item:
                item_index = int(selected_item[0])
                contacts = load_data(self.CONTACTS_DATA)
                del contacts[item_index]
                save_data(contacts, self.CONTACTS_DATA)
                # messagebox.showinfo("Success", "Contact removed successfully!")
                show_toast("Contact removed successfully!", "info")
                clear_fields()
                update_contact_list()
                update_company_list()
            else:
                # messagebox.showwarning("Selection Error", "No contact selected!")
                show_toast("No contact selected!", "warning")


        def search_contact():
            """
            Search for contacts in the contact book based on the search term.

            This function retrieves the search term from the Tkinter entry widget 
            and searches for contacts in the JSON file that match the search term 
            in either the company name or client name. If matching contacts are 
            found, it displays the results in a new Tkinter window. If no matches 
            are found, it shows an information message. If the search term is 
            empty, it shows a warning message.

            Parameters:
            None

            Returns:
            None
            """
            global filtered_contacts
            company = combo_company.get()
            client = entry_client.get()

            if not company and not client:
                # messagebox.showwarning("Input Error", 
                                    # "Please enter a company name or client name to search.")
                show_toast("Please enter a company name or client name to search.", "warning")
                return

            contacts = load_data(self.CONTACTS_DATA)
            filtered_contacts = [contact for contact in contacts if (company.lower() in contact['company'].lower() \
                    if company else True) and (client.lower() in contact['client'].lower() if client else True)]
            update_contact_list(filtered_contacts)


        def clear_results():
            """
            Clear the search results and display the complete list of contacts.

            This function clears the search results and displays the complete list 
            of contacts in the contact list.

            Parameters:
            None

            Returns:
            None
            """
            global filtered_contacts
            filtered_contacts = []
            update_contact_list()
            clear_fields()


        # Handle double-click event on contact list
        def on_item_double_click(event):
            """
            Handle the double-click event on the contact list.

            This function retrieves the selected contact from the contact list and 
            populates the Tkinter entry widgets with the contact's details.

            Parameters:
            event (Event): The event object representing the double-click event.

            Returns:
            None
            """
            selected_item = contact_list.selection()
            if selected_item:
                item_index = int(selected_item[0])
                contacts = self.filtered_contacts if self.filtered_contacts else load_data(self.CONTACTS_DATA)
                selected_contact = contacts[item_index]
                combo_company.set(selected_contact["company"])
                entry_billing_address.delete(0, tk.END)
                entry_billing_address.insert(0, selected_contact.get("billing address", ""))
                entry_client.delete(0, tk.END)
                entry_client.insert(0, selected_contact.get("client", ""))
                entry_phone.delete(0, tk.END)
                entry_phone.insert(0, selected_contact.get("phone", ""))
                entry_email.delete(0, tk.END)
                entry_email.insert(0, selected_contact.get("email", ""))


        def update_contact_list(filtered_contacts=None):
            """
            Update the contact list display.

            This function updates the contact list display with the contacts from 
            the JSON file. If a filtered contacts list is provided, it displays 
            the filtered contacts instead. The contacts are sorted by company name
            in alphabetical order.

            Parameters:
            filtered_contacts (list, optional): A list of filtered contacts to be 
            displayed. Defaults to None.

            Returns:
            None
            """
            contacts = load_data(self.CONTACTS_DATA) if filtered_contacts is None else filtered_contacts
            contact_list.delete(*contact_list.get_children())
            for index, contact in enumerate(contacts):
                contact_list.insert(
                    "", "end", iid=index, values=(
                        contact.get("company", "N/A"), 
                        contact.get("billing address", "N/A"), 
                        contact.get("client", "N/A"), 
                        contact.get("phone", "N/A"),
                        contact.get("email", "N/A")
                        )
                    )


        def update_company_list():
            """
            Update the company list in the company combobox.

            This function updates the company list in the company combobox with 
            the unique company names from the contacts list.

            Parameters:
            None

            Returns:
            None
            """
            contacts = load_data(self.CONTACTS_DATA)
            companies = sorted(set(contact["company"] for contact in contacts \
                                if contact["company"] != "N/A"))
            combo_company["values"] = companies


        def select_contact():
            """
            Select a contact from the contact list and populate the main GUI fields.

            This function retrieves the selected contact from the contact list and 
            populates the corresponding fields in the main GUI (e.g., contact name, 
            company, phone, and email). If the contact list is filtered, it uses the 
            filtered data; otherwise, it loads the complete contact data. If no 
            contact is selected, it displays a warning message.

            Parameters:
            None

            Returns:
            None
            """
            selected_item = contact_list.selection()
            if selected_item:
                item_index = int(selected_item[0])
                contacts = self.filtered_contacts if self.filtered_contacts else load_data(self.CONTACTS_DATA)
                selected_contact = contacts[item_index]

                # Populate the fields in the main GUI
                company_var.set(selected_contact["company"])
                billing_address_var.set(selected_contact["billing address"])
                contact_name_var.set(selected_contact["client"])
                phone_var.set(selected_contact["phone"])
                email_var.set(selected_contact["email"])

                contact_book_window.destroy()  # Close the contact book window
            else:
                # messagebox.showwarning("Selection Error", "No contact selected!")
                show_toast("No contact selected!", "warning")

# =========================================================================== #
# ============================ Contact Book GUI ============================= #
# =========================================================================== #
        contact_book_window = Tk()
        contact_book_window.title("Contact Book")
        contact_book_window.config(padx=25, pady=25)

        # Labels and entry fields for contact information
        Label(contact_book_window, text="Company Name:").grid(row=0, column=0, 
                                                            padx=10, pady=5)
        combo_company = ttk.Combobox(contact_book_window, width=37)
        combo_company.grid(row=0, column=1, padx=10, pady=5)

        Label(contact_book_window, text="*Billing Address:").grid(row=1, column=0,
                                                                padx=10, pady=5)
        entry_billing_address = Entry(contact_book_window, width=40)
        entry_billing_address.grid(row=1, column=1, padx=10, pady=5)

        Label(contact_book_window, text="*Client Name:").grid(row=2, column=0, 
                                                            padx=10, pady=5)
        entry_client = Entry(contact_book_window, width=40)
        entry_client.grid(row=2, column=1, padx=10, pady=5)

        Label(contact_book_window, text="*Phone Number:").grid(row=3, column=0, 
                                                            padx=10, pady=5)
        entry_phone = Entry(contact_book_window, width=40)
        entry_phone.grid(row=3, column=1, padx=10, pady=5)

        Label(contact_book_window, text="Email:").grid(row=4, column=0, 
                                                    padx=10, pady=5)
        entry_email = Entry(contact_book_window, width=40)
        entry_email.grid(row=4, column=1, padx=10, pady=5)

        # Buttons to add, update, and search contacts
        Button(contact_book_window, width=15, text="Add Contact", 
                command=add_contact).grid(row=0, column=2, pady=5)
        Button(contact_book_window, width=15, text="Update Contact", 
                command=update_contact).grid(row=1, column=2, pady=5)
        Button(contact_book_window, width=15, text="Remove Contact", 
                command=remove_contact).grid(row=2, column=2, pady=5)
        Button(contact_book_window, width=15, text="Search Contacts", 
                command=search_contact).grid(row=3, column=2, pady=5)
        Button(contact_book_window, width=15, text="Select Contact",
            command=select_contact).grid(row=4, column=2, pady=5)    
        Button(contact_book_window, width=15, text="Clear Results", 
                command=clear_results).grid(row=5, column=2, pady=5)


        # Create contact list display
        contact_list = ttk.Treeview(contact_book_window, 
                                    columns=("Company Name", "Billing Address", 
                                            "Client Name", "Phone Number", 
                                            "Email"), show="headings")
        contact_list.heading("Company Name", text="Company Name")
        contact_list.heading("Billing Address", text="Billing Address")
        contact_list.heading("Client Name", text="Client Name")
        contact_list.heading("Phone Number", text="Phone Number")
        contact_list.heading("Email", text="Email")
        contact_list.grid(row=7, column=0, columnspan=3, padx=10, pady=10, sticky="nsew")

        # Bind double-click event to inventory list
        contact_list.bind("<Double-1>", on_item_double_click)

        # Bind the function to auto-populate billing address when a company is selected
        def on_company_selected(event):
            """
            Auto-populate the Billing Address when a company is selected from the dropdown.
            """
            selected_company = combo_company.get()
            contacts = load_data(self.CONTACTS_DATA)
            for contact in contacts:
                if contact.get("company", "") == selected_company:
                    entry_billing_address.delete(0, tk.END)
                    entry_billing_address.insert(0, contact.get("billing address", ""))
                    break

        # After creating combo_company:
        combo_company.bind("<<ComboboxSelected>>", on_company_selected)

        # Update contact list display on startup
        update_contact_list()
        update_company_list()

        contact_book_window.mainloop()
        

if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()  # Hide the root window

    contact_book = ContactBook()
    contact_book.open_contact_book(
        company_var=tk.StringVar(),
        billing_address_var=tk.StringVar(),
        contact_name_var=tk.StringVar(),
        phone_var=tk.StringVar(),
        email_var=tk.StringVar()
    )
