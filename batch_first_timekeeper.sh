pj=$1
mkdir -p ./projects/${pj}/tmp
log="./projects/${pj}/tmp/batch_first_timekeeper.log"
./batch.sh ${pj} x x voice 2>&1 | tee ${log}
if [[ "${PIPESTATUS[0]}" == 1 ]] || [[ "$pipestatus[1]" == 1 ]]; then exit 1; fi;
echo '# pdf2png' 2>&1 | tee -a ${log}
mkdir -p ./work/page_images 2>&1 | tee -a ${log}
docker run --rm -v $PWD/work:/work gkmr/pdf-tools /bin/sh -c "pdftocairo -png -r 200 /work/novel.pdf /work/page_images/novel" 2>&1 | tee -a ${log}
if [[ "${PIPESTATUS[0]}" == 1 ]] || [[ "$pipestatus[1]" == 1 ]]; then exit 1; fi;
echo '# build_timekeeper' 2>&1 | tee -a ${log}
docker run --rm -v $PWD/work:/work lp-python /bin/sh -c "python -u build_timekeeper.py" 2>&1 | tee -a ${log}