import os
import sqlite3
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import tkinter.font as tkfont  # Import tkinter.font for custom fonts

class InventoryApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Inventory Control System")
        self.root.attributes('-fullscreen', True)  # Set the window to full-screen

        # Bind the Escape key to exit full-screen mode
        self.root.bind("<Escape>", self.exit_fullscreen)

        self.conn = self.create_connection()
        self.create_table()
        self.reset_autoincrement_sequence()  # Reset the AUTOINCREMENT sequence if necessary
        self.create_widgets()

    def exit_fullscreen(self, event=None):
        """Exit full-screen mode."""
        self.root.attributes('-fullscreen', False)

    def close_application(self):
        """Close the application."""
        self.conn.close()
        self.root.quit()

    def create_connection(self):
        """Create a database connection with the absolute path."""
        # Get the directory where the script is located
        script_dir = os.path.dirname(os.path.abspath(__file__))
        # Create the full path to the database file
        db_path = os.path.join(script_dir, 'inventory.db')
        # Connect to the database using the full path
        conn = sqlite3.connect(db_path)
        return conn

    def create_table(self):
        """Create the inventory table with the correct schema."""
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS inventory (
                part_number INTEGER PRIMARY KEY AUTOINCREMENT,
                part_name TEXT NOT NULL,
                description TEXT,
                origin_partnumber TEXT,
                mcmaster_carr_partnumber TEXT,
                cost REAL,
                quantity INTEGER NOT NULL,
                min_on_hand INTEGER NOT NULL,
                location TEXT
            )
        ''')
        self.conn.commit()

    def reset_autoincrement_sequence(self):
        """Reset the AUTOINCREMENT sequence in case of table or numbering issues."""
        cursor = self.conn.cursor()
        # Check if there are any items in the inventory, if not reset the sequence
        cursor.execute("SELECT MAX(part_number) FROM inventory")
        max_part_number = cursor.fetchone()[0]
        if max_part_number is None:
            # Reset the AUTOINCREMENT sequence
            cursor.execute("DELETE FROM sqlite_sequence WHERE name='inventory'")
            self.conn.commit()

    def create_widgets(self):
        """Create the main GUI components."""
        # Create a frame at the top for the close button
        top_bar = tk.Frame(self.root)
        top_bar.pack(side=tk.TOP, fill=tk.X)

        # Add a close button to exit the application
        close_button = tk.Button(top_bar, text="X", command=self.close_application, fg="red", font=("Arial", 12, "bold"))
        close_button.pack(side=tk.RIGHT, padx=5, pady=5)

        # Create a custom font for the tabs
        tab_font = tkfont.Font(family='Helvetica', size=16, weight='bold')

        # Create a style for the Notebook tabs
        style = ttk.Style()
        style.configure('Custom.TNotebook.Tab', padding=[10, 5], font=tab_font, borderwidth=2, relief='raised')
        style.map('Custom.TNotebook.Tab',
                  background=[('selected', 'lightblue'), ('!selected', 'lightgrey')],
                  foreground=[('selected', 'black'), ('!selected', 'black')])

        # Create the Notebook with the custom style
        notebook = ttk.Notebook(self.root, style='Custom.TNotebook')
        notebook.pack(fill='both', expand=True)

        # Create frames for each tab
        self.list_frame = tk.Frame(notebook)
        self.check_frame = tk.Frame(notebook)
        self.scan_out_frame = tk.Frame(notebook)
        self.scan_in_frame = tk.Frame(notebook)

        # Add frames to notebook with tab labels
        notebook.add(self.list_frame, text='List Items')
        notebook.add(self.check_frame, text='Check Inventory Levels')
        notebook.add(self.scan_out_frame, text='Scan Out Parts')
        notebook.add(self.scan_in_frame, text='Scan In Parts')

        # Initialize the contents of each frame
        self.init_list_frame()
        self.init_check_frame()
        self.init_scan_out_frame()
        self.init_scan_in_frame()

    def init_list_frame(self):
        """Initialize the List Items tab."""
        top_frame = tk.Frame(self.list_frame)
        top_frame.pack(pady=5)

        controls_frame = tk.Frame(top_frame)
        controls_frame.pack(anchor='center')

        refresh_button = tk.Button(controls_frame, text="Refresh List", command=self.populate_list_tree)
        refresh_button.pack(side=tk.LEFT, padx=5)

        search_label = tk.Label(controls_frame, text="Search:")
        search_label.pack(side=tk.LEFT, padx=5)
        self.search_entry = tk.Entry(controls_frame)
        self.search_entry.pack(side=tk.LEFT, padx=5)

        search_button = tk.Button(controls_frame, text="Search", command=self.search_items)
        search_button.pack(side=tk.LEFT, padx=5)
        clear_button = tk.Button(controls_frame, text="Clear", command=self.clear_search)
        clear_button.pack(side=tk.LEFT, padx=5)

        action_frame = tk.Frame(self.list_frame)
        action_frame.pack(pady=5)

        add_button = tk.Button(action_frame, text="Add New Item", command=self.add_new_item)
        add_button.pack(side=tk.LEFT, padx=5)
        update_button = tk.Button(action_frame, text="Update Selected Item", command=self.update_selected_item)
        update_button.pack(side=tk.LEFT, padx=5)
        remove_button = tk.Button(action_frame, text="Remove Selected Item", command=self.remove_selected_item)
        remove_button.pack(side=tk.LEFT, padx=5)

        columns = (
            'part_number', 'part_name', 'description', 'origin_partnumber',
            'mcmaster_carr_partnumber', 'cost', 'quantity', 'min_on_hand', 'location'
        )
        self.list_tree = ttk.Treeview(self.list_frame, columns=columns, show='headings', selectmode='browse')
        self.list_tree.pack(fill='both', expand=True)

        for col in columns:
            self.list_tree.heading(col, text=col.replace('_', ' ').title())
            self.list_tree.column(col, width=150)

        self.list_tree.tag_configure('below_min', background='yellow')
        self.list_tree.tag_configure('out_of_stock', background='red')

        self.populate_list_tree()

    def init_check_frame(self):
        """Initialize the Check Inventory Levels tab."""
        top_frame = tk.Frame(self.check_frame)
        top_frame.pack(pady=5)

        controls_frame = tk.Frame(top_frame)
        controls_frame.pack(anchor='center')

        refresh_button = tk.Button(controls_frame, text="Refresh List", command=self.populate_check_tree)
        refresh_button.pack(pady=5)

        columns = (
            'part_number', 'part_name', 'quantity', 'min_on_hand', 'origin_partnumber',
            'mcmaster_carr_partnumber', 'cost', 'location'
        )
        self.check_tree = ttk.Treeview(self.check_frame, columns=columns, show='headings', selectmode='browse')
        self.check_tree.pack(fill='both', expand=True)

        for col in columns:
            self.check_tree.heading(col, text=col.replace('_', ' ').title())
            self.check_tree.column(col, width=150)

        self.check_tree.tag_configure('out_of_stock', background='red')

        self.populate_check_tree()

    def init_scan_out_frame(self):
        """Initialize the Scan Out Parts tab."""
        instruction_label = tk.Label(self.scan_out_frame, text="Scan the part number to check out parts:")
        instruction_label.pack(pady=10)

        self.scan_entry = tk.Entry(self.scan_out_frame, font=('Arial', 24))
        self.scan_entry.pack(pady=5)
        self.scan_entry.focus_set()

        quantity_frame = tk.Frame(self.scan_out_frame)
        quantity_frame.pack(pady=5)

        quantity_label = tk.Label(quantity_frame, text="Quantity to Remove:")
        quantity_label.pack(side=tk.LEFT)

        self.scan_quantity_entry = tk.Entry(quantity_frame, width=5)
        self.scan_quantity_entry.pack(side=tk.LEFT, padx=5)
        self.scan_quantity_entry.insert(0, "1")

        self.scan_entry.bind('<Return>', self.process_scan)

        self.scan_message = tk.Label(self.scan_out_frame, text="", font=('Arial', 14))
        self.scan_message.pack(pady=10)

    def process_scan(self, event=None):
        """Process the scanned part number for scanning out."""
        part_number_str = self.scan_entry.get().strip()
        quantity_str = self.scan_quantity_entry.get().strip()

        self.scan_entry.delete(0, tk.END)
        self.scan_entry.focus_set()

        try:
            quantity = int(quantity_str)
            if quantity <= 0:
                raise ValueError
        except ValueError:
            self.scan_message.config(text="Invalid quantity. Please enter a positive integer.", fg='red')
            return

        if not part_number_str:
            self.scan_message.config(text="No part number detected. Please try again.", fg='red')
            return

        try:
            part_number = int(part_number_str)
        except ValueError:
            self.scan_message.config(text="Invalid part number. Must be an integer.", fg='red')
            return

        cursor = self.conn.cursor()
        cursor.execute('SELECT quantity FROM inventory WHERE part_number = ?', (part_number,))
        result = cursor.fetchone()

        if result:
            current_quantity = result[0]
            if current_quantity >= quantity:
                cursor.execute('UPDATE inventory SET quantity = quantity - ? WHERE part_number = ?', (quantity, part_number))
                self.conn.commit()
                new_quantity = current_quantity - quantity
                self.scan_message.config(
                    text=f"Removed {quantity} units of item with part number '{part_number}'. Remaining quantity: {new_quantity}", fg='green'
                )
                self.populate_list_tree()
                self.populate_check_tree()
            else:
                self.scan_message.config(text=f"Insufficient stock. Available quantity: {current_quantity}", fg='red')
        else:
            self.scan_message.config(text=f"Item with part number '{part_number}' not found in inventory.", fg='red')

    def init_scan_in_frame(self):
        """Initialize the Scan In Parts tab."""
        instruction_label = tk.Label(self.scan_in_frame, text="Scan the part number to add parts to inventory:")
        instruction_label.pack(pady=10)

        self.scan_in_entry = tk.Entry(self.scan_in_frame, font=('Arial', 24))
        self.scan_in_entry.pack(pady=5)
        self.scan_in_entry.focus_set()

        quantity_frame = tk.Frame(self.scan_in_frame)
        quantity_frame.pack(pady=5)

        quantity_label = tk.Label(quantity_frame, text="Quantity to Add:")
        quantity_label.pack(side=tk.LEFT)

        self.scan_in_quantity_entry = tk.Entry(quantity_frame, width=5)
        self.scan_in_quantity_entry.pack(side=tk.LEFT, padx=5)
        self.scan_in_quantity_entry.insert(0, "1")

        self.scan_in_entry.bind('<Return>', self.process_scan_in)

        self.scan_in_message = tk.Label(self.scan_in_frame, text="", font=('Arial', 14))
        self.scan_in_message.pack(pady=10)

    def process_scan_in(self, event=None):
        """Process the scanned part number for scanning in."""
        part_number_str = self.scan_in_entry.get().strip()
        quantity_str = self.scan_in_quantity_entry.get().strip()

        self.scan_in_entry.delete(0, tk.END)
        self.scan_in_entry.focus_set()

        try:
            quantity = int(quantity_str)
            if quantity <= 0:
                raise ValueError
        except ValueError:
            self.scan_in_message.config(text="Invalid quantity. Please enter a positive integer.", fg='red')
            return

        if not part_number_str:
            self.scan_in_message.config(text="No part number detected. Please try again.", fg='red')
            return

        try:
            part_number = int(part_number_str)
        except ValueError:
            self.scan_in_message.config(text="Invalid part number. Must be an integer.", fg='red')
            return

        cursor = self.conn.cursor()
        cursor.execute('SELECT quantity FROM inventory WHERE part_number = ?', (part_number,))
        result = cursor.fetchone()

        if result:
            cursor.execute('UPDATE inventory SET quantity = quantity + ? WHERE part_number = ?', (quantity, part_number))
            self.conn.commit()
            new_quantity = result[0] + quantity
            self.scan_in_message.config(
                text=f"Added {quantity} units of item with part number '{part_number}'. New quantity: {new_quantity}", fg='green'
            )
            self.populate_list_tree()
            self.populate_check_tree()
        else:
            self.scan_in_message.config(text=f"Item with part number '{part_number}' not found in inventory.", fg='red')

    def add_new_item(self):
        """Open a window to add a new item."""
        add_win = tk.Toplevel(self.root)
        add_win.title("Add New Item")

        labels = [
            'Part Name', 'Description', 'Origin Part Number',
            'McMaster-Carr Part Number', 'Cost', 'Quantity', 'Min on Hand', 'Location'
        ]
        entries = {}

        for idx, label_text in enumerate(labels):
            label = tk.Label(add_win, text=label_text)
            label.grid(row=idx, column=0, padx=5, pady=5, sticky='e')
            entry = tk.Entry(add_win)
            entry.grid(row=idx, column=1, padx=5, pady=5)
            entries[label_text] = entry

        def save_item():
            part_name = entries['Part Name'].get().strip()
            description = entries['Description'].get().strip()
            origin_partnumber = entries['Origin Part Number'].get().strip()
            mcmaster_carr_partnumber = entries['McMaster-Carr Part Number'].get().strip()
            cost = entries['Cost'].get().strip()
            quantity = entries['Quantity'].get().strip()
            min_on_hand = entries['Min on Hand'].get().strip()
            location = entries['Location'].get().strip()

            if not (part_name and quantity and min_on_hand):
                messagebox.showerror("Error", "Please fill in all required fields (Part Name, Quantity, Min on Hand).")
                return

            try:
                cost = float(cost) if cost else 0.0
                quantity = int(quantity)
                min_on_hand = int(min_on_hand)
            except ValueError:
                messagebox.showerror("Error", "Quantity and Min on Hand must be integers and Cost must be a number.")
                return

            cursor = self.conn.cursor()
            try:
                cursor.execute('''
                    INSERT INTO inventory (
                        part_name, description, origin_partnumber,
                        mcmaster_carr_partnumber, cost, quantity, min_on_hand, location
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    part_name, description, origin_partnumber,
                    mcmaster_carr_partnumber, cost, quantity, min_on_hand, location
                ))
                self.conn.commit()
                messagebox.showinfo("Success", "Item added successfully.")
                add_win.destroy()
                self.populate_list_tree()
                self.populate_check_tree()
            except sqlite3.IntegrityError:
                messagebox.showerror("Error", "Failed to add item due to database integrity error.")

        save_button = tk.Button(add_win, text="Save Item", command=save_item)
        save_button.grid(row=len(labels), column=0, columnspan=2, pady=10)

    def search_items(self):
        """Search for items based on the search entry."""
        search_term = self.search_entry.get().strip()
        if not search_term:
            messagebox.showwarning("Warning", "Please enter a search term.")
            return

        for row in self.list_tree.get_children():
            self.list_tree.delete(row)

        cursor = self.conn.cursor()
        sql_query = '''
            SELECT part_number, part_name, description, origin_partnumber,
                   mcmaster_carr_partnumber, cost, quantity, min_on_hand, location
            FROM inventory
            WHERE CAST(part_number AS TEXT) LIKE ?
                OR part_name LIKE ?
                OR description LIKE ?
                OR origin_partnumber LIKE ?
                OR mcmaster_carr_partnumber LIKE ?
                OR CAST(cost AS TEXT) LIKE ?
                OR CAST(quantity AS TEXT) LIKE ?
                OR CAST(min_on_hand AS TEXT) LIKE ?
                OR location LIKE ?
        '''
        search_params = tuple('%' + search_term + '%' for _ in range(9))
        cursor.execute(sql_query, search_params)
        items = cursor.fetchall()
        if items:
            for item in items:
                quantity = int(item[6])     
                min_on_hand = int(item[7])  

                if quantity == 0:
                    tags = ('out_of_stock',)
                elif quantity < min_on_hand:
                    tags = ('below_min',)
                else:
                    tags = ()

                self.list_tree.insert('', tk.END, values=item, tags=tags)
        else:
            messagebox.showinfo("Info", "No items found matching the search criteria.")

    def clear_search(self):
        """Clear the search entry and refresh the list."""
        self.search_entry.delete(0, tk.END)
        self.populate_list_tree()

    def populate_list_tree(self):
        """Populate the Treeview with inventory items."""
        for row in self.list_tree.get_children():
            self.list_tree.delete(row)
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT part_number, part_name, description, origin_partnumber,
                   mcmaster_carr_partnumber, cost, quantity, min_on_hand, location
            FROM inventory
        ''')
        items = cursor.fetchall()
        for item in items:
            quantity = int(item[6])     
            min_on_hand = int(item[7])  

            if quantity == 0:
                tags = ('out_of_stock',)
            elif quantity < min_on_hand:
                tags = ('below_min',)
            else:
                tags = ()

            self.list_tree.insert('', tk.END, values=item, tags=tags)

    def update_selected_item(self):
        """Update the selected item from the list."""
        selected_item = self.list_tree.selection()
        if not selected_item:
            messagebox.showwarning("Warning", "Please select an item to update.")
            return

        item_values = self.list_tree.item(selected_item, 'values')
        part_number = item_values[0]

        self.open_update_window(part_number)

    def open_update_window(self, part_number):
        """Open a window to update the selected item."""
        update_win = tk.Toplevel(self.root)
        update_win.title(f"Update Item - Part Number {part_number}")

        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT part_name, description, origin_partnumber, mcmaster_carr_partnumber,
                   cost, quantity, min_on_hand, location
            FROM inventory WHERE part_number = ?
        ''', (part_number,))
        item = cursor.fetchone()
        if not item:
            messagebox.showerror("Error", "Item not found.")
            update_win.destroy()
            return

        labels = [
            'Part Name', 'Description', 'Origin Part Number', 'McMaster-Carr Part Number',
            'Cost', 'Quantity', 'Min on Hand', 'Location'
        ]
        entries = {}

        for idx, label_text in enumerate(labels):
            label = tk.Label(update_win, text=label_text)
            label.grid(row=idx, column=0, padx=5, pady=5, sticky='e')
            entry = tk.Entry(update_win)
            entry.grid(row=idx, column=1, padx=5, pady=5)
            entry.insert(0, item[idx])
            entries[label_text] = entry

        def save_updates():
            part_name = entries['Part Name'].get().strip()
            description = entries['Description'].get().strip()
            origin_partnumber = entries['Origin Part Number'].get().strip()
            mcmaster_carr_partnumber = entries['McMaster-Carr Part Number'].get().strip()
            cost = entries['Cost'].get().strip()
            quantity = entries['Quantity'].get().strip()
            min_on_hand = entries['Min on Hand'].get().strip()
            location = entries['Location'].get().strip()

            if not (part_name and quantity and min_on_hand):
                messagebox.showerror("Error", "Please fill in all required fields (Part Name, Quantity, Min on Hand).")
                return

            try:
                cost = float(cost) if cost else 0.0
                quantity = int(quantity)
                min_on_hand = int(min_on_hand)
            except ValueError:
                messagebox.showerror("Error", "Quantity and Min on Hand must be integers and Cost must be a number.")
                return

            cursor = self.conn.cursor()
            try:
                cursor.execute('''
                    UPDATE inventory
                    SET part_name = ?, description = ?, origin_partnumber = ?, mcmaster_carr_partnumber = ?,
                        cost = ?, quantity = ?, min_on_hand = ?, location = ?
                    WHERE part_number = ?
                ''', (
                    part_name, description, origin_partnumber, mcmaster_carr_partnumber,
                    cost, quantity, min_on_hand, location, part_number
                ))
                self.conn.commit()
                messagebox.showinfo("Success", "Item updated successfully.")
                update_win.destroy()
                self.populate_list_tree()
                self.populate_check_tree()
            except sqlite3.IntegrityError:
                messagebox.showerror("Error", "Failed to update item due to database integrity error.")

        save_button = tk.Button(update_win, text="Save Updates", command=save_updates)
        save_button.grid(row=len(labels), column=0, columnspan=2, pady=10)

    def remove_selected_item(self):
        """Remove the selected item from the list."""
        selected_item = self.list_tree.selection()
        if not selected_item:
            messagebox.showwarning("Warning", "Please select an item to remove.")
            return

        item_values = self.list_tree.item(selected_item, 'values')
        part_number = item_values[0]

        confirm = messagebox.askyesno("Confirm", f"Are you sure you want to remove item with Part Number '{part_number}'?")
        if confirm:
            cursor = self.conn.cursor()
            cursor.execute('DELETE FROM inventory WHERE part_number = ?', (part_number,))
            self.conn.commit()
            messagebox.showinfo("Success", "Item removed successfully.")
            self.populate_list_tree()
            self.populate_check_tree()

    def populate_check_tree(self):
        """Populate the Treeview with items below minimum on-hand levels."""
        for row in self.check_tree.get_children():
            self.check_tree.delete(row)
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT part_number, part_name, quantity, min_on_hand, origin_partnumber,
                   mcmaster_carr_partnumber, cost, location
            FROM inventory WHERE quantity < min_on_hand
        ''')
        items = cursor.fetchall()
        if items:
            for item in items:
                quantity = int(item[2])
                if quantity == 0:
                    tags = ('out_of_stock',)
                else:
                    tags = ()
                self.check_tree.insert('', tk.END, values=item, tags=tags)
        else:
            messagebox.showinfo("Info", "All items meet minimum on-hand levels.")

if __name__ == '__main__':
    root = tk.Tk()
    app = InventoryApp(root)
    root.mainloop()
