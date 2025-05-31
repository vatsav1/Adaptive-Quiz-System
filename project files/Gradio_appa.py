import gradio as gr
import pandas as pd
import numpy as np
import random
from sqlalchemy import create_engine, text
from urllib.parse import quote_plus
from datetime import datetime
from openai import OpenAI
import os

# --- OpenAI Configuration ---
client = OpenAI(api_key="")  # Set your API key in environment variables

# --- Database Configuration ---
password = "Sri140299@"
encoded_password = quote_plus(password)
connection_string = f"mysql+mysqlconnector://root:{encoded_password}@127.0.0.1/question_bank"

def get_engine():
    return create_engine(connection_string)

# --- Utility Functions ---
def clean_answer(answer):
    """Clean answer text by removing extra formatting"""
    if pd.isna(answer):
        return "Not answered"
    return str(answer).replace('$', '').strip()

def generate_performance_analysis(results_df):
    """Generate AI analysis of student performance"""
    try:
        prompt = f"""
        Analyze this student's quiz performance and provide specific feedback:
        
        Quiz Results:
        {results_df.to_markdown(index=False)}
        
        Please provide:
        1. A summary of strengths and weaknesses
        2. Topic areas needing improvement
        3. Specific study recommendations
        4. Encouraging conclusion
        
        Keep the analysis concise (4-5 paragraphs) and educational.
        """
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=500
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"OpenAI error: {str(e)}")
        return "Performance analysis unavailable at this time."

# --- User Management ---
def is_existing_user(student_id, student_name):
    """Check if user exists or create new user"""
    try:
        engine = get_engine()
        with engine.connect() as conn:
            query = text("SELECT student_name FROM students WHERE id = :student_id")
            result = conn.execute(query, {"student_id": int(student_id)})
            row = result.fetchone()
            
            if row:
                return row[0].strip().lower() == student_name.strip().lower()
            else:
                insert_query = text("""
                    INSERT INTO students (id, student_name) 
                    VALUES (:student_id, :student_name)
                """)
                conn.execute(insert_query, {
                    "student_id": int(student_id),
                    "student_name": student_name
                })
                conn.commit()
                return False
    except Exception as e:
        print(f"Database error in is_existing_user: {str(e)}")
        raise

# --- Question Recommendation Algorithms ---
def get_popularity_based(student_id, limit=10):
    """Get questions based on popularity"""
    try:
        engine = get_engine()
        query = text("""
            SELECT q.id, q.question, q.correct_answer, q.wrong_answer_1, q.wrong_answer_2, q.wrong_answer_3, q.topic_number
            FROM questions q
            JOIN (
                SELECT question_id, AVG(is_correct) as score
                FROM student_attempts
                GROUP BY question_id
            ) sq ON q.id = sq.question_id
            WHERE q.id NOT IN (
                SELECT question_id FROM student_attempts WHERE student_id = :student_id
            )
            ORDER BY sq.score DESC LIMIT :limit
        """)
        df = pd.read_sql_query(
            query, 
            engine, 
            params={"student_id": int(student_id), "limit": int(limit)}
        )
        df['source'] = 'popularity'
        return df
    except Exception as e:
        print(f"Database error in get_popularity_based: {str(e)}")
        return pd.DataFrame()

def get_user_based(student_id, limit=3):
    """Get random questions for user-based recommendations"""
    try:
        engine = get_engine()
        query = text("""
            SELECT id, question, correct_answer, wrong_answer_1, wrong_answer_2, wrong_answer_3, topic_number 
            FROM questions 
            ORDER BY RAND() 
            LIMIT :limit
        """)
        df = pd.read_sql_query(
            query,
            engine,
            params={"limit": int(limit)}
        )
        df['source'] = 'user_based'
        return df
    except Exception as e:
        print(f"Database error in get_user_based: {str(e)}")
        return pd.DataFrame()

def get_svd_based(student_id, limit=3):
    """Get random questions for SVD-based recommendations"""
    try:
        engine = get_engine()
        query = text("""
            SELECT id, question, correct_answer, wrong_answer_1, wrong_answer_2, wrong_answer_3, topic_number 
            FROM questions 
            ORDER BY RAND() 
            LIMIT :limit
        """)
        df = pd.read_sql_query(
            query,
            engine,
            params={"limit": int(limit)}
        )
        df['source'] = 'svd'
        return df
    except Exception as e:
        print(f"Database error in get_svd_based: {str(e)}")
        return pd.DataFrame()

def generate_quiz(student_id, is_new):
    """Generate quiz based on user status"""
    try:
        if is_new:
            return get_popularity_based(student_id, limit=7)
        else:
            return pd.concat([
                get_popularity_based(student_id, limit=4),
                get_user_based(student_id, limit=3),
                get_svd_based(student_id, limit=3)
            ]).sample(frac=1).reset_index(drop=True).head(10)
    except Exception as e:
        print(f"Error generating quiz: {str(e)}")
        return pd.DataFrame()

def log_attempts(student_id, quiz_df, answers):
    """Log quiz attempts and return results"""
    try:
        engine = get_engine()
        result_data = []
        with engine.connect() as conn:
            summary = []
            for i, ans in enumerate(answers):
                if i >= len(quiz_df):
                    continue
                row = quiz_df.iloc[i]
                is_correct = int(ans == row['correct_answer'])

                conn.execute(text("""
                    INSERT INTO student_attempts 
                    (student_id, question_id, is_correct, time_taken_sec) 
                    VALUES (:student_id, :question_id, :is_correct, :time_taken)
                """), {
                    "student_id": int(student_id),
                    "question_id": int(row['id']),
                    "is_correct": is_correct,
                    "time_taken": int(random.randint(20, 60))
                })
                conn.commit()
                summary.append(f"Q{i+1:02d}: {'✅' if is_correct else '❌'}")
                result_data.append({
                    "Question": f"Q{i+1:02d}",
                    "Your Answer": clean_answer(ans),
                    "Correct Answer": clean_answer(row['correct_answer']),
                    "Status": "Correct" if is_correct else "Incorrect",
                    "Topic": row.get('topic_number', 'General'),
                    "Difficulty": row.get('difficulty', 'Medium')
                })
        return "\n".join(summary), pd.DataFrame(result_data)
    except Exception as e:
        print(f"Database error in log_attempts: {str(e)}")
        return f"Error logging attempts: {str(e)}", pd.DataFrame()

# --- Gradio Interface ---
def build_interface():
    """Build the Gradio interface"""
    with gr.Blocks(title="Adaptive Quiz System") as demo:
        quiz_df = gr.State(pd.DataFrame())

        with gr.Tab("Login"):
            gr.Markdown("## Student Login")
            with gr.Row():
                student_id = gr.Textbox(label="Student ID", placeholder="Enter your student ID")
                student_name = gr.Textbox(label="Student Name", placeholder="Enter your full name")
            start_btn = gr.Button("Start Quiz", variant="primary")
            login_status = gr.Textbox(label="Status", interactive=False)

        with gr.Tab("Quiz") as quiz_tab:
            gr.Markdown("## Quiz Questions")
            question_components = []
            for i in range(10):
                with gr.Accordion(f"Question {i+1}", open=False, visible=False) as accordion:
                    question_text = gr.Markdown("Question will appear here")
                    options = gr.Radio([], label="Select your answer", interactive=True)
                    question_components.append((accordion, question_text, options))
            submit_btn = gr.Button("Submit Quiz", visible=False, variant="primary")

        with gr.Tab("Results"):
            gr.Markdown("## Quiz Results")
            with gr.Row():
                summary_box = gr.Textbox(label="Results Summary", interactive=False)
            with gr.Row():
                details_box = gr.DataFrame(
                    label="Detailed Results", 
                    headers=["Question", "Your Answer", "Correct Answer", "Status", "Topic", "Difficulty"],
                    datatype=["str"]*6,
                    interactive=False
                )
            with gr.Row():
                ai_analysis = gr.Textbox(label="AI Performance Analysis", lines=8, interactive=False)

        def load_quiz(student_id, student_name):
            """Load quiz questions"""
            try:
                if not student_id or not student_name:
                    return "Please enter both student ID and name", *([gr.update()]*30), gr.update(visible=False)

                student_id = int(student_id)
                existing = is_existing_user(student_id, student_name)
                df = generate_quiz(student_id, not existing)

                if df.empty:
                    return "Error: No questions available", *([gr.update()]*30), gr.update(visible=False)

                quiz_df.value = df
                updates = []

                for i in range(10):
                    if i < len(df):
                        row = df.iloc[i]
                        options = [
                            clean_answer(row['correct_answer']),
                            clean_answer(row['wrong_answer_1']),
                            clean_answer(row['wrong_answer_2']),
                            clean_answer(row['wrong_answer_3'])
                        ]
                        random.shuffle(options)
                        updates.extend([
                            gr.update(visible=True),
                            gr.update(value=f"**Question {i+1}:** {clean_answer(row['question'])}"),
                            gr.update(choices=options, value=None)
                        ])
                    else:
                        updates.extend([
                            gr.update(visible=False),
                            gr.update(value=""),
                            gr.update(choices=[], value=None)
                        ])

                return (
                    "Welcome back! Loading your personalized quiz..." if existing 
                    else "New user detected. Starting with popular questions...",
                    *updates,
                    gr.update(visible=True)
                )
            except ValueError:
                return "Student ID must be a number", *([gr.update()]*30), gr.update(visible=False)
            except Exception as e:
                return f"Error: {str(e)}", *([gr.update()]*30), gr.update(visible=False)

        def submit_quiz(student_id, *answers):
            """Handle quiz submission"""
            try:
                if quiz_df.value.empty:
                    return "No active quiz to submit", None, None

                student_id = int(student_id)
                answers = answers[:len(quiz_df.value)]

                summary, result_df = log_attempts(student_id, quiz_df.value, answers)
                analysis = generate_performance_analysis(result_df)
                return summary, result_df, analysis
            except Exception as e:
                return f"Submission error: {str(e)}", None, None

        # Event bindings
        start_btn.click(
            fn=load_quiz,
            inputs=[student_id, student_name],
            outputs=[login_status] + [comp for q in question_components for comp in q] + [submit_btn]
        )

        submit_btn.click(
            fn=submit_quiz,
            inputs=[student_id] + [q[2] for q in question_components],
            outputs=[summary_box, details_box, ai_analysis]
        )

    return demo

# Launch the application
if __name__ == "__main__":
    try:
        # Test database connection first
        engine = create_engine(connection_string)
        with engine.connect() as conn:
            print("Database connection successful")

        demo = build_interface()
        demo.launch(
            server_name="127.0.0.1",
            server_port=7860,
            show_error=True,
            debug=True,
            share=True
        )
    except Exception as e:
        print(f"Failed to start application: {str(e)}")
        print("Please check:")
        print("1. MySQL server is running")
        print("2. Database 'question_bank' exists")
        print("3. Username and password are correct")
        print("4. MySQL connector is installed (pip install mysql-connector-python)")
        print("5. OpenAI API key is properly set in environment variables")