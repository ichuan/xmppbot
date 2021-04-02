
if [ "${!#}" != "--yes" ]; then
  echo "Please confirm with --yes"
  exit -1
fi
