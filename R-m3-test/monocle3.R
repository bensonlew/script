# Monocle3 Script
# First Module of Monocle3 Pipeline
# To get principal graph from the embedding 
# Using external embedding from Seurat
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

# script_path <- "~/wpm2/sanger_bioinfo/src/mbio/packages/scrna"
# source(paste0(script_path,"/basic/m3_custom_func.R"))

source("~/sg-users/liubinxu/script/R-m3-test/m3_custom_func.R")
#get parameters
options(bitmapType='cairo')
command = matrix(c(
    'help' ,                'h',  0,  'loical',
    'rds',                  'r',  1,  'character',
    'out',                  'o',  1,  'character',
    'keep_umap',            'ku', 1,  'character',
    'umap_min_dist',        'ud', 2,  'double',
    'npcs',                 'n',  2,  'integer',
    'min_branch_len',       'ml', 2,  'integer',
    'euclidean_dist_ratio', 'er', 2,  'double',
    'geodesic_dist_ratio',  'gr', 2,  'double',
    'ncenter',              'nc', 2,  'integer',
    'eps',                  'e',  2,  'double'

  ),byrow=TRUE,ncol =4);
opt = getopt(command);
print_usage <- function(command=NULL){
        cat(getopt(command, usage=TRUE));
        cat("Usage example: \n")
        cat("
Usage example: 
Options:
        
           --help ,                 -h   loical     get help
           --rds,                   -r   character  rds path
           --out,                   -o   character  out dir

           # UMAP Control
           --umap_min_dist,         -ud  double     optional when not using original umap, default 1 
           --npcs                   -n   integer    optional, indicate # of pcs used for monocle3 preprocessing, default 50

           # Use External UMAP
           --keep_umap,             -ku  character  T for keep seurat generated umap, F for letting monocle3 re-gen

           # Monocle3 Graph Control
           --min_branch_len,        -ml  integer    parameter for learn_graph, optional, default 15
           --euclidean_dist_ratio,  -er  double     parameter for learn_graph, optional, default 0.5
           --geodesic_dist_ratio,   -gr  double     parameter for learn_graph, optional, default 0.7
           --ncenter,               -nc  double     the node# for the principal graph, leave blank to let the program determine
           --eps,                   -e   double     optional, do not change unless you know how it works

        \n")
        q(status=1);
}


#test opt
#opt <- list(rds = "D:/proj/Wuyue/03.Seurat.rds",
#            keep_umap = "F",out = "D:/proj/Wuyue/", ncenter = 40, eps = 0, umap_min_dist = 1.5, min_branch_len = 5)

if(is.null(opt$rds)|is.null(opt$out)|is.null(opt$keep_umap)|!is.null(opt$help))print_usage(command)

if(is.null(opt$min_branch_len))opt$min_branch_len = 15
if(is.null(opt$euclidean_dist_ratio))opt$euclidean_dist_ratio = 0.5
if(is.null(opt$geodesic_dist_ratio))opt$geodesic_dist_ratio = 0.7
if(is.null(opt$umap_min_dist))opt$umap_min_dist = 1
if(is.null(opt$npcs))opt$npcs = 50

if (!dir.exists(opt$out)){ dir.create(opt$out)} 

seurat_obj <- readRDS(normalizePath(opt$rds))

#Create cds
cds <- new_cell_data_set(seurat_obj@assays$RNA@counts,
                         cell_metadata = data.frame(row.names = colnames(seurat_obj),seurat_obj@meta.data),
                         gene_metadata = data.frame(row.names = row.names(seurat_obj), gene_short_name = row.names(seurat_obj)))


cds <-  preprocess_cds(cds, num_dim = opt$npcs)

if(as.logical(opt$keep_umap)){
        cds@int_colData@listData$reducedDims@listData$UMAP <- seurat_obj@reductions$umap@cell.embeddings
}else {
        cds <- reduce_dimension(cds,reduction_method = "UMAP",
                                umap.min_dist = opt$umap_min_dist)
}
message("Preprocess Complete")

graph_ctrl <- list(euclidean_distance_ratio = opt$euclidean_dist_ratio,
                   geodesic_distance_ratio = opt$geodesic_dist_ratio, 
                   minimal_branch_len = opt$min_branch_len)

if(!is.null(opt$ncenter)) graph_ctrl[["ncenter"]] <- opt$ncenter
if(!is.null(opt$eps)) graph_ctrl[["eps"]] <- opt$eps

cds <- cluster_cells(cds)
cds <- learn_graph(cds,close_loop = F,
                        learn_graph_control = graph_ctrl)
message("Learn Graph Complete")
#Export cds and Figure
opt$out <- normalizePath(opt$out)
saveRDS(cds,paste0(opt$out,"/monocle3.rds"))

save_img <- function(p,file_path,pdf_w = 12, pdf_h = 9, png_w = 800, png_h = 600){
        pdf(file = paste0(file_path,".pdf"), width = pdf_w, height = pdf_h, useDingbats = F)
        print(p)
        dev.off()
        png(file = paste0(file_path,".png"), width = png_w, height = png_h)
        print(p)
        dev.off()
}

if(!is.null(cds@colData@listData$seurat_clusters)){
  qual_col_pals = brewer.pal.info[brewer.pal.info$category == 'qual',]
  col_vector = unlist(mapply(brewer.pal, qual_col_pals$maxcolors, rownames(qual_col_pals)))
  mycolors <- sample(col_vector, cds@colData$seurat_clusters %>% as.factor %>% levels  %>% length)
        p <- my_plot_cells(cds, color_cells_by = "seurat_clusters",label_cell_groups=FALSE,
                       label_leaves=TRUE,label_branch_points=TRUE,graph_label_size=5, cell_size = 0.7, alpha = 0.8
        ) + scale_color_manual(values = mycolors)
        save_img(p,paste0(opt$out,"/umap_seurat_clusters"))
}


if(!is.null(cds@colData@listData$sample)){
        p <- my_plot_cells(cds, color_cells_by = "sample",label_cell_groups=FALSE, 
                       label_leaves=TRUE,label_branch_points=TRUE,graph_label_size=5, cell_size = 0.7, alpha = 0.8
        )
        save_img(p,paste0(opt$out,"/umap_sample"))
}

if(!is.null(cds@colData@listData$cell.names)){
          p <- my_plot_cells(cds, color_cells_by = "cell.names",label_cell_groups=FALSE, 
                       label_leaves=TRUE,label_branch_points=TRUE,graph_label_size=5, cell_size = 0.7, alpha = 0.8
        )
        save_img(p,paste0(opt$out,"/umap_cell.names"))
}

p <- my_plot_cells(cds, color_cells_by = "partition",label_cell_groups=FALSE, 
  label_leaves=TRUE,label_branch_points=TRUE,graph_label_size=5, cell_size = 0.7, alpha = 0.8)
save_img(p,paste0(opt$out,"/umap_partition"))

message("Done!")



