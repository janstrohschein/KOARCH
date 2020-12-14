###################################################################################
#'
#' File covers several helper function
#' @author Andreas Fischbach (andreas.fischbach@th-koeln.de)
###################################################################################

# install devtools if not yet
if(!require(devtools)) {
  install.packages(devtools) 
  library(devtools)
}
# install COBBS from GitHub
if(!require(COBBS)) {
  devtools::install_github("martinzaefferer/COBBS") 
  library(COBBS)
}
if(!require(SPOT)) {
  install.packages(SPOT)
  library(SPOT)
}
if(!require(CEGO)) {
  install.packages(CEGO)
  library(CEGO)
}
if(!require(profmem)) {
  install.packages(profmem)
  library(profmem)
}
if(!require(tictoc)) {
  install.packages(tictoc)
  library(tictoc)
}
if(!require(GenSA)) {
  install.packages(GenSA)
  library(GenSA)
}
if(!require(data.table)) {
  install.packages(data.table)
  library(data.table)
}

# source optimization interfaces
source("optimizers.R")
source("benchmark.R")
source("feasiblePipelines.R")

# data files
file1 <- "data/vpsFeatures_It1_20191220.csv"
file3 <- "data/vpsFeatures_It2_Premium.csv"

###################################################################################
#' normalize (data.frame) column vector from 0 to 1 (min-max scaling)
#'
#' @param x numerical vector to be normalized 
#' @return normalized vector
#'  
###################################################################################
normalize <- function(x) {
  return ((x - min(x)) / (max(x) - min(x)))
}



###################################################################################
#' Objective Function based on data points from the VPS 
#' Compute a Kriging model to estimate the VPS behaviour on real data
#' returns 
#' @param data data.frame with x (data$conveyorRuntimeMean) and y (data$yAgg) 
#'
#' @return objFunction with parameter x to predict new values 
#'  
###################################################################################
funVPS <- function(data) {
  # model y ~ x 
  kriging <- buildKriging(as.matrix(data$conveyorRuntimeMean), as.matrix(data$yAgg), control = list(useLambda=TRUE, reinterpolate=TRUE))
  tmp <- function(x) {
    predict(kriging, x)$y
  }
  return(tmp)
}

###################################################################################
#' Plots simulations and estimation of COBBS result
#'
#' @param lower vector of lower bounds
#' @param upper vector of upper bounds
#' @param objFunction the groundtruth function
#' @param simulationModel the COBBS result 
#'  
###################################################################################
plotSimulation <- function(lower, upper, objFun, simulationModel) {
  simfile <- paste("results/", Sys.Date(), "_simulations.pdf", sep ="", collapse = NULL)
  print(paste("Plot groundtruth and simulation instances: ", simfile, sep = "", collapse = NULL))
  ## legend: dashed (groundtruth), red (estimation), blue (simulations)
  xplot <- seq(from=lower,to=upper, length.out=100)
  pdf(file = simfile)
    # plot ground truth function
    plot(xplot, objFun(xplot),type="l", ylim=c(0, 1), lty=2, xlab = "Conveyor runtime (ms)", ylab = "y")
    # plot estimation (prediction) 
    # lines(xplot, simulationModel$estimation(xplot), col="red")
    # plot simulations
    for(sim in simulationModel$simulation) {
      lines(xplot, sim(xplot), col="blue") 
    }
  dev.off()
}

###################################################################################
#' creates an empty data.frame with given columns and corr. datatypes
#' 
#'  
#' @return This function returns a data.frame with:
#' id (int)
#' usecase (character)
#' repetition (int)
#' optimizer (character)
#' tuned (logical)
#' y (numeric)
#' cpu (numeric)
#' mem (numeric)
#' seed (numeric)
#' 
###################################################################################
initResults <- function() {
  results <- data.frame(id = integer(0),
                        budget = integer(0),
                        usecase = character(0),
                        repetition = integer(0),
                        optimizer = character(0),
                        objective = character(0),
                        tuned = logical(0),
                        y = numeric(0),
                        cpu = numeric(0),
                        mem = numeric(0),
                        seed = numeric(0),
                        evals = integer(0),
                        stringsAsFactors = FALSE)
  return(results) 
}

###################################################################################
#' Updates the experiments result data.frame with an 
#' added row of given parameters
#' 
#' @param results data.frame to update
#' @param row row nr to add, used for addressing 
#' @param id counter
#' @param usecase describes the used data file
#' @param repetition the repetition nr
#' @param optimizer used algorithm
#' @param tuned algorithm tuned (TRUE) or not (FALSE)
#' @param y achieved function value
#' @param cpu computation time
#' @param mem memory usage
#' @param seed used random seed
#' 
#' @return returns the updated data.frame
###################################################################################
updateResults <- function(id = NULL, budget = NULL, usecase = NULL, repetition = NULL, optimizer = NULL, objective = NULL, tuned = NULL, y = NULL, cpu = NULL, mem = NULL, seed = NULL, evals = NULL) {
  force(seed)
  results <- initResults()
  row <- 1
  results[row, 'id'] <- id
  results[row, 'budget'] <- budget
  results[row, 'usecase'] <- usecase
  results[row, 'repetition'] <- repetition
  results[row, 'optimizer'] <- optimizer
  results[row, 'objective'] <- objective
  results[row, 'tuned'] <- tuned
  results[row, 'y'] <- y
  results[row, 'cpu'] <- cpu
  results[row, 'mem'] <- mem
  results[row, 'seed'] <- seed
  results[row, 'evals'] <- evals
  return(results)
}