import pandas as pd
from surprise import SVD, Dataset, Reader
from surprise.model_selection import train_test_split, GridSearchCV
from surprise.model_selection import cross_validate
from surprise import accuracy
import mysql.connector

# Step 1: Connect to the MySQL database and load student_attempts
conn = mysql.connector.connect(
     host="127.0.0.1",
    user="root",
    password="Sri140299@",
    database="question_bank"
)

df = pd.read_sql("SELECT student_id, question_id, is_correct FROM student_attempts", conn)
conn.close()

# Step 2: Prepare data for Surprise
reader = Reader(rating_scale=(0, 1))
data = Dataset.load_from_df(df[['student_id', 'question_id', 'is_correct']], reader)

# Step 3: Define parameter grid and perform GridSearchCV
param_grid = {
    'n_factors': [50, 100, 150],
    'n_epochs': [20, 30, 40],
    'lr_all': [0.002, 0.005, 0.01],
    'reg_all': [0.2,0.4,0.6]
}

gs = GridSearchCV(SVD, param_grid, measures=['rmse', 'mae'], cv=3)
gs.fit(data)

# Step 4: Output the best model parameters
print("\n✅ Best RMSE Score:", gs.best_score['rmse'])
print("🔧 Best Parameters:", gs.best_params['rmse'])

# Step 5: Train the best model on full training set
trainset, testset = train_test_split(data, test_size=0.2, random_state=42)
best_model = gs.best_estimator['rmse']
best_model.fit(trainset)

# Step 6: Evaluate model performance on test set
predictions = best_model.test(testset)
print("\n📊 Evaluation Metrics:")
print("RMSE:", accuracy.rmse(predictions))
print("MAE:", accuracy.mae(predictions))

cross_validate(best_model, data, measures=['RMSE', 'MAE'], cv=5,verbose=True)

# Step 7: Function to recommend top-N questions for a student
def recommend_questions_for_student(student_id, all_question_ids, attempted_question_ids, top_n=5):
    recommendations = []

    for qid in all_question_ids:
        if qid not in attempted_question_ids:
            pred = best_model.predict(student_id, qid)
            recommendations.append((qid, pred.est))

    recommendations.sort(key=lambda x: x[1], reverse=True)
    return recommendations[:top_n]

# Step 8: Example usage
target_student_id = 1
attempted_qs = df[df['student_id'] == target_student_id]['question_id'].tolist()
all_qs = df['question_id'].unique().tolist()

top_recommendations = recommend_questions_for_student(target_student_id, all_qs, attempted_qs, top_n=5)

print(f"\n📌 Top 5 SVD-based recommendations for Student {target_student_id}:")
for qid, score in top_recommendations:
    print(f"Question ID: {qid}, Predicted Success Score: {score:.3f}")