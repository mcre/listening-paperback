cid=`git log -n 1 --format=%ad-%h --date=format:'%Y%m%d'`
ntc=`git status | grep 'nothing to commit' -c`

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

cp ./materials/fonts/`cat ./projects/${1}/config.json | jq -r .font` ./work/font.ttf || exit 1
cp ./materials/covers/`cat ./projects/${1}/config.json | jq -r .cover.file` ./work/cover.png || exit 1
cp ./materials/musics/`cat ./projects/${1}/config.json | jq -r .music.file` ./work/music.mp3 || exit 1

echo '# az2tex'
docker run --rm -v $PWD/work:/work lp-python /bin/sh -c "python az2tex.py" || exit 1
echo '# tex2pdf'
docker run --rm -v $PWD/work:/work paperist/alpine-texlive-ja /bin/sh -c "cd /work && uplatex -halt-on-error novel.tex > tex_output.txt" || exit 1
docker run --rm -v $PWD/work:/work paperist/alpine-texlive-ja /bin/sh -c "cd /work && dvipdfmx novel.dvi" || exit 1
docker run --rm -v $PWD/work:/work lp-python /bin/sh -c "python parse_tex_output.py" || exit 1
echo '# pdf2png'
mkdir ./work/page_images
docker run --rm -v $PWD/work:/work gkmr/pdf-tools /bin/sh -c "pdftocairo -png -r 200 /work/novel.pdf /work/page_images/novel" || exit 1
echo '# tex2ssml'
docker run --rm -v $PWD/work:/work lp-python-mecab /bin/sh -c "python tex2ssml.py" || exit 1
echo '# ssml2voice'
docker run --rm -v $PWD/work:/work lp-python /bin/sh -c "python ssml2voice.py ${2} ${3}" || exit 1
cp -r ./work/cache/* ./cache || exit 1
echo '# build_timekeeper'
docker run --rm -v $PWD/work:/work lp-python /bin/sh -c "python build_timekeeper.py" || exit 1
echo '# create_cover_images'
docker run --rm -v $PWD/work:/work lp-python /bin/sh -c "python create_cover_images.py" || exit 1
echo '# build_animation_images'
docker run --rm -v $PWD/work:/work lp-python-pymupdf /bin/sh -c "python build_animation_images.py" || exit 1
echo '# build_page_movies'
docker run --rm -v $PWD/work:/work lp-python-movie /bin/sh -c "python build_page_movies.py" || exit 1
echo '# build_chapter_movies'
docker run --rm -v $PWD/work:/work lp-python-movie /bin/sh -c "python build_chapter_movies.py" || exit 1
echo '# build_part_movies'
docker run --rm -v $PWD/work:/work lp-python-movie /bin/sh -c "python3 build_part_movies.py" || exit 1
echo '# generate_descriptions'
docker run --rm -v $PWD/work:/work lp-python /bin/sh -c "python generate_descriptions.py ${cid}" || exit 1

echo '# postprocessing'
if [ $ntc = 1 ]; then
  cid="${cid}"
else
  cid="${cid}_work"
fi
rm -rf ./projects/${1}/output/${cid} || exit 1

mkdir -p ./projects/${1}/output || exit 1
mkdir ./projects/${1}/output/${cid} || exit 1
cd ./projects/${1}/output/${cid} || exit 1
mkdir input work || exit 1
mkdir work/ssml work/marks work/page_movies || exit 1
cd ../../../../ || exit 1

cd ./work/ || exit 1
cp -r part_movies/* ../projects/${1}/output/${cid}/ || exit 1
cp novel.tex config.json ../projects/${1}/output/${cid}/input || exit 1
cp rubies.json tex_output.txt novel.pdf chapters_and_pages.json timekeeper.json ../projects/${1}/output/${cid}/work || exit 1
cp ssml/* ../projects/${1}/output/${cid}/work/ssml/ || exit 1
cp marks/* ../projects/${1}/output/${cid}/work/marks/ || exit 1
cp page_movies/* ../projects/${1}/output/${cid}/work/page_movies/ || exit 1
cd .. || exit 1

echo '# done !!!'