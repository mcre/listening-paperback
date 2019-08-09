for file in ./animations/*.pdf; do
  bn="$(basename -- ${file} .pdf)"
  pdftocairo -png -r 200 ${file} ./animations/${bn} || exit 1
done
