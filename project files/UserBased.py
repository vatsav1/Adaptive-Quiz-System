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

# Load attempts and question metadata
attempts_df = pd.read_sql("SELECT student_id, question_id, is_correct FROM student_attempts", conn)
questions_df = pd.read_sql("SELECT id, topic_number, variation, difficulty_level FROM questions", conn)

# Ensure the recommendation_log table exists
cursor = conn.cursor()
cursor.execute("""
    CREATE TABLE IF NOT EXISTS recommendation_log (
        id INT AUTO_INCREMENT PRIMARY KEY,
        student_id INT,
        question_id INT,
        topic_number VARCHAR(10),
        difficulty_level INT,
        recommendation_reason VARCHAR(100),
        recommended_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
""")
conn.commit()

# Step 2: Merge attempts with question info
merged_df = attempts_df.merge(questions_df, left_on='question_id', right_on='id')

# Step 3: Compute student's average correctness per topic
topic_perf = merged_df.groupby(['student_id', 'topic_number'])['is_correct'].mean().reset_index()
topic_perf.columns = ['student_id', 'topic_number', 'avg_score']

# Step 4: Define function to get and log performance-based recommendations
def recommend_and_log(student_id, questions_df, merged_df, topic_perf, top_n=5):
    recommendations = []
    attempted_questions = merged_df[merged_df['student_id'] == student_id]['question_id'].unique()
    student_perf = topic_perf[topic_perf['student_id'] == student_id]
    strong_topics = student_perf[student_perf['avg_score'] >= 0.7]['topic_number'].tolist()
    weak_topics = student_perf[student_perf['avg_score'] < 0.7]['topic_number'].tolist()
    #debug#print(student_perf['avg_score'])
    def insert_log(rec_list, reason):
        for rec in rec_list.itertuples():
            recommendations.append({
                'question_id': rec.id,
                'topic_number': rec.topic_number,
                'difficulty_level': rec.difficulty_level,
                'reason': reason
            })
            cursor.execute("""
                INSERT INTO recommendation_log (student_id, question_id, topic_number, difficulty_level, recommendation_reason)
                VALUES (%s, %s, %s, %s, %s)
            """, (student_id, rec.id, rec.topic_number, rec.difficulty_level, reason))
    
    for topic in strong_topics:
        pool = questions_df[
            (questions_df['topic_number'] == topic) &
            (~questions_df['id'].isin(attempted_questions)) &
            (questions_df['difficulty_level'] >= 3)
        ]
        if not pool.empty:
            top_qs = pool.sample(n=min(top_n, len(pool)), random_state=42)
            insert_log(top_qs, "Challenge from strong topic")
        else:
            #debug
            print('pool is empty')
            #print(questions_df['topic_number'])
            #print(questions_df['topic_number'] == topic)
            #print(questions_df['id'] )
            #print(~questions_df['id'].isin(attempted_questions))
            #print(attempted_questions)
            

    for topic in weak_topics:
        pool = questions_df[
            (questions_df['topic_number'] == topic) &
            (~questions_df['id'].isin(attempted_questions)) &
            (questions_df['difficulty_level'] <= 2)
        ]
        if not pool.empty:
            top_qs = pool.sample(n=min(top_n, len(pool)), random_state=42)
            insert_log(top_qs, "Practice from weak topic")
        else:
            #debug
            print('pool is empty')
            #print(questions_df['topic_number'])
            #print(questions_df['topic_number'] == topic)
            #print(questions_df['id'] )
            #print(~questions_df['id'].isin(attempted_questions))
            #print(attempted_questions)

    conn.commit()
    return recommendations[:top_n]

# Step 5: Example usage
student_id = 33
recommendations = recommend_and_log(student_id, questions_df, merged_df, topic_perf, top_n=5)

print(f"📌 Logged Recommendations for Student {student_id}:")
for rec in recommendations:
    print(f"Question ID: {rec['question_id']} | Topic: {rec['topic_number']} | DOD: {rec['difficulty_level']} | {rec['reason']}")

# Cleanup
cursor.close()
conn.close()