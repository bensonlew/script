pipline_id=$1
out_dir=$2
basic_model="/home/liubinxu/work/ref_report_model/admin/dist"
python ../download_from_sql.py $pipline_id
python ../html2json.py sg_report_category_${pipline_id}.json  sg_report_image_${pipline_id}.json sg_report_result_table_${pipline_id}.json
cp -r $basic_model $out_dir
cp *.js $out_dir/static/
cp *.png $out_dir/static/
cp *.jpg $out_dir/static/
