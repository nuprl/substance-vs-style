inpdir=$1
output_dir=$2
problem_clues=$3
echo $output_dir

problems=( "add_int"  "add_up"  "altText"  "assessVowels"  "changeSection"  "check_prime"  "combine"  "convert"  
"create_list"  "fib"  "findHorizontals"  "find_multiples"  "generateCardDeck"  "getSeason"  "increaseScore"  
"laugh"  "pattern"  "percentWin"  "planets_mass"  "print_time"  "readingIceCream"  "remove_odd"  "reverseWords"  
"set_chars"  "sortBySuccessRate"  "sort_physicists"  "sortedBooks"  "student_grades"  "subtract_add"  "times_with"  
"topScores"  "total_bill"  "translate"
)
for filename in ${problems[@]}; 
    do
        echo $filename
        python3 -m student_progress_graph.analyse_single $inpdir/$filename.yaml $output_dir/$filename $problem_clues -q
    done