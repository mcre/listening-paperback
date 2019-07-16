rm -rf ./work
mkdir work
cp ./fonts/* work
cp ./${1}.tex work # あとでtxtにする

docker run --rm -it -v $PWD/work:/workdir paperist/alpine-texlive-ja /bin/bash -c "cd /workdir && uplatex ${1}.tex && dvipdfmx ${1}.dvi"
rm ./work/*.aux ./work/*.dvi ./work/*.log ./work/*.ttf ./work/*.otf