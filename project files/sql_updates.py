import mysql.connector
import random

# Step 1: Connect to the database
conn = mysql.connector.connect(
     host="127.0.0.1",
    user="root",
    password="Sri140299@",
    database="question_bank"
)
cursor = conn.cursor()

# Step 2: Update difficulty_level to a random value between 1 and 5
update_query = """
UPDATE questions
SET difficulty_level = FLOOR(1 + (RAND() * 5));
"""

cursor.execute(update_query)
conn.commit()

# Step 3: Confirm update
cursor.execute("SELECT COUNT(*), difficulty_level FROM questions GROUP BY difficulty_level")
results = cursor.fetchall()

print("✅ Questions updated with temporary random DODs:")
for count, dod in results:
    print(f"DOD {dod}: {count} questions")

cursor.close()
conn.close()