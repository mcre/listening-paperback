pj=$1
log="./projects/${pj}/batch_first.log"
./batch.sh ${pj} x x voice | tee ${log} || exit 1
echo '# pdf2png' | tee -a ${log}
mkdir ./work/page_images | tee -a ${log}
docker run --rm -v $PWD/work:/work gkmr/pdf-tools /bin/sh -c "pdftocairo -png -r 200 /work/novel.pdf /work/page_images/novel" | tee -a ${log} || exit 1
echo '# build_timekeeper' | tee -a ${log}
docker run --rm -v $PWD/work:/work lp-python /bin/sh -c "python -u build_timekeeper.py" | tee -a ${log} || exit 1