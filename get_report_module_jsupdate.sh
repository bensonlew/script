
out_dir=$1
basic_model="/home/liubinxu/work/ref_report_model/admin/dist"
# python ../download_from_sql.py $pipline_id
# python ../html2json.py sg_report_category_${pipline_id}.json  sg_report_image_${pipline_id}.json sg_report_result_table_${pipline_id}.json
cp -r $basic_model/static/js $out_dir/static/
cp $basic_model/index.html $out_dir/
