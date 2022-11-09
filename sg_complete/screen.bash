# for auto complete dir file cmd
# liubinxu
#

# set sg complete paths
screen_log_path=$HOME"/sg-users/liubinxu/.local/screen_log/"

# set error file location



# default autojump command
scs() {
    name="${@}"
    datestr=`date -d today +"%Y%m%d_%H%M%S"`
    namestr=$name"_"$datestr
    screen -L -Logfile $screen_log_path$namestr -S $namestr
    source $HOME/sg-users/liubinxu/.bash_profile
}


_get_sc_list(){
    sc_list=$(screen -ls |sed '$d' |sed '1d')
    while read i; do  
	file=`echo $i | sed 's/ .*//;s/[0-9]*\.//g'`
	# echo "**"$file
	log_file=$screen_log_path$file
	# echo $log_file
	if [[ -f "${log_file}" ]]; then
	    # echo $log_file
	    path=`tail -1 $log_file |sed 's/.*://;s/\$.*//g'`
	    echo -e $i"\t"$path; 
	else
	    echo -e $i"\t "
        fi
    done <<EOF
$sc_list
EOF
}

_scer() {
    string="${@}"
    comps=$(_get_sc_list |pec)
    while read i j; do
        COMPREPLY=("${COMPREPLY[@]}" "${i}")
    done <<EOF
        $comps
EOF
}

scer() {
    name="${@}"
    screen -R $name
}
complete -F _scer scer


# screen -ls | grep '(Detached)' | awk 'sys {screen -S $1 -X quit}'
