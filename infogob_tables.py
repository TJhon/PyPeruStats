import sqlite3

db_path = "./data/infogob/db.db"

conn = sqlite3.connect(db_path)
cursor = conn.cursor()


cursor.execute("""
    SELECT name 
    FROM sqlite_master 
    WHERE type='table'
    ORDER BY name;
""")

tables = cursor.fetchall()

for (table_name,) in tables:
    print(f"\nTabla: {table_name}")
    print("-" * 40)
    print("Columna\t\tTipo")

    cursor.execute(f"PRAGMA table_info('{table_name}')")
    columns = cursor.fetchall()

    for col in columns:
        col_name = col[1]
        col_type = col[2]
        print(f"{col_name}\t\t{col_type}")

conn.close()
