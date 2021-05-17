from collections import namedtuple
import pandas as pd
import numpy as np

from sklearn.model_selection import LeaveOneOut, cross_val_predict
from sklearn.metrics import mean_squared_error as mse
from sklearn.metrics import mean_absolute_error as mae
from sklearn.metrics import r2_score as r2
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.gaussian_process import kernels

from scipy.optimize import differential_evolution, dual_annealing, minimize

class ObjectiveFunction:
    def __init__(self):
        self.model = None
        self.X = None
        self.y = None

    def load_data(self, data_path, x_columns, y_columns, seperator=";", decimal_sign=","):

        # extract_columns = ["conveyorRuntimeMean", "yAgg"]
        extract_columns = list(x_columns.keys()) + list(y_columns.keys())
        # extract_columns_types = {"conveyorRuntimeMean": float, "yAgg": float}
        extract_columns_types = {**x_columns, **y_columns}

        vps_df = pd.read_csv(
            data_path,
            sep=seperator,
            usecols=extract_columns,
            dtype=extract_columns_types,
            decimal=decimal_sign,
        )

        vps_df = vps_df.drop_duplicates()

        self.X = np.array(vps_df[x_columns.keys()]).reshape(-1, 1)
        self.y = np.array(vps_df[y_columns.keys()])

        return True

    def fit_model(self):

        kernel = 1.0 * kernels.RationalQuadratic(length_scale=1.0, alpha=0.1)

        self.model = GaussianProcessRegressor(kernel=kernel)
        self.model.fit(self.X, self.y)

        return True

    def get_objective(self, x):
        result = self.model.predict(np.array(x).reshape(-1, 1))

        return result[0].item()

class OptAlgorithm:
    def __init__(self, bounds, algorithmName, parameters={}):
        self.opt = None
        self.algorithName = algorithmName
        self.bounds = bounds

        parameter_eval = parameters
        print("Optimizer configurations [" + algorithmName + "]:")
        print(parameter_eval)

        if algorithmName == "Differential evolution":
            # Configurations, where from?
            self.N_MAX_ITER = parameter_eval['maxiter']
            self.N_POP_SIZE = parameter_eval['popsize']
            self.MUTATION = parameter_eval['mutation']
            self.RECOMBINATION = parameter_eval['recombination']
            self.STRATEGY = parameter_eval['strategy']
        elif algorithmName == "Dual annealing":
            self.INITIAL_TEMP = parameter_eval['initial_temp']
            self.VISIT = parameter_eval['visit']
            self.ACCEPT = parameter_eval['accept']
            self.N_MAX_FUN = parameter_eval['maxfun']
        elif algorithmName == "L-BFGS-B":
            self.N_MAX_FUN = parameter_eval['maxfun']

    def run(self, objFunction):
        if self.algorithName == "Differential evolution":
            result = differential_evolution(objFunction,
                                        self.bounds,
                                        maxiter=self.N_MAX_ITER,
                                        popsize=self.N_POP_SIZE,
                                        strategy=self.STRATEGY,
                                        mutation=self.MUTATION,
                                        recombination=self.RECOMBINATION)
            return result
        elif self.algorithName == "Dual annealing":
            result = dual_annealing(func=objFunction, 
                            bounds=self.bounds,
                            maxiter=self.N_MAX_FUN, 
                            no_local_search=True,
                            initial_temp=self.INITIAL_TEMP,
                            visit=self.VISIT,
                            accept=self.ACCEPT)
            return result
        elif self.algorithName == "L-BFGS-B":
            opts = {}
            opts['maxfun'] = self.N_MAX_FUN
            init = np.linspace(self.bounds[0][0], self.bounds[0][1], num=1) # random start point
            result = minimize(fun=objFunction, 
                            x0=init,
                            method="L-BFGS-B",
                            options=opts)
            return result

class ModelLearner:
    def __init__(self, learning_algorithm, parameters={}):
        self.model = None
        self.reshape_x = False
        self.reshape_y = False
        parameter_eval = {
            key: value if type(value) is not str else eval(value)
            for key, value in parameters.items()
        }

        if learning_algorithm == "Kriging":
            self.model = GaussianProcessRegressor(**parameter_eval)
            self.reshape_x = True
            self.reshape_y = True

        elif learning_algorithm == "Random Forest":
            self.model = RandomForestRegressor(**parameter_eval)
            self.reshape_x = True
            self.reshape_y = False


class DataWindow:
    def __init__(self, window_size=None):

        self.window_size = window_size
        self.Data_Point = namedtuple("Data_Point", ("id_x", "x", "y"))
        self.data = []

    def append_and_check(self, data_point):

        self.data.append(data_point)

        if self.window_size is not None and len(self.data) > self.window_size:
            del self.data[0]

    def get_arrays(self, reshape_x=True, reshape_y=True):

        X = np.asarray([data_point.x for data_point in self.data])
        if reshape_x:
            X = X.reshape(-1, 1)

        y = np.asarray([data_point.y for data_point in self.data])
        if reshape_y:
            y = y.reshape(-1, 1)

        return X, y

    def get_id_start_x(self):

        return self.data[0].id_x

    def to_df(self):
        return pd.DataFrame(self.data)

def get_cv_scores(model, X, y):
    """ Leave-one-out cross-validation, calculates and returns RMSE, MAE and R2 """

    y_pred = cross_val_predict(model, X, y, cv=LeaveOneOut(), n_jobs=-1)

    rmse_score = mse(y, y_pred, squared=False)

    mae_score = mae(y, y_pred)
    r2_score = r2(y, y_pred)

    return rmse_score, mae_score, r2_score
