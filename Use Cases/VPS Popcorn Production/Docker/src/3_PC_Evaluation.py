import os
from time import sleep
from datetime import datetime

import pandas as pd
import numpy as np

from classes.KafkaPC import KafkaPC
from classes.util import ObjectiveFunction

pd.set_option('display.max_columns', None)
pd.options.display.float_format = '{:.3f}'.format


class CognitionPC(KafkaPC):
    def __init__(self, config_path, config_section, n_initial_design, x_min, x_max):
        super().__init__(config_path, config_section)

        df_columns = ['phase', 'model_name', 'n_data_points', 'id_start_x',
                      'model_size', 'best_x', 'best_pred_y', 'y', 'y_delta',
                      'rmse', 'mae', 'rsquared', 'CPU_ms', 'RAM', 'timestamp']

        self.df = pd.DataFrame(columns=df_columns)

        self.MAX_DATA_POINTS = 50
        self.current_data_point = 0

        """initialize objective function"""
        self.new_objective = ObjectiveFunction()
        self.new_objective.load_data()
        self.new_objective.fit_model()

        self.n_initial_design = n_initial_design
        self.generate_initial_design(n_initial_design, x_min, x_max)

        # maps topics and functions, which process the incoming data
        self.func_dict = {"AB_model_application": self.process_model_application,
                          "AB_monitoring": self.process_monitoring}

    def generate_initial_design(self, n_initial_design, x_min, x_max):
        # number n_initial_design equally spaced X between X_MIN, X_MAX
        self.X = np.linspace(x_min, x_max, num=n_initial_design)

    def process_model_application(self, msg):
        """
        "name": "Model_Application",
        "fields": [
            {"name": "phase", "type": ["enum"], "symbols": ["init", "observation"]},
            {"name": "model_name", "type": ["string"]},
            {"name": "n_data_points", "type": ["int"]},
            {"name": "id_start_x", "type": ["int"]},
            {"name": "model_size", "type": ["int"]},
            {"name": "best_x", "type": ["float"]},
            {"name": "best_pred_y", "type": ["float"]},
            {"name": "rmse", "type": ["null, float"]},
            {"name": "mae", "type": ["null, float"]},
            {"name": "rsquared", "type": ["null, float"]},
            {"name": "CPU_ms", "type": ["int"]},
            {"name": "RAM", "type": ["int"]}
        ]
        """
        new_model_appl = self.decode_avro_msg(msg)
        best_pred_y = new_model_appl['best_pred_y']
        y = self.new_objective.get_objective(new_model_appl['best_x'])
        y_delta = abs(y - best_pred_y)  # absoluter Wert?

        new_model_appl['y'] = y
        new_model_appl['y_delta'] = y_delta
        new_model_appl['timestamp'] = datetime.now()

        self.df = self.df.append(new_model_appl, ignore_index=True)

        print(self.df[["model_name", "best_x", "best_pred_y", "rmse",
                       "rsquared", "CPU_ms", "RAM"]].iloc[-1:])
        """
        "name": "New X",
        "fields": [
            {"name": "phase", "type": ["string"]},
            {"name": "id_x", "type": ["int"]},
            {"name": "new_x", "type": ["float"]}
            ]
        """

    def process_monitoring(self, msg):

        new_monitoring = self.decode_avro_msg(msg)

        # print(f"CPPS sent x={new_monitoring['x']}, y={new_monitoring['y']}")

        """
        "name": "Data",
        "fields": [
            {"name": "phase", "type": ["string"]},
            {"name": "id_x", "type": ["int"]},
            {"name": "x", "type": ["float"]},
            {"name": "y", "type": ["float"]}
            ]
        """

        if self.current_data_point < self.n_initial_design:

            new_x = {'phase': 'init',
                     'id_x': new_cog.current_data_point,
                     'new_x': new_cog.X[new_cog.current_data_point]}
            # new_cog.current_data_point += 1

            new_cog.send_msg(new_x)
            print(f'Sent next point from initial design x={new_x["new_x"]}')

        elif self.current_data_point < self.MAX_DATA_POINTS:

            # best / last dataframe value
            if self.df.empty is True:
                new_x = {"phase": "observation", "id_x": self.current_data_point,
                         "new_x": new_monitoring['x']}
                self.send_msg(new_x)
                print(f"The value x={new_monitoring['x']} is sent to the "
                      f"CPPS, since no optimization results arrived yet.")
            else:
                min_best_pred_y = self.df.loc[self.df["best_pred_y"].idxmin()]
                new_x = min_best_pred_y.best_x

                """
                    "name": "New X",
                    "fields": [
                        {"name": "phase", "type": ["string"]},
                        {"name": "id_x", "type": ["int"]},
                        {"name": "new_x", "type": ["float"]}
                        ]
                    """
                new_x = {"phase": "observation", "id_x": self.current_data_point,
                         "new_x": new_x}

                self.send_msg(new_x)
                print(f"The x value of the algorithm "
                      f"{min_best_pred_y['model_name']} is applied to the CPPS "
                      f"since the lowest y is expected "
                      f"(y={round(min_best_pred_y['best_pred_y'], 3)}).")

        self.current_data_point += 1
        self.commit_offset(msg)


env_vars = {'config_path': os.getenv('config_path'),
            'config_section': os.getenv('config_section')}

"""
env_vars = {'in_topic': {'AB_model_application': './schema/model_appl.avsc',
                         'AB_monitoring': './schema/monitoring.avsc'},
            'in_group': 'evaluation',
            'in_schema_file': ['./schema/model_appl.avsc', './schema/monitoring.avsc'],
            'out_topic': 'AB_model_evaluation',
            'out_schema_file': './schema/new_x.avsc'
            }
"""

"""generate initial design"""
N_INITIAL_DESIGN = 5
X_MIN = 4000.
X_MAX = 10100.

new_cog = CognitionPC(**env_vars, n_initial_design=N_INITIAL_DESIGN, x_min=X_MIN, x_max=X_MAX)

"""
"name": "New X",
"fields": [
     {"name": "phase", "type": ["enum"], "symbols": ["init", "observation"]},
     {"name": "id_x", "type": ["int"]},
     {"name": "new_x", "type": ["float"]}
 ]
"""

new_x = {'phase': 'init',
         'id_x': new_cog.current_data_point,
         'new_x': new_cog.X[new_cog.current_data_point]}
new_cog.current_data_point += 1

sleep(3)
new_cog.send_msg(new_x)

print(f"Creating initial design of the system by applying {N_INITIAL_DESIGN} "
      f"equally distributed values x over the whole working area of the CPPS."
      f"\nSent x={new_x['new_x']}")

for msg in new_cog.consumer:
    # print("Cognition received message")
    new_cog.func_dict[msg.topic](msg)
