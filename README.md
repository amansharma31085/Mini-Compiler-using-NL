# 🚀 Mini-Compiler-using-NL: Bridging Natural Language and SQL

A powerful and intuitive Mini-Compiler that translates natural language queries into executable SQL, and also supports direct SQL execution. This project leverages a pre-trained `bart-large-nl2sql` model for robust NL-to-SQL translation and provides a user-friendly Graphical User Interface (GUI) for seamless interaction with your data.

---

## ✨ Features

* **Natural Language to SQL Translation**: Convert your plain English questions into valid SQL queries effortlessly using an integrated AI model.
* **Comprehensive SQL Support**: Execute a wide range of SQL commands, including:
    * `SELECT` (with `WHERE` clauses and `*` for all columns)
    * `INSERT INTO`
    * `UPDATE` (with `SET` and optional `WHERE` clauses)
    * `DELETE FROM` (with optional `WHERE` clauses)
    * `CREATE TABLE`
    * `DROP TABLE`
    * `JOIN` operations between two tables (with `ON` and optional `WHERE` clauses)
    * `SHOW TABLES` to list available databases
    * `DESCRIBE` to view table schemas
* **Dynamic Database Management**: Interact with JSON files as your database, allowing for flexible data storage and retrieval.
* **Intuitive GUI**: A Tkinter-based graphical interface for easy query input, output display, and table visualization.
* **Data Export Capabilities**: Export query results directly to CSV or Excel formats.
* **Command-Line Interface (CLI)**: For those who prefer terminal-based interaction, a CLI is also available.

---

## 🛠️ Technologies Used

* **Python 3.x**
* **Tkinter**: For building the graphical user interface.
* **Transformers (Hugging Face)**: For loading and utilizing the `bart-large-nl2sql` model for NL-to-SQL translation.
* **PyTorch**: Deep learning framework, a dependency of Transformers.
* **pandas**: For efficient data manipulation and exporting results to CSV/Excel.

---

## 📦 Installation & Setup

1.  **Clone the repository**:
    ```bash
    git clone [https://github.com/amansharma31085/mini-compiler-using-nl.git](https://github.com/amansharma31085/mini-compiler-using-nl.git)
    cd mini-compiler-using-nl
    ```

2.  **Create a virtual environment (recommended)**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    ```

3.  **Install the required libraries**:
    *( you will need to install `transformers`, `torch`, and `pandas` manually:)*
    ```bash
    pip install transformers torch pandas
    ```

4.  **Database Directory**: Ensure you have a `database` folder in the root directory. This is where your JSON tables will be stored.
    ```
    mini-compiler-using-nl/
    ├── database/
    │   ├── student.json
    │   └── aman.json
    ├── gui.py
    ├── main.py
    ├── README.md
    └── ...
    ```

---

## 🚀 Usage

### Graphical User Interface (GUI)

To launch the GUI, run the `gui.py` file:
Run: python gui.py
