# for auto complete dir file cmd
# liubinxu
#

# set sg complete paths
curpath=$HOME"/sg-users/liubinxu/script/sg_complete"
pecopath=$HOME"/sg-users/liubinxu/soft/peco_linux_amd64"
# $(readlink -f "$(dirname "$0")")
export PATH=$pecopath:$curpath:"${PATH}"
export SG_COM_HOST="10.2.3.76"
export SG_COM_PORT="21590"

# set error file location

export SC_LOG=$curpath"/log.txt"
export SC_ERR=$curpath"/err.txt"



# enable tab completion
_autodir() {
    local cur
    cur=${COMP_WORDS[*]:1}
    comps=$(cmd_client text_search dir num $cur |pec)
    while read i; do
        COMPREPLY=("${COMPREPLY[@]}" "${i}")
    done <<EOF
    $comps
EOF
}
complete -F _autodir d

_autocmd() {
        local cur
        cur=${COMP_WORDS[*]:1}
        comps=$(cmd_client text_search cmds num $cur |pec)
        while read -r i; do
            COMPREPLY=("${COMPREPLY[@]}" "${i}")
        done <<EOF
        $comps
EOF
}
complete -F _autocmd c

_autofile() {
        local cur
        cur=${COMP_WORDS[*]:1}
        comps=$(cmd_client text_search file num $cur| pec)
        while read i; do
            COMPREPLY=("${COMPREPLY[@]}" "${i}")
        done <<EOF
        $comps
EOF
}
complete -F _autofile f


# default autojump command
d() {
    output="${@}"
    if [[ -d "${output}" ]]; then
        echo -e "${output}"
        cd "${output}"
    else
        echo "directory '${@}' not found"
        echo "\n${output}\n"
    fi
}

c() {
    output="${@}"
    `${output}`
}

f() {
    output="${@}"
    echo "cat ${output}"
}

sgc() {
    string="${@}"
    cmd_client text_search cmds num $string |pec
}

sgd() {
    string="${@}"
    cmd_client text_search dir num $string |pec
}

sgf() {
    string="${@}"
    cmd_client text_search file num $string |pec
}

bash_prompt_client() {
    msgs=$(history 1 | { read -r x y; echo $y; })
    # echo $msg
    if [ "$msgs" != "$PRE_CMD" ]; then
        cmd_client auto_cmd $PWD $msgs
        PRE_CMD=$msgs
    fi
}

# auto record

PRE_CMD=""
if [ "$PROMPT_COMMAND" ];
then
    PROMPT_COMMAND=${PROMPT_COMMAND}'; bash_prompt_client'
else
    PROMPT_COMMAND='bash_prompt_client'
fi
