inpdir=$1
homedir=$(pwd)
alias firefox=/Applications/Firefox.app/Contents/MacOS/firefox

echo $homedir
for i in $inpdir/*/*.html; do
    echo $file://$homedir/$i
    firefox file://$homedir/$i       
done