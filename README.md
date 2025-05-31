from pathlib import Path

readme_text = """
# AI-Powered Adaptive Quiz System

## 📚 Overview
This project implements an adaptive quiz platform using:
- **Gradio** for the front-end interface
- **MySQL** for storing user and question data
- **OpenAI GPT-3.5 API** for AI-generated explanations and performance analysis
- **Hybrid Recommendation Logic** including Popularity-based, User-based, and SVD-based models

It is designed to adaptively recommend questions based on the student's performance, log their responses, and provide actionable feedback.

---

## 🧠 Features
- Dynamic Gradio interface with LaTeX support for math questions
- Student registration/login (with name verification)
- AI-generated per-question explanations (OpenAI)
- AI performance analysis post-submission
- Stores all attempts and correctness in MySQL
- Three-tiered recommendation strategy:
  - **Popularity-based** (most commonly answered correctly)
  - **User-based** (similar user preferences)
  - **SVD-based** (collaborative filtering logic)

---

## 🏗️ Project Structure
├── Gradio_APP.py # Main application entry point
├── UserBased.py # User-based recommendation logic
├── SVD.py # SVD-based recommendation logic
├── sql_connectivity.py # SQL connection helpers (optional)
├── datasets/ # Optional dataset storage
├── clean_env/ # Virtual environment (optional)
├── question_bank (MySQL) # MySQL DB with students, questions, attempts

