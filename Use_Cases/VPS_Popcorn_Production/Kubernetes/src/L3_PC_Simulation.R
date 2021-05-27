library(COBBS)
library(SPOT)


# (1) S <- generateTestFunctions(d)

# generate test functions utilizing COBBS using data points d
# d has the form: id, x, y
generateTestFunctions <- function(d, n) {
  print("R: generate Test Functions call")

  # names(d) <- c('id', 'x', 'y')

  S <- list()

  # print(summary(d))
  x <- cbind(unique(d$x))
  y <- cbind(unique(d$y))

  ## nr of functions to generate
  nrTestFunctions <- n

  ## specify Kriging model configuration for COBBS
  mc <- list(useLambda=FALSE, thetaLower=1e-6, thetaUpper=1e12)

  ## and some configuration details for the simulation
  cntrl <- list(modelControl = mc,
                nsim = nrTestFunctions,
                seed = 1,
                method = "spectral",
                Ncos = 20, #for simplicity sake a relatively low number of cosines
                #method="decompose",xsim=matrix(c(runif(200,-32,32)),,1),
                conditionalSimulation = FALSE)

  # groundtruth function to compare simulations with (visually)
  objFun <- funVPS(d)

  # generate model and functions
  cobbsResult <- generateCOBBS(x, y, cntrl)

  # shuffle simulation functions
  cobbsResult$simulation <- sample(cobbsResult$simulation, length(cobbsResult$simulation), replace=FALSE)

  # plot groundtruth (dashed), model prediction (red), and simulation (blue)
  # plotSimulation(lower = 3000, upper = 11000, objFun, cobbsResult)

  # random sample sims
  id <- sample.int(length(cobbsResult$simulation), 1)
  print(paste("R: Sim id ", id, " chosen", sep = "", collapse = NULL))
  S <- cobbsResult$simulation[[id]]

  return(S)
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
  kriging <- buildKriging(as.matrix(data$x), as.matrix(data$y), control = list(useLambda=TRUE, reinterpolate=TRUE))
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
