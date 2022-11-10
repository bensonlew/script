# Monocle3 Script
# Second Module of Monocle3 Pipeline
# Calc pseudotime after indicating the root node 
# Partition/Sample Visualization 
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
# source("/mnt/ilustre/users/haowen.zhou/dev_files/R-m3-test/m3_custom_func.R")
source("~/sg-users/liubinxu/script/R-m3-test/m3_custom_func.R")


#get parameters
options(bitmapType='cairo')
command = matrix(c(
    'help' ,                'h',  0,  'loical',
    'cds',                  'C',  1,  'character',
    'out',                  'o',  1,  'character',
    'root_node',            'n',  1,  'character',
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
           --cds,                  -c   character  cds path
           --out,                  -o   character  out dir
           --root_node,            -n   character  root node(s), separated by comma only','
           

        \n")
        q(status=1);
}

#Test opt
#opt <- list(cds = "D:/proj/Wuyue/monocle3.rds",out = "D:/proj/Wuyue/", root_node = "10,21")
if(is.null(opt$test_inout))opt$test_inout = F

if(as.logical(opt$test_inout) == T){
  cds <- readRDS("/mnt/ilustre/users/haowen.zhou/proj/t/Fanweijuan_MJ20211111006/result_2/monocle3_psdtime.rds")
  graph_test_res <- read.csv("/mnt/ilustre/users/haowen.zhou/proj/t/Fanweijuan_MJ20211111006/result_2/m3_result/graph_test_res.csv")
}else{
  if (!dir.exists(opt$out)){ dir.create(opt$out)} 

  cds <- readRDS(normalizePath(opt$cds))

  root_node_vec <- str_split(opt$root_node,pattern = ",") %>% unlist() %>% paste0("Y_",.)

  cds <- order_cells(cds, root_pr_nodes = root_node_vec)

  graph_test_res <- my_graph_test(cds, neighbor_graph="principal_graph", cores=4)

  graph_test_res <- graph_test_res %>% as.data.frame() %>% arrange(desc(morans_I), q_value)

  write.csv(graph_test_res,paste0(opt$out,"/graph_test_res.csv"), row.names=FALSE)

  gene_list <- graph_test_res$gene_short_name[1:10]

#Export cds and Figure
  opt$out <- normalizePath(opt$out)
  saveRDS(cds,paste0(opt$out,"/monocle3_psdtime.rds"))
  #write.csv(graph_test_res, paste0(opt$out,"Monocle3_graph_test_res.csv"), row.names = F)
}


p <- plot_cells(cds,
           genes=gene_list,
           label_cell_groups=FALSE, cell_size = 0.7, alpha = 0.8,
           show_trajectory_graph=FALSE)
save_img(p,paste0(opt$out,"/umap_sig_genes"),pdf_w = 12, pdf_h = 9, png_w = 800, png_h = 600)

cds_subset <- cds[rowData(cds)$gene_short_name %in% gene_list,]

p <- plot_cells(cds,
           color_cells_by = "pseudotime",
           label_cell_groups=FALSE,
           label_leaves=FALSE,
           label_branch_points=FALSE, cell_size = 0.7, alpha = 0.8,
           graph_label_size=1.5)
save_img(p,paste0(opt$out,"/umap_pseudotime"),pdf_w = 12, pdf_h = 9, png_w = 800, png_h = 600)

if(!is.null(cds@colData@listData$seurat_clusters)){
  qual_col_pals = brewer.pal.info[brewer.pal.info$category == 'qual',]
  col_vector = unlist(mapply(brewer.pal, qual_col_pals$maxcolors, rownames(qual_col_pals)))
  mycolors <- sample(col_vector, cds@colData$seurat_clusters %>% as.factor %>% levels  %>% length)
  p <- plot_genes_in_pseudotime(cds_subset,color_cells_by = "seurat_clusters",min_expr = 0.5) + scale_color_manual(values = mycolors)
  save_img(p,paste0(opt$out,"/seurat_clusters_jitter"))
}


if(!is.null(cds@colData@listData$sample)){
  p <- plot_genes_in_pseudotime(cds_subset,color_cells_by = "sample",min_expr = 0.5)
  save_img(p,paste0(opt$out,"/sample_jitter"))
  plot_list <- list()
  for(i in levels(as.factor(cds@colData@listData$sample))){
    plot_list[[i]] <- plot_cells(cds[,cds@colData@listData$sample == i],
              color_cells_by = "pseudotime",
              label_cell_groups=FALSE,
              label_leaves=FALSE,
              label_branch_points=FALSE, cell_size = 0.7, alpha = 0.8,
              graph_label_size=1.5) + labs(title = paste0("Sample: ",i))
  }
  n_col = min(4,length(levels(as.factor(cds@colData@listData$sample))))
  n_row = ceiling(length(levels(as.factor(cds@colData@listData$sample)))/4)
  p <- ggarrange(plotlist = plot_list, ncol = n_col, nrow = n_row)
  save_img(p,paste0(opt$out,"/umap_sample_sep_pseudotime"),pdf_w = n_col * 6, pdf_h = n_row * 4.5, png_w = n_col * 400, png_h = n_row * 300)
}

if(!is.null(cds@colData@listData$group)){
  p <- plot_genes_in_pseudotime(cds_subset,color_cells_by = "group",min_expr = 0.5)
  save_img(p,paste0(opt$out,"/group_jitter"))
  plot_list <- list()
  for(i in levels(as.factor(cds@colData@listData$group))){
    plot_list[[i]] <- plot_cells(cds[,cds@colData@listData$group == i],
              color_cells_by = "pseudotime",
              label_cell_groups=FALSE,
              label_leaves=FALSE,
              label_branch_points=FALSE, cell_size = 0.7, alpha = 0.8,
              graph_label_size=1.5) + labs(title = paste0("Group: ",i))
  }
  n_col = min(4,length(levels(as.factor(cds@colData@listData$group))))
  n_row = ceiling(length(levels(as.factor(cds@colData@listData$group)))/4)
  p <- ggarrange(plotlist = plot_list, ncol = n_col, nrow = n_row)
  save_img(p,paste0(opt$out,"/umap_group_sep_pseudotime"),pdf_w = n_col * 6, pdf_h = n_row * 4.5, png_w = n_col * 400, png_h = n_row * 300)
}

if(!is.null(cds@colData@listData$cell.names)){
  p <- plot_genes_in_pseudotime(cds_subset,color_cells_by = "cell.names",min_expr = 0.5)
  save_img(p,paste0(opt$out,"/cell.names_jitter"))
}

message("Monocle Done!")










