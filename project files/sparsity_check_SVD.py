import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import mysql.connector

# Step 1: Connect to MySQL and load data
conn = mysql.connector.connect(
     host="127.0.0.1",
    user="root",
    password="Sri140299@",
    database="question_bank"
)

# Load student attempts
df = pd.read_sql("SELECT student_id, question_id, is_correct FROM student_attempts", conn)
conn.close()

# Step 2: Calculate sparsity
n_students = df['student_id'].nunique()
n_questions = df['question_id'].nunique()
n_attempts = len(df)

total_possible = n_students * n_questions
sparsity = 1 - (n_attempts / total_possible)

print(f"🔍 Total Students: {n_students}")
print(f"🔍 Total Questions: {n_questions}")
print(f"🧮 Total Attempts: {n_attempts}")
print(f"📉 Sparsity: {sparsity:.2%}")

# Step 3: Create a binary user-item matrix
interaction_matrix = df.pivot_table(index='student_id', columns='question_id', values='is_correct', fill_value=0)

# Step 4: Visualize sparsity heatmap (only a sample for readability)
sample_matrix = interaction_matrix.iloc[:25, :25]  # Visualize 25x25 block
plt.figure(figsize=(12, 8))
sns.heatmap(sample_matrix, cmap="Blues", cbar=False, linewidths=0.5, linecolor='gray')
plt.title("📊 Student-Question Interaction Heatmap (Sample 25x25)")
plt.xlabel("Question ID")
plt.ylabel("Student ID")
plt.xticks(rotation=45)
plt.yticks(rotation=0)
plt.tight_layout()
plt.show()