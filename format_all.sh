dir=$1
outdir=$2
mkdir -p $outdir
for file in $(ls $dir/*.yaml);
do
    fname=$(basename $file)
    python format_yaml.py $file $outdir/$fname
done