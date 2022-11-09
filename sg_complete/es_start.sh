nohup elasticsearch-7.12.0/bin/elasticsearch > elasticsearch.log 2> elasticsearch.err &
sleep 30
nohup kibana-7.2.0-linux-x86_64/bin/kibana > kibana.log 2> kibana.er &
export PYTHONIOENCODING=utf-8
/mnt/lustre/users/sanger-dev/sg-users/liubinxu/work/spacemacs/miniconda2/bin/python cmd_listener.py
