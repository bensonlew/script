tab_select() {
    tab=$1
    lines=`head -1 $tab | sed 's/\t/\n/g'  |awk '{print NR"\t"$0}' |pec |cut -f 1 | awk '{ if(NR>1){printf ","$1}else{printf $1}}'`
    cut -f $lines $tab | less
}
