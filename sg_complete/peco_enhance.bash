BIOCLUSTER_DIR=$HOME/wpm2/sanger_bioinfo

cdf() {
    tag=$1
    dir=`find ./ -type d -iname "*$tag*" | pec`
    cd $dir
}

lessf() {
    tag=$1
    dir=`find ./ -type f -iname "*$tag*" | pec`
    less $dir
}

find_biocluster_less(){
    tag=$1
    file=`find $BIOCLUSTER_DIR -type f -print | grep -i "$tag" | pec`
    less $file
}

find_biocluster_cd(){
    tag=$1
    dir=`find $BIOCLUSTER_DIR -type d -print | grep -i "$tag" | pec`
    cd $dir
}

sg_log_f(){
 regrex=$1
 rg  $regrex  --no-heading  --line-number |fzf --preview='line={}; array=(${line//:/ }); file=${array[0]}; linenum=${array[1]}; awk -v l="$linenum" 
"NR>l-5&&NR<l+20" $file' --preview-window up
}
