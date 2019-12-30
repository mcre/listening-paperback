echo $1
pj=$1
mkdir -p ./projects/${pj}/tmp
log="./projects/${pj}/tmp/batch_first_voice_check.log"
./batch.sh ${pj} x x voice_check 2>&1 | tee ${log}
cp ./work/novel.pdf ./projects/${pj}/tmp/novel.pdf
cp ./work/novel.tex ./projects/${pj}/tmp/novel.tex
cp ./work/fast_check_movie.mp4 ./projects/${pj}/tmp/fast_check_movie.mp4
