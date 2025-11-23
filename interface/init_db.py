import sqlite3

# Connect to (or create) your SQLite database file.
conn = sqlite3.connect('food_db.db')
cursor = conn.cursor()

# Create the FoodDatabase table
cursor.execute('''
    CREATE TABLE FoodDatabase (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name varchar(100),
        expirydate date
    )
''')

# Create the Pantry table
cursor.execute('''
    CREATE TABLE Pantry (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name varchar(100),
        expirydate date
    )
''')

conn.commit()
conn.close()
print("Database and tables created successfully.")
