###################################################################################
#' This file contains initializations for the VPS use case. 
#' The considered algorithm are configured in the function 
#' getFeasiblePipelinesNames()
#' 
#' This experiments refer to the correlation analysis and shall demonstrate the 
#' applicability of data-driven simulations for the algorithm selection problem
#' on the VPS use case. 
#' 
#' @author Andreas Fischbach (andreas.fischbach@th-koeln.de)
###################################################################################

# clear env
rm(list = ls())

# source R scripts - packages and dependencies are handled there
source("misc.R")

# two data files are available, file2 contains the premium corn data
data <- read.csv2(file1)
usecase <- "VPS_1"
objFunEvals <- 20 # optimization budget 
repetitions <- 10 # repetitions
printSimPlots <- TRUE # logical indicating if the simulations shall be plotted in a PDF file
tune <- FALSE # logical indicating if tuning will be performed
evaluateSimulation <- TRUE # logical indicating if simulations will be generated and evaluated
saveResultFile <- TRUE # logical indicating if the resulting data.frame shall be stored in an RData file

# filename of the results RData file, will contain the 'results' data.frame  
resultsFileName <- paste('results/', Sys.Date(), usecase, "rep", repetitions, "Budget", objFunEvals, "tune", tune, ".RData", sep = "", collapse = NULL) 

# init result data.frame with empty columns by type
results <- initResults()

# global vars, counter of simulation loops to perform repetitions, and id as counter 
# will be used to check, if plots should be performed, to prevent multiple plottings
it <<- 1
id <<- 1

# call the simulation iteratively from 10:budget for each value
# and bind the data.frame results returned by the fnSims function
results <- setDF(rbindlist(lapply(10:objFunEvals, fnSims)))

# save results
if(TRUE == saveResultFile) {
  save(results, file = resultsFileName)
}

