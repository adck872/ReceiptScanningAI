#testing queries
import sqlite3

conn = sqlite3.connect('food_db.db')
cursor = conn.cursor()

print("FoodDatabase contents:")
for row in cursor.execute("SELECT * FROM FoodDatabase"):
    print(row)

print("\nPantry contents:")
for row in cursor.execute("SELECT * FROM Pantry"):
    print(row)

conn.close()
