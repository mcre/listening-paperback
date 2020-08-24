build_movie() {
  part_id=$1
  echo "### < part_id: ${part_id} >"
  echo '### build_animation_images'
  docker run --rm -v $PWD/work:/work lp-python-pymupdf /bin/sh -c "python -u build_animation_images.py ${part_id}" || exit 1
  echo '### build_page_movies'
  docker run --rm -v $PWD/work:/work lp-python-movie /bin/sh -c "python -u build_page_movies.py ${part_id}" || exit 1
  echo '### build_chapter_movies'
  docker run --rm -v $PWD/work:/work lp-python-movie /bin/sh -c "python -u build_chapter_movies.py ${part_id}" || exit 1
  rm -rf ./work/animation_images
  echo '### build_part_movie'
  docker run --rm -v $PWD/work:/work lp-python-movie /bin/sh -c "python3 -u build_part_movie.py ${part_id}" || exit 1
  rm -rf ./work/chapter_movies
  echo '### generate_upload_settings'
  docker run --rm -v $PWD/work:/work lp-python /bin/sh -c "python -u generate_upload_settings.py ${part_id} ${cid}" || exit 1
  echo '### copy_output_movies'
  strid=`printf "%05d" "${part_id}"` || exit 1
  mkdir -p ./projects/${pj}/output/${dir}/${strid}/ || exit 1
  cp -rp ./work/part_movies/${strid}/* ./projects/${pj}/output/${dir}/${strid}/ || exit 1
  mkdir -p ./projects/${pj}/output/${config_ub}latest/${strid}/ || exit 1
  cp -rp ./work/part_movies/${strid}/* ./projects/${pj}/output/${config_ub}latest/${strid}/ || exit 1
}

stop="blank"
while getopts r:s:c: opt; do
  case ${opt} in
    r) range=${OPTARG};;
    s) stop=${OPTARG};;
    c) config_dot="${OPTARG}."; config_ub="${OPTARG}_";;
    :) echo "引数が指定されていません: -$OPTARG" >&2; exit 1;;
    *) echo "未定義のオプション: -$OPTARG" >&2; exit 1;;
  esac
done
shift `expr "${OPTIND}" - 1`
if [ $# -ge 1 ]; then
  pj=$@
else
  echo "プロジェクトが指定されていません"
  exit 1
fi

if [ "${stop}" != "blank" ]; then
  stop_list=("tex,pdf,ssml,voice,timekeeper,before_movie,voice_check,voice_check_old")
  if ! [[ ",${stop_list[@]}," =~ ",${stop}," ]]; then
    echo "-s に指定できる引数はこちらだけです: ${stop_list}"
    exit 1
  fi
fi

if [ -n "${range}" ]; then
  range_start=`echo ${range} | cut -d ':' -f 1`
  expr "${range_start}" + 1 >&/dev/null
  if [ $? -gt 1 ];then
    echo "-r の引数のフォーマットが不正です。例: 0, 2:10"
    exit 1
  fi

  range_end=`echo ${range} | cut -d ':' -f 2`
  expr "${range_end}" + 1 >&/dev/null
  if [ $? -gt 1 ];then
    echo "-r の引数のフォーマットが不正です。例: 0, 2:10"
    exit 1
  fi
fi

home=`pwd`
cid=`git log -n 1 --format=%ad-%h --date=format:'%Y%m%d'`
ntc=`git status | grep 'nothing to commit' -c`
if [ $ntc = 1 ]; then
  dir="${config_ub}${cid}"
else
  dir="${config_ub}${cid}_work"
fi

if [ -n "${range}" ]; then
  dir="${dir}_${range_start}-${range_end}"
fi

echo '# docker-build'
docker build -t lp-python ./Dockerfiles/python 1>/dev/null || exit 1
docker build -t lp-python-mecab ./Dockerfiles/python_mecab 1>/dev/null || exit 1
docker build -t lp-python-movie ./Dockerfiles/python_movie 1>/dev/null || exit 1
docker build -t lp-python-pymupdf ./Dockerfiles/python_pymupdf 1>/dev/null || exit 1
docker build -t lp-kkc ./Dockerfiles/kkc 1>/dev/null || exit 1

echo '# preprocessing'
rm -rf ./work || exit 1
mkdir ./work || exit 1
mkdir -p ./work/cache || exit 1
mkdir -p ./work/ssml_before || exit 1
cp ./src/* ./work/ || exit 1
cp ./projects/${pj}/novel.txt ./work/ || exit 1
cp ./projects/${pj}/config.${config_dot}json ./work/config.json || exit 1
cp ./projects/${pj}/images/* ./work/
cp ./projects/${pj}/cache/ssml/* ./work/ssml_before

cp -p ./materials/fonts/`cat ./work/config.json | jq -r .font` ./work/font.ttf || exit 1
cp -p ./materials/fonts/ipaexg.ttf ./work/font_gothic.ttf || exit 1
cp -p ./materials/covers/`cat ./work/config.json | jq -r .cover.file` ./work/cover.png || exit 1
cp -p ./materials/musics/`cat ./work/config.json | jq -r .music.file` ./work/music.mp3 || exit 1
cp -p ./materials/libs/* ./work/ || exit 1

echo '# az2tex'
docker run --rm -v $PWD/work:/work lp-python /bin/sh -c "python -u az2tex.py" || exit 1
if [ $stop = 'tex' ]; then exit 0; fi
echo '# tex2pdf'
docker run --rm -v $PWD/work:/work paperist/alpine-texlive-ja /bin/sh -c "cd /work && uplatex -halt-on-error novel.tex > tex_output.txt" || exit 1
docker run --rm -v $PWD/work:/work paperist/alpine-texlive-ja /bin/sh -c "cd /work && uplatex -halt-on-error novel.tex > tex_output.txt" || exit 1 # 2回コンパイルが必要なコマンド用
docker run --rm -v $PWD/work:/work paperist/alpine-texlive-ja /bin/sh -c "cd /work && dvipdfmx novel.dvi" || exit 1
docker run --rm -v $PWD/work:/work lp-python /bin/sh -c "python -u build_chapters.py" || exit 1
if [ $stop = 'pdf' ]; then exit 0; fi
echo '# tex2ssml'
docker run --rm -v $PWD/work:/work lp-python-mecab /bin/sh -c "python -u tex2ssml.py" || exit 1
if [ $stop = 'ssml' ]; then exit 0; fi
echo '# ssml2voice'
mkdir -p ./projects/${pj}/cache || exit 1
cp -rp ./projects/${pj}/cache/* ./work/cache
aws_access_key_id=`cat ./certs/aws_credentials.json | jq -r .aws_access_key_id`
aws_secret_access_key=`cat ./certs/aws_credentials.json | jq -r .aws_secret_access_key`
if [ $stop = 'voice' ]; then
  docker run --rm -it -v $PWD/work:/work lp-python /bin/sh -c "python -u ssml2voice.py ${pj} ${aws_access_key_id} ${aws_secret_access_key}" || exit 1
else
  docker run --rm -v $PWD/work:/work lp-python /bin/sh -c "python -u ssml2voice.py ${pj} ${aws_access_key_id} ${aws_secret_access_key}" || exit 1
fi
cp -rp ./work/cache/* ./projects/${pj}/cache || exit 1
rm -rf ./projects/${pj}/cache/ssml/ || exit 1
mkdir ./projects/${pj}/cache/ssml/ || exit 1
cp -r ./work/ssml/* ./projects/${pj}/cache/ssml/ || exit 1
if [ $stop = 'voice' ]; then exit 0; fi
echo '# pdf2png'
hash=`docker run --rm -v $PWD/work:/work lp-python /bin/sh -c "tail -n +2 /work/novel.log | md5sum | cut -d ' ' -f 1"` || exit 1
if [ -e ./projects/${pj}/cache/page_images/${hash}.zip ]; then
  echo '## exists cache'
  unzip -q ./projects/${pj}/cache/page_images/${hash}.zip
else
  echo '## processing...'
  mkdir -p ./work/page_images || exit 1
  docker run --rm -v $PWD/work:/work gkmr/pdf-tools /bin/sh -c "pdftocairo -png -r 200 /work/novel.pdf /work/page_images/novel" || exit 1
  rm -rf ./projects/${pj}/cache/page_images/ || exit 1
  mkdir ./projects/${pj}/cache/page_images/ || exit 1
  zip -r -q "./projects/${pj}/cache/page_images/${hash}.zip" ./work/page_images || exit 1
fi
echo '# build_timekeeper'
docker run --rm -v $PWD/work:/work lp-python /bin/sh -c "python -u build_timekeeper.py" || exit 1
if [ $stop = 'timekeeper' ]; then exit 0; fi
if [ $stop = 'voice_check' ]; then
  echo '# voice_check'
  mkdir ./work/page_images_mini
  docker run --rm -v $PWD/work:/work gkmr/pdf-tools /bin/sh -c "pdftocairo -png -r 100 /work/novel.pdf /work/page_images_mini/novel" || exit 1
  docker run --rm -v $PWD/work:/work lp-python-movie /bin/sh -c "python -u build_fast_check_movie.py" || exit 1
  exit 0
fi
if [ $stop = 'voice_check_old' ]; then
  echo '# voice_check_old'
  docker run --rm -v $PWD/work:/work lp-python /bin/sh -c "python -u timekeeper2viseme_tex.py" || exit 1
  docker run --rm -v $PWD/work:/work paperist/alpine-texlive-ja /bin/sh -c "cd /work && uplatex -halt-on-error viseme.tex > dummy.txt" || exit 1
  docker run --rm -v $PWD/work:/work paperist/alpine-texlive-ja /bin/sh -c "cd /work && dvipdfmx viseme.dvi" || exit 1
  docker run --rm -v $PWD/work:/work lp-python /bin/sh -c "python -u create_voice_text_images.py" || exit 1
  docker run --rm -v $PWD/work:/work lp-python-movie /bin/sh -c "python -u build_voice_movie.py" || exit 1
  exit 0
fi
echo '# create_cover_images_and_ssml'
docker run --rm -v $PWD/work:/work lp-python /bin/sh -c "python -u create_cover_images_and_ssml.py" || exit 1
echo '# re-ssml2voice' # パート数確定したので再度polly
if [ $stop = 'before_movie' ]; then
  docker run --rm -it -v $PWD/work:/work lp-python /bin/sh -c "python -u ssml2voice.py ${pj} ${aws_access_key_id} ${aws_secret_access_key}" || exit 1
else
  docker run --rm -v $PWD/work:/work lp-python /bin/sh -c "python -u ssml2voice.py ${pj} ${aws_access_key_id} ${aws_secret_access_key}" || exit 1
fi
cp -rp ./work/cache/* ./projects/${pj}/cache || exit 1
if [ $stop = 'before_movie' ]; then exit 0; fi

echo '# prepare_output_directory'
rm -rf ./projects/${pj}/output/${dir} || exit 1
mkdir -p ./projects/${pj}/output || exit 1
mkdir ./projects/${pj}/output/${dir} || exit 1
mkdir -p ./projects/${pj}/output/${config_ub}latest || exit 1
cd ./projects/${pj}/output/${dir} || exit 1
mkdir input work || exit 1
mkdir work/ssml work/marks || exit 1
cd ${home} || exit 1
cd ./work/ || exit 1
cp novel.txt config.json ../projects/${pj}/output/${dir}/input || exit 1
cp novel.tex rubies.json tex_output.txt novel.pdf chapters.json timekeeper.json ../projects/${pj}/output/${dir}/work || exit 1
cp ssml/* ../projects/${pj}/output/${dir}/work/ssml/ || exit 1
cp marks/* ../projects/${pj}/output/${dir}/work/marks/ || exit 1
cd ${home} || exit 1

echo '# build_movie'
if [ -n "${range}" ]; then
  echo "## part_id: ${range_start} から ${range_end} を build"
  for part_id in `seq ${range_start} ${range_end}`
  do
    build_movie ${part_id}
  done
else
  echo '## すべてのパートを build'
  for part_id in `cat ./work/timekeeper.json | jq .parts[].part_id`
  do
    build_movie ${part_id}
  done
fi

echo '# done !!!'