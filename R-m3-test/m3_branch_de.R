# Monocle3 Script
# Second Module of Monocle3 Pipeline
# DE analysis of differnent branch
# By haowen.zhou@majorbio.com        ______    ________
#_______ _______________________________  /______|__  /
#__  __ `__ \  __ \_  __ \  __ \  ___/_  /_  _ \__/_ < 
#_  / / / / / /_/ /  / / / /_/ / /__ _  / /  __/___/ / 
#/_/ /_/ /_/\____//_/ /_/\____/\___/ /_/  \___//____/ 


suppressMessages(require(readr))
suppressMessages(require(monocle3))
suppressMessages(library(tidyverse))
suppressMessages(library(getopt))
suppressMessages(library(Seurat))
suppressMessages(library(RColorBrewer))
suppressMessages(library(ggpubr))
source("/mnt/ilustre/users/haowen.zhou/dev_files/R-m3-test/m3_custom_func.R")



#get parameters
options(bitmapType='cairo')
command = matrix(c(
    'help' ,                'h',  0,  'loical',
    'cds',                  'c',  1,  'character',
    'out',                  'o',  1,  'character',
    'start_node',           's',  1,  'character',
    'end_node',             'e',  1,  'character',
    'title',                'i',  2,  'character',
    'core',                 'n',  2,  'integer',
    'top_gene',             'g',  2,  'integer',
    'test_inout',           't',  0,  'character'

  ),byrow=TRUE,ncol =4);
opt = getopt(command);
print_usage <- function(command=NULL){
        cat(getopt(command, usage=TRUE));
        cat("Usage example: \n")
        cat("
Usage example: 
Options:
        
           --help ,                -h   loical     get help
           --cds,                  -c   character  cds path, must be a cds has learnt pseudo-time
           --out,                  -o   character  out dir
           --start_node,           -s   character  start node(s), separated by comma only','
           --end_node,             -e   character  end node(s), separated by comma only','
           --title,                -i   character  figure title
           --core,                 -n   integer    #cores used, default 8
           --top_gene,             -g   integer    #top genes showed, default 10
        \n")
        q(status=1);
}

#Test opt
#opt <- list(cds = "D:/proj/Wuyue/monocle3.rds",out = "D:/proj/Wuyue/", root_node = "10,21")
if(is.null(opt$test_inout))opt$test_inout = F
if(is.null(opt$title))opt$title = "subset"
if(is.null(opt$core))opt$core = 8 else opt$core <- as.numeric(opt$core)
if(is.null(opt$top_gene))opt$top_gene = 10 else opt$top_gene <- as.numeric(opt$top_gene)



if(as.logical(opt$test_inout) == T){
  cds <- readRDS("/mnt/ilustre/users/haowen.zhou/proj/t/Fanweijuan_MJ20211111006/result_2/monocle3_psdtime.rds")
  graph_test_res <- read.csv("/mnt/ilustre/users/haowen.zhou/proj/t/Fanweijuan_MJ20211111006/result_2/m3_result/graph_test_res.csv")
}else{
  if (!dir.exists(opt$out)){ dir.create(opt$out)} 

  cds <- readRDS(normalizePath(opt$cds))

  start_node_vec <- str_split(opt$start_node,pattern = ",") %>% unlist() %>% paste0("Y_",.)
  end_node_vec <- str_split(opt$end_node,pattern = ",") %>% unlist() %>% paste0("Y_",.)

  cds_sub <- choose_graph_segments(cds, starting_pr_node = start_node_vec, ending_pr_nodes = end_node_vec)
  cds_sub <- cds[,row.names(colData(cds_sub))]

  graph_test_res <- my_graph_test(cds_sub, neighbor_graph="principal_graph", cores=opt$core)

  graph_test_res <- graph_test_res %>% as.data.frame() %>% arrange(desc(morans_I), q_value)

  gene_list <- graph_test_res$gene_short_name[seq_len(opt$top_gene)]

#Export cds and Figure
  opt$out <- normalizePath(opt$out)
  #saveRDS(cds,paste0(opt$out,"/",opt$title,"_monocle3_psdtime.rds"))
  write.csv(graph_test_res,paste0(opt$out,"/",opt$title,"_graph_test_res.csv"), row.names=FALSE)
}

cds_subset <- cds[rowData(cds)$gene_short_name %in% gene_list,]

p <- plot_cells(cds_subset,
           genes=gene_list,
           label_cell_groups=FALSE,
           show_trajectory_graph=FALSE)
save_img(p,paste0(opt$out,"/",opt$title,"_umap_gene_expr"),pdf_w = 12, pdf_h = 9, png_w = 800, png_h = 600)


