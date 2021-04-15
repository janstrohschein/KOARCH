###################################################################################
#' This file contains the simulateAndBenchmark and additional convenience functions.
#' SimulateAndBenchmark performs
#' experiments as configured for a given budget on simulations.
#' 
#' @author Andreas Fischbach (andreas.fischbach@th-koeln.de)
################################################################################### 
source("misc.R")

# TODO This should be read from knowledge
lower = c(4000.0)
upper = c(10100.0)
id <- 1
set.seed(1)

readYamlFile <- function() {
  filename <- "data/knowledge.yaml"
  data <- read_yaml(filename)
  # print(typeof(data))
}

# (0) getKB
getKnowledgeBase <- function() {
  print("R: getKnowledgeBase call")

  readYamlFile()

  # TODO access knowledge API 
  # MOCK: Read knowledge json/yaml
  # MOCKIGER: liste von String mit feasible Algorithms
  algorithms <- list("optLhd","optDE","optKrigingBP","optKrigingEI","optRF","optLBFGSB","optLM")
  algorithms <- list("optLBFGSB", "optDE", "optKrigingBP", "optRF", "optRS")
  KB <- list()
  for(item in algorithms) {
    KB[[length(KB) + 1]] <- list(name=item, feasible=TRUE)
  }
  return(KB)
}

# (1) S <- generateTestFunctions(d)
# generate test functions utilizing COBBS using data points d
# d has the form: id, x, y 
generateTestFunctions <- function(d) {
  print("R: generateTestFunctions call")
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
  
  S <- cobbsResult$simulation

  return(S)
}


# stores feasible pipelines list p in global environment for later usage
# need user defined goal g (min/max stuff), and already available data d for checks 
# according to amount and dimensionality 
# (2) p <- getFeasiblePipelines(KB,g,d)
getFeasiblePipelines <- function(KB = NULL, g = NULL, d = NULL, e = NULL) {
  print('R: getFeasiblePipelines call')
  
  # KB contains list with name/feasible, so extract names with feasible = TRUE
  # print(KB)
  p <- list()
  for(entry in KB) {
    if(entry$feasible == TRUE)
      p[[length(p) + 1]] <- entry$name
  }
  
  print(paste('R: determined nr of feasible pipelines: ', length(p), sep = "", collapse = NULL))
  return(p)
}

## (3) p <- selectCandidatePipelines(KB,r,p,e)
selectCandidatePipelines <- function(KB = NULL, r = NULL, p = NULL, e = NULL) {
  print("R: selectCandidatePipelines call")
  # TODO sample promising candidates from p, utilizing performance model (SPOT)
  pSample <- list()

  # until now: use all candidates
  return(p)
}

## (4) e <- applyPipelinesOnSimulations(S)
applyPipelinesOnSimulations <- function(S = NULL, p = NULL, e = NULL, sequence = NULL) {
  print("R: applyPipelinesOnSimulations call")
  ## perform experiments 
  # print(length(S))

  # TODO get from KB/API: lower, upper, budget (initDesignSize + theta? current cycle + theta?)
  lower <- c(4000)
  upper <- c(10000)
  repetitions <- 10

  # get controls per algorithm
  listControls <- getPipelineConfigurations(funEvals = 20)
  listOptimizer <- getOptimizerInterfaces(lower = lower, upper = upper)

  # get simulation instance 
  simId <- sample(rep(1, length(S)),1)
  evaluationObj <- S[[simId]]

  for(algorithmName in p) {
    alg <- listOptimizer[[algorithmName]]
    contr <- listControls[[algorithmName]]
    name <- algorithmName
    # print(name)
    # print(contr)

    for(k in 1:repetitions) {
      id <- nrow(e) + 1
      experimentId <- id 

      res <- alg(evaluationObj, contr, seed = id)
      objectiveName <- paste("simulation", simId, collapse = NULL, sep = "")
      print(paste('x:', res$xbest, 'y:', res$ybest, 'count:', res$count)) 

      ## update results and return data.frame
      repetition <- k
      e <- updateResults(data = e,
                              id = id, 
                              experimentId = experimentId, 
                              sequence = sequence, 
                              repetition = repetition, 
                              algorithm = algorithmName, 
                              simulationId = objectiveName, 
                              cpu = res$cpu, 
                              memory = res$mem,
                              y = res$ybest, 
                              xBest = res$xbest)
      
    }

    tmp <- aggregate(y ~ algorithm, data = e, FUN = mean)
    e[e$algorithm == algorithmName, ]$y_mean <- tmp[tmp$algorithm == algorithmName, 'y']
    tmp <- aggregate(memory ~ algorithm, data = e, FUN = mean)
    e[e$algorithm == algorithmName, ]$memory_mean <- tmp[tmp$algorithm == algorithmName, 'memory']
    tmp <- aggregate(cpu ~ algorithm, data = e, FUN = mean)
    e[e$algorithm == algorithmName, ]$cpu_mean <- tmp[tmp$algorithm == algorithmName, 'cpu']
  }

  # get baseline reference performance
  randomSearch <- e[e$algorithm == 'optRS', ]
  e <- e[e$algorithm != 'optRS', ]

  reference <- aggregate(cpu ~ algorithm, data = randomSearch, FUN = mean)
  reference$memory <- aggregate(memory ~ algorithm, data = randomSearch, FUN = mean)$memory
  reference$y <- aggregate(y ~ algorithm, data = randomSearch, FUN = mean)$y

  # we have mean metrics, and baseline reference as mean
  # now compute relative performance (1) and normalize it (2) 
  # compute mem, y, cpu divided by reference (baseline)
  e$relY <- (reference$y - e$y_mean) / reference$y
  e$relCpu <- e$cpu_mean / reference$cpu
  e$relMemory <- e$memory_mean / reference$memory

  # normalize (min-max) performance metrics columns from the last experiments   
  e$relYNorm <- normalize(e$relY)
  e$relCpuNorm <- 1-normalize(e$relCpu)
  e$relMemoryNorm <- 1-normalize(e$relMemory)

  # print(e)
  
  #e$cpu_norm <- normalize(e$cpu_mean)
  #e$memory_norm <- normalize(e$memory_mean)
  #e$y_norm <- normalize(e$y_mean)
 
  return(e)
}

# sample candidate pipelines according to available resources r
## calls inside: 
## After finishing 
## (5) KB, p_best <- ratePipelines(KB,p,e) ## move to Python
## (6) returns p_best 

# d data points
# g goal
# r available ressources
# e evaluation list
# e = simulateAndBenchmark() # should use previously grabbed feasiblePipelines inside r

###################################################################################
#' This function creates simulations according to VPS data, 
#' and evalutes feasible pipelines according to available resources, data, and goal of the process. 
#' (1) S <- generateTestFunctions(d)
#' (2) p <- getFeasiblePipelines(KB,g,d)
#' (3) pSample <- selectCandidatePipelines(KB,r,p,e)
#' (4) e <- applyPipelinesOnSimulations(S, pSample, e)
#' 
#' Best performer will be selected to adapt VPS.
#' 
#' @param d data points as data.frame
#' @param g goal for the process, named list?
#' @param r available resources (nr of pipelines to sample)
#' @param e evaluation list-data.frame 
#' @param sequence sequence of benchmark, will be incremented for each simulateAndBenchmark call
#' 
#' @return updated data.frame e
###################################################################################
simulateAndBenchmark <- function(d = NULL,
                                 g = NULL, 
                                 r = NULL, 
                                 e = NULL,
                                 sequence = NULL
) {
  print("R: start simulateAndBenchmark")

  if(nrow(e) == 0) {
    ## fixme
    ## python inits an empty data.frame (as None can not be converted by rpy2), so we re init it for R usage here, 
    ## and transform it back implicetly via rpy2
    print('R: Init evaluation data.frame')
    e <- initResults()
  }

  # TODO appropriate budget estimates? 
  KB <- getKnowledgeBase()

  S <- generateTestFunctions(d)

  p <- getFeasiblePipelines(KB, g, d)

  pSample <- selectCandidatePipelines(KB, r, p, e) 

  e <- applyPipelinesOnSimulations(S, pSample, e, sequence)
  
  print("R: finished simulateAndBenchmark")
  return(e)
}
