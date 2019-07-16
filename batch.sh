docker build -t listening-paperback-python ./Dockerfiles/python || exit 1

rm -rf ./work
mkdir ./work
cp ./fonts/* ./work
cp ./az2tex.py ./work
cp ./template.tex ./work
cp ./input/${1}.txt ./work

docker run --rm -it -v $PWD/work:/app listening-paperback-python /bin/sh -c "python az2tex.py ${1}.txt" || exit 1
docker run --rm -it -v $PWD/work:/workdir paperist/alpine-texlive-ja /bin/bash -c "cd /workdir && uplatex ${1}.tex && dvipdfmx ${1}.dvi" || exit 1

#rm ./work/*.aux ./work/*.dvi ./work/*.log ./work/*.ttf ./work/*.otf ./work/*.py ./work/template.tex