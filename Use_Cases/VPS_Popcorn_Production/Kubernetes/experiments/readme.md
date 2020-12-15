# VPS Popcorn Production
This section describes extended experiments using data-driven simulations to perform benchmark of optimization algorithms and choose
promising algorithms to solve the VPS problem.

The R-scripts in this section can be used to reproduce the results of the publication "Cognitive Capabilities for the CAAI in Cyber-Physical Production Systems", see [our pre-print](https://arxiv.org/abs/2012.01823).

## main01.R
This script contains the configuration and runs the experiments.
Considered algorithms can be configured in the script 'feasiblePipelines.R'.
By default, Kriging, Random forest, DEOptim, GenSA, L-BFGS-B, and random search (as a baseline) are chosen.
As a result, a data.frame is stored inside an RData file in the 'results' subdirectory.
It can be used by the plot script (see description below) to produce the figures.

## plots01.R
The plot script produce the figures presented in the publication as PDF files.
It takes the result data.frame produced by the main script and stores the PDF figures in the 'result' subdirectory.

See, e.g., cpu, memory, and achieved objective function y:\
[Cpu consumption](results/2020-12-14_cpu.pdf)\
[Memory consumption](results/2020-12-14_mem.pdf)\
[Achieved objective](results/2020-12-14_y.pdf)
