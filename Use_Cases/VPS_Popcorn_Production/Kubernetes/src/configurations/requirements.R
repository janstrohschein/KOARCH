library(devtools)

install_version("CEGO", version = "2.4.0", repos = "http://cran.us.r-project.org")
install_version("data.table", version = "1.13.0", repos = "http://cran.us.r-project.org")
install_version("nloptr", version = "1.2.2.0", repos = "http://cran.us.r-project.org")
install_version("SPOT", version = "2.0.6", repos = "http://cran.us.r-project.org")
withr::with_libpaths(new = "/usr/local/lib/R/site-library", install_github("martinzaefferer/COBBS", upgrade="never"))
