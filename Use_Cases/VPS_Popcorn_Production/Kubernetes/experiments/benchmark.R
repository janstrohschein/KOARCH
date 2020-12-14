###################################################################################
#' This file contains the simulateAndBenchmark and the fnSims functions.
#' fnSims basically is a wrapper for the simulateAndBenchmark function to 
#' be applied with the listable apply functions. SimulateAndBenchmark performs
#' experiment as configured for a given budget. 
#' 
#' @author Andreas Fischbach (andreas.fischbach@th-koeln.de)
################################################################################### 

###################################################################################
#' This method performs benchmarking for given pipelines based on 
#' simulations and plots created instances if desired. 
#' 
#' @param objFunEvals the budget for each optimizer/pipeline
#' @return data.frame with the results of this benchmark 
###################################################################################
fnSims <- function(objFunEvals) {
  if(it > 1) {
    # only need to be plotted once (if at all) 
    printSimPlots <- FALSE
  } 
  if(!exists("tune")) {
    tune <- FALSE
  }
  if(!exists("evaluateSimulation")) {
    evaluateSimulation <- FALSE
  }
  if(!exists("repeatEvaluation")) {
    repeatEvaluation <- FALSE
  }
  
  results <- simulateAndBenchmark(data = data, 
                                  tune = tune, 
                                  evaluateSimulation = evaluateSimulation, 
                                  repeatEvaluation = repeatEvaluation, 
                                  usecase = usecase, 
                                  evals = objFunEvals, 
                                  tuningBudget = tuningBudget,  
                                  seed = randomSeed, 
                                  repetitions = repetitions, 
                                  plot = printSimPlots)
  it <<- it + 1
  return(results)
}

###################################################################################
#' This function creates simulations according to VPS data, 
#' 
#' @param data
#' @param tune
#' @param evaluateSimulation
#' @param repeatEvaluation
#' @param usecase name of the case, e.g. 'vps_1' or 'vps_2' (premium corn)
#' @param evals budget for the optimization, i.e., nr of objective function evaluations
#' @param tuningBudget budget for SPOT for the tuning of each algorithm
#' @param seed seed for the random number generator
#' @param repetitions number of repetitions of each single experiment
#' @param results data.frame to be updated 
#' @param plot logical, indicating if groundtruth and simulations shall be plotted in an PDF file
#' 
#' @return updated data.frame
###################################################################################
simulateAndBenchmark <- function(data = NULL, 
                                 tune = TRUE, 
                                 evaluateSimulation = FALSE, 
                                 repeatEvaluation = FALSE, 
                                 usecase = NULL, 
                                 evals = NULL, 
                                 tuningBudget = NULL, 
                                 seed = NULL, 
                                 repetitions = NULL, 
                                 plot = NULL) {
  # get control parameter x and aggregated objective from vps data file as x and y
  x <- cbind(unique(data$conveyorRuntimeMean))
  y <- cbind(unique(data$yAgg))
  
  # specify model configuration for the simulation of the vps
  mc <- list(useLambda=FALSE, thetaLower=1e-6, thetaUpper=1e12)
  
  # roi of objective (and simulations)
  lower <- c(3500)
  upper <- c(10000)
  
  # get list of feasible pipelines, their controls, tuning interfaces, tuning calls, etc.
  listOptimizer <- getFeasiblePipelines(lower = lower, upper = upper)
  listOptimizerNames <- getFeasiblePipelinesNames()
  listControls <- getPipelineConfigurations(funEvals = evals)
  listTunedControls <- getPipelineConfigurations(funEvals = evals)
  listTuningMethod <- getTuningInterfaces()
  listSpotTuning <- getSpotTuningList(tuningBudget = tuningBudget, lower = lower, upper = upper, objFunctionBudget = evals)
  
  # nr of simulations needed
  nSim <- length(listOptimizerNames)
  
  # configuration details for the simulation of the groundthruth
  # conditional simulation is used here
  cntrlObjective <- list(modelControl = mc,
                         nsim = 1,
                         seed = 1,
                         method = "spectral",
                         Ncos = 20, #for simplicity sake a relatively low number of cosines
                         conditionalSimulation = TRUE
  )
  
  # and some configuration details for the simulations for the benchmark runs
  # unconditional simulations will be used here
  cntrl <- list(modelControl = mc,
                nsim = nSim,
                seed = 2,
                method = "spectral",
                Ncos = 20, #for simplicity sake a relatively low number of cosines
                conditionalSimulation = FALSE
  )
  
  # get the interface for the groundtruth
  objFun <- generateCOBBS(x, y, cntrlObjective)$simulation[[1]] 
  groundtruth <- objFun
  
  # generate model and functions for the simulations
  cobbsResult <- generateCOBBS(x, y, cntrl)
  
  # shuffle simulation functions
  cobbsResult$simulations <- sample(cobbsResult$simulations, length(cobbsResult$simulations), replace=FALSE)
  
  # plot groundtruth (dashed) and simulation (blue)
  if(TRUE == plot) {
    plotSimulation(lower = 3000, upper = 11000, objFun, cobbsResult)  
  }
  
  # optim groundtruth first
  print(paste("Optimize groundtruth for budget ", evals))
  nrExperiments <- repetitions * length(listOptimizerNames)
  
  # call each pipeline  
  optimizerCall <- function(name) {
    # over k repetitions
    repetitionCall <- function(k) {
      alg <- listOptimizer[[name]]
      contr <- listControls[[name]]
      res <- alg(groundtruth, contr, seed = id)
      objectiveName <- usecase
      print(paste('repetition', k, "Id/seed:", id, 'optimizer:', name, 'x:', res$xbest, 'y:', res$ybest, 'count:', res$count)) 
      if(length(res) <= 2) {
        warning(paste("res$xbest and res$ybest are null; algorithm didnt provide result!", "row:", nrow(results) + 1, "Optimizer:", name, "rep:", k, "obj:", objectiveName, sep = " ", collapse = NULL))
        res$xbest <- NA
        res$ybest <- NA
        res$count <- budget
      }
      results <- updateResults(budget = evals, id = id, usecase = usecase, objective = objectiveName, repetition = k, optimizer = name, tuned = FALSE, y = res$ybest, cpu = res$cpu, mem = res$mem, seed = id, evals = res$count)
      id <<- id + 1
      return(results)
    }
    
    # iteratively call inner function over repetitions
    results <- setDF(rbindlist(lapply(c(1:repetitions), repetitionCall)))
    return(results)
  }
  results <- setDF(rbindlist(lapply(listOptimizerNames, optimizerCall)))
  
  # Tuning?
  if(TRUE == tune) {
    print("Tune algorithms on simulations")
    
    print("Controls before tuning: ")
    lapply(listOptimizerNames, function(name) {
      print(listControls[name])
    })
    
    simId <- sample(seq(1, length(listOptimizerNames)), 1)
    tuningObjective <- cobbsResult$simulation[[simId]]

    # call each pipeline  
    optimizerCall <- function(name, i) {
      #tuningObjective <- cobbsResult$simulation[[i]]
      objectiveName <- paste("simulation", i, sep = "", collapse = NULL)
      tuningInterface <- listTuningMethod[[name]]
      tune <- listSpotTuning[[name]]
      res <- tune(tuningInterface = tuningInterface, objFunction = tuningObjective, seed = id)
      id <<- id + 1
      
      ctrNames <- names(res)

      # get default controls
      contr <- listControls[[name]]
      if(length(res) > 0) {
        for(j in 1:length(res)) {
          parName <- ctrNames[[j]]
          value <- res[[j]]
          contr[[parName]] <- value
        }
        return(contr)
      }
    }
    
    ids <- seq(1, length(listOptimizerNames))
    optimizedControls <- mapply(FUN = optimizerCall, name = listOptimizerNames, i = sample(ids), SIMPLIFY = FALSE)

    ## merge optimized controls into listControls somehow
    for(i in ids) {
      optimName <- listOptimizerNames[[i]]
      subContr <- listControls[[optimName]]
      optContr <- optimizedControls[[i]]
      for(item in names(optContr)) {
        subContr[[item]] <- optContr[[item]]
      }
      listControls[[optimName]] <- subContr
    }

    print("Tuning finished")
  }
  
  if(TRUE == evaluateSimulation) {
    print(paste("Evaluate simulations for budget ", evals))
    nrExperiments <- repetitions * length(listOptimizerNames)
    
    # randomly pick simulation 
    # simId <- sample(rep(length(listOptimizer) + 1, length(cobbsResult$simulation)),1)
    simId <- sample(1:nSim, 1)
    evaluationObj <- cobbsResult$simulation[[simId]]
    
    # call each pipeline  
    optimizerCall <- function(name) {
      # over k repetitions
      repetitionCall <- function(k) {
        alg <- listOptimizer[[name]]
        contr <- listControls[[name]]
        res <- alg(evaluationObj, contr, seed = id)
        objectiveName <- paste("simulation", simId, collapse = NULL, sep = "")
        print(paste('repetition', k, "Id/seed:", id, 'optimizer:', name, 'x:', res$xbest, 'y:', res$ybest, 'count:', res$count))         
        # check if algorithm finished correctly
        if(length(res) <= 2) {
          warning(paste("res$xbest and res$ybest are null; algorithm didnt provide result!", "row:", nrow(results) + 1, "Optimizer:", name, "rep:", k, "obj:", objectiveName, sep = " ", collapse = NULL))
          res$xbest <- NA
          res$ybest <- NA
          res$count <- evals
        }
        
        results <- updateResults(budget = evals, id = id, usecase = usecase, objective = objectiveName, 
                                 repetition = k, optimizer = name, tuned = FALSE, y = res$ybest, cpu = res$cpu, mem = res$mem, seed = id, evals = res$count)
        id <<- id + 1
        return(results)
      }
      results <- setDF(rbindlist(lapply(c(1:repetitions), repetitionCall)))
      return(results)
    }
    results <- rbind(results, setDF(rbindlist(lapply(listOptimizerNames, optimizerCall))))
  }
  
  if(TRUE == repeatEvaluation) {
    # optim groundtruth with tuned parameters
    print("Optimize groundtruth again")
    objFun <- groundtruth
    
    # call each pipeline  
    optimizerCall <- function(name) {
      # over k repetitions
      repetitionCall <- function(k) {
        alg <- listOptimizer[[name]]
        contr <- listControls[[name]]
        res <- alg(objFun, contr, seed = id)
        objectiveName <- usecase
        print(paste('repetition', k, "Id/seed:", id, 'optimizer:', name, 'x:', res$xbest, 'y:', res$ybest, 'count:', res$count))         
        results <- updateResults(budget = evals, id = id, usecase = usecase, objective = objectiveName, repetition = k, optimizer = name, tuned = TRUE, y = res$ybest, cpu = res$cpu, mem = res$mem, seed = id, evals = res$count)
        id <<- id + 1
        return(results)
      }
      results <- setDF(rbindlist(lapply(c(1:repetitions), repetitionCall)))
      return(results)
    }
    results <- rbind(results, setDF(rbindlist(lapply(listOptimizerNames, optimizerCall))))
  }
  
  print("Finished benchmark")
  return(results)
}