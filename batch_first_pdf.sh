echo $1
pj=$1
mkdir -p ./projects/${pj}/tmp
log="./projects/${pj}/tmp/batch_first_pdf.log"
./batch.sh -s pdf ${pj} 2>&1 | tee ${log}
cp ./work/novel.pdf ./projects/${pj}/tmp/novel.pdf
cp ./work/chapters.json ./projects/${pj}/tmp/chapters.json
cp ./work/tex_output.txt ./projects/${pj}/tmp/tex_output.txt
cp ./work/novel.tex ./projects/${pj}/tmp/novel.tex
