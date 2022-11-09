comps="a
b b
c c
s
d
"
aa=()
while read i; do
    echo $i
    aa=("${aa[@]}" "${i}")
done <<EOF
$comps
EOF

echo ${aa[@]}
