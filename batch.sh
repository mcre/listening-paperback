echo '# docker-build'
docker build -t lp-python ./Dockerfiles/python || exit 1
docker build -t lp-python-mecab ./Dockerfiles/python_mecab || exit 1
docker build -t lp-python-movie ./Dockerfiles/python_movie || exit 1
docker build -t lp-python-pymupdf ./Dockerfiles/python_pymupdf || exit 1

echo '# preprocessing'
rm -rf ./work || exit 1
mkdir ./work || exit 1
mkdir -p ./work/cache || exit 1
mkdir -p ./cache || exit 1
cp ./src/* ./work/ || exit 1
cp ./projects/${1}/novel.txt ./work/ || exit 1
cp ./projects/${1}/config.json ./work/ || exit 1
cp -r ./cache/* ./work/cache

cp ./materials/covers/`cat ./projects/${1}/config.json | jq -r .cover` ./work/cover.png || exit 1
cp ./materials/fonts/`cat ./projects/${1}/config.json | jq -r .font` ./work/font.ttf || exit 1
cp ./materials/musics/`cat ./projects/${1}/config.json | jq -r .music` ./work/music.mp3 || exit 1

echo '# az2tex'
docker run --rm -it -v $PWD/work:/work lp-python /bin/sh -c "python az2tex.py" || exit 1
echo '# tex2pdf'
docker run --rm -it -v $PWD/work:/work paperist/alpine-texlive-ja /bin/bash -c "cd /work && uplatex -halt-on-error novel.tex > tex_output.txt" || exit 1
docker run --rm -it -v $PWD/work:/work paperist/alpine-texlive-ja /bin/bash -c "cd /work && dvipdfmx novel.dvi" || exit 1
docker run --rm -it -v $PWD/work:/work lp-python /bin/sh -c "python parse_tex_output.py" || exit 1
echo '# pdf2png'
mkdir ./work/page_images
docker run --rm -it -v $PWD/work:/work gkmr/pdf-tools /bin/sh -c "pdftocairo -png -r 200 /work/novel.pdf /work/page_images/novel" || exit 1
echo '# tex2ssml'
docker run --rm -it -v $PWD/work:/work lp-python-mecab /bin/sh -c "python tex2ssml.py" || exit 1
echo '# ssml2voice'
docker run --rm -it -v $PWD/work:/work lp-python /bin/sh -c "python ssml2voice.py ${2} ${3}" || exit 1
cp -r ./work/cache/* ./cache || exit 1
echo '# build_timekeeper'
docker run --rm -it -v $PWD/work:/work lp-python /bin/sh -c "python build_timekeeper.py" || exit 1
echo '# create_cover_images'
docker run --rm -it -v $PWD/work:/work lp-python /bin/sh -c "python create_cover_images.py" || exit 1
echo '# build_animation_images'
docker run --rm -it -v $PWD/work:/work lp-python-pymupdf /bin/sh -c "python build_animation_images.py" || exit 1
echo '# build_page_movies'
docker run --rm -it -v $PWD/work:/work lp-python-movie /bin/sh -c "python build_page_movies.py" || exit 1
echo '# build_chapter_movies'
docker run --rm -it -v $PWD/work:/work lp-python-movie /bin/sh -c "python build_chapter_movies.py" || exit 1
echo '# build_part_movies'
docker run --rm -it -v $PWD/work:/work lp-python-movie /bin/sh -c "python3 build_part_movies.py" || exit 1

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
mkdir ssml page_images chapter_movies voices marks || exit 1
cd ../../../

cp ./work/config.json ./projects/${1}/output_${cid}/ || exit 1
cp ./work/novel.tex ./projects/${1}/output_${cid}/ || exit 1
cp ./work/timekeeper.json ./projects/${1}/output_${cid}/ || exit 1
cp ./work/rubies.json ./projects/${1}/output_${cid}/ || exit 1
cp ./work/novel.pdf ./projects/${1}/output_${cid}/ || exit 1

cp ./work/page_images/* ./projects/${1}/output_${cid}/page_images/ || exit 1
cp ./work/chapter_movies/* ./projects/${1}/output_${cid}/chapter_movies/ || exit 1
cp ./work/ssml/* ./projects/${1}/output_${cid}/ssml/ || exit 1
cp ./work/voices/* ./projects/${1}/output_${cid}/voices/ || exit 1
cp ./work/marks/* ./projects/${1}/output_${cid}/marks/ || exit 1

echo '# done !!!'