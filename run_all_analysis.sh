problems=("topScores" "total_bill" "add_up" "add_int" "laugh" "readingIceCream" \
        "assessVowels" \
        # EXCEPTIONS
         "planets_mass" "altText" "changeSection")

echo ${problems[@]}

for prob in ${problems[@]};
    do
        echo $prob
        python3 -m student_progress_graph.run_analysis tagging_clues/tagging_graphs_sep27/$prob.yaml \
            tagging_clues/analysis/$prob tagging_clues/problem_clues.yaml
    done

echo "Checking that exceptions are in fact a minority..."
python3 student_progress_graph/analysis_data.py
echo "Checking all problems"
python3 -m student_progress_graph.run_analysis tagging_clues/tagging_graphs_sep27 tagging_clues/analysis/all_problems \
    tagging_ckues/problem_clues.yaml