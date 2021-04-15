###################################################################################
#'
#' File covers several functions related to optimizers and tuning via SPOT
#' 
###################################################################################

###################################################################################
#' Get a list of optimizers, returned as list of functions
#' 
#' @param lower vector of lower bounds for objFunction
#' @param upper vector of upper bounds for objFunction
#' 
#' @return This function returns a list with optimizers
#' and following arguments:
#' @param objFunction objective function on which optimizer will be tuned
#' @param ctrl a named list of control parameters
#' @param seed a seed for RNG
#' 
###################################################################################
getOptimizerInterfaces <- function(lower = NULL, upper = NULL) {
  optRS <- function(objFunction = NULL, ctrl = NULL, seed = NULL) {
    tic("RandomSearch")
    force(seed)
    set.seed(seed)

    budget <- ctrl$funEvals
    res <- NULL
    memProfile <- profmem({
      yBest <- Inf
      xBest <- NULL
      for(i in 1:budget) {
        # random par values
        x <- lower + runif(length(lower)) * (upper-lower)
        # evaluate function
        y <- objFunction(x = as.matrix(x))
        # update best
        if(y < yBest) {
          yBest <- y
          xBest <- x
        }
      } 
      res <- list(ybest=yBest, xbest=xBest, count=budget)
    })
    
    # cpu time 
    cpu <- toc(quiet = TRUE)
    cpu <- cpu$toc[[1]] - cpu$tic[[1]]
    cpu <- round(cpu, digits=2)
    # memory usage in MB
    mem <- sum(memProfile$bytes, na.rm = TRUE)/(1024*1024)
    
    res$cpu <- cpu
    res$mem <- mem
    return(res)
  }
  optLhd <- function(objFunction = NULL, ctrl = NULL, seed = NULL) {
    tic("Lhd")
    force(seed)
    set.seed(seed)
    print("LHD: ")
    
    res <- NULL
    memProfile <- profmem({
      res <- SPOT::optimLHD(fun = objFunction, lower = lower, upper = upper, control = ctrl)  
    })
    
    # cpu time 
    cpu <- toc(quiet = TRUE)
    cpu <- cpu$toc[[1]] - cpu$tic[[1]]
    cpu <- round(cpu, digits=2)
    # memory usage in MB
    mem <- sum(memProfile$bytes, na.rm = TRUE)/(1024*1024)
    
    res$cpu <- cpu
    res$mem <- mem
    return(res)
  }
  
  
  # pop-based global optimizer
  optDE <- function(objFunction = NULL, ctrl = NULL, seed = NULL) {
    tic("DEoptim")
    force(seed)
    set.seed(seed)
    ctrl['seed'] <- seed
    print("OptimDE: ")
    # print(ctrl)
    # SPOT::optimES(fun = objFunction, lower = lower, upper = upper, control = ctrl)
    
    budget <- ctrl$funEvals
    popsize <- ctrl$populationSize
    c <- ctrl$c
    strategy <- ctrl$strategy
    Fval <- ctrl$F
    CR <- ctrl$CR

    # max nr iterations according to budget
    itermax = floor((budget - popsize)/popsize)
    #print(paste("itermax:", itermax, "budget:", budget, "popsize:", popsize, sep=" ", collapse = NULL))
    
    # check and correct itermax if <= 0
    if(itermax <= 0) {
      ## correct NP as well? at least one iteration MUST be performed
      popsize <- floor(budget/2)
      itermax = floor((budget - popsize)/popsize)
      warning(paste('Corrected popsize:', popsize, 'itermax: ', itermax))
    }
    
    res <- NULL
    memProfile <- profmem({
      # call DEoptim
      res <- DEoptim::DEoptim(fn = objFunction, 
                              lower = lower, 
                              upper = upper, 
                              control = list(NP=popsize, itermax=itermax, c=c, strategy=strategy, F=Fval, CR=CR ,reltol=1e-10, trace=FALSE))
      # save interesting result values
      res <- list(ybest=res$optim$bestval, xbest=res$optim$bestmem, count=res$optim$nfeval)
    })
    
    # print results
    # print(paste('yBest: ', res$ybest, collapse = NULL, sep = ""))
    
    # cpu time 
    cpu <- toc(quiet = TRUE)
    cpu <- cpu$toc[[1]] - cpu$tic[[1]]
    cpu <- round(cpu, digits=2)
    # memory usage in MB
    mem <- sum(memProfile$bytes, na.rm = TRUE)/(1024*1024)
    
    res$cpu <- cpu
    res$mem <- mem
    
    return(res)
  }
  
  optKrigingBP <- function(objFunction = NULL, ctrl = NULL, seed = NULL) {
    tic("KrigingBP")
    force(seed)
    set.seed(seed)
    ctrl['seedSPOT'] <- seed
    print("KrigingBP: ")
    
    res <- NULL
    memProfile <- profmem({
      res <- SPOT::spot(fun = objFunction, lower = lower, upper = upper, control= ctrl)
    })
    
    # cpu time 
    cpu <- toc(quiet = TRUE)
    cpu <- cpu$toc[[1]] - cpu$tic[[1]]
    cpu <- round(cpu, digits=2)
    # memory usage in MB
    mem <- sum(memProfile$bytes, na.rm = TRUE)/(1024*1024)
    
    res$cpu <- cpu
    res$mem <- mem
    return(res)
  }
  
  optKrigingEI <- function(objFunction = NULL, ctrl = NULL, seed = NULL) {
    tic("KrigingEI")
    force(seed)
    set.seed(seed)
    ctrl['seedSPOT'] <- seed
    print("KrigingEI: ")
    
    res <- NULL
    memProfile <- profmem({
      res <- SPOT::spot(fun = objFunction, lower = lower, upper = upper, control= ctrl)
    })
    
    # cpu time 
    cpu <- toc(quiet = TRUE)
    cpu <- cpu$toc[[1]] - cpu$tic[[1]]
    cpu <- round(cpu, digits=2)
    # memory usage in MB
    mem <- sum(memProfile$bytes, na.rm = TRUE)/(1024*1024)
    
    res$cpu <- cpu
    res$mem <- mem
    return(res)
  }
  
  optRF <- function(objFunction = NULL, ctrl = NULL, seed = NULL) {
    tic("RF")
    force(seed)
    set.seed(seed)
    ctrl['seedSPOT'] <- seed
    print("OptimRF: ")
    
    res <- NULL
    memProfile <- profmem({
      res <- SPOT::spot(fun = objFunction, lower = lower, upper = upper, control = ctrl)
    })
    
    # cpu time 
    cpu <- toc(quiet = TRUE)
    cpu <- cpu$toc[[1]] - cpu$tic[[1]]
    cpu <- round(cpu, digits=2)
    # memory usage in MB
    mem <- sum(memProfile$bytes, na.rm = TRUE)/(1024*1024)
    
    res$cpu <- cpu
    res$mem <- mem
    return(res)
  }
  
  optLBFGSB <- function(objFunction = NULL, ctrl = NULL, seed = NULL) {
    tic("LBFGSB")
    force(seed)
    set.seed(seed)
    print("OptimLBFGSB:")
    
    res <- NULL
    memProfile <- profmem({
      res <- SPOT::optimLBFGSB(fun = objFunction, lower = lower, upper = upper, control = ctrl)
    })
    
    # cpu time 
    cpu <- toc(quiet = TRUE)
    cpu <- cpu$toc[[1]] - cpu$tic[[1]]
    cpu <- round(cpu, digits=2)
    # memory usage in MB
    mem <- sum(memProfile$bytes, na.rm = TRUE)/(1024*1024)
    
    res$cpu <- cpu
    res$mem <- mem
    return(res)
  }
  
  optLM <- function(objFunction = NULL, ctrl = NULL, seed = NULL) {
    tic("LM")
    force(seed)
    set.seed(seed)
    ctrl['seedSPOT'] <- seed
    print("OptimLM: ")
    
    res <- NULL
    memProfile <- profmem({
      res <- SPOT::spot(fun = objFunction, lower = lower, upper = upper, control = ctrl)
    })
    
    # cpu time 
    cpu <- toc(quiet = TRUE)
    cpu <- cpu$toc[[1]] - cpu$tic[[1]]
    cpu <- round(cpu, digits=2)
    # memory usage in MB
    mem <- sum(memProfile$bytes, na.rm = TRUE)/(1024*1024)
    
    res$cpu <- cpu
    res$mem <- mem
    return(res)
  }

 # optimizerList <- list(optLhd, optDE, optKrigingBP, optKrigingEI, optRF, optLBFGSB, optLM)
  optimizerList <- setNames(list(optLhd, optDE, optKrigingBP, optKrigingEI, optRF, optLBFGSB, optLM, optRS), 
                          c("optLhd","optDE","optKrigingBP","optKrigingEI","optRF","optLBFGSB","optLM","optRS"))
  return(optimizerList)

}

###################################################################################
#' Get a list of parameters for optimizers, corresponding to 
#' the list of feasiblePipelines
#' @param funEvals nr of function evaluations for each parameter list 
#' 
#' @return list of names parameter values for each optimizer
###################################################################################
getPipelineConfigurations <- function(funEvals = NULL) {
  ctrRS <- list(funEvals = funEvals)
  ctrLhd <- list(funEvals = funEvals, retries = 100)
  
  popsize <- 10
  itermax <- floor((funEvals - popsize)/popsize)
  ctrDE <- list(funEvals = funEvals, itermax = itermax, populationSize = 10, F = 0.8, CR = 0.5, strategy = 2, c = 0.5)
  ctrKrigingBP <- list(funEvals = funEvals, model = buildKriging, modelControl = list(target="y"))
  ctrKrigingEI <- list(funEvals = funEvals, model = buildKriging, modelControl = list(target="ei"))
  ctrRF <- list(funEvals = funEvals, model = buildRandomForest)
  ctrLBFSG <- list(funEvals = funEvals)
  ctrLM <- list(funEvals = funEvals, model = buildLM, optimizer = optimLBFGSB)  
  #configurationList <- list(ctrLhd, ctrDE, ctrKrigingBP, ctrKrigingEI, ctrRF, ctrLBFSG, ctrLM)
  configurationList <- setNames(list(ctrLhd, ctrDE, ctrKrigingBP, ctrKrigingEI, ctrRF, ctrLBFSG, ctrLM, ctrRS), 
                          c("optLhd","optDE","optKrigingBP","optKrigingEI","optRF","optLBFGSB","optLM","optRS"))
  return(configurationList)
}


###################################################################################
#' Get a list of interface functions for SPOT tuning 
#' 
#' 
#' @return This function returns a list with functions for each optimizer
#' and following arguments:
#' @param algpar matrix of optimizer configurations suggested by SPOT
#' @param objFunction objective function on which optimizer will be tuned
#' @param objFunctionBudget budget for optimizer to solve the objFunction 
#' @param lowerObj vector of lower bounds for objFunction
#' @param upperObj vector of upper bounds for objFunction
#' 
###################################################################################
getTuningInterfaces <- function() {
  
  lhd2spot <- function(algpar, objFunction, objFunctionBudget, lowerObj, upperObj) {
    print("Tuning LHD")
    #    print(algpar)
    performance <- NULL
    for (i in 1:nrow(algpar)) { 
      nRetries = algpar[i, 1]
      result <- SPOT::optimLHD(fun = objFunction, control = list(funEvals = objFunctionBudget, retries = nRetries), lower = lowerObj, upper = upperObj)
      performance <- c(performance, result$ybest[1,1])
    }
    return(matrix(performance, , 1))
  }
  
  de2spot <- function(algpar, objFunction, objFunctionBudget, lowerObj, upperObj) {
    print("Tuning DEoptim")
    #    print(algpar)
    resultList <- NULL
    budget <- objFunctionBudget
    
    for (i in 1:nrow(algpar)) { 
      popsize <- algpar[i, 1]
      Fval <- algpar[i,2]
      CR <- algpar[i,3]
      strategy <- algpar[i,4]
      c <- algpar[i,5]
      
      # max nr iterations according to budget
      itermax = floor((budget - popsize)/popsize)
      # check and correct itermax if <= 0
      if(itermax <= 0) {
        ## correct NP as well? at least one iteration MUST be performed
        popsize <- floor(budget/2)
        itermax = floor((budget - popsize)/popsize)
        warning(paste('Corrected popsize:', popsize, 'itermax: ', itermax))
      }
      
      res <- DEoptim::DEoptim(fn = objFunction, 
                              lower = lowerObj, 
                              upper = upperObj, 
                              control = list(NP=popsize, 
                                             F=Fval, 
                                             CR=CR, 
                                             c=c, 
                                             itermax=itermax, 
                                             strategy=strategy, 
                                             reltol=1e-10, 
                                             trace=0))
      resultList <- c(resultList, res$optim$bestval)
    }
    return(resultList)
  }

  krigingBP2spot <- function(algpar, lowerObj, upperObj, objFunction, objFunctionBudget) {
    resultList <- NULL
    budget <- objFunctionBudget
    
    # algpar is matrix of row-wise settings
    for (i in 1:nrow(algpar)) {
      designSize <- algpar[i,1]
      designType <- algpar[i,2] # 1 = designLHD, 2 = designUniformRandom
      # set design 
      design <- designLHD
      if(designType == 2) {
        design <- designUniformRandom
      }
      
      spotConfig <- list(funEvals = budget,
                         model = buildKriging,
                         modelControl = list(algTheta=optimizerLikelihood, useLambda=TRUE, reinterpolate=TRUE, target="y"),
                         optimizer = optimizerForSPOT,
                         optimizerControl = list(funEvals=150),
                         design = design,
                         designControl = list(size=designSize)
      )
      
      res <- SPOT::spot(fun = objFunction, 
                        lower = lowerObj, 
                        upper = upperObj, 
                        control = spotConfig)
      resultList <- c(resultList, res$ybest)
    }
    
    return(resultList)
  }
  
  krigingEI2spot <- function(algpar, lowerObj, upperObj, objFunction, objFunctionBudget) {
    resultList <- NULL
    budget <- objFunctionBudget

    # algpar is matrix of row-wise settings
    for (i in 1:nrow(algpar)) {
      designSize <- algpar[i,1]
      designType <- algpar[i,2] # 1 = designLHD, 2 = designUniformRandom
      # set design 
      design <- designLHD
      if(designType == 2) {
        design <- designUniformRandom
      }
      
      spotConfig <- list(funEvals = budget,
                         model = buildKriging,
                         modelControl = list(algTheta=optimizerLikelihood, useLambda=TRUE, reinterpolate=TRUE, target="ei"),
                         optimizer = optimizerForSPOT,
                         optimizerControl = list(funEvals=150),
                         design = design,
                         designControl = list(size=designSize)
      )
      
      res <- SPOT::spot(fun = objFunction, 
                        lower = lowerObj, 
                        upper = upperObj, 
                        control = spotConfig)
      resultList <- c(resultList, res$ybest)
    }
    
    return(resultList)
  }
  
  rf2spot <- function(algpar, objFunction, objFunctionBudget, lowerObj, upperObj) {
    resultList <- NULL
    budget <- objFunctionBudget
    
    # algpar is matrix of row-wise settings
    for (i in 1:nrow(algpar)) {
      designSize <- algpar[i,1]
      designType <- algpar[i,2] # 1 = designLHD, 2 = designUniformRandom
      # set design 
      design <- designLHD
      if(designType == 2) {
        design <- designUniformRandom
      }
      
      spotConfig <- list(funEvals = budget,
                         model = buildRandomForest,
                         optimizer = optimizerForSPOT,
                         optimizerControl = list(funEvals=150),
                         design = design,
                         designControl = list(size=designSize)
      )
      
      res <- SPOT::spot(fun = objFunction, 
                        lower = lowerObj, 
                        upper = upperObj, 
                        control = spotConfig)
      resultList <- c(resultList, res$ybest)
    }
    
    return(resultList)
  }
  
  lbfgsb2spot <- function(algpar, objFunction, objFunctionBudget, lowerObj, upperObj) {
  }
  
  lm2spot <- function(algpar, objFunction, objFunctionBudget, lowerObj, upperObj) {
  }
 
  
  ## concatenate list 
  tunings <- list(lhd2spot, de2spot, krigingBP2spot, krigingEI2spot, rf2spot, lbfgsb2spot, lm2spot)
  return(tunings)
}


###################################################################################
#' Get a list of functions which process tuning of given optimizers
#' 
#' @param tuningBudget is a point (vector) in the decision space of fun
#' @param lowerObj is the target function of type y = f(x, ...)
#' @param upperObj is a vector that defines the lower boundary of search space
#' @param objFunctionBudget is a vector that defines the upper boundary of search space
#' 
#' @return This function returns a list with functions for each optimizer
#' and following arguments:
#' @param tuningInterface function which can be passed to SPOT
#' @param objFunction objective function on which optimizer will be tuned
#' @param seed seed for random number generator
###################################################################################
getSpotTuningList <- function(tuningBudget = NULL, lowerObj = NULL, upperObj = NULL, objFunctionBudget = NULL) {
  # force(stuff)?
  lowerObj <- force(lowerObj)
  upperObj <- force(upperObj)
  # seed <- force(seed)
  objFunctionBudget <- force(objFunctionBudget)
  tuningBudget <- force(tuningBudget)
  
  ## tune LHD with Spot
  tuneLhd <- function(tuningInterface = NULL, objFunction = NULL, seed = NULL) {
    print("Tune optimLhd")
    #print(paste("objFunctionBudget: ", objFunctionBudget, collapse = NULL, sep = ""))
    #print(paste("tuningBudget: ", tuningBudget, collapse = NULL, sep = ""))
    
    force(seed)
    set.seed(seed)
    spotConfig <- list(funEvals = tuningBudget,
                       types = c("integer"), 
                       model = buildKriging,
                       optimizer = optimizerForSPOT,
                       optimizerControl = list(funEvals=150),
                       designControl = list(size=10),
                       seedSPOT = seed
    )
    # range repetitions
    lowerSPO <- c(1)
    upperSPO <- c(200)
    spotResult <- SPOT::spot(fun = tuningInterface,
                             lower = lowerSPO,
                             upper = upperSPO,
                             control = spotConfig,
                             lowerObj = lowerObj,
                             upperObj = upperObj,
                             objFunction = objFunction,
                             objFunctionBudget = objFunctionBudget)
    result <- list()
    result['retries'] <- spotResult$xbest[1]
    print(paste("Tuned nrRepetitions: ", result['retries'], collapse = NULL, sep = ""))
    return(result)
  }
  
  tuneDE <- function(tuningInterface = NULL, objFunction = NULL, seed = NULL) {
    print("Tune optimDE")
    #print(paste("objFunctionBudget: ", objFunctionBudget, collapse = NULL, sep = ""))
    #print(paste("tuningBudget: ", tuningBudget, collapse = NULL, sep = ""))
    force(seed)
    set.seed(seed)
    
    lowerNP <- 4 # dim * 2
    upperNP <- floor(objFunctionBudget/2)
    lowerSPO <- c(lowerNP, 0, 0, 1, 0)
    upperSPO <- c(upperNP, 2, 1, 5, 1)
    
    spotConfig <- list(funEvals = tuningBudget,
                       types = c("integer", "numeric", "numeric", "factor", "numeric"),
                       # model = buildKriging,
                       # modelControl = list(algTheta=optimizerLikelihood, useLambda=TRUE, reinterpolate=TRUE),
                       model = buildKriging,
                       optimizer = optimizerForSPOT,
                       optimizerControl = list(funEvals=150),
                       designControl = list(size=10),
                       seedSPOT = seed
    )
    
    ## call SPO 
    spotResult <- SPOT::spot(fun = tuningInterface,
                             lower = lowerSPO,
                             upper = upperSPO,
                             control = spotConfig,
                             lowerObj = lowerObj,
                             upperObj = upperObj,
                             objFunction = objFunction,
                             objFunctionBudget = objFunctionBudget)
    
    ## return xBest, as a named list
    result <- list()
    result['popsize'] <- spotResult$xbest[1]
    result['F'] <- spotResult$xbest[2]
    result['CR'] <- spotResult$xbest[3]
    result['strategy'] <- spotResult$xbest[4]
    result['c'] <- spotResult$xbest[5]

    print("Tuned DEOptim: ")
    print(paste(mapply(paste, names(result), as.numeric(result)), collapse=" / "))
    return(result)
  }
  
  ## tune Kriging with Spot
  tuneKrigingBP <- function(tuningInterface = NULL, objFunction = NULL, seed = NULL) {
    print('tuning KrigingBP')
    set.seed(seed)
  
    # configure spot
    spotConfig <- list(funEvals = tuningBudget,
                       types = c("integer", "factor"), # factor, number
                       # model = buildRandomForest,
                       model = buildKriging,
                       modelControl = list(algTheta=optimizerLikelihood, useLambda=TRUE, reinterpolate=TRUE),
                       optimizer = optimizerForSPOT,
                       optimizerControl = list(funEvals=150),
                       designControl = list(size=10),
                       seedSPOT = seed
    )
    
    # design Type 
    designTypeLHD <- 1
    designTypeUniform <- 2
    
    # design Type 
    minDesignSize <- max(4, floor(objFunctionBudget/4))
    maxDesignSize <- min(50, objFunctionBudget - 3)
    
    lowerSPO <- c(minDesignSize, designTypeLHD)
    upperSPO <- c(maxDesignSize, designTypeUniform)
    
    ## call SPO 
    spotResult <- SPOT::spot(fun = tuningInterface,
                             lower = lowerSPO,
                             upper = upperSPO,
                             control = spotConfig,
                             lowerObj = lowerObj,
                             upperObj = upperObj,
                             objFunction = objFunction,
                             objFunctionBudget = objFunctionBudget)
    
    ## return xBest, as a named list
    result <- list()
    result['designSize'] <- spotResult$xbest[1]
    result['designType'] <- spotResult$xbest[2]

    print("Tuned KrigingBP: ")
    print(paste(mapply(paste, names(result), as.numeric(result)), collapse=" / "))
    return(result)
  }
  
  ## tune Kriging with Spot
  tuneKrigingEI <- function(tuningInterface = NULL, objFunction = NULL, seed = NULL) {
    print('tuning KrigingEI')
    set.seed(seed)
    
    # configure spot
    spotConfig <- list(funEvals = tuningBudget,
                       types = c("integer", "factor"), # factor, number
                       model = buildKriging,
                       # model = buildKriging,
                       # modelControl = list(algTheta=optimizerLikelihood, useLambda=TRUE, reinterpolate=TRUE),
                       optimizer = optimizerForSPOT,
                       optimizerControl = list(funEvals=150),
                       designControl = list(size=10),
                       seedSPOT = seed
    )
    
    
    # design Type 
    designTypeLHD <- 1
    designTypeUniform <- 2
    
    # design Type 
    minDesignSize <- max(4, floor(objFunctionBudget/4))
    maxDesignSize <- min(50, objFunctionBudget - 3)
    lowerSPO <- c(minDesignSize, designTypeLHD)
    upperSPO <- c(maxDesignSize, designTypeUniform)
    
    ## call SPO 
    spotResult <- SPOT::spot(fun = tuningInterface,
                             lower = lowerSPO,
                             upper = upperSPO,
                             control = spotConfig,
                             lowerObj = lowerObj,
                             upperObj = upperObj,
                             objFunction = objFunction,
                             objFunctionBudget = objFunctionBudget)
    
    ## return xBest, as a named list
    result <- list()
    result['designSize'] <- spotResult$xbest[1]
    result['designType'] <- spotResult$xbest[2]
    
    print("Tuned KrigingEI: ")
    print(paste(mapply(paste, names(result), as.numeric(result)), collapse=" / "))
    
    return(result)
  }
  
  ## tune RandomForest with Spot
  tuneRandomForest <- function(tuningInterface = NULL, objFunction = NULL, seed = NULL) {
    print('tuning RandomForest')
    set.seed(seed)
    
    # configure spot
    spotConfig <- list(funEvals = tuningBudget,
                       types = c("integer", "factor"), # factor, number
                       model = buildKriging,
                       # modelControl = list(algTheta=optimizerLikelihood, useLambda=TRUE, reinterpolate=TRUE),
                       optimizer = optimizerForSPOT,
                       optimizerControl = list(funEvals=150),
                       designControl = list(size=10),
                       seedSPOT = seed
    )
    
    
    # design Type 
    designTypeLHD <- 1
    designTypeUniform <- 2
    
    # design Type 
    minDesignSize <- max(4, floor(objFunctionBudget/4))
    maxDesignSize <- min(50, objFunctionBudget - 3)
    lowerSPO <- c(minDesignSize, designTypeLHD)
    upperSPO <- c(maxDesignSize, designTypeUniform)
    
    ## call SPO 
    spotResult <- SPOT::spot(fun = tuningInterface,
                             lower = lowerSPO,
                             upper = upperSPO,
                             control = spotConfig,
                             lowerObj = lowerObj,
                             upperObj = upperObj,
                             objFunction = objFunction,
                             objFunctionBudget = objFunctionBudget)
    
    ## return xBest, as a named list
    result <- list()
    result['designSize'] <- spotResult$xbest[1]
    result['designType'] <- spotResult$xbest[2]
    
    print("Tuned KrigingEI: ")
    print(paste(mapply(paste, names(result), as.numeric(result)), collapse=" / "))
    
    return(result)
  }
  
  ## tune LBFGSB with Spot
  tuneLBFGSB <- function(tuningInterface = NULL, objFunction = NULL, seed = NULL) {
    print('tuning L-BFGS-B by doing nothing')
    result <- list()
    return(result)
  }
  
  ## tune LM with Spot
  tuneLM <- function(tuningInterface = NULL, objFunction = NULL, seed = NULL) {
    print('tuning LM by doing nothing')
    result <- list()
    return(result)
  }
  
  res <- list(tuneLhd, tuneDE, tuneKrigingBP, tuneKrigingEI, tuneRandomForest, tuneLBFGSB, tuneLM)
}

###################################################################################
#' Another numerical optimizer. Directly calls nloptr. 
#' 
#' @param x is a point (vector) in the decision space of fun
#' @param fun is the target function of type y = f(x, ...)
#' @param lower is a vector that defines the lower boundary of search space
#' @param upper is a vector that defines the upper boundary of search space
#' @param control is a list of additional settings, defaults to:
#'  list(funEvals=200, method="NLOPT_LN_NELDERMEAD", reltol=1e-4, verbosity=0)
#' 
#' @return This function returns a list with:
#' xbest parameters of the found solution
#' ybest target function value of the found solution
#' count number of evaluations of fun
###################################################################################
optimizerForSPOT <- function(x=NULL, fun, lower, upper, control, ...){
  ## generate random start point
  if(is.null(x)) 
    x <- lower + runif(length(lower)) * (upper-lower)
  else
    x <- x[1,] #requires vector start point

  con <- list(funEvals=200, method="NLOPT_LN_NELDERMEAD", reltol=1e-4, verbosity=0) # NLOPT_GN_DIRECT_L
  con[names(control)] <- control
  control <- con
  
  # wrapper for target function: vector to matrix	
  f2 <- function(x){
    x <- matrix(data=x, nrow = 1)
    fun(x)
  }
  
  dots <- list(...) 
  if(length(dots) > 0) {
    cat("The arguments in ... are\n")
    print(dots)
  }
  
  opts = list(algorithm = control$method, 
              maxeval = control$funEvals, 
              ftol_rel = control$reltol, 
              xtol_rel = -Inf, 
              print_level = control$verbosity)
  
  # call optimizer
  res <- nloptr::nloptr(x, f2, lb = lower, ub = upper, opts = opts, ...) 
  res$count <- res$iterations
  res$xbest <- matrix(data=res$solution, nrow = 1)
  res$ybest <- res$objective
  
  return(res)
}

###################################################################################
#' Numerical optimizer, useful for MLE (e.g. during Kriging model fit). 
#' Calls CEGO::optimInterface
#' 
#' @param x is a point (vector) in the decision space of fun
#' @param fun is the target function of type y = f(x, ...)
#' @param lower is a vector that defines the lower boundary of search space
#' @param upper is a vector that defines the upper boundary of search space
#' @param control is a list of additional settings, defaults to:
#'  list(method="NLOPT_GN_DIRECT_L",funEvals=400,reltol=1e-8)
#' 
#' @return This function returns a list with:
#' xbest parameters of the found solution
#' ybest target function value of the found solution
#' count number of evaluations of fun
###################################################################################
optimizerLikelihood <- function(x = NULL, fun, lower, upper, control, ...){
  # print(x)
  # ## generate random start point
  # if(is.null(x)) 
  #   x <- lower + runif(length(lower)) * (upper-lower)
  # else
  #   x <- x[1,] #requires vector start point
  # print(x)
  CEGO::optimInterface(x,fun,lower,upper,control=list(method="NLOPT_GN_DIRECT_L",funEvals=400,reltol=1e-8),...)
}
