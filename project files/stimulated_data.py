import mysql.connector
import random
from faker import Faker
from collections import defaultdict

# Initialize Faker for student names
fake = Faker()

# Connect to the MySQL database
conn = mysql.connector.connect(
    host="127.0.0.1",
    user="root",
    password="Sri140299@",
    database="question_bank"
)
cursor = conn.cursor()

# Step 0: Clear existing data from students and student_attempts
print("🗑 Deleting existing data...")
cursor.execute("DELETE FROM student_attempts;")
cursor.execute("DELETE FROM students;")
cursor.execute("ALTER TABLE student_attempts AUTO_INCREMENT = 1;")
cursor.execute("ALTER TABLE students AUTO_INCREMENT = 1;")
conn.commit()

# Step 1: Insert 50 unique students
num_students = 50
student_names = [fake.name() for _ in range(num_students)]
student_ids = []

print("📥 Inserting students...")
for name in student_names:
    cursor.execute("INSERT INTO students (student_name) VALUES (%s)", (name,))
    student_ids.append(cursor.lastrowid)

conn.commit()

# Step 2: Fetch all question IDs and their DOD
cursor.execute("SELECT id, difficulty_level FROM questions")
questions = cursor.fetchall()  # List of (question_id, difficulty_level)

# Step 3: Distribute each question to 5 random students
print("📥 Assigning every question to 5 different students...")
question_distribution = defaultdict(list)

for question_id, _ in questions:
    assigned_students = random.sample(student_ids, min(5, len(student_ids)))
    question_distribution[question_id] = assigned_students

# Step 4: Build reverse mapping: student_id -> list of question_ids
student_question_map = defaultdict(list)
for qid, students in question_distribution.items():
    for sid in students:
        student_question_map[sid].append(qid)

# Step 5: Prepare DOD lookup
dod_lookup = {qid: dod for qid, dod in questions}

# Step 6: Simulate attempts per student
print("📥 Simulating student attempts...")
simulated_attempts = []

for student_id, qid_list in student_question_map.items():
    ability = random.choice(['high', 'medium', 'low'])

    for qid in qid_list:
        dod = dod_lookup[qid]

        if ability == 'high':
            is_correct = random.choices([1, 0], weights=[0.85, 0.15])[0]
        elif ability == 'medium':
            is_correct = random.choices([1, 0], weights=[0.6, 0.4])[0]
        else:
            is_correct = random.choices([1, 0], weights=[0.35, 0.65])[0]

        time_taken = random.randint(30, 90) + dod * 5
        simulated_attempts.append((student_id, qid, is_correct, time_taken, dod))

# Step 7: Insert simulated attempts into student_attempts
print("📤 Inserting simulated attempts into database...")
insert_query = """
INSERT INTO student_attempts
(student_id, question_id, is_correct, time_taken_sec, degree_of_difficulty)
VALUES (%s, %s, %s, %s, %s)
"""

cursor.executemany(insert_query, simulated_attempts)
conn.commit()

# Cleanup
cursor.close()
conn.close()

print(f"✅ Done: {len(simulated_attempts)} new student_attempts inserted with reduced sparsity.")