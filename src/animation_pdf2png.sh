for file in ./animation_images/*.pdf; do
  bn="$(basename -- ${file} .pdf)"
  pdftocairo -png -r 200 ${file} ./animation_images/${bn} || exit 1
done
