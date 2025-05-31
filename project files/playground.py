attempts_df = pd.read_sql_query(
            "SELECT student_id, question_id, is_correct FROM student_attempts",
            engine
        )
        questions_df = pd.read_sql_query(
            "SELECT id, topic_number, variation, difficulty_level FROM questions",
            engine
        )

        # Step 3: Merge and recommend
        merged_df = attempts_df.merge(questions_df, left_on='question_id', right_on='id')
        topic_perf = (
            merged_df.groupby(['student_id', 'topic_number'])['is_correct']
            .mean().reset_index().rename(columns={'is_correct': 'avg_score'})
        )

        recommendations = recommend_and_log(student_id, questions_df, merged_df, topic_perf, top_n=5)
        question_ids = [rec['question_id'] for rec in recommendations][:limit]
