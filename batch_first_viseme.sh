echo $1
pj=$1
mkdir -p ./projects/${pj}/tmp
log="./projects/${pj}/tmp/batch_first_viseme.log"
./batch.sh ${pj} x x viseme 2>&1 | tee ${log}
if [[ "${PIPESTATUS[0]}" == 1 ]] || [[ "$pipestatus[1]" == 1 ]]; then exit 0; fi;
cp ./work/novel.pdf ./projects/${pj}/tmp/novel.pdf
cp ./work/novel.tex ./projects/${pj}/tmp/novel.tex
cp ./work/viseme.pdf ./projects/${pj}/tmp/viseme.pdf
cp ./work/voice_movie.mp4 ./projects/${pj}/tmp/voice_movie.mp4
