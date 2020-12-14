###################################################################################
#' This file contains the code to plot the results shown in the publication
#' "Cognitive Capabilities for the
#' CAAI in Cyber-Physical Production Systems" available
#' at arXiv: https://arxiv.org/abs/2012.01823
#' @author Andreas Fischbach (andreas.fischbach@th-koeln.de)
###################################################################################

# clear env
rm(list = ls())

# plot stuff
if(!require(ggplot2)) {
  install.packages(ggplot2)
  library(ggplot2)
}
if(!require(gridExtra)) {
  install.packages(gridExtra)
  library(gridExtra)
}

if(!require(plyr)) {
  install.packages(plyr)
  library(plyr)
}

source("misc.R")

# Specify here the filename of the result data.frame
filename <- "results/2020-12-14VPS_1rep10Budget20tuneFALSE.RData"

# loads results data.frame into environment
load(filename)

# short summary
summary(results)

data <- results

aggregationFunction <- mean

# subsample usecase as groundtruth(vps) and simulations
vps <- data[data$usecase == data$objective, ]
sim <- data[data$usecase != data$objective, ]
budgetlist <- unique(vps$budget)

# (0) plot development of simple y/mem/cpu over time on groundtruth
yVpsMed <- data.frame()# data[data$usecase == data$objective, ]

# (1) med aggregation of metric first (over repetitions for each budget)
for(i in budgetlist) {
  # j <- repetitions
  tmp <- vps[vps$budget == i, ]

  # y, cpu, mem -> normalisieren
  tmp$yNorm <- normalize(tmp$y)
  tmp$cpuNorm <- normalize(tmp$cpu)
  tmp$memNorm <- normalize(tmp$mem)

  # median aggregation over repetitions
  medAgg <- aggregate(y ~ optimizer, data = tmp, FUN = aggregationFunction)
  medAgg$cpu <- aggregate(cpu ~ optimizer, data = tmp, FUN = aggregationFunction)$cpu
  medAgg$mem <- aggregate(mem ~ optimizer, data = tmp, FUN = aggregationFunction)$mem

  medAgg$rankY <- rank(medAgg$y)
  medAgg$rankCpu <- rank(medAgg$cpu)
  medAgg$rankMem <- rank(medAgg$mem)
  medAgg$budget <- rep(i, nrow(medAgg))
  medAgg$objective <- rep(unique(tmp$objective), nrow(medAgg))

  yVpsMed <- rbind(yVpsMed, medAgg)
}

yVpsMed$optimizer <- as.factor(yVpsMed$optimizer)

  filenameY <- paste("results/", Sys.Date(), "_y.pdf", sep = "")
  pdf(file = filenameY)
  ggplot(aes(x = budget, y = y, group = optimizer), data = yVpsMed) +
    geom_line(aes(linetype = optimizer, color = optimizer)) +
    geom_point(aes(shape = optimizer, color = optimizer), size=3) +
    scale_shape_manual(values=1:nlevels(yVpsMed$optimizer)) +
    theme_linedraw() +
    theme_light() +
    scale_x_continuous(breaks = seq(budgetlist[1],budgetlist[length(budgetlist)], by=2)) +
    xlab("Production cycle") +
    ylab("Objective function value y")
  dev.off()

  filenameMem <- paste("results/", Sys.Date(), "_mem.pdf", sep = "")
  pdf(file = filenameMem)
  ggplot(aes(x = budget, y = mem, group = optimizer), data = yVpsMed) +
    geom_line(aes(linetype = optimizer, color = optimizer)) +
    geom_point(aes(shape = optimizer, color = optimizer), size=3) +
    scale_shape_manual(values=1:nlevels(yVpsMed$optimizer)) +
    theme_linedraw() +
    theme_light() +
    scale_x_continuous(breaks = seq(budgetlist[1],budgetlist[length(budgetlist)], by=2)) +
    xlab("Production cycle") +
    ylab("Memory usage (MB)")
  dev.off()

  filenameCpu <- paste("results/", Sys.Date(), "_cpu.pdf", sep = "")
  pdf(file = filenameCpu)
  ggplot(aes(x = budget, y = cpu, group = optimizer), data = yVpsMed) +
    geom_line(aes(linetype = optimizer, color = optimizer)) +
    geom_point(aes(shape = optimizer, color = optimizer), size=3) +
    scale_shape_manual(values=1:nlevels(yVpsMed$optimizer)) +
    theme_linedraw() +
    theme_light() +
    scale_x_continuous(breaks = seq(budgetlist[1],budgetlist[length(budgetlist)], by=2)) +
    xlab("Production cycle") +
    ylab("Cpu usage (s)")
  dev.off()

# (2) rank based correlation analysis
ranks <- data.frame()

for(i in budgetlist) {
  # (0) subselect the results from the groundtruth
	tmpVps <- vps[vps$budget == i, ]

	# (1) y, cpu, mem -> mean aggregation
	medAgg <- aggregate(y ~ optimizer, data = tmpVps, FUN = aggregationFunction)
	medAgg$cpu <- aggregate(cpu ~ optimizer, data = tmpVps, FUN = aggregationFunction)$cpu
	medAgg$mem <- aggregate(mem ~ optimizer, data = tmpVps, FUN = aggregationFunction)$mem

	# (2) normalization of aggregated (over repetitions) performance
	medAgg$yNorm <- normalize(medAgg$y)
	medAgg$cpuNorm <- normalize(medAgg$cpu)
	medAgg$memNorm <- normalize(medAgg$mem)

	# (3) add budget and objective for comparisons
	medAgg$budget <- rep(i, nrow(medAgg))
	medAgg$objective <- rep(unique(tmpVps$objective), nrow(medAgg))
	medAgg$usecase <- rep(unique(data$usecase), nrow(medAgg))
	medAgg$rankY <- rank(medAgg$yNorm)
	ranks <- rbind(ranks, medAgg)

	# (0) subselect the results from the simulations
	tmpSim <- sim[sim$budget == i, ]

	# (1) y, cpu, mem -> mean aggregation
	medAgg <- aggregate(y ~ optimizer, data = tmpSim, FUN = aggregationFunction)
	medAgg$cpu <- aggregate(cpu ~ optimizer, data = tmpSim, FUN = aggregationFunction)$cpu
	medAgg$mem <- aggregate(mem ~ optimizer, data = tmpSim, FUN = aggregationFunction)$mem

	# (2) normalization of aggregated (over repetitions) performance
	medAgg$yNorm <- normalize(medAgg$y)
	medAgg$cpuNorm <- normalize(medAgg$cpu)
	medAgg$memNorm <- normalize(medAgg$mem)

	# (3) add budget and objective for comparisons
	medAgg$budget <- rep(i, nrow(medAgg))
	medAgg$objective <- rep(unique(tmpSim$objective), nrow(medAgg))
	medAgg$usecase <- rep(unique(data$usecase), nrow(medAgg))
	medAgg$rankY <- rank(medAgg$yNorm)
	ranks <- rbind(ranks, medAgg)
}

sim <- ranks[ranks$objective != ranks$usecase,]
sim$optimizer <- as.factor(sim$optimizer)
vps <- ranks[ranks$objective == ranks$usecase,]
vps$optimizer <- as.factor(vps$optimizer)

## ----- plot normalized performs over budget

pdf(file = paste("results/", Sys.Date(), "_rankYVps.pdf", sep = ""))
  ggplot(aes(x = budget, y = rankY, group = optimizer), data = vps) +
    geom_line(aes(linetype = optimizer, color = optimizer)) +
    geom_point(aes(shape = optimizer, color = optimizer), size=3) +
    scale_shape_manual(values=1:nlevels(vps$optimizer)) +
    theme_linedraw() +
    theme_light() +
    scale_x_continuous(breaks = seq(budgetlist[1],budgetlist[length(budgetlist)], by=2)) +
    xlab("Production cycle") +
    ylab("Rank Performance (y) on ground-truth")
  dev.off()

pdf(file = paste("results/", Sys.Date(), "_rankYSim.pdf", sep = ""))
  ggplot(aes(x = budget, y = rankY, group = optimizer), data = sim) +
    geom_line(aes(linetype = optimizer, color = optimizer)) +
    geom_point(aes(shape = optimizer, color = optimizer), size=3) +
    scale_shape_manual(values=1:nlevels(sim$optimizer)) +
    theme_linedraw() +
    theme_light() +
    scale_x_continuous(breaks = seq(budgetlist[1],budgetlist[length(budgetlist)], by=2)) +
    xlab("Production cycle") +
    ylab("Rank Performance (y) on simulations")
  dev.off()

# compute pearson's r coefficient
cor.test(sim$yNorm, vps$yNorm, method = "pearson") # spearman, kendall

ySimMed <- data.frame()

for(i in budgetlist) {
  simDataBudget <- data[data$objective != data$usecase, ]
  simDataBudget <- simDataBudget[simDataBudget$budget == i, ]

  # compute reference (unit) via Random Search
  randomSearch <- simDataBudget[simDataBudget$optimizer == 'Random Search', ]
  others <- simDataBudget[simDataBudget$optimizer != 'Random Search', ]
  reference <- aggregate(cpu ~ optimizer, data = randomSearch, FUN = aggregationFunction)
  reference$mem <- aggregate(mem ~ optimizer, data = randomSearch, FUN = aggregationFunction)$mem
  reference$y <- aggregate(y ~ optimizer, data = randomSearch, FUN = aggregationFunction)$y

  # compute mean consumption and performance per algorithm over rep
  meanSim <- aggregate(y ~ optimizer, data = others, FUN = aggregationFunction)
  meanSim$cpu <- aggregate(cpu ~ optimizer, data = others, FUN = aggregationFunction)$cpu
  meanSim$mem <- aggregate(mem ~ optimizer, data = others, FUN = aggregationFunction)$mem
  # add meta data (budget and test instance)
  meanSim$budget <- rep(i, nrow(meanSim))
  meanSim$objective <- rep(unique(simDataBudget$objective), nrow(meanSim))

  # remove optims worse than randoms search
  meanSim <- meanSim[meanSim$y < reference$y,]

  # compute mem, y, cpu divided by reference (baseline)
  meanSim$relY <- (reference$y - meanSim$y) / reference$y
  meanSim$relCpu <- meanSim$cpu / reference$cpu
  meanSim$relMem <- meanSim$mem / reference$mem

  meanSim$relYNorm <- normalize(meanSim$relY)
  meanSim$relCpuNorm <- 1-normalize(meanSim$relCpu)
  meanSim$relMemNorm <- 1-normalize(meanSim$relMem)

  meanSim$referenceY <- rep(reference$y, nrow(meanSim))
  meanSim$referenceMem <- rep(reference$mem, nrow(meanSim))
  meanSim$referenceCpu <- rep(reference$cpu, nrow(meanSim))

  # compute weighted aggregation
  weightY <- 0.8
  weightC <- 0.1
  weightM <- 0.1

  # equal weights first
  meanSim$aggY0 <- meanSim$relYNorm + meanSim$relCpuNorm + meanSim$relMemNorm
  meanSim$aggRank0 <- rank(meanSim$aggY0)

  # 0.8/0.1/0.1 performance (y) focus
  meanSim$aggY1 <- (weightY * meanSim$relYNorm) + (weightC * meanSim$relCpuNorm) + (weightM * meanSim$relMemNorm)
  meanSim$aggRank1 <- rank(meanSim$aggY1)

  weightY <- 0.5
  weightC <- 0.25
  weightM <- 0.25

  # 0.5/0.25/0.25 performance decreased, resources increased
  meanSim$aggY2 <- (weightY * meanSim$relYNorm) + (weightC * meanSim$relCpuNorm) + (weightM * meanSim$relMemNorm)
  meanSim$aggRank2 <- rank(meanSim$aggY2)

  ySimMed <- rbind(ySimMed, meanSim)
}

print(ySimMed[, c('optimizer', 'budget', 'y', 'cpu', 'mem', 'relYNorm', 'relCpuNorm', 'relMemNorm', 'aggRank0', 'aggRank1', 'aggRank2')])

# left plot for scenario1 (0.8,0.1,0.1)
# legend is left out
pdf(file = paste("results/", Sys.Date(), "_aggRanksScen1.pdf", sep = ""))
ggplot(aes(x = budget, y = aggRank1, group = optimizer), data = ySimMed) +
  geom_line(aes(linetype = optimizer, color = optimizer)) +
  geom_point(aes(shape = optimizer, color = optimizer), size=3) +
  scale_shape_manual(values=1:nlevels(sim$optimizer)) +
  theme_linedraw() +
  theme_light() +
  scale_x_continuous(breaks = seq(budgetlist[1],budgetlist[length(budgetlist)], by=2)) +
  xlab("Production cycle") +
  ylab("Aggregated Rank Performance (y) on simulations") +
  theme(legend.position="none")
dev.off()

# right plot for scenario1 (0.5,0.25,0.25)
pdf(file = paste("results/", Sys.Date(), "_aggRanksScen2.pdf", sep = ""))
ggplot(aes(x = budget, y = aggRank2, group = optimizer), data = ySimMed) + # rankYAgg
  geom_line(aes(linetype = optimizer, color = optimizer)) +
  geom_point(aes(shape = optimizer, color = optimizer), size=3) +
  scale_shape_manual(values=1:nlevels(sim$optimizer)) +
  theme_linedraw() +
  theme_light() +
  scale_x_continuous(breaks = seq(budgetlist[1],budgetlist[length(budgetlist)], by=2)) +
  xlab("Production cycle") +
  ylab("Aggregated Rank Performance (y) on simulations")
dev.off()
