###################################################################################
#' File covers several helper functions for optimization in CAAI
#' 
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
if(!require(yaml)) {
  install.packages(yaml)
  library(yaml)
}

# source optimization interfaces
source("optimizers.R")

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
  simfile <- paste("data/", Sys.Date(), "_simulations.png", sep ="", collapse = NULL)
  print(paste("Plot groundtruth and simulation instances: ", simfile, sep = "", collapse = NULL))
  ## legend: dashed (groundtruth), red (estimation), blue (simulations)
  xplot <- seq(from=lower,to=upper, length.out=100)
  png(file = simfile)
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
#' Creates an empty data.frame with a given column data type structure.
#'
#' @return data.frame with 0 rows
###################################################################################
initResults <- function() {
  res <- data.frame(
           id = integer(),# unique id for the table
           experimentId = integer(), # experiment nr. Each 5th iteration e.g. produces experiment nr 1 after 5 cycles, 2 after 10 cycles, ...
           sequence = integer(), # id, but not unique as each method has an entry in each sequence
           repetition = integer(), # pure repetition counter
           algorithm = character(), # name according to knowledge, e.g., "kriging", "randomForest"
           simulationId = character(), # label of the simulation test function
           cpu = double(), # cpu time (s) used
           memory = integer(), # memory (MB) used
           y = double(), # evaluated value on the objective function
           cpu_norm = double(), #0-1
           memory_norm = double(), #0-1
           y_norm = double(), #0-1
           cpu_mean = double(), #0-1
           memory_mean = double(), #0-1
           y_mean = double(), #0-1
           xBest = double(), # best found x value?
           stringsAsFactors = FALSE) 
  return(res)
}

###################################################################################
#' Updates the data.frame with a new row. 
#' 
#' @param data data.frame to update
#' @param id id and row number to add
#' @param experimentId subsequent number of experiment (not unique)
#' @param sequence production cycle of the experiment
#' 
#' @return data.frame with a new row
###################################################################################
updateResults <- function(data = NULL,
                          id = NULL, 
                          experimentId = NULL, 
                          sequence = NULL, 
                          repetition = NULL, 
                          algorithm = NULL, 
                          simulationId = NULL, 
                          cpu = NULL, 
                          memory = NULL, 
                          y = NULL, 
                          cpu_norm = 1, #0-1
                          memory_norm = 1, #0-1
                          y_norm = 1, #0-1
                          cpu_mean = Inf, #0-1
                          memory_mean = Inf, #0-1
                          y_mean = Inf, #0-1
                          xBest = NULL) {

  # print(colnames(data))
  data[id,] <- list(id = id,
                    experimentId = experimentId,
                    sequence = sequence,
                    repetition = repetition,
                    algorithm = algorithm,
                    simulationId = simulationId,
                    cpu = cpu,
                    memory = memory,
                    y = y,
                    cpu_norm = cpu_norm, 
                    memory_norm = memory_norm, #0-1
                    y_norm = y_norm, #0-1
                    cpu_mean = cpu_mean, #0-1
                    memory_mean = memory_mean, #0-1
                    y_mean = y_mean,
                    xBest = xBest
  )
  return(data)
}
