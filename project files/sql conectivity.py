import os
import pandas as pd
import mysql.connector
import time

# Define folder and DB connection
csv_folder = r"C:\Users\HP\Documents\dataMining\Final Project\Archive"

conn = mysql.connector.connect(
    host="127.0.0.1",
    user="root",
    password="Sri140299@",
    database="question_bank"
)
cursor = conn.cursor()

# Required CSV → SQL field mapping
required_columns = {
    "Topic_Number": "topic_number",
    "Variation": "variation",
    "Question": "question",
    "Correct_Answer_1": "correct_answer",
    "Wrong_Answer_1": "wrong_answer_1",
    "Wrong_Answer_2": "wrong_answer_2",
    "Wrong_Answer_3": "wrong_answer_3",
    "Answer_Type": "answer_type",
    "Solution_text": "solution_text",
    "ContributorMail": "contributor_email",
    "Solution_IAV": "solution_IAV",
    "Time_in_seconds": "time_in_seconds",
    "Difficulty_Level": "difficulty_level",
    "Question_Type": "question_type",
    "Question_IAV": "question_IAV"
}

sql_fields = ", ".join(required_columns.values())

def insert_csv(file_path):
    try:
        df = pd.read_csv(file_path)

        # Add missing columns with default values
        for col in required_columns:
            if col not in df.columns:
                df[col] = ""

        df = df[list(required_columns.keys())]  # ensure correct order

        for _, row in df.iterrows():
            values = tuple(row[col] for col in required_columns)
            cursor.execute(
                f"INSERT INTO questions ({sql_fields}) VALUES ({','.join(['%s']*len(values))})",
                values
            )
        conn.commit()
        print(f"✅ Successfully imported: {os.path.basename(file_path)}")

    except Exception as e:
        print(f"❌ Failed to import {os.path.basename(file_path)}: {e}")
        conn.rollback()

# Import all CSVs from folder
for file in os.listdir(csv_folder):
    if file.endswith(".csv"):
        print(f"📥 Importing {file}...")
        file_path = os.path.join(csv_folder, file)
        insert_csv(file_path)
        time.sleep(0.5)

cursor.close()
conn.close()