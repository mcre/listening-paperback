echo '# docker-build'
docker build -t listening-paperback-python ./Dockerfiles/python || exit 1

echo '# preprocessing'
rm -rf ./work
mkdir ./work
cp ./fonts/* ./work
cp ./*.py ./work
cp ./template.tex ./work
cp ./projects/${1}/novel.txt ./work

echo '# az2tex'
docker run --rm -it -v $PWD/work:/work listening-paperback-python /bin/sh -c "python az2tex.py" || exit 1
echo '# tex2pdf'
docker run --rm -it -v $PWD/work:/work paperist/alpine-texlive-ja /bin/bash -c "cd /work && uplatex novel.tex && dvipdfmx novel.dvi" || exit 1
echo '# pdf2png'
mkdir ./work/pages
docker run --rm -it -v $PWD/work:/work gkmr/pdf-tools /bin/sh -c "pdftocairo -png -r 200 /work/novel.pdf /work/pages/output" || exit 1
echo '# tex2ssml'
docker run --rm -it -v $PWD/work:/work listening-paperback-python /bin/sh -c "python tex2ssml.py" || exit 1
echo '# ssml2voice'
docker run --rm -it -v $PWD/work:/work listening-paperback-python /bin/sh -c "python ssml2voice.py ${2} ${3}" || exit 1

echo '# postprocessing'
cid=`git log -n 1 --format=%ad-%h --date=format:'%Y%m%d'`
rm -rf ./projects/${1}/output_${cid}

mkdir ./projects/${1}/output_${cid}
cd ./projects/${1}/output_${cid}
mkdir ssml voices marks
cd ../../../

cp ./work/novel.tex ./projects/${1}/output_${cid}/
cp ./work/novel.pdf ./projects/${1}/output_${cid}/
cp ./work/pages/* ./projects/${1}/output_${cid}/pages/
cp ./work/ssml/* ./projects/${1}/output_${cid}/ssml/
cp ./work/voices/* ./projects/${1}/output_${cid}/voices/
cp ./work/marks/* ./projects/${1}/output_${cid}/marks/
