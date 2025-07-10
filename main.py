import os
import json
import re
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import torch

class NL2SQLModel:
    def __init__(self):
        print("Loading SwastikM/bart-large-nl2sql model for NL-to-SQL translation...")
        self.tokenizer = AutoTokenizer.from_pretrained("SwastikM/bart-large-nl2sql")
        self.model = AutoModelForSeq2SeqLM.from_pretrained("SwastikM/bart-large-nl2sql")

    def translate(self, nl_query: str) -> str:
        prompt = f"sql_prompt: {nl_query} sql_context: CREATE TABLE student (id INT, name TEXT, age INT);"
        inputs = self.tokenizer(prompt, return_tensors="pt", max_length=512, truncation=True)
        outputs = self.model.generate(**inputs, max_length=150)
        sql_query = self.tokenizer.decode(outputs[0], skip_special_tokens=True).strip()
        if not sql_query.endswith(";"):
            sql_query += ";"
        return sql_query

DB_DIR = "database"

def load_table(table_name):
    path = os.path.join(DB_DIR, f"{table_name}.json")
    if not os.path.exists(path):
        raise FileNotFoundError(f"Table '{table_name}' does not exist.")
    with open(path, "r") as f:
        return json.load(f)

def save_table(table_name, data):
    os.makedirs(DB_DIR, exist_ok=True)
    path = os.path.join(DB_DIR, f"{table_name}.json")
    with open(path, "w") as f:
        json.dump(data, f, indent=2)

def table_exists(table_name):
    return os.path.exists(os.path.join(DB_DIR, f"{table_name}.json"))

def parse_sql(query):
    q = query.strip().rstrip(";").strip()

    if q.upper() == "SHOW TABLES":
        return {"type": "SHOW_TABLES"}

    if q.upper().startswith("DESCRIBE "):
        table = q[9:].strip()
        return {"type": "DESCRIBE", "table": table}

    create_match = re.match(r"CREATE TABLE (\w+)\s*\((.+)\)$", q, re.IGNORECASE)
    if create_match:
        table, cols_str = create_match.groups()
        cols = [c.strip() for c in cols_str.split(",")]
        schema = {col.split()[0]: col.split()[1] for col in cols}
        return {"type": "CREATE_TABLE", "table": table, "schema": schema}

    drop_match = re.match(r"DROP TABLE (\w+)$", q, re.IGNORECASE)
    if drop_match:
        return {"type": "DROP_TABLE", "table": drop_match.group(1)}

    join_match = re.match(
        r"SELECT (.+) FROM (\w+)\s+JOIN\s+(\w+)\s+ON\s+(\w+\.\w+)\s*=\s*(\w+\.\w+)(?:\s+WHERE\s+(.+))?$",
        q, re.IGNORECASE
    )
    if join_match:
        cols, t1, t2, left_on, right_on, where = join_match.groups()
        return {
            "type": "JOIN",
            "columns": [col.strip() for col in cols.split(",")],
            "left_table": t1,
            "right_table": t2,
            "on": (left_on.strip(), right_on.strip()),
            "where": where
        }

    select_match = re.match(r"SELECT (.+) FROM (\w+)(?: WHERE (.+))?$", q, re.IGNORECASE)
    if select_match:
        cols, table, where = select_match.groups()
        return {
            "type": "SELECT",
            "columns": [col.strip() for col in cols.split(",")],
            "table": table,
            "where": where
        }

    insert_match = re.match(r"INSERT INTO (\w+)\s*\((.+)\)\s*VALUES\s*\((.+)\)$", q, re.IGNORECASE)
    if insert_match:
        table, cols_str, vals_str = insert_match.groups()
        return {
            "type": "INSERT",
            "table": table,
            "columns": [c.strip() for c in cols_str.split(",")],
            "values": [v.strip().strip("'") for v in vals_str.split(",")]
        }

    update_match = re.match(r"UPDATE (\w+)\s+SET\s+(.+?)(?:\s+WHERE\s+(.+))?$", q, re.IGNORECASE)
    if update_match:
        table, set_clause, where = update_match.groups()
        updates = dict(pair.strip().split("=") for pair in set_clause.split(","))
        updates = {k.strip(): v.strip().strip("'") for k, v in updates.items()}
        return {"type": "UPDATE", "table": table, "updates": updates, "where": where}

    delete_match = re.match(r"DELETE FROM (\w+)(?: WHERE (.+))?$", q, re.IGNORECASE)
    if delete_match:
        table, where = delete_match.groups()
        return {"type": "DELETE", "table": table, "where": where}

    raise SyntaxError(f"Unsupported or invalid SQL statement: '{query}'")

def evaluate_where(row, clause):
    if not clause:
        return True
    m = re.match(r"(\w+(?:\.\w+)?)\s*(=|>|<|>=|<=|!=)\s*(\d+|'.*?')", clause)
    if not m:
        raise ValueError("Invalid WHERE clause.")
    col, op, val = m.groups()
    val = int(val) if val.isdigit() else val.strip("'")
    x = row.get(col)
    return {
        "=": lambda x: x == val,
        ">": lambda x: x > val,
        "<": lambda x: x < val,
        ">=": lambda x: x >= val,
        "<=": lambda x: x <= val,
        "!=": lambda x: x != val,
    }[op](x)

def get_nested_value(row, dotted_key):
    parts = dotted_key.split(".")
    return row.get(parts[1]) if len(parts) == 2 else None

def execute(ast):
    if ast["type"] == "SELECT":
        table = load_table(ast["table"])
        return [
            row if ast["columns"] == ["*"] else {c: row.get(c) for c in ast["columns"]}
            for row in table if evaluate_where(row, ast["where"])
        ]

    elif ast["type"] == "INSERT":
        try:
            table = load_table(ast["table"])
        except FileNotFoundError:
            table = []
        row = dict(zip(ast["columns"], [int(v) if v.isdigit() else v for v in ast["values"]]))
        table.append(row)
        save_table(ast["table"], table)
        return "1 row inserted."

    elif ast["type"] == "UPDATE":
        table = load_table(ast["table"])
        cnt = 0
        for row in table:
            if evaluate_where(row, ast["where"]):
                for c, v in ast["updates"].items():
                    row[c] = int(v) if v.isdigit() else v
                cnt += 1
        save_table(ast["table"], table)
        return f"{cnt} row(s) updated."

    elif ast["type"] == "DELETE":
        table = load_table(ast["table"])
        new = [r for r in table if not evaluate_where(r, ast["where"])]
        deleted = len(table) - len(new)
        save_table(ast["table"], new)
        return f"{deleted} row(s) deleted."

    elif ast["type"] == "JOIN":
        L = load_table(ast["left_table"])
        R = load_table(ast["right_table"])
        res = []
        for l in L:
            for r in R:
                if get_nested_value(l, ast["on"][0]) == get_nested_value(r, ast["on"][1]):
                    j = {f"{ast['left_table']}.{k}": v for k, v in l.items()}
                    j.update({f"{ast['right_table']}.{k}": v for k, v in r.items()})
                    if evaluate_where(j, ast["where"]):
                        res.append({c: j.get(c) for c in ast["columns"]})
        return res

    elif ast["type"] == "CREATE_TABLE":
        save_table(ast["table"], [])
        return f"Table '{ast['table']}' created."

    elif ast["type"] == "DROP_TABLE":
        path = os.path.join(DB_DIR, f"{ast['table']}.json")
        if os.path.exists(path):
            os.remove(path)
            return f"Table '{ast['table']}' dropped."
        return f"Table '{ast['table']}' does not exist."

    elif ast["type"] == "SHOW_TABLES":
        files = [f[:-5] for f in os.listdir(DB_DIR) if f.endswith(".json")]
        return files or ["No tables found."]

    elif ast["type"] == "DESCRIBE":
        try:
            tbl = load_table(ast["table"])
        except FileNotFoundError:
            return f"Table '{ast['table']}' does not exist."
        return list(tbl[0].keys()) if tbl else "Table is empty."

def repl():
    print("SQL Engine with JOIN + AI NL-to-SQL. Type 'exit;' to quit.")
    nl = NL2SQLModel()
    while True:
        q = input("sql> ").strip()
        if q.lower() in ("exit;", "exit"):
            break

        try:
            ast = parse_sql(q)
        except SyntaxError:
            q = nl.translate(q)
            print("[AI NL→SQL]:", q)
            ast = parse_sql(q)

        out = execute(ast)
        if isinstance(out, list):
            for row in out:
                print(row)
        else:
            print(out)

if __name__ == "__main__":
    import sys
    nl = NL2SQLModel()
    if len(sys.argv) > 1:
        inp = " ".join(sys.argv[1:])
        try:
            ast = parse_sql(inp)
        except SyntaxError:
            inp = nl.translate(inp)
            print("[AI NL→SQL]:", inp)
            ast = parse_sql(inp)

        out = execute(ast)
        if isinstance(out, list):
            for r in out:
                print(r)
        else:
            print(out)
    else:
        repl()
