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
docker run --rm -it -v $PWD/work:/app listening-paperback-python /bin/sh -c "python az2tex.py" || exit 1
echo '# tex2pdf'
docker run --rm -it -v $PWD/work:/workdir paperist/alpine-texlive-ja /bin/bash -c "cd /workdir && uplatex novel.tex && dvipdfmx novel.dvi" || exit 1
echo '# tex2ssml'
docker run --rm -it -v $PWD/work:/app listening-paperback-python /bin/sh -c "python tex2ssml.py" || exit 1
echo '# ssml2voice'
#docker run --rm -it -v $PWD/work:/app listening-paperback-python /bin/sh -c "python ssml2voice.py" || exit 1

echo '# postprocessing'
#rm ./work/*.aux ./work/*.dvi ./work/*.log ./work/*.ttf ./work/*.otf ./work/*.py ./work/template.tex
cid=`git log -n 1 --format=%h`
rm -rf ./projects/${1}/output_${cid}
mkdir ./projects/${1}/output_${cid} ./projects/${1}/output_${cid}/ssml
cp ./work/novel.tex ./projects/${1}/output_${cid}/
cp ./work/novel.pdf ./projects/${1}/output_${cid}/
cp ./work/ssml/* ./projects/${1}/output_${cid}/ssml/