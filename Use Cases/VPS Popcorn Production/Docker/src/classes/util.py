from collections import namedtuple
import re
import pandas as pd
import numpy as np

from sklearn.model_selection import LeaveOneOut, cross_val_predict
from sklearn.metrics import mean_squared_error as mse
from sklearn.metrics import mean_absolute_error as mae
from sklearn.metrics import r2_score as r2
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.ensemble import RandomForestRegressor
# from sklearn.gaussian_process.kernels import RationalQuadratic
from sklearn.gaussian_process import kernels


class ObjectiveFunction:

    def __init__(self):
        self.model = None
        self.X = None
        self.y = None


    def load_data(self):

        file_path = "data/vpsFeatures.csv"
        extract_columns = ['conveyorRuntimeMean', 'yAgg']
        extract_columns_types = {'conveyorRuntimeMean': float, 'yAgg': float}

        vps_df = pd.read_csv(file_path, sep=";", usecols=extract_columns,
                             dtype=extract_columns_types, decimal=',')

        vps_df = vps_df.drop_duplicates()

        self.X = np.array(vps_df['conveyorRuntimeMean']).reshape(-1, 1)
        self.y = np.array(vps_df['yAgg'])

        return True

    def fit_model(self):

        kernel = 1.0 * kernels.RationalQuadratic(length_scale=1.0, alpha=0.1)

        self.model = GaussianProcessRegressor(kernel=kernel)
        self.model.fit(self.X, self.y)

        return True

    def get_objective(self, x):
        result = self.model.predict(np.array(x).reshape(-1, 1))

        return result[0].item()


class ModelLearner:
    def __init__(self, learning_algorithm, parameters={}):
        self.model = None
        self.reshape_x = False
        self.reshape_y = False
        parameter_eval = {key: eval(value) for key, value in parameters.items()}

        if learning_algorithm == 'Kriging':
            self.model = GaussianProcessRegressor(**parameter_eval)
            self.reshape_x = True
            self.reshape_y = True

        elif learning_algorithm == 'RF':
            self.model = RandomForestRegressor(**parameter_eval)
            self.reshape_x = True
            self.reshape_y = False


class DataWindow:

    def __init__(self, window_size = None):

        self.window_size = window_size
        self.Data_Point = namedtuple('Data_Point', ('id_x', 'x', 'y'))
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

def get_cv_scores(model, X, y):
    """ Leave-one-out cross-validation, calculates and returns RMSE, MAE and R2 """

    y_pred = cross_val_predict(model, X, y, cv=LeaveOneOut(), n_jobs=-1)

    rmse_score = np.sqrt(mse(y, y_pred))
    mae_score = mae(y, y_pred)
    r2_score = r2(y, y_pred)

    print(f'Update CPPS model with new data point. RMSE of the model: {rmse_score}')
 #   print(f'Mean MAE: {mae_score}')
 #   print(f'Mean R2: {r2_score}')

    return rmse_score, mae_score, r2_score

def get_parameter_dict_from_yml(parameter_string):
    parameter_name = [x for x in re.finditer(r'\"([a-zA-Z_-]+)\"', parameter_string)]
    parameter = [x for x in re.finditer(r': \"(.*?)\"', parameter_string)]

    parameter_name = [item.group(1) for item in parameter_name]
    parameter = [item.group(1) for item in parameter]

    d = {}
    len_parameter = len(parameter)
    for i in range(len_parameter):
        d[parameter_name[i]] = parameter[i]

    return d
