from datetime import datetime

import pandas as pd
import numpy as np

from classes.KafkaPC import KafkaPC
from classes.caai_util import ObjectiveFunction

pd.set_option("display.max_columns", None)
pd.options.display.float_format = "{:.3f}".format


class CognitionPC(KafkaPC):
    def __init__(self, config_path, config_section):
        super().__init__(config_path, config_section)

        df_columns = [
            "phase",
            "model_name",
            "id_x",
            "n_data_points",
            "id_start_x",
            "model_size",
            "x",
            "pred_y",
            "pred_y_norm",
            "y",
            "y_norm",
            "y_delta",
            "y_delta_norm",
            "rmse",
            "rmse_norm",
            "mae",
            "rsquared",
            "CPU_ms",
            "CPU_norm",
            "RAM",
            "RAM_norm",
            "pred_quality",
            "real_quality",
            "resources",
            "timestamp",
        ]

        self.df = pd.DataFrame(columns=df_columns)
        self.current_data_point = 0
        self.initialize_objective_function()
        self.generate_initial_design()

        # maps topics and functions, which process the incoming data
        self.func_dict = {
            "AB_model_application": self.process_model_application,
            "AB_monitoring": self.process_monitoring,
        }

    def initialize_objective_function(self):
        """initialize objective function and fit the model on the historic data"""
        self.new_objective = ObjectiveFunction()
        self.new_objective.load_data(data_path=self.config['data_path'],
                                     x_columns=self.config['x_columns'],
                                     y_columns=self.config['y_columns'])
        self.new_objective.fit_model()

    def generate_initial_design(self):
        """ number n_initial_design equally spaced X between X_MIN, X_MAX """

        self.N_INITIAL_DESIGN = self.config['N_INITIAL_DESIGN']
        self.X_MIN = self.config['X_MIN']
        self.X_MAX = self.config['X_MAX']

        self.X = np.linspace(self.X_MIN, self.X_MAX, num=self.N_INITIAL_DESIGN)

    def strategy_min_best_pred_y(self):
        min_best_pred_y = self.df.loc[self.df["pred_y"].idxmin()]
        selected_algo_id = self.df["pred_y"].idxmin()
        selected_algo = min_best_pred_y['model_name']
        best_x = min_best_pred_y['x']

        return selected_algo_id, selected_algo, best_x

    def strategy_model_quality(self):
        selected_algo_id = selected_algo = best_x = None
        df_pred_y = self.df[self.df.y.isnull()].copy()
        df_real_y = self.df[self.df.y.notnull()].copy()

        if df_pred_y.empty is False:
            df_pred_y['pred_quality'] = df_pred_y['pred_quality'] * self.config['USER_WEIGHTS']['QUALITY']
            df_pred_y['resources'] = df_pred_y['resources'] * self.config['USER_WEIGHTS']['RESOURCES']
            df_pred_y['overall_quality'] = df_pred_y.apply(lambda row: self.calc_avg((row['pred_quality'],
                                                                                      row['resources'])), axis=1)

        if df_real_y.empty is False:
            df_real_y['real_quality'] = df_real_y['real_quality'] * self.config['USER_WEIGHTS']['QUALITY']
            df_real_y['resources'] = df_real_y['resources'] * self.config['USER_WEIGHTS']['RESOURCES']
            df_real_y['overall_quality'] = df_real_y.apply(lambda row: self.calc_avg((row['real_quality'],
                                                                                      row['resources'])), axis=1)

        combined_df = pd.concat([df_pred_y, df_real_y], axis=0, sort=False)
        if combined_df['overall_quality'].empty is False:
            best_quality = combined_df.loc[combined_df['overall_quality'].idxmin()]

            selected_algo_id = best_quality.name
            selected_algo = best_quality['model_name']
            best_x = best_quality['x']

            print(f"Algorithm selection: {selected_algo}({selected_algo_id})\nDetails:")

            print(best_quality[["model_name",
                                "x",
                                "pred_y",
                                "y",
                                "rmse",
                                "CPU_ms",
                                "RAM",
                                "pred_quality",
                                "real_quality",
                                "resources",
                                "overall_quality"
                                ]
                               ]
                  )

            print(f"Send x={round(best_x, 3)} to Adaption")

        return selected_algo_id, selected_algo, best_x

    def get_best_x(self, strategy="model_quality"):

        selected_algo_id = None
        selected_algo = None
        best_x = None

        if strategy == 'min_best_pred_y':
            selected_algo_id, selected_algo, best_x = self.strategy_min_best_pred_y()

        elif strategy == 'model_quality':
            selected_algo_id, selected_algo, best_x = self.strategy_model_quality()

        return selected_algo_id, selected_algo, best_x

    def send_point_from_initial_design(self):
        """ Sends the next point from the initial design as message """
        id = self.current_data_point
        phase = "init"
        algorithm = "initial design"
        self.send_new_x(id=id, x=self.X[id], phase=phase, algorithm=algorithm)

    def send_new_x(self, id, x, phase, algorithm):
        new_x = {"id": id,
                 "new_x": x,
                 "phase": phase,
                 "algorithm": algorithm
                 }
        self.send_msg(new_x)

    def calc_y_delta(self, row):
        return abs(row['y'] - row['pred_y'])

    def calc_avg(self, columns):
        result = 0
        for column in columns:
            result += column
        result = result / len(columns)

        return result

    def normalize_values(self, norm_source, norm_dest):
        self.df[norm_dest] = (self.df[norm_source] - self.df[norm_source].min()) /\
                (self.df[norm_source].max()-self.df[norm_source].min())

    def assign_real_y(self, x, y):
        if self.df.empty is False:
            self.df.loc[self.df['x'] == x, 'y'] = y
            self.df['y_delta'] = self.df.apply(self.calc_y_delta, axis=1)

            self.normalize_values('y', 'y_norm')
            self.normalize_values('y_delta', 'y_delta_norm')

    def process_model_application(self, msg):
        """
        "name": "Model_Application",
        "fields": [
            {"name": "phase", "type": ["enum"], "symbols": ["init", "observation"]},
            {"name": "model_name", "type": ["string"]},
            {"name": "id_x", "type": ["int"]},
            {"name": "n_data_points", "type": ["int"]},
            {"name": "id_start_x", "type": ["int"]},
            {"name": "model_size", "type": ["int"]},
            {"name": "x", "type": ["float"]},
            {"name": "pred_y", "type": ["float"]},
            {"name": "rmse", "type": ["null, float"]},
            {"name": "mae", "type": ["null, float"]},
            {"name": "rsquared", "type": ["null, float"]},
            {"name": "CPU_ms", "type": ["int"]},
            {"name": "RAM", "type": ["int"]}
        ]
        """
        new_model_appl = self.decode_avro_msg(msg)
        new_model_appl["timestamp"] = datetime.now()

        self.df = self.df.append(new_model_appl, ignore_index=True)
        self.normalize_values('pred_y', 'pred_y_norm')
        self.normalize_values('rmse', 'rmse_norm')
        self.normalize_values('CPU_ms', 'CPU_norm')
        self.normalize_values('RAM', 'RAM_norm')

        self.df['pred_quality'] = self.df.apply(lambda row: self.calc_avg((row['pred_y_norm'],
                                                                           row['rmse_norm'])), axis=1)

        self.df['resources'] = self.df.apply(lambda row: self.calc_avg((row['CPU_norm'], row['RAM_norm'])), axis=1)

    def process_monitoring(self, msg):

        new_monitoring = self.decode_avro_msg(msg)

        """
        "name": "Data",
        "fields": [
            {"name": "phase", "type": ["string"]},
            {"name": "id_x", "type": ["int"]},
            {"name": "x", "type": ["float"]},
            {"name": "y", "type": ["float"]}
            ]
        """

        """
        [x] reales y muss dem Algorithmus der vorherigen Iteration zugeordnet werden


        [x] wenn Modell Wert sendet
        pred_model_quality = get_pred_model_quality(surrogate_y, new_model['rmse'])
        - normalisieren über alle Module
        - beide 1/2


        [x] wenn Monitoring reales Ergebnis sendet
        real_model_quality = get_real_model_quality(surrogate_y, real_y, rmse)
        - delta_y = | surrogate_y - real_y |
        - normalisieren
        - alle 1/3

        [x] resources = CPU, RAM
        - normalisieren
        - beide 1/2



        [x] wenn neues X ausgewählt wird
        quality = real_model_quality if real_model_quality is not None else pred_model_quality
        model = min(quality * user_spec + resources * user_spec)


        """
        id = self.current_data_point
        # send initial design first
        if self.current_data_point < self.N_INITIAL_DESIGN:

            self.send_point_from_initial_design()
            print(f'Sent next point from initial design x={self.X[self.current_data_point]} to Adaption.')

        # then send new data points
        else:
            phase = "observation"
            # select best value, otherwise CPPS will use last value from controller
            if self.df.empty is False:
                self.assign_real_y(new_monitoring['x'], new_monitoring['y'])
                self.df['real_quality'] = self.df.apply(lambda row: self.calc_avg((row['y_norm'], row['y_delta_norm'],
                                                                                   row['rmse_norm'])), axis=1)

                selected_algo_id, selected_algo, selected_x = self.get_best_x()
                algorithm = f"{selected_algo}({selected_algo_id})"
                if selected_algo_id is not None:
                    self.send_new_x(id=id, x=selected_x, phase=phase, algorithm=algorithm)

        self.current_data_point += 1
