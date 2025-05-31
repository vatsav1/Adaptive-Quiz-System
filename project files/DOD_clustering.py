import pandas as pd
import numpy as np
import mysql.connector
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score
import matplotlib.pyplot as plt

# Step 1: Connect to MySQL and load data
conn = mysql.connector.connect(
    host="127.0.0.1",
    user="root",
    password="Sri140299@",
    database="question_bank"
)

# Load questions and attempts
questions_df = pd.read_sql("SELECT id AS question_id FROM questions", conn)
attempts_df = pd.read_sql("SELECT question_id, is_correct, time_taken_sec FROM student_attempts", conn)

# Step 2: Aggregate metrics per question
grouped = attempts_df.groupby('question_id').agg(
    Attempted=('is_correct', 'count'),
    CorrectlyAttempted=('is_correct', 'sum'),
    Total_Time=('time_taken_sec', 'sum'),
    Correct_Time=('time_taken_sec', lambda x: x[attempts_df.loc[x.index, 'is_correct'] == 1].sum())
).reset_index()

# Step 3: Compute ratios and time-based metrics
grouped['Correction_Ratio'] = grouped['CorrectlyAttempted'] / grouped['Attempted']
grouped['Correction_Ratio'] = grouped['Correction_Ratio'].fillna(0)
grouped['Time_Assigned'] = grouped['Correct_Time'] / grouped['CorrectlyAttempted']
grouped['Time_Assigned'] = grouped['Time_Assigned'].replace([np.inf, -np.inf], np.nan).fillna(0)
grouped['Expected_Time'] = grouped['CorrectlyAttempted'] * grouped['Time_Assigned']
grouped['Proportional_Diff'] = (grouped['Correct_Time'] - grouped['Expected_Time']) / grouped['Expected_Time']
grouped['Proportional_Diff'] = grouped['Proportional_Diff'].replace([np.inf, -np.inf], 0).fillna(0)

# Step 4: Normalize features
scaler = StandardScaler()
scaled_features = scaler.fit_transform(grouped[['Correction_Ratio', 'Proportional_Diff']])
grouped[['Correction_Ratio_scaled', 'Proportional_Diff_scaled']] = scaled_features

# Elbow and Silhouette Evaluation
inertias, silhouettes = [], []
X_corr = grouped[['Correction_Ratio_scaled']]
X_time = grouped[['Proportional_Diff_scaled']]

for k in range(2, 11):
    km_corr = KMeans(n_clusters=k, random_state=42)
    km_corr.fit(X_corr)
    inertias.append(km_corr.inertia_)
    silhouettes.append(silhouette_score(X_corr, km_corr.labels_))

# Plot Elbow and Silhouette Score
plt.figure(figsize=(10, 5))
plt.subplot(1, 2, 1)
plt.plot(range(2, 11), inertias, marker='o')
plt.title('Elbow Method (Correction Ratio)')
plt.xlabel('Number of Clusters')
plt.ylabel('Inertia')

plt.subplot(1, 2, 2)
plt.plot(range(2, 11), silhouettes, marker='o', color='green')
plt.title('Silhouette Score (Correction Ratio)')
plt.xlabel('Number of Clusters')
plt.ylabel('Score')

plt.tight_layout()
plt.show()

# Step 5: Apply KMeans with 5 clusters
kmeans_corr = KMeans(n_clusters=5, random_state=42)
grouped['clusters'] = kmeans_corr.fit_predict(X_corr) + 1

kmeans_time = KMeans(n_clusters=5, random_state=42)
grouped['time_clusters'] = kmeans_time.fit_predict(X_time) + 1

# Step 6: Compute DOD and Suggested Time
grouped['suggested_dods'] = ((grouped['clusters'] + grouped['time_clusters']) / 2).round().clip(1, 5).astype(int)
grouped['suggested_time_in_seconds'] = grouped['Time_Assigned'].round().astype(int)

# Step 7: Log to dod_clustering_log
cursor = conn.cursor()
cursor.execute("""
    CREATE TABLE IF NOT EXISTS dod_clustering_log (
        question_id INT PRIMARY KEY,
        CorrectlyAttempted INT,
        Attempted INT,
        Total_Time FLOAT,
        clusters INT,
        time_clusters INT,
        suggested_time_in_seconds INT,
        suggested_dods INT
    )
""")
cursor.execute("DELETE FROM dod_clustering_log")

log_data = grouped[[
    'question_id', 'CorrectlyAttempted', 'Attempted', 'Total_Time',
    'clusters', 'time_clusters', 'suggested_time_in_seconds', 'suggested_dods'
]].values.tolist()

cursor.executemany("""
    INSERT INTO dod_clustering_log
    (question_id, CorrectlyAttempted, Attempted, Total_Time, clusters, time_clusters, suggested_time_in_seconds, suggested_dods)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
""", log_data)
conn.commit()

# Step 8: Update questions table with DOD and Time
update_query = """
    UPDATE questions
    SET difficulty_level = %s, time_in_seconds = %s
    WHERE id = %s
"""
update_data = grouped[['suggested_dods', 'suggested_time_in_seconds', 'question_id']].values.tolist()
cursor.executemany(update_query, update_data)
conn.commit()

cursor.close()
conn.close()

# Print DOD distribution
dod_counts = grouped['suggested_dods'].value_counts().sort_index()
print("✅ DOD and time updated in questions table. Distribution:")
for dod, count in dod_counts.items():
    print(f"DOD {dod}: {count} questions")