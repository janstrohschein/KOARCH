print("before run: ")
print(sessionInfo())
print(".libPaths():")
print(.libPaths())

library(devtools)
library(COBBS)

# (1) S <- generateTestFunctions(d)
# generate test functions utilizing COBBS using data points d
# d has the form: id, x, y 
generateTestFunctions <- function(d) {
  print("R: generate Test Functions call")

  S <- list()

  # print(summary(d))
  x <- cbind(unique(d$conveyorRuntimeMean))
  y <- cbind(unique(d$yAgg))

  ## nr of functions to generate
  nrTestFunctions <- 5 

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
  plotSimulation(lower = 3000, upper = 11000, objFun, cobbsResult)  
  
  S <- cobbsResult$simulation[[1]]

  return(S)
}
