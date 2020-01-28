echo $1
pj=$1
mkdir -p ./projects/${pj}/tmp
log="./projects/${pj}/tmp/batch_first_timekeeper.log"
./batch.sh ${pj} x x voice 2>&1 | tee ${log}
if [[ "${PIPESTATUS[0]}" == 1 ]] || [[ "$pipestatus[1]" == 1 ]]; then exit 0; fi;
echo '# pdf2png' 2>&1 | tee -a ${log}
hash=`docker run --rm -v $PWD/work:/work lp-python /bin/sh -c "tail -n +2 /work/novel.log | md5sum | cut -d ' ' -f 1"`
if [ -e ./projects/${pj}/cache/page_images/${hash}.zip ]; then
  echo '## exists cache'
  unzip -q ./projects/${pj}/cache/page_images/${hash}.zip
else
  echo '## processing...'
  mkdir -p ./work/page_images
  docker run --rm -v $PWD/work:/work gkmr/pdf-tools /bin/sh -c "pdftocairo -png -r 200 /work/novel.pdf /work/page_images/novel" 2>&1 | tee -a ${log}
  rm -rf ./projects/${pj}/cache/page_images/
  mkdir ./projects/${pj}/cache/page_images/
  zip -r -q "./projects/${pj}/cache/page_images/${hash}.zip" ./work/page_images
fi
if [[ "${PIPESTATUS[0]}" == 1 ]] || [[ "$pipestatus[1]" == 1 ]]; then exit 0; fi;
echo '# build_timekeeper' 2>&1 | tee -a ${log}
docker run --rm -v $PWD/work:/work lp-python /bin/sh -c "python -u build_timekeeper.py" 2>&1 | tee -a ${log}
cp ./work/novel.pdf ./projects/${pj}/tmp/novel.pdf
cp ./work/novel.tex ./projects/${pj}/tmp/novel.tex
cp ./work/chapters.json ./projects/${pj}/tmp/chapters.json
cp ./work/timekeeper.json ./projects/${pj}/tmp/timekeeper.json
