import mysql.connector
import pandas as pd
from datetime import datetime

# Step 1: Connect to MySQL and load student_attempts and questions
conn = mysql.connector.connect(
     host="127.0.0.1",
    user="root",
    password="Sri140299@",
    database="question_bank"
)

cursor = conn.cursor()

# Load student_attempts and questions
attempts_df = pd.read_sql("SELECT student_id, question_id, is_correct FROM student_attempts", conn)
questions_df = pd.read_sql("SELECT id, topic_number, difficulty_level FROM questions", conn)

# # Ensure recommendation_log table exists
# cursor.execute("""
#     CREATE TABLE IF NOT EXISTS recommendation_log (
#         id INT AUTO_INCREMENT PRIMARY KEY,
#         student_id INT,
#         question_id INT,
#         topic_number VARCHAR(10),
#         difficulty_level INT,
#         recommendation_reason VARCHAR(100),
#         recommended_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
#     );
# """)
# conn.commit()

# Step 2: Define popularity-based recommender
def recommend_by_popularity(student_id=None, attempts_df=None, questions_df=None, top_n=5):
    recommendations = []

    # Step 2a: Calculate correctness rate for each question
    correctness_rate = attempts_df.groupby('question_id')['is_correct'].mean().round(3).reset_index()
    correctness_rate.columns = ['question_id', 'correctness_rate']

    # Step 2b: Exclude already-attempted questions (if student ID is provided)
    if student_id:
        attempted = attempts_df[attempts_df['student_id'] == student_id]['question_id'].unique()
        correctness_rate = correctness_rate[~correctness_rate['question_id'].isin(attempted)]

    # Step 2c: Merge with question metadata
    top_questions = correctness_rate.merge(questions_df, left_on='question_id', right_on='id')
    top_questions = top_questions.sort_values(by='correctness_rate', ascending=False).head(top_n)

    # Step 2d: Log recommendations to database
    for row in top_questions.itertuples():
        cursor.execute("""
            INSERT INTO recommendation_log (student_id, question_id, topic_number, difficulty_level, recommendation_reason)
            VALUES (%s, %s, %s, %s, %s)
        """, (
            student_id if student_id else 0,
            row.question_id,
            row.topic_number,
            row.difficulty_level,
            "Popularity-based recommendation"
        ))
        recommendations.append({
            'question_id': row.question_id,
            'topic_number': row.topic_number,
            'difficulty_level': row.difficulty_level,
            'correctness_rate': round(row.correctness_rate, 3)
        })

    conn.commit()
    return recommendations

# Step 3: Example usage
student_id = 20 # replace with a new or existing student
recommendations = recommend_by_popularity(student_id, attempts_df, questions_df, top_n=5)


print(f"📊 Popularity-Based Recommendations for Student {student_id}:")
for rec in recommendations:
    print(f"Question ID: {rec['question_id']} | Topic: {rec['topic_number']} | DOD: {rec['difficulty_level']} | Correctness: {rec['correctness_rate']}")

# # Step 4: Example usage
# student_id = None # replace with a new or existing student
# recommendations = recommend_by_popularity(student_id, attempts_df, questions_df, top_n=500)

# print(f"📊 Popularity-Based Recommendations for model:")
# for rec in recommendations:
#     print(f"Question ID: {rec['question_id']} | Topic: {rec['topic_number']} | DOD: {rec['difficulty_level']} | Correctness: {rec['correctness_rate']}")


# Cleanup
cursor.close()
conn.close()