
import numpy as np
import pandas as pd

from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.gaussian_process import kernels

import rpy2.robjects as robjects
from rpy2.robjects import pandas2ri
from rpy2.robjects.conversion import localconverter

N_INITIAL_DESIGN = 5
X_MIN = 4000.0
X_MAX = 10100.0

# get groundthrouth data 
seperator=";"
decimal_sign=","
data_path = "data/vpsFeatures.csv"
extract_columns = ["conveyorRuntimeMean","yAgg"]
extract_columns_types = float
vps_df = pd.read_csv(
            data_path,
            sep=seperator,
            usecols=extract_columns,
            dtype=extract_columns_types,
            decimal=decimal_sign,)
vps_df = vps_df.drop_duplicates()

# df for simulations
df = vps_df[['conveyorRuntimeMean', 'yAgg']]
df = df.rename(columns={"conveyorRuntimeMean": "x", "yAgg": "y"})

# create sim function
r = robjects.r
r.source('L3_PC_Simulation.R')
pandas2ri.activate()
generateTestFunctions = robjects.r["generateTestFunctions"]
# test instance according to VPS data 
testInstance = generateTestFunctions(df, 5)

# get x/y from testInstance
# sample test instance: equidistant, 10 points
X = np.linspace(X_MIN, X_MAX, num=10)
# evaluate X on test instance
y = testInstance(X)

kernel = 1.0 * kernels.RationalQuadratic(length_scale=1.0, alpha=0.1)
model = GaussianProcessRegressor(kernel=kernel)
model = model.fit(X.reshape(-1, 1), y)

X = np.linspace(X_MIN + 1000, X_MAX - 1000, num=3).reshape(-1, 1)
pred_y = model.predict(X)

print(pred_y)





