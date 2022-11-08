save_img <- function(p,file_path,pdf_w = 9, pdf_h = 18, png_w = 1200, png_h = 2400){
  pdf(file = paste0(file_path,".pdf"), width = pdf_w, height = pdf_h, useDingbats = F)
  print(p)
  dev.off()
  png(file = paste0(file_path,".png"), width = png_w, height = png_h)
  print(p)
  dev.off()
}

my_graph_test <- function(cds,
                       neighbor_graph = c("knn", "principal_graph"),
                       reduction_method = "UMAP",
                       k = 25,
                       method = c('Moran_I'),
                       alternative = 'greater',
                       expression_family="quasipoisson",
                       cores=1,
                       verbose=FALSE) {
  neighbor_graph <- match.arg(neighbor_graph)
  lw <- my_calculateLW(cds,
                    k = k,
                    verbose = verbose,
                    neighbor_graph = neighbor_graph,
                    reduction_method = reduction_method)

  if(verbose) {
    message("Performing Moran's I test: ...")
  }
  exprs_mat <- SingleCellExperiment::counts(cds)[, attr(lw, "region.id"), drop=FALSE]
  sz <- size_factors(cds)[attr(lw, "region.id")]

  wc <- spdep::spweights.constants(lw, zero.policy = TRUE, adjust.n = TRUE)
  test_res <- pbmcapply::pbmclapply(row.names(exprs_mat),
                                    FUN = function(x, sz, alternative,
                                                   method, expression_family) {
    exprs_val <- exprs_mat[x, ]

    if (expression_family %in% c("uninormal", "binomialff")){
      exprs_val <- exprs_val
    }else{
      exprs_val <- log10(exprs_val / sz + 0.1)
    }

    test_res <- tryCatch({
      if(method == "Moran_I") {
        mt <- suppressWarnings(my.moran.test(exprs_val, lw, wc, alternative = alternative))
        data.frame(status = 'OK', p_value = mt$p.value,
                   morans_test_statistic = mt$statistic,
                   morans_I = mt$estimate[["Moran I statistic"]])
      } else if(method == 'Geary_C') {
        gt <- suppressWarnings(my.geary.test(exprs_val, lw, wc, alternative = alternative))
        data.frame(status = 'OK', p_value = gt$p.value,
                   geary_test_statistic = gt$statistic,
                   geary_C = gt$estimate[["Geary C statistic"]])
      }
    },
    error = function(e) {
      data.frame(status = 'FAIL', p_value = NA, morans_test_statistic = NA,
                 morans_I = NA)
    })
  }, sz = sz, alternative = alternative, method = method,
  expression_family = expression_family, mc.cores=cores,
  ignore.interactive = TRUE)

  if(verbose) {
    message("returning results: ...")
  }

  test_res <- do.call(rbind.data.frame, test_res)
  row.names(test_res) <- row.names(cds)
  test_res <- merge(test_res, rowData(cds), by="row.names")
  #remove the first column and set the row names to the first column
  row.names(test_res) <- test_res[, 1]
  test_res[, 1] <- NULL
  test_res$q_value <- 1
  test_res$q_value[which(test_res$status == 'OK')] <-
    stats::p.adjust(subset(test_res, status == 'OK')[, 'p_value'], method="BH")
  test_res$status = as.character(test_res$status)
  # make sure gene name ordering in the DEG test result is the same as the CDS
  test_res[row.names(cds), ]
}

my.moran.test <- function (x, listw, wc, alternative = "greater",
                           randomisation = TRUE) {
  zero.policy = TRUE
  adjust.n = TRUE
  na.action = stats::na.fail
  drop.EI2 = FALSE
  xname <- deparse(substitute(x))
  wname <- deparse(substitute(listw))
  NAOK <- deparse(substitute(na.action)) == "na.pass"
  x <- na.action(x)
  na.act <- attr(x, "na.action")
  if (!is.null(na.act)) {
    subset <- !(1:length(listw$neighbours) %in% na.act)
    listw <- subset(listw, subset, zero.policy = zero.policy)
  }
  n <- length(listw$neighbours)
  if (n != length(x))
    stop("objects of different length")

  S02 <- wc$S0 * wc$S0
  res <- spdep::moran(x, listw, wc$n, wc$S0, zero.policy = zero.policy,
                      NAOK = NAOK)
  I <- res$I
  K <- res$K

  EI <- (-1)/wc$n1
  if (randomisation) {
    VI <- wc$n * (wc$S1 * (wc$nn - 3 * wc$n + 3) - wc$n *
                    wc$S2 + 3 * S02)
    tmp <- K * (wc$S1 * (wc$nn - wc$n) - 2 * wc$n * wc$S2 +
                  6 * S02)
    if (tmp > VI)
      warning(paste0("Kurtosis overflow,\ndistribution of variable does ",
                     "not meet test assumptions"))
    VI <- (VI - tmp)/(wc$n1 * wc$n2 * wc$n3 * S02)
    if (!drop.EI2)
      VI <- (VI - EI^2)
    if (VI < 0)
      warning(paste0("Negative variance,\ndistribution of variable does ",
                     "not meet test assumptions"))
  }
  else {
    VI <- (wc$nn * wc$S1 - wc$n * wc$S2 + 3 * S02)/(S02 *
                                                      (wc$nn - 1))
    if (!drop.EI2)
      VI <- (VI - EI^2)
    if (VI < 0)
      warning(paste0("Negative variance,\ndistribution of variable does ",
                     "not meet test assumptions"))
  }
  ZI <- (I - EI)/sqrt(VI)
  statistic <- ZI
  names(statistic) <- "Moran I statistic standard deviate"
  if (alternative == "two.sided")
    PrI <- 2 * stats::pnorm(abs(ZI), lower.tail = FALSE)
  else if (alternative == "greater")
    PrI <- stats::pnorm(ZI, lower.tail = FALSE)
  else PrI <- stats::pnorm(ZI)
  if (!is.finite(PrI) || PrI < 0 || PrI > 1)
    warning("Out-of-range p-value: reconsider test arguments")
  vec <- c(I, EI, VI)
  names(vec) <- c("Moran I statistic", "Expectation", "Variance")
  method <- paste("Moran I test under", ifelse(randomisation,
                                               "randomisation", "normality"))

  res <- list(statistic = statistic, p.value = PrI, estimate = vec)
  if (!is.null(na.act))
    attr(res, "na.action") <- na.act
  class(res) <- "htest"
  res
}

my.geary.test <- function (x, listw, wc, randomisation = TRUE,
                           alternative = "greater")
{
  zero.policy = TRUE
  adjust.n = TRUE
  spChk = NULL
  alternative <- match.arg(alternative, c("less", "greater",
                                          "two.sided"))
  if (!inherits(listw, "listw"))
    stop(paste(deparse(substitute(listw)), "is not a listw object"))
  if (!is.numeric(x))
    stop(paste(deparse(substitute(x)), "is not a numeric vector"))
  if (any(is.na(x)))
    stop("NA in X")
  n <- length(listw$neighbours)
  if (n != length(x))
    stop("objects of different length")
  if (is.null(spChk))
    spChk <- spdep::get.spChkOption()
  if (spChk && !spdep::chkIDs(x, listw))
    stop("Check of data and weights ID integrity failed")
  S02 <- wc$S0 * wc$S0
  res <- spdep::geary(x, listw, wc$n, wc$n1, wc$S0, zero.policy)
  C <- res$C
  if (is.na(C))
    stop("NAs generated in geary - check zero.policy")
  K <- res$K
  EC <- 1
  if (randomisation) {
    VC <- (wc$n1 * wc$S1 * (wc$nn - 3 * n + 3 - K * wc$n1))
    VC <- VC - ((1/4) * (wc$n1 * wc$S2 * (wc$nn + 3 * n -
                                            6 - K * (wc$nn - n + 2))))
    VC <- VC + (S02 * (wc$nn - 3 - K * (wc$n1^2)))
    VC <- VC/(n * wc$n2 * wc$n3 * S02)
  }
  else {
    VC <- ((2 * wc$S1 + wc$S2) * wc$n1 - 4 * S02)/(2 * (n +
                                                          1) * S02)
  }
  ZC <- (EC - C)/sqrt(VC)
  statistic <- ZC
  names(statistic) <- "Geary C statistic standard deviate"
  PrC <- NA
  if (is.finite(ZC)) {
    if (alternative == "two.sided")
      PrC <- 2 * stats::pnorm(abs(ZC), lower.tail = FALSE)
    else if (alternative == "greater")
      PrC <- stats::pnorm(ZC, lower.tail = FALSE)
    else PrC <- stats::pnorm(ZC)
    if (!is.finite(PrC) || PrC < 0 || PrC > 1)
      warning("Out-of-range p-value: reconsider test arguments")
  }
  vec <- c(C, EC, VC)
  names(vec) <- c("Geary C statistic", "Expectation", "Variance")
  method <- paste("Geary C test under", ifelse(randomisation,
                                               "randomisation", "normality"))
  data.name <- paste(deparse(substitute(x)), "\nweights:",
                     deparse(substitute(listw)), "\n")
  res <- list(statistic = statistic, p.value = PrC, estimate = vec,
              alternative = ifelse(alternative == "two.sided", alternative,
                                   paste("Expectation", alternative,
                                         "than statistic")),
              method = method, data.name = data.name)
  class(res) <- "htest"
  res
}




my_calculateLW <- function(cds,
                        k,
                        neighbor_graph,
                        reduction_method,
                        verbose = FALSE
) {
  if(verbose) {
    message("retrieve the matrices for Moran's I test...")
  }
  knn_res <- NULL
  principal_g <- NULL

  cell_coords <- reducedDims(cds)[[reduction_method]]
  if (neighbor_graph == "knn") {
    knn_res <- RANN::nn2(cell_coords, cell_coords,
                         min(k + 1, nrow(cell_coords)),
                         searchtype = "standard")[[1]]
  } else if(neighbor_graph == "principal_graph") {
    pr_graph_node_coords <- cds@principal_graph_aux[[reduction_method]]$dp_mst
    principal_g <-
      igraph::get.adjacency(
        cds@principal_graph[[reduction_method]])[colnames(pr_graph_node_coords),
                                                 colnames(pr_graph_node_coords)]
  }

  exprs_mat <- exprs(cds)
  if(neighbor_graph == "knn") {
    if(is.null(knn_res)) {
      knn_res <- RANN::nn2(cell_coords, cell_coords,
                           min(k + 1, nrow(cell_coords)),
                           searchtype = "standard")[[1]]
    }
    links <- monocle3:::jaccard_coeff(knn_res[, -1], F)
    links <- links[links[, 1] > 0, ]
    relations <- as.data.frame(links)
    colnames(relations) <- c("from", "to", "weight")
    knn_res_graph <- igraph::graph.data.frame(relations, directed = T)

      knn_list <- lapply(1:nrow(knn_res), function(x) knn_res[x, -1])
      region_id_names <- colnames(cds)

      id_map <- 1:ncol(cds)
      names(id_map) <- id_map

      points_selected <- 1:nrow(knn_res)

    knn_list <- lapply(points_selected,
                       function(x) id_map[as.character(knn_res[x, -1])])
  }
  else if (neighbor_graph == "principal_graph") {
    # mapping from each cell to the principal points
    cell2pp_map <-
      cds@principal_graph_aux[[
        reduction_method]]$pr_graph_cell_proj_closest_vertex
    if(is.null(cell2pp_map)) {
      stop(paste("Error: projection matrix for each cell to principal",
                 "points doesn't exist, you may need to rerun learn_graph"))
    }

    # This cds object might be a subset of the one on which ordering was
    # performed, so we may need to subset the nearest vertex and low-dim
    # coordinate matrices:
    cell2pp_map <-  cell2pp_map[row.names(cell2pp_map) %in%
                                  row.names(colData(cds)),, drop=FALSE]
    cell2pp_map <- cell2pp_map[colnames(cds), ]

    if(verbose) {
      message("Identify connecting principal point pairs ...")
    }
    # an alternative approach to make the kNN graph based on the principal
    # graph
    knn_res <- RANN::nn2(cell_coords, cell_coords,
                         min(k + 1, nrow(cell_coords)),
                         searchtype = "standard")[[1]]
    # convert the matrix of knn graph from the cell IDs into a matrix of
    # principal points IDs
    # kNN_res_pp_map <- matrix(cell2pp_map[knn_res], ncol = k + 1, byrow = F)

    # kNN can be built within group of cells corresponding to each principal
    # points
    principal_g_tmp <- principal_g
    diag(principal_g_tmp) <- 1 # so set diagnol as 1
    cell_membership <- as.factor(cell2pp_map)
    uniq_member <- sort(unique(cell_membership))

    membership_matrix <- Matrix::sparse.model.matrix( ~ cell_membership + 0)
    colnames(membership_matrix) <- levels(uniq_member)
    # sparse matrix multiplication for calculating the feasible space
    feasible_space <- membership_matrix %*%
      Matrix::tcrossprod(principal_g_tmp[as.numeric(levels(uniq_member)),
                                         as.numeric(levels(uniq_member))],
                         membership_matrix)

    links <- monocle3:::jaccard_coeff(knn_res[, -1], F)
    links <- links[links[, 1] > 0, ]
    relations <- as.data.frame(links)
    colnames(relations) <- c("from", "to", "weight")
    knn_res_graph <- igraph::graph.data.frame(relations, directed = T)

    # remove edges across cells belong to two disconnected principal points
    tmp_a <- igraph::get.adjacency(knn_res_graph)
    block_size <- 10000
    num_blocks = ceiling(nrow(tmp_a) / block_size)
    if(verbose) {
      message('start calculating valid kNN graph ...')
    }

    tmp <- NULL

    for (j in 1:num_blocks){
      if (j < num_blocks){
        block_a <- tmp_a[((((j-1) * block_size)+1):(j*block_size)), ]
        block_b <- feasible_space[((((j-1) * block_size)+1):(j*block_size)), ]
      }else{
        block_a <- tmp_a[((((j-1) * block_size)+1):(nrow(tmp_a))), ]
        block_b <- feasible_space[((((j-1) * block_size)+1):(nrow(tmp_a))), ]
      }

      cur_tmp <- block_a * block_b

      if(is.null(tmp)) {
        tmp <- cur_tmp
      } else {
        tmp <- rbind(tmp, cur_tmp)
      }
    }

    #close(pb_feasible_knn)
    if(verbose) {
      message('Calculating valid kNN graph, done ...')
    }

      region_id_names <- colnames(cds)

      id_map <- 1:ncol(cds)
      names(id_map) <- id_map

    knn_list <-
      slam::rowapply_simple_triplet_matrix(slam::as.simple_triplet_matrix(tmp),
                                           function(x) {
                                             res <- which(as.numeric(x) > 0)
                                             if(length(res) == 0)
                                               res <- 0L
                                             res
                                           })
  } else {
    stop("Error: unrecognized neighbor_graph option")
  }
  # create the lw list for moran.test
  names(knn_list) <- id_map[names(knn_list)]
  class(knn_list) <- "nb"
  attr(knn_list, "region.id") <- region_id_names
  attr(knn_list, "call") <- match.call()
  # attr(knn_list, "type") <- "queen"
  lw <- spdep::nb2listw(knn_list, zero.policy = TRUE)
  lw
}

# Plot Func

# Define New plot_cell function
branch_nodes <- function(cds,reduction_method="UMAP"){
  g = principal_graph(cds)[[reduction_method]]
  branch_points <- which(igraph::degree(g) > 2)
  branch_points = branch_points[branch_points %in% root_nodes(cds, reduction_method) == FALSE]
  return(branch_points)
}

leaf_nodes <- function(cds,reduction_method="UMAP"){
  g = principal_graph(cds)[[reduction_method]]
  leaves <- which(igraph::degree(g) == 1)
  leaves = leaves[leaves %in% root_nodes(cds, reduction_method) == FALSE]
  return(leaves)
}

root_nodes <- function(cds, reduction_method="UMAP"){
  g = principal_graph(cds)[[reduction_method]]
  root_pr_nodes <- which(names(igraph::V(g)) %in%
                           cds@principal_graph_aux[[reduction_method]]$root_pr_nodes)
  names(root_pr_nodes) <-
    cds@principal_graph_aux[[reduction_method]]$root_pr_nodes
  return(root_pr_nodes)
}

monocle_theme_opts <- function()
{
  theme(strip.background = element_rect(colour = 'white', fill = 'white')) +
    theme(panel.border = element_blank()) +
    theme(axis.line.x = element_line(size=0.25, color="black")) +
    theme(axis.line.y = element_line(size=0.25, color="black")) +
    theme(panel.grid.minor.x = element_blank(), panel.grid.minor.y = element_blank()) +
    theme(panel.grid.major.x = element_blank(), panel.grid.major.y = element_blank()) + 
    theme(panel.background = element_rect(fill='white')) +
    theme(legend.key=element_blank())
}

my_plot_cells <- function (cds, x = 1, y = 2, reduction_method = c("UMAP", 
                                                  "tSNE", "PCA", "LSI", "Aligned"), 
          color_cells_by = "cluster", group_cells_by = c("cluster", 
                                                         "partition"), genes = NULL, show_trajectory_graph = TRUE, 
          trajectory_graph_color = "grey28", trajectory_graph_segment_size = 0.75, 
          norm_method = c("log", "size_only"), label_cell_groups = TRUE, 
          label_groups_by_cluster = TRUE, group_label_size = 2, labels_per_group = 1, 
          label_branch_points = TRUE, label_roots = TRUE, label_leaves = TRUE, 
          graph_label_size = 2, cell_size = 0.35, cell_stroke = I(cell_size/2), 
          alpha = 1, min_expr = 0.1, rasterize = FALSE, scale_to_range = FALSE, 
          label_principal_points = FALSE) 
{
  reduction_method <- match.arg(reduction_method)
  assertthat::assert_that(methods::is(cds, "cell_data_set"))
  assertthat::assert_that(!is.null(reducedDims(cds)[[reduction_method]]), 
                          msg = paste("No dimensionality reduction for", 
                                      reduction_method, "calculated.", "Please run reduce_dimension with", 
                                      "reduction_method =", reduction_method, "before attempting to plot."))
  low_dim_coords <- reducedDims(cds)[[reduction_method]]
  assertthat::assert_that(ncol(low_dim_coords) >= max(x, y), 
                          msg = paste("x and/or y is too large. x and y must", 
                                      "be dimensions in reduced dimension", "space."))
  if (!is.null(color_cells_by)) {
    assertthat::assert_that(color_cells_by %in% c("cluster", 
                                                  "partition", "pseudotime") | color_cells_by %in% 
                              names(colData(cds)), msg = paste("color_cells_by must one of", 
                                                               "'cluster', 'partition', 'pseudotime,", "or a column in the colData table."))
    if (color_cells_by == "pseudotime") {
      tryCatch({
        pseudotime(cds, reduction_method = reduction_method)
      }, error = function(x) {
        stop(paste("No pseudotime for", reduction_method, 
                   "calculated. Please run order_cells with", 
                   "reduction_method =", reduction_method, 
                   "before attempting to color by pseudotime."))
      })
    }
  }
  assertthat::assert_that(!is.null(color_cells_by) || !is.null(markers), 
                          msg = paste("Either color_cells_by or markers must", 
                                      "be NULL, cannot color by both!"))
  norm_method = match.arg(norm_method)
  group_cells_by = match.arg(group_cells_by)
  assertthat::assert_that(!is.null(color_cells_by) || !is.null(genes), 
                          msg = paste("Either color_cells_by or genes must be", 
                                      "NULL, cannot color by both!"))
  if (show_trajectory_graph && is.null(principal_graph(cds)[[reduction_method]])) {
    message("No trajectory to plot. Has learn_graph() been called yet?")
    show_trajectory_graph = FALSE
  }
  if (label_principal_points && is.null(principal_graph(cds)[[reduction_method]])) {
    message("Cannot label principal points when no trajectory to plot. Has learn_graph() been called yet?")
    label_principal_points = FALSE
  }
  if (label_principal_points) {
    label_branch_points <- FALSE
    label_leaves <- FALSE
    label_roots <- FALSE
  }
  gene_short_name <- NA
  sample_name <- NA
  data_dim_1 <- NA
  data_dim_2 <- NA
  if (rasterize) {
    plotting_func <- ggrastr::geom_point_rast
  }
  else {
    plotting_func <- ggplot2::geom_point
  }
  S_matrix <- reducedDims(cds)[[reduction_method]]
  data_df <- data.frame(S_matrix[, c(x, y)])
  colnames(data_df) <- c("data_dim_1", "data_dim_2")
  data_df$sample_name <- row.names(data_df)
  data_df <- as.data.frame(cbind(data_df, colData(cds)))
  if (group_cells_by == "cluster") {
    data_df$cell_group <- tryCatch({
      clusters(cds, reduction_method = reduction_method)[data_df$sample_name]
    }, error = function(e) {
      NULL
    })
  }
  else if (group_cells_by == "partition") {
    data_df$cell_group <- tryCatch({
      partitions(cds, reduction_method = reduction_method)[data_df$sample_name]
    }, error = function(e) {
      NULL
    })
  }
  else {
    stop("Error: unrecognized way of grouping cells.")
  }
  if (color_cells_by == "cluster") {
    data_df$cell_color <- tryCatch({
      clusters(cds, reduction_method = reduction_method)[data_df$sample_name]
    }, error = function(e) {
      NULL
    })
  }
  else if (color_cells_by == "partition") {
    data_df$cell_color <- tryCatch({
      partitions(cds, reduction_method = reduction_method)[data_df$sample_name]
    }, error = function(e) {
      NULL
    })
  }
  else if (color_cells_by == "pseudotime") {
    data_df$cell_color <- tryCatch({
      pseudotime(cds, reduction_method = reduction_method)[data_df$sample_name]
    }, error = function(e) {
      NULL
    })
  }
  else {
    data_df$cell_color <- colData(cds)[data_df$sample_name, 
                                       color_cells_by]
  }
  if (show_trajectory_graph) {
    ica_space_df <- t(cds@principal_graph_aux[[reduction_method]]$dp_mst) %>% 
      as.data.frame() %>% dplyr::select_(prin_graph_dim_1 = x, 
                                         prin_graph_dim_2 = y) %>% dplyr::mutate(sample_name = rownames(.), 
                                                                                 sample_state = rownames(.))
    dp_mst <- cds@principal_graph[[reduction_method]]
    edge_df <- dp_mst %>% igraph::as_data_frame() %>% dplyr::select_(source = "from", 
                                                                     target = "to") %>% dplyr::left_join(ica_space_df %>% 
                                                                                                           dplyr::select_(source = "sample_name", source_prin_graph_dim_1 = "prin_graph_dim_1", 
                                                                                                                          source_prin_graph_dim_2 = "prin_graph_dim_2"), 
                                                                                                         by = "source") %>% dplyr::left_join(ica_space_df %>% 
                                                                                                                                               dplyr::select_(target = "sample_name", target_prin_graph_dim_1 = "prin_graph_dim_1", 
                                                                                                                                                              target_prin_graph_dim_2 = "prin_graph_dim_2"), 
                                                                                                                                             by = "target")
  }
  markers_exprs <- NULL
  expression_legend_label <- NULL
  if (!is.null(genes)) {
    if (!is.null(dim(genes)) && dim(genes) >= 2) {
      markers = unlist(genes[, 1], use.names = FALSE)
    }
    else {
      markers = genes
    }
    markers_rowData <- rowData(cds)[(rowData(cds)$gene_short_name %in% 
                                       markers) | (row.names(rowData(cds)) %in% markers), 
                                    , drop = FALSE]
    markers_rowData <- as.data.frame(markers_rowData)
    if (nrow(markers_rowData) == 0) {
      stop("None of the provided genes were found in the cds")
    }
    if (nrow(markers_rowData) >= 1) {
      cds_exprs <- SingleCellExperiment::counts(cds)[row.names(markers_rowData), 
                                                     , drop = FALSE]
      cds_exprs <- Matrix::t(Matrix::t(cds_exprs)/size_factors(cds))
      if (!is.null(dim(genes)) && dim(genes) >= 2) {
        genes = as.data.frame(genes)
        row.names(genes) = genes[, 1]
        genes = genes[row.names(cds_exprs), ]
        agg_mat = as.matrix(aggregate_gene_expression(cds, 
                                                      genes, norm_method = norm_method, scale_agg_values = FALSE))
        markers_exprs = agg_mat
        markers_exprs <- reshape2::melt(markers_exprs)
        colnames(markers_exprs)[1:2] <- c("feature_id", 
                                          "cell_id")
        if (is.factor(genes[, 2])) 
          markers_exprs$feature_id = factor(markers_exprs$feature_id, 
                                            levels = levels(genes[, 2]))
        markers_exprs$feature_label <- markers_exprs$feature_id
        norm_method = "size_only"
        expression_legend_label = "Expression score"
      }
      else {
        cds_exprs@x = round(10000 * cds_exprs@x)/10000
        markers_exprs = matrix(cds_exprs, nrow = nrow(markers_rowData))
        colnames(markers_exprs) = colnames(SingleCellExperiment::counts(cds))
        row.names(markers_exprs) = row.names(markers_rowData)
        markers_exprs <- reshape2::melt(markers_exprs)
        colnames(markers_exprs)[1:2] <- c("feature_id", 
                                          "cell_id")
        markers_exprs <- merge(markers_exprs, markers_rowData, 
                               by.x = "feature_id", by.y = "row.names")
        if (is.null(markers_exprs$gene_short_name)) {
          markers_exprs$feature_label <- as.character(markers_exprs$feature_id)
        }
        else {
          markers_exprs$feature_label <- as.character(markers_exprs$gene_short_name)
        }
        markers_exprs$feature_label <- ifelse(is.na(markers_exprs$feature_label) | 
                                                !as.character(markers_exprs$feature_label) %in% 
                                                markers, as.character(markers_exprs$feature_id), 
                                              as.character(markers_exprs$feature_label))
        markers_exprs$feature_label <- factor(markers_exprs$feature_label, 
                                              levels = markers)
        if (norm_method == "size_only") 
          expression_legend_label = "Expression"
        else expression_legend_label = "log10(Expression)"
      }
      if (scale_to_range) {
        markers_exprs = dplyr::group_by(markers_exprs, 
                                        feature_label) %>% dplyr::mutate(max_val_for_feature = max(value), 
                                                                         min_val_for_feature = min(value)) %>% dplyr::mutate(value = 100 * 
                                                                                                                               (value - min_val_for_feature)/(max_val_for_feature - 
                                                                                                                                                                min_val_for_feature))
        expression_legend_label = "% Max"
      }
    }
  }
  if (label_cell_groups && is.null(color_cells_by) == FALSE) {
    if (is.null(data_df$cell_color)) {
      if (is.null(genes)) {
        message(paste(color_cells_by, "not found in colData(cds), cells will", 
                      "not be colored"))
      }
      text_df = NULL
      label_cell_groups = FALSE
    }
    else {
      if (is.character(data_df$cell_color) || is.factor(data_df$cell_color)) {
        if (label_groups_by_cluster && is.null(data_df$cell_group) == 
            FALSE) {
          text_df = data_df %>% dplyr::group_by(cell_group) %>% 
            dplyr::mutate(cells_in_cluster = dplyr::n()) %>% 
            dplyr::group_by(cell_color, .add = TRUE) %>% 
            dplyr::mutate(per = dplyr::n()/cells_in_cluster)
          median_coord_df = text_df %>% dplyr::summarize(fraction_of_group = dplyr::n(), 
                                                         text_x = stats::median(x = data_dim_1), text_y = stats::median(x = data_dim_2))
          text_df = suppressMessages(text_df %>% dplyr::select(per) %>% 
                                       dplyr::distinct())
          text_df = suppressMessages(dplyr::inner_join(text_df, 
                                                       median_coord_df))
          text_df = text_df %>% dplyr::group_by(cell_group) %>% 
            dplyr::top_n(labels_per_group, per)
        }
        else {
          text_df = data_df %>% dplyr::group_by(cell_color) %>% 
            dplyr::mutate(per = 1)
          median_coord_df = text_df %>% dplyr::summarize(fraction_of_group = dplyr::n(), 
                                                         text_x = stats::median(x = data_dim_1), text_y = stats::median(x = data_dim_2))
          text_df = suppressMessages(text_df %>% dplyr::select(per) %>% 
                                       dplyr::distinct())
          text_df = suppressMessages(dplyr::inner_join(text_df, 
                                                       median_coord_df))
          text_df = text_df %>% dplyr::group_by(cell_color) %>% 
            dplyr::top_n(labels_per_group, per)
        }
        text_df$label = as.character(text_df %>% dplyr::pull(cell_color))
      }
      else {
        message(paste("Cells aren't colored in a way that allows them to", 
                      "be grouped."))
        text_df = NULL
        label_cell_groups = FALSE
      }
    }
  }
  if (!is.null(markers_exprs) && nrow(markers_exprs) > 0) {
    data_df <- merge(data_df, markers_exprs, by.x = "sample_name", 
                     by.y = "cell_id")
    data_df$value <- with(data_df, ifelse(value >= min_expr, 
                                          value, NA))
    ya_sub <- data_df[!is.na(data_df$value), ]
    na_sub <- data_df[is.na(data_df$value), ]
    if (norm_method == "size_only") {
      g <- ggplot(data = data_df, aes(x = data_dim_1, y = data_dim_2)) + 
        plotting_func(aes(data_dim_1, data_dim_2), size = I(cell_size), 
                      stroke = I(cell_stroke), color = "grey80", 
                      alpha = alpha, data = na_sub) + plotting_func(aes(color = value), 
                                                                    size = I(cell_size), stroke = I(cell_stroke), 
                                                                    data = ya_sub[order(ya_sub$value), ]) + viridis::scale_color_viridis(option = "viridis", 
                                                                                                                                         name = expression_legend_label, na.value = NA, 
                                                                                                                                         end = 0.8, alpha = alpha) + guides(alpha = FALSE) + 
        facet_wrap(~feature_label)
    }
    else {
      g <- ggplot(data = data_df, aes(x = data_dim_1, y = data_dim_2)) + 
        plotting_func(aes(data_dim_1, data_dim_2), size = I(cell_size), 
                      stroke = I(cell_stroke), color = "grey80", 
                      data = na_sub, alpha = alpha) + plotting_func(aes(color = log10(value + 
                                                                                        min_expr)), size = I(cell_size), stroke = I(cell_stroke), 
                                                                    data = ya_sub[order(ya_sub$value), ], alpha = alpha) + 
        viridis::scale_color_viridis(option = "viridis", 
                                     name = expression_legend_label, na.value = NA, 
                                     end = 0.8, alpha = alpha) + guides(alpha = FALSE) + 
        facet_wrap(~feature_label)
    }
  }
  else {
    g <- ggplot(data = data_df, aes(x = data_dim_1, y = data_dim_2))
    if (color_cells_by %in% c("cluster", "partition")) {
      if (is.null(data_df$cell_color)) {
        g <- g + geom_point(color = I("gray"), 
                            size = I(cell_size), stroke = I(cell_stroke), 
                            na.rm = TRUE, alpha = I(alpha))
        message(paste("cluster_cells() has not been called yet, can't", 
                      "color cells by cluster"))
      }
      else {
        g <- g + geom_point(aes(color = cell_color), 
                            size = I(cell_size), stroke = I(cell_stroke), 
                            na.rm = TRUE, alpha = alpha)
      }
      g <- g + guides(color = guide_legend(title = color_cells_by, 
                                           override.aes = list(size = 4)))
    }
    else if (class(data_df$cell_color) == "numeric") {
      g <- g + geom_point(aes(color = cell_color), size = I(cell_size), 
                          stroke = I(cell_stroke), na.rm = TRUE, alpha = alpha)
      g <- g + viridis::scale_color_viridis(name = color_cells_by, 
                                            option = "C")
    }
    else {
      g <- g + geom_point(aes(color = cell_color), size = I(cell_size), 
                          stroke = I(cell_stroke), na.rm = TRUE, alpha = alpha)
      g <- g + guides(color = guide_legend(title = color_cells_by, 
                                           override.aes = list(size = 4)))
    }
  }
  if (show_trajectory_graph) {
    g <- g + geom_segment(aes_string(x = "source_prin_graph_dim_1", 
                                     y = "source_prin_graph_dim_2", xend = "target_prin_graph_dim_1", 
                                     yend = "target_prin_graph_dim_2"), size = trajectory_graph_segment_size, 
                          color = I(trajectory_graph_color), linetype = "solid", 
                          na.rm = TRUE, data = edge_df)
    if (label_principal_points) {
      mst_branch_nodes <- branch_nodes(cds, reduction_method)
      mst_leaf_nodes <- leaf_nodes(cds, reduction_method)
      mst_root_nodes <- root_nodes(cds, reduction_method)
      pps <- c(mst_branch_nodes, mst_leaf_nodes, mst_root_nodes)
      princ_point_df <- ica_space_df %>% dplyr::slice(match(names(pps), 
                                                            sample_name))
      g <- g + geom_point(aes_string(x = "prin_graph_dim_1", 
                                     y = "prin_graph_dim_2"), shape = 21, stroke = I(trajectory_graph_segment_size), 
                          color = "white", fill = "black", 
                          size = I(graph_label_size * 1.5), na.rm = TRUE, 
                          princ_point_df) + ggrepel::geom_text_repel(aes_string(x = "prin_graph_dim_1", 
                                                                                y = "prin_graph_dim_2", label = "sample_name"), 
                                                                     size = I(graph_label_size * 1.5), color = "Black", 
                                                                     na.rm = TRUE, princ_point_df)
    }
    if (label_branch_points) {
      mst_branch_nodes <- branch_nodes(cds, reduction_method)
      branch_point_df <- ica_space_df %>% dplyr::slice(match(names(mst_branch_nodes), 
                                                             sample_name)) %>% dplyr::mutate(branch_point_idx = seq_len(dplyr::n()))
      branch_point_df$sample_name <- str_remove(branch_point_df$sample_name,pattern = "Y_")
      g <- g + geom_point(aes_string(x = "prin_graph_dim_1", 
                                     y = "prin_graph_dim_2"), shape = 21, stroke = I(trajectory_graph_segment_size), 
                          color = "white", fill = "black", 
                          size = I(graph_label_size * 1.5), na.rm = TRUE, 
                          branch_point_df) + geom_text(aes_string(x = "prin_graph_dim_1", 
                                                                  y = "prin_graph_dim_2", label = "sample_name"), 
                                                       size = I(graph_label_size), color = "white", 
                                                       na.rm = TRUE, branch_point_df)
    }
    if (label_leaves) {
      mst_leaf_nodes <- leaf_nodes(cds, reduction_method)
      leaf_df <- ica_space_df %>% dplyr::slice(match(names(mst_leaf_nodes), 
                                                     sample_name)) %>% dplyr::mutate(leaf_idx = seq_len(dplyr::n()))
      leaf_df$sample_name <- str_remove(leaf_df$sample_name,pattern = "Y_")
      g <- g + geom_point(aes_string(x = "prin_graph_dim_1", 
                                     y = "prin_graph_dim_2"), shape = 21, stroke = I(trajectory_graph_segment_size), 
                          color = "black", fill = "lightgray", 
                          size = I(graph_label_size * 1.5), na.rm = TRUE, 
                          leaf_df) + geom_text(aes_string(x = "prin_graph_dim_1", 
                                                          y = "prin_graph_dim_2", label = "sample_name"), 
                                               size = I(graph_label_size), color = "black", 
                                               na.rm = TRUE, leaf_df)
    }
    if (label_roots) {
      mst_root_nodes <- root_nodes(cds, reduction_method)
      root_df <- ica_space_df %>% dplyr::slice(match(names(mst_root_nodes), 
                                                     sample_name)) %>% dplyr::mutate(root_idx = seq_len(dplyr::n()))
      root_df$sample_name <- str_remove(root_df$sample_name,pattern = "Y_")
      g <- g + geom_point(aes_string(x = "prin_graph_dim_1", 
                                     y = "prin_graph_dim_2"), shape = 21, stroke = I(trajectory_graph_segment_size), 
                          color = "black", fill = "white", 
                          size = I(graph_label_size * 1.5), na.rm = TRUE, 
                          root_df) + geom_text(aes_string(x = "prin_graph_dim_1", 
                                                          y = "prin_graph_dim_2", label = "sample_name"), 
                                               size = I(graph_label_size), color = "black", 
                                               na.rm = TRUE, root_df)
    }
  }
  if (label_cell_groups) {
    g <- g + ggrepel::geom_text_repel(data = text_df, mapping = aes_string(x = "text_x", 
                                                                           y = "text_y", label = "label"), size = I(group_label_size))
    if (is.null(markers_exprs)) 
      g <- g + theme(legend.position = "none")
  }
  g <- g + monocle_theme_opts() + xlab(paste(reduction_method, 
                                             x)) + ylab(paste(reduction_method, y)) + theme(legend.key = element_blank()) + 
    theme(panel.background = element_rect(fill = "white"))
  g
}


