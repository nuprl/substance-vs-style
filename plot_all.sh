inpdir=$1
outpdir=$2
for file in $inpdir/*.yaml; 
    do
        filename="${file##*/}"
        filename="${filename%.*}"
        echo $filename
        python3.11 -m student_progress_graph.plot_graph $file $outpdir/$filename
    done