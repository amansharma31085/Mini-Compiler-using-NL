import tkinter as tk
from tkinter import scrolledtext, messagebox, filedialog, ttk
from main import NL2SQLModel, parse_sql, execute
import pandas as pd

class NL2SQLApp:
    def __init__(self, root):
        self.root = root
        self.root.title("NL2SQL Engine GUI")
        self.root.configure(bg="#f0f0f0")

       
        tk.Label(root, text="Enter Natural Language or SQL Query:",
                 font=("Arial", 12, "bold"), bg="#f0f0f0").pack(anchor="w", padx=10, pady=(10, 0))
        self.input_box = tk.Text(root, height=5, width=80, font=("Consolas", 10), bg="#ffffff",
                                 relief=tk.SUNKEN, bd=2)
        self.input_box.pack(padx=10, pady=(0, 10))

        button_frame = tk.Frame(root, bg="#f0f0f0")
        button_frame.pack()
        tk.Button(button_frame, text="Execute", command=self.run_query,
                  font=("Arial", 10, "bold"), bg="#4CAF50", fg="white").pack(side="left", padx=5)
        tk.Button(button_frame, text="Export as CSV", command=self.export_csv,
                  font=("Arial", 10, "bold"), bg="#2196F3", fg="white").pack(side="left", padx=5)
        tk.Button(button_frame, text="Export as Excel", command=self.export_excel,
                  font=("Arial", 10, "bold"), bg="#9C27B0", fg="white").pack(side="left", padx=5)
        tk.Button(button_frame, text="Save Table", command=self.save_table_dialog,
                  font=("Arial", 10, "bold"), bg="#FF9800", fg="white").pack(side="left", padx=5)

       
        tk.Label(root, text="Output:",
                 font=("Arial", 12, "bold"), bg="#f0f0f0").pack(anchor="w", padx=10)
        self.output_box = scrolledtext.ScrolledText(root, height=10, width=80,
                                                    font=("Courier", 10), bg="#fdfdfd",
                                                    relief=tk.SUNKEN, bd=2)
        self.output_box.pack(padx=10, pady=(0, 10))

       
        self.table_frame = tk.Frame(root, bg="#f0f0f0")
        self.table_frame.pack(fill="both", expand=True)
        self.tree = None
        self.last_table_data = []

       
        self.model = NL2SQLModel()

    def run_query(self):
        query = self.input_box.get("1.0", tk.END).strip()
        if not query:
            messagebox.showwarning("Empty Input", "Please enter a query.")
            return

        self.output_box.insert(tk.END, f">>> {query}\n")

        try:
            try:
                ast = parse_sql(query)
                self.output_box.insert(tk.END, "[Valid SQL query]\n")
            except SyntaxError:
                ai_query = self.model.translate(query)
                self.output_box.insert(tk.END, f"[AI NL→SQL]: {ai_query}\n")
                ast = parse_sql(ai_query)
                self.output_box.insert(tk.END, "[Translated successfully]\n")

            result = execute(ast)

            # Display result safely
            if isinstance(result, list):
                for row in result:
                    self.output_box.insert(tk.END, f"{row}\n")
                # Display table if result is a list of dicts (SELECT/JOIN)
                if result and isinstance(result[0], dict):
                    rows = [list(row.values()) for row in result]
                    self.display_table(rows)
                else:
                    self.display_table([])
            else:
                self.output_box.insert(tk.END, f"{result}\n")
                self.display_table([])

            # Preview table if a valid one exists
            if ast['type'] in ['CREATE_TABLE', 'INSERT', 'UPDATE', 'DELETE']:
                table = ast.get('table')
                if table:
                    try:
                        preview_ast = parse_sql(f"SELECT * FROM {table}")
                        preview = execute(preview_ast)
                        self.output_box.insert(tk.END, f"\n[{table} Overview]:\n")
                        for row in preview:
                            self.output_box.insert(tk.END, f"{row}\n")
                        if preview and isinstance(preview[0], dict):
                            rows = [list(row.values()) for row in preview]
                            self.display_table(rows)
                    except Exception as e:
                        self.output_box.insert(tk.END, f"Preview Error: {e}\n")

        except Exception as e:
            self.output_box.insert(tk.END, f"Error: {e}\n\n")

    def display_table(self, rows):
     
        for widget in self.table_frame.winfo_children():
            widget.destroy()

        if not rows:
            return

        
        self.last_table_data = rows
        columns = [f"col{i+1}" for i in range(len(rows[0]))]

        self.tree = ttk.Treeview(self.table_frame, columns=columns, show="headings", height=10)
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100)
        for row in rows:
            self.tree.insert("", tk.END, values=row)
        self.tree.pack(fill="both", expand=True)

    def export_csv(self):
        if not self.last_table_data:
            messagebox.showinfo("No Data", "No table data available to export.")
            return
        file_path = filedialog.asksaveasfilename(defaultextension=".csv",
                                                 filetypes=[("CSV files", "*.csv")])
        if file_path:
            pd.DataFrame(self.last_table_data).to_csv(file_path, index=False, header=False)
            messagebox.showinfo("Exported", f"CSV file saved to:\n{file_path}")

    def export_excel(self):
        if not self.last_table_data:
            messagebox.showinfo("No Data", "No table data available to export.")
            return
        file_path = filedialog.asksaveasfilename(defaultextension=".xlsx",
                                                 filetypes=[("Excel files", "*.xlsx")])
        if file_path:
            pd.DataFrame(self.last_table_data).to_excel(file_path, index=False, header=False)
            messagebox.showinfo("Exported", f"Excel file saved to:\n{file_path}")

    def save_table_dialog(self):
        if not self.last_table_data:
            messagebox.showinfo("No Data", "No table data available to save.")
            return

        file_path = filedialog.asksaveasfilename(defaultextension=".csv",
                                                 filetypes=[("CSV files", "*.csv"),
                                                            ("Excel files", "*.xlsx")],
                                                 title="Save Table As")
        if not file_path:
            return

        try:
            df = pd.DataFrame(self.last_table_data)
            if file_path.endswith(".csv"):
                df.to_csv(file_path, index=False, header=False)
            elif file_path.endswith(".xlsx"):
                df.to_excel(file_path, index=False, header=False)
            else:
                messagebox.showerror("Invalid Format", "Unsupported file extension.")
                return
            messagebox.showinfo("Success", f"Table saved to:\n{file_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save file:\n{e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = NL2SQLApp(root)
    root.mainloop()
