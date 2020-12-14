###################################################################################
#'
#' File covers several functions related to optimizers and tuning via SPOT
#' 
###################################################################################


###################################################################################
#' Get a list of parameters for optimizers, corresponding to 
#' the list of feasiblePipelines
#' @param funEvals nr of function evaluations for each parameter list 
#' 
#' @return list of names parameter values for each optimizer
###################################################################################
getPipelineConfigurations <- function(funEvals = NULL) {
  force(funEvals)
  listPipelineControls <- list()
  listPipelineControls[['Generalized SA']] <- list(temp = 100, qv = 2.56, qa=-5, max.call=funEvals)
  listPipelineControls[['Random Search']] <- list(funEvals = funEvals)
  listPipelineControls[['Lhd']] <- list(funEvals = funEvals, retries = 100)
  
  popsize <- 5
  itermax <- floor(((funEvals-popsize)/popsize)) 
  listPipelineControls[['Differential Evolution']]  <- list(funEvals = funEvals, itermax = itermax, popsize = popsize, F = 0.8, CR = 0.5, strategy = 2, c = 0.5)
  mue <- 10
  if(mue >= funEvals) {
    mue <- funEvals/2
  }
  listPipelineControls[['Evolution Strategy']] <- list(funEvals = funEvals, mue = mue)
  listPipelineControls[['Kriging']] <- list(funEvals = funEvals, model = buildKriging, modelControl = list(target="y"), designControl = list(size=7))
  listPipelineControls[['Kriging EI']] <- list(funEvals = funEvals, model = buildKriging, modelControl = list(target="ei"), designControl = list(size=7))
  listPipelineControls[['Random Forest']] <- list(funEvals = funEvals, model = buildRandomForest, designControl = list(size=7))
  listPipelineControls[['L-BFGS-B']] <- list(funEvals = funEvals, lmm=5)
  listPipelineControls[['Linear Model']] <- list(funEvals = funEvals, model = buildLM, optimizer = optimLBFGSB, designControl = list(size=7))  
  return(listPipelineControls)
}



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
getFeasiblePipelines <- function(lower = NULL, upper = NULL) {
  # init result list
  listPipelines <- list()
  
  listPipelines[['Generalized SA']] <- function(objFunction = NULL, ctrl = NULL, seed = NULL) {
    tic("GenSA")
    force(seed)
    set.seed(seed)
    
    temp <- ctrl$temp
    qv <- ctrl$qv # 2.62
    qa <- ctrl$qa # -5
    maxEval <- ctrl$max.call
    res <- NULL
    memProfile <- profmem({
      res <- GenSA(lower = lower, upper = upper, fn = objFunction,
            control=list(max.call=maxEval, temperature=temp, visiting.param=qv, acceptance.param=qa, seed = seed))
      # rename consistently
      res <- list(ybest=res$value, xbest=res$par, count=res$counts)
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
  
  listPipelines[['Random Search']] <- function(objFunction = NULL, ctrl = NULL, seed = NULL) {
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
  
  listPipelines[['Lhd']] <- function(objFunction = NULL, ctrl = NULL, seed = NULL) {
    tic("Lhd")
    force(seed)
    set.seed(seed)

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
  
  listPipelines[['Differential Evolution']] <- function(objFunction = NULL, ctrl = NULL, seed = NULL) {
    tic("DEoptim")
    force(seed)
    set.seed(seed)

    budget <- ctrl$funEvals
    popsize <- ctrl$popsize
    c <- ctrl$c
    strategy <- ctrl$strategy
    Fval <- ctrl$F
    CR <- ctrl$CR
    itermax <- ctrl$itermax

    if(itermax < 1) {
      itermax <- 1
      warning("Itermax ist 1 oder kleiner: Auf 1 korrigiert (übersteigt aber Budget)")
    }
    
    print(paste("budget", budget, "popsize", popsize, "itermax", itermax, sep = " ", collapse = NULL))
    
    res <- NULL
    memProfile <- profmem({
      # call DEoptim
      res <- DEoptim::DEoptim(fn = objFunction, 
                              lower = lower, 
                              upper = upper, 
                              control = list(NP=popsize, itermax=itermax, c=c, strategy=strategy, F=Fval, CR=CR ,reltol=1e-10, trace=FALSE))

      # save interesting result values
      nfEvals <- popsize + (popsize * itermax)
      res <- list(ybest=res$optim$bestval, xbest=res$optim$bestmem, count=nfEvals)
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
  
  listPipelines[['Kriging']] <- function(objFunction = NULL, ctrl = NULL, seed = NULL) {
    tic("KrigingBP")
    force(seed)
    set.seed(seed)
    ctrl['seedSPOT'] <- seed

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
  
  listPipelines[['Kriging EI']] <- function(objFunction = NULL, ctrl = NULL, seed = NULL) {
    tic("KrigingEI")
    force(seed)
    set.seed(seed)
    ctrl['seedSPOT'] <- seed

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
  
  listPipelines[['Random Forest']] <- function(objFunction = NULL, ctrl = NULL, seed = NULL) {
    tic("RF")
    force(seed)
    set.seed(seed)
    ctrl['seedSPOT'] <- seed

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
  
  listPipelines[['L-BFGS-B']] <- function(objFunction = NULL, ctrl = NULL, seed = NULL) {
    tic("LBFGSB")
    force(seed)
    set.seed(seed)
    #ctrl['seedSPOT'] <- seed
    
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
  
  listPipelines[['Linear Model']] <- function(objFunction = NULL, ctrl = NULL, seed = NULL) {
    tic("LM")
    force(seed)
    set.seed(seed)
    ctrl['seedSPOT'] <- seed

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
  return(listPipelines)
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

  # init list of tuning interfaces 
  listTuningInterfaces <- list()
  
  listTuningInterfaces[['Generalized SA']] <- function(algpar, objFunction, objFunctionBudget, lowerObj, upperObj){
    print("Tuning GenSA")
    # create result list
    resultList <- NULL
    
    # budget for each optimization run
    budget <- objFunctionBudget
    
    # algpar is matrix of row-wise settings
    for (i in 1:nrow(algpar)) {
      temp <- algpar[i,1]
      qv <- algpar[i,2]
      qa <- algpar[i,3]
      
      # requires random starting point
      par <- lowerObj + runif(length(lowerObj)) * (upperObj-lowerObj)
      
      res <- GenSA::GenSA(fn = objFunction, 
                          par = par,
                          lower = lowerObj, 
                          upper = upperObj, 
                          control = list(threshold.stop = -Inf, 
                                         max.call = budget, 
                                         temperature = temp, 
                                         visiting.param = qv,
                                         acceptance.param = qa))
      resultList <- c(resultList, res$value)
    }
    
    return(resultList)
  }

  listTuningInterfaces[['Random Search']] <- function(algpar, objFunction, objFunctionBudget, lowerObj, upperObj) {
  }
  
  listTuningInterfaces[['Lhd']] <- function(algpar, objFunction, objFunctionBudget, lowerObj, upperObj) {
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
  
  listTuningInterfaces[['Differential Evolution']]  <- function(algpar, objFunction, objFunctionBudget, lowerObj, upperObj) {
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
  
  
  listTuningInterfaces[['Kriging']]  <- function(algpar, lowerObj, upperObj, objFunction, objFunctionBudget) {
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
  
  listTuningInterfaces[['Kriging EI']]  <- function(algpar, lowerObj, upperObj, objFunction, objFunctionBudget) {
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
  
  listTuningInterfaces[['Random Forest']]  <- function(algpar, objFunction, objFunctionBudget, lowerObj, upperObj) {
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
  
  
  listTuningInterfaces[['L-BFGS-B']] <- function(algpar, objFunction, objFunctionBudget, lowerObj, upperObj) {
    print("Tuning L-BFGS-B")
    resultList <- NULL
    budget <- objFunctionBudget
    for (i in 1:nrow(algpar)) { 
      lmm <- algpar[i, 1]
      spotConfig <- list(funEvals = budget, lmm = lmm)
      res <- SPOT::optimLBFGSB(fun = objFunction, 
                               lower = lowerObj, 
                               upper = upperObj, 
                               control = spotConfig)
      resultList <- c(resultList, res$ybest)
    }
    return(resultList)
  }
  
  listTuningInterfaces[['Linear Model']] <- function(algpar, objFunction, objFunctionBudget, lowerObj, upperObj) {
  }
 
  return(listTuningInterfaces)
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
#  lowerObj <- force(lowerObj)
#  upperObj <- force(upperObj)
#  objFunctionBudget <- force(objFunctionBudget)
#  tuningBudget <- force(tuningBudget)
  
  # init result list
  listSpotTuningCalls <- list()
  
  listSpotTuningCalls[['Generalized SA']] <- function(tuningInterface = NULL, objFunction = NULL, seed = NULL) {
    print('tune GenSA')
    force(seed)
    set.seed(seed)

    # configure spot
    spotConfig <- list(funEvals = tuningBudget,
                       types = c("integer", "numeric", "numeric"), # integer
                       model = buildKriging,
                       optimizer = optimizerForSPOT,
                       optimizerControl = list(funEvals=150),
                       designControl = list(size=10),
                       seedSPOT = seed
    )

    ## https://journal.r-project.org/archive/2013/RJ-2013-002/RJ-2013-002.pdf
    # max.call - funEval
    # between 2 and 3 for qv and any value < 0 for qa
    # defaults: qv 2.65 ; qa -5
    ## temp, qv, qa
    lowerSPO <- c(1,   2, -1000)
    upperSPO <- c(100, 3, 1)

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
    result['temp'] <- spotResult$xbest[1]
    result['qv'] <- spotResult$xbest[2]
    result['qa'] <- spotResult$xbest[3]

    print("Tuned GenSA: ")
    print(paste(mapply(paste, names(result), as.numeric(result)), collapse=" / "))
    
    return(result)
  }
  
  ## tune LHD with Spot
  listSpotTuningCalls[['Lhd']] <- function(tuningInterface = NULL, objFunction = NULL, seed = NULL) {
    print("Tune optimLhd")

    force(seed)
    set.seed(seed)
    spotConfig <- list(funEvals = tuningBudget,
                       types = c("integer"), # integer
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
  
  listSpotTuningCalls[['Differential Evolution']] <- function(tuningInterface = NULL, objFunction = NULL, seed = NULL) {
    print("Tune optimDE")
    #print(paste("objFunctionBudget: ", objFunctionBudget, collapse = NULL, sep = ""))
    #print(paste("tuningBudget: ", tuningBudget, collapse = NULL, sep = ""))
    force(seed)
    set.seed(seed)
    
    lowerNP <- 4 # dim * 2
    upperNP <- floor(objFunctionBudget/2)
    # upperNP <- min(dim*15, objFunctionBudget)
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
  listSpotTuningCalls[['Kriging']] <- function(tuningInterface = NULL, objFunction = NULL, seed = NULL) {
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
  listSpotTuningCalls[['Kriging EI']] <- function(tuningInterface = NULL, objFunction = NULL, seed = NULL) {
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
  listSpotTuningCalls[['Random Forest']] <- function(tuningInterface = NULL, objFunction = NULL, seed = NULL) {
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
  listSpotTuningCalls[['L-BFGS-B']] <- function(tuningInterface = NULL, objFunction = NULL, seed = NULL) {
    print('tuning L-BFGS-B lmm parameter')
    force(seed)
    set.seed(seed)
    spotConfig <- list(funEvals = tuningBudget,
                       types = c("integer"), # integer
                       model = buildKriging,
                       optimizer = optimizerForSPOT,
                       optimizerControl = list(funEvals=150),
                       designControl = list(size=10),
                       seedSPOT = seed
    )
    # range repetitions
    lowerSPO <- c(1)
    upperSPO <- c(10)
    spotResult <- SPOT::spot(fun = tuningInterface,
                             lower = lowerSPO,
                             upper = upperSPO,
                             control = spotConfig,
                             lowerObj = lowerObj,
                             upperObj = upperObj,
                             objFunction = objFunction,
                             objFunctionBudget = objFunctionBudget)
    result <- list()
    result['lmm'] <- spotResult$xbest[1]
    print(paste("Tuned lmm: ", result['lmm'], collapse = NULL, sep = ""))
    return(result)
  }
  
  ## tune LM with Spot
  listSpotTuningCalls[['Linear Model']] <- function(tuningInterface = NULL, objFunction = NULL, seed = NULL) {
    print('tuning LM by doing nothing')
    result <- list()
    return(result)
  }
  
  ## tune RS with Spot doing nothing
  listSpotTuningCalls[['Random Search']] <- function(tuningInterface = NULL, objFunction = NULL, seed = NULL) {
    print('tuning RS by doing nothing')
    result <- list()
    return(result)
  }
  
  listSpotTuningCalls[['Evolution Strategy']] <- function(tuningInterface = NULL, objFunction = NULL, seed = NULL) {
    print('tuning ES by doing nothing')
    result <- list()
    return(result)
  }
  
  return(listSpotTuningCalls)
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
  
  # print nr of function evaluations used to otpimize model
  # if(res$count != control$funEvals)
  # print(paste('optimEvals: ', res$count, '/', control$funEvals, sep = ""))
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
  # print("blubb")
  # print(x)
  # ## generate random start point
  # if(is.null(x)) 
  #   x <- lower + runif(length(lower)) * (upper-lower)
  # else
  #   x <- x[1,] #requires vector start point
  # print(x)
  CEGO::optimInterface(x,fun,lower,upper,control=list(method="NLOPT_GN_DIRECT_L",funEvals=400,reltol=1e-8),...)
}

