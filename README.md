# AI-Powered Adaptive Quiz System

## Overview
This project implements an adaptive quiz platform using:
- **Gradio** for the front-end interface
- **MySQL** for storing user and question data
- **OpenAI GPT-3.5 API** for AI-generated explanations and performance analysis
- **Hybrid Recommendation Logic** including Popularity-based, User-based, and SVD-based models
- **DOD (Degree of Difficulty) Clustering** and **Time Clustering** using KMeans

It is designed to adaptively recommend questions based on the student's performance, log their responses, and provide actionable feedback.

---

## Features
- Dynamic Gradio interface with LaTeX support for math questions
- Student registration/login (with name verification)
- AI performance analysis post-submission
- Stores all attempts and correctness in MySQL
- Adaptive recommendation logic based on user type:
  - **New Users** receive questions based only on popularity-based recommendations (easier and high-success-rate)
  - **Existing Users** receive a blend of all three models (Popularity + User-Based + SVD) to challenge and improve their skills
- Three-tiered recommendation strategy:
  - **Popularity-based** (most commonly answered correctly)
  - **User-based** (similar user preferences)
  - **SVD-based** (collaborative filtering logic)
- DOD clustering to assign difficulty levels based on historical correctness and time deviation

---

## DOD & Time Clustering (KMeans-based)
The project uses a **2-step clustering approach** to assign and update the Degree of Difficulty (DOD) and Time expectations for each variation:

### 1. **Correction Ratio Clustering**
- We compute correction ratio: `CorrectlyAttempted / Attempted`
- KMeans is applied to cluster into 5 groups → **Success Clusters**

### 2. **Proportional Time Clustering**
- ExpectedTime = CorrectlyAttempted × TimeAssigned
- TimeDeviation = (TimeTaken - ExpectedTime) / ExpectedTime
- KMeans is applied to this ratio → **Time Clusters**

### Final DOD Assignment:
- If a variation is in Correction Cluster = 3 and Time Cluster = 5 → final DOD = 4 (via swapping logic)
- All DODs and suggested_times are then updated in the questions table

---

## Project Structure
```
├── Gradio_APP.py           # Main application entry point
├── UserBased.py            # User-based recommendation logic
├── SVD.py                  # SVD-based recommendation logic
├── DOD_clustering.py       # KMeans-based clustering for DOD and time clustering
├── sql_connectivity.py     # SQL connection helpers (optional)
├── datasets/               # Optional dataset storage
├── clean_env/              # Virtual environment (optional)
├── question_bank (MySQL)   # MySQL DB with students, questions, attempts
```

---


---

## Running the App
```bash
python Gradio_APP.py
```
Visit `http://127.0.0.1:7860` in your browser.

To update DODs and time clusters:
```bash
python DOD_clustering.py
```

---

## How It Works
1. **Login Tab** – Student enters ID and name. New users are registered.
2. **Quiz Tab** – 10 questions loaded using hybrid recommendation logic.
3. **Results Tab** – AI summarizes performance and logs answers.

---

## Requirements
- Python 3.8+
- MySQL database with tables: `students`, `questions`, `student_attempts`
- OpenAI API Key

---

## Future Improvements
- Real SVD matrix factorization using Surprise or LightFM
- Dynamic topic-wise dashboards and personalized revision plans
- Admin control panel for batch uploading and DOD curation

---

## Contact
For queries or contributions, please open an issue or submit a pull request.
