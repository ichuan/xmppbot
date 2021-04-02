ls `dirname $0` | tr '[:space:]' '\n' | sed 's/.sh$//g' | grep -v '^_'
