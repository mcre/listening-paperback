pj=$1
mkdir -p ./projects/${pj}/tmp
log="./projects/${pj}/tmp/batch_first_pdf.log"
./batch.sh ${pj} x x pdf 2>&1 | tee ${log}
cp ./work/novel.pdf ./projects/${pj}/tmp/novel.pdf
cp ./work/chapters_and_pages.json ./projects/${pj}/tmp/chapters_and_pages.json
cp ./work/tex_output.txt ./projects/${pj}/tmp/tex_output.txt
cp ./work/novel.tex ./projects/${pj}/tmp/novel.tex
echo $1