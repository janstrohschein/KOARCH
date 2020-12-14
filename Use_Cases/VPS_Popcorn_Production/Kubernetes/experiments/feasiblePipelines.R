###################################################################################
#' This file contains the management of feasible pipelines for given budget
#'  
#' @author Andreas Fischbach (andreas.fischbach@th-koeln.de)
################################################################################### 

###################################################################################
#' Get a list of names of optimizers to include as candidate pipelines
#' @param budget budget for optimizers, only pipelines which 
#' are capable of computing results based on given budget will be used
#' 
#' @return list of names of optimizers used
###################################################################################
getFeasiblePipelinesNames <- function(budget = NULL) {
  nameGenSA <- 'Generalized SA'
  nameRS <- 'Random Search'
  nameLhd <- 'Lhd'
  nameDE <- 'Differential Evolution'
  nameES <- 'Evolution Strategy'
  nameKrigingBP <- 'Kriging'  
  nameKrigingEI <- 'Kriging EI'  
  nameRF <- 'Random Forest'  
  nameLBFSGB <- 'L-BFGS-B'
  nameLM <- 'Linear Model'  
  
  names <- list()  
  
  # comment/uncomment algos as desired
  names <- c(names, nameGenSA)
  names <- c(names, nameRS)
  # names <- c(names, nameLhd)
  # names <- c(names, nameES)
  names <- c(names, nameDE)
  names <- c(names, nameKrigingBP)
  # names <- c(names, nameKrigingEI)
  names <- c(names, nameRF)
  names <- c(names, nameLBFSGB)
  # names <- c(names, nameLM)
  
  return(names)
}