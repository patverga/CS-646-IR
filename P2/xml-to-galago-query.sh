cat $1 |grep '\<num\|<title' | sed 's/<num>\(.*\)<\/num>/{\n\"number\" : \"\1\",/g' | sed 's/<title>\(.*\)<\/title>/\"text\" : \"#sdm\(\1\)\"\n},/g' 
