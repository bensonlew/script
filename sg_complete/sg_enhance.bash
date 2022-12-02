
# for auto complete enhance sanger work
# liubinxu
#

# set sg complete paths
curpath=$HOME"/sg-users/liubinxu/script/sg_complete"
pecopath=$HOME"/sg-users/liubinxu/soft/peco_linux_amd64"
runwork=$HOME"/wpm2/bin/run_work "
tool_ele=$HOME"/sg-users/liubinxu/script/tool_ele.py "
tool_env=$HOME"/sg-users/liubinxu/script/tool_env.py "
tool_ele_edit=$HOME"/sg-users/liubinxu/script/sg_pickle_edit.sh "
BIOCLUSTER_DIR=$HOME/wpm2/sanger_bioinfo

# enable tab completion
_auto_sgcd() {
    local cur
    cur=${COMP_WORDS[*]:1}
    regex=".*"$cur".*"
    comps=$(find ./ -type d -regex $regex -print| peco)
    while read i; do
        COMPREPLY=("${COMPREPLY[@]}" "${i}")
    done <<EOF
    $comps
EOF
}
complete -F _auto_sgcd sgcd


_auto_sgcdw() {
    # local cur
    # cur=${COMP_WORDS[*]:1}
    # regex=".*"$cur".*"
    date_str=`date +"20%y%m%d"`
    comps=$(ls -d /mnt/lustre/sanger-dev_workspace*/${date_str}/* | peco)
    while read i; do
        COMPREPLY=("${COMPREPLY[@]}" "${i}")
    done <<EOF
    $comps
EOF
}
complete -F _auto_sgcdw sgcdw

_auto_sgcdwt() {
    local cur
    cur=${COMP_WORDS[*]:1}
    # regex=".*"$cur".*"

    comps=$(ls -d /mnt/lustre/sanger-dev_workspace*/*/*$cur* | peco)
    while read i; do
        COMPREPLY=("${COMPREPLY[@]}" "${i}")
    done <<EOF
    $comps
EOF
}
complete -F _auto_sgcdwt sgcdwt


# 获取工作流目录
_get_wd() {
    dir=$1
    # echo $dir
    if [[ -f $dir"/data.json" ]]; then
        echo $dir
    else
        nowwd=`_get_wd $(dirname $dir)`
        echo $nowwd
    fi
}


_run_work(){
    task=$1
    wd=$2
    echo -e $runwork" -t "$task" -m show"
    echo -e $runwork" -t "$task" -m show |grep -v finish"
    echo -e $runwork" -t "$task" -m stop"
    echo -e $runwork" -j data.json"
    echo -e $runwork" -j "$wd"/data.json"
}

# enable tab completion
_auto_sgrw() {
    local cur
    cur=${COMP_WORDS[*]:1}
    wd=`_get_wd $PWD`
    # echo $wd
    task=`basename $wd | sed 's/[^_]*_//'`

    # strs=""
    # strs=$strs`echo -e $runwork" -t "$task" -m show\n"`
    # strs=$strs`echo -e $runwork" -t "$task" -m show |grep -v finished\n"`
    # strs=$strs`echo -e $runwork" -t "$task" -m stop\n"`
    # strs=$strs`echo -e $runwork" -j data.json\n"`
    # strs=$strs`echo -e $runwork" -j "$wd"/data.json\n"`
    comps=$(_run_work $task $wd | peco)
    # comps=""
    # echo $comps[@]
    while read i; do
        COMPREPLY=("${COMPREPLY[@]}" "${i}")
    done <<EOF
    $comps
EOF
}
complete -F _auto_sgrw sgrw

# default autojump command
sgcd() {
    output="${@}"
    if [[ -d "${output}" ]]; then
        echo -e "${output}"
        cd "${output}"
    else
        echo "directory '${@}' not found"
        echo "\n${output}\n"
    fi
}

sgcdw(){
    output="${@}"
    if [[ -d "${output}" ]]; then
        echo -e "${output}"
        cd "${output}"
    else
        echo "directory '${@}' not found"
        echo "\n${output}\n"
    fi
}

sgcdwt(){
    output="${@}"
    if [[ -d "${output}" ]]; then
        echo -e "${output}"
        cd "${output}"
    else
        echo "directory '${@}' not found"
        echo "\n${output}\n"
    fi
}

sgrw() {
    cmds="${@}"
    echo ${cmds}
    eval $cmds
}


#展示tool的参数
_auto_sgtool_ele() {
    local cur
    cur=${COMP_WORDS[*]:1}
    regex="*.pk"
    comps=$(find ./ -type f -name "*.pk" -print |grep -v "class.pk"| peco)
    while read i; do
        COMPREPLY=("${COMPREPLY[@]}" "${i}")
    done <<EOF
    $comps
EOF
}

_auto_sgtool_ele2() {
    local cur
    cur=${COMP_WORDS[*]:1}
    regex="*.pk"
    comps=$(find ./ -type f -name "*.pk" -print |grep "class.pk"| peco)
    while read i; do
        COMPREPLY=("${COMPREPLY[@]}" "${i}")
    done <<EOF
    $comps
EOF
}

complete -F _auto_sgtool_ele sgtool_ele
complete -F _auto_sgtool_ele sgtool_env
complete -F _auto_sgtool_ele sgtool_edit
complete -F _auto_sgtool_ele2 sgtool_path

sgtool_ele() {
    tool_pk=$1
    python $tool_ele $tool_pk 
}

sgtool_edit() {
    tool_pk=$1
    bash $tool_ele_edit $tool_pk
}

sgtool_ele() {
    tool_pk=$1
    python $tool_ele $tool_pk 
}

sgtool_env() {
    tool_pk=$1
    class_pk=`echo "Psudotime.pk" |sed 's/\.pk/_class\.pk/g'`
    python $tool_env $class_pk $tool_pk 
}

sgtool_path() {
    tool_class_pk=$1
    cat $tool_class_pk |grep "mbio.tools" |sed 's/\./\//g'
}

sgcode_less(){
    tag=$1
    regex=".*"tag".*"
    file=`find $BIOCLUSTER_DIR -type f -print -regex $regex | pec`
    less $file
}

sglog_f(){
    regrex=$1
    rg  $regrex --smart-case -g 'log.txt' -g '*.out' -g '*.err' -g '*.o' -g '*.log' --no-heading  --line-number |fzf --preview='line={}; array=(${line//:/ }); file=${array[0]}; linenum=${array[1]}; awk -v l="$linenum" "NR>l-5&&NR<l+20" $file' --preview-window up
}


open_code(){
    line="${@}"
    file=$(echo $line| sed 's/.*File "//;s/".*//')
    linenum=$(echo $line| sed 's/.*line //;s/,.*//')
    awk -v l="$linenum" "NR>l-5&&NR<l+20" $file
}
export -f open_code

sglog_code(){
    regrex="File.*line"
    rg  $regrex --smart-case -g 'log.txt' -g '*.out' -g '*.err' -g '*.o' -g '*.log' --no-heading  --line-number |fzf --preview='line={}; open_code $line' --preview-window up
}
