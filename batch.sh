echo '# docker-build'
docker build -t lp-python ./Dockerfiles/python || exit 1
docker build -t lp-python-movie ./Dockerfiles/python_movie || exit 1

echo '# preprocessing'
rm -rf ./work || exit 1
mkdir ./work || exit 1
cp ./src/* ./work/ || exit 1
cp ./projects/${1}/novel.txt ./work/ || exit 1
cp ./projects/${1}/config.json ./work/ || exit 1

cp ./materials/fonts/`cat ./projects/${1}/config.json | jq -r .font` ./work/font.ttf || exit 1
cp ./materials/musics/`cat ./projects/${1}/config.json | jq -r .music` ./work/music.mp3 || exit 1

echo '# az2tex'
docker run --rm -it -v $PWD/work:/work lp-python /bin/sh -c "python az2tex.py" || exit 1
echo '# tex2pdf'
docker run --rm -it -v $PWD/work:/work paperist/alpine-texlive-ja /bin/bash -c "cd /work && uplatex novel.tex > tex_output.txt" || exit 1
docker run --rm -it -v $PWD/work:/work paperist/alpine-texlive-ja /bin/bash -c "cd /work && dvipdfmx novel.dvi" || exit 1
docker run --rm -it -v $PWD/work:/work lp-python /bin/sh -c "python parse_tex_output.py" || exit 1
echo '# pdf2png'
mkdir ./work/pages
docker run --rm -it -v $PWD/work:/work gkmr/pdf-tools /bin/sh -c "pdftocairo -png -r 200 /work/novel.pdf /work/pages/novel" || exit 1
echo '# tex2ssml'
docker run --rm -it -v $PWD/work:/work lp-python /bin/sh -c "python tex2ssml.py" || exit 1
echo '# ssml2voice'
mkdir ./work/voices ./work/marks & cp ./tmp/voices/* ./work/voices/ & cp ./tmp/marks/* ./work/marks/ || exit 1 # debug
# docker run --rm -it -v $PWD/work:/work lp-python /bin/sh -c "python ssml2voice.py ${2} ${3}" || exit 1
echo '# buildmovie'
docker run --rm -it -v $PWD/work:/work lp-python-movie /bin/sh -c "python3 buildmovie.py" || exit 1

echo '# postprocessing'
cid=`git log -n 1 --format=%ad-%h --date=format:'%Y%m%d'`
ntc=`git status | grep 'nothing to commit' -c`
if [ $ntc = 1 ]; then
  cid="${cid}"
else
  cid="${cid}_work"
fi
rm -rf ./projects/${1}/output_${cid} || exit 1

mkdir ./projects/${1}/output_${cid} || exit 1
cd ./projects/${1}/output_${cid}
mkdir ssml pages voices marks || exit 1
cd ../../../

cp ./work/config.json ./projects/${1}/output_${cid}/ || exit 1
cp ./work/novel.tex ./projects/${1}/output_${cid}/ || exit 1
cp ./work/pages.json ./projects/${1}/output_${cid}/ || exit 1
cp ./work/novel.pdf ./projects/${1}/output_${cid}/ || exit 1
cp ./work/novel.mp4 ./projects/${1}/output_${cid}/ || exit 1

cp ./work/pages/* ./projects/${1}/output_${cid}/pages/ || exit 1
cp ./work/ssml/* ./projects/${1}/output_${cid}/ssml/ || exit 1
cp ./work/voices/* ./projects/${1}/output_${cid}/voices/ || exit 1
cp ./work/marks/* ./projects/${1}/output_${cid}/marks/ || exit 1
