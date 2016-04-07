file=tabular
pdflatex $file
bibtex $file
pdflatex $file
pdflatex $file 

rm *log *aux *bbl *blg

evince ${file}.pdf &> /dev/null &
