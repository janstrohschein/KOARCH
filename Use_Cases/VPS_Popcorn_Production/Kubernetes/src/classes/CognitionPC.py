from datetime import datetime
from typing import Tuple
import requests

import pandas as pd
import numpy as np

# from classes.KafkaPC import KafkaPC
from classes.CKafkaPC import KafkaPC
from classes.caai_util import ObjectiveFunction

pd.set_option("display.max_columns", None)
pd.options.display.float_format = "{:.3f}".format


class CognitionPC(KafkaPC):
    def __init__(self, config_path, config_section):
        super().__init__(config_path, config_section)
        df_sim_columns = [
            "selection_phase",
            "algorithm",
            "repetition",
            "budget",
            "x",
            "y",
            "CPU_ms",
            "RAM",
            "rel_y",
            "rel_CPU_ms",
            "rel_RAM",
            "norm_y",
            "norm_CPU_ms",
            "norm_RAM",
        ]

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
        self.df_sim = pd.DataFrame(columns=df_sim_columns)
        self.df = pd.DataFrame(columns=df_columns)
        API_URL = self.config["API_URL"]
        ENDPOINT = "/production_parameter/algorithm"
        self.URL = API_URL + ENDPOINT
        self.nr_of_iterations = 0
        self.theta = 25
        self.zeta = 1
        self.best_algorithm = "baseline"  # TODO default?
        # self.initialize_objective_function()
        self.generate_initial_design()
        # self.generate_test_function()
        # maps topics and functions, which process the incoming data
        self.func_dict = {
            "AB_apply_on_cpps": self.process_apply_on_cpps,
            "AB_application_results": self.process_application_results,
            "AB_monitoring": self.process_monitoring,
            "AB_simulation_results": self.process_simulation_results,
        }

    def aggregatePerformance(self, cpu, memory, y):
        # compute weighted aggregation
        weightY = self.config["USER_WEIGHTS"]["QUALITY"]
        weightC = self.config["USER_WEIGHTS"]["RESOURCES"] / 2
        weightM = self.config["USER_WEIGHTS"]["RESOURCES"] / 2
        return (weightY * y) + (weightC * cpu) + (weightM * memory)

    def initialize_objective_function(self):
        """initialize objective function and fit the model on the historic data"""
        self.new_objective = ObjectiveFunction()
        self.new_objective.load_data(
            data_path=self.config["data_path"],
            x_columns=self.config["x_columns"],
            y_columns=self.config["y_columns"],
        )
        self.new_objective.fit_model()

    def generate_initial_design(self):
        """ number n_initial_design equally spaced X between X_MIN, X_MAX """

        self.N_INITIAL_DESIGN = self.config["N_INITIAL_DESIGN"]
        self.X_MIN = self.config["X_MIN"]
        self.X_MAX = self.config["X_MAX"]

        self.X = np.linspace(self.X_MIN, self.X_MAX, num=self.N_INITIAL_DESIGN)

    def strategy_min_best_pred_y(self) -> Tuple[int, str, float]:
        """ Finds the algorithm with the lowest prediction for the y-value.

        Returns:
            selected_algo_id (int), selected_algo (str), best_x (float)
        """
        min_best_pred_y = self.df.loc[self.df["pred_y"].idxmin()]
        selected_algo_id = self.df["pred_y"].idxmin()
        selected_algo = min_best_pred_y["model_name"]
        best_x = min_best_pred_y["x"]

        return selected_algo_id, selected_algo, best_x

    def strategy_model_quality(self) -> Tuple[int, str, float]:
        """ Finds the algorithm with the best overall quality.

        Steps:
        - calculates the quality for algorithms without a real y-value, also considering the
          resources and the user weights for quality and resource consumption
        - calculates the quality for algorithms with a real y-value, also considering the
          resources and the user weights for quality and resource consumption
        - combines the calculated quality values and selects the best (min) quality

        Returns:
            selected_algo_id (int), selected_algo (str), best_x (float)
        """

        selected_algo_id = selected_algo = best_x = None
        df_pred_y = self.df[self.df.y.isnull()].copy()
        df_real_y = self.df[self.df.y.notnull()].copy()

        if df_pred_y.empty is False:
            df_pred_y["pred_quality"] = (
                df_pred_y["pred_quality"] * self.config["USER_WEIGHTS"]["QUALITY"]
            )
            df_pred_y["resources"] = (
                df_pred_y["resources"] * self.config["USER_WEIGHTS"]["RESOURCES"]
            )
            df_pred_y["overall_quality"] = df_pred_y.apply(
                lambda row: self.calc_avg((row["pred_quality"], row["resources"])),
                axis=1,
            )

        if df_real_y.empty is False:
            df_real_y["real_quality"] = (
                df_real_y["real_quality"] * self.config["USER_WEIGHTS"]["QUALITY"]
            )
            df_real_y["resources"] = (
                df_real_y["resources"] * self.config["USER_WEIGHTS"]["RESOURCES"]
            )
            df_real_y["overall_quality"] = df_real_y.apply(
                lambda row: self.calc_avg((row["real_quality"], row["resources"])),
                axis=1,
            )

        combined_df = pd.concat([df_pred_y, df_real_y], axis=0, sort=False)
        if combined_df["overall_quality"].empty is False:
            best_quality = combined_df.loc[combined_df["overall_quality"].idxmin()]

            selected_algo_id = best_quality.name
            selected_algo = best_quality["model_name"]
            best_x = best_quality["x"]

            print(f"Algorithm selection: {selected_algo}({selected_algo_id})\nDetails:")

            print(
                best_quality[
                    [
                        "model_name",
                        "x",
                        "pred_y",
                        "y",
                        "rmse",
                        "CPU_ms",
                        "RAM",
                        "pred_quality",
                        "real_quality",
                        "resources",
                        "overall_quality",
                    ]
                ]
            )

            print(f"Send x={round(best_x, 3)} to Adaption")

        return selected_algo_id, selected_algo, best_x

    def get_best_x(self, strategy="model_quality") -> Tuple[int, str, float]:
        """ Uses different strategies to find the best new x-value.
            The strategies can be extended by creating a new function and
            adding it to the strategy dictionary.

        Args:
            strategy (str, optional): Defaults to "model_quality".

        Returns:
            selected_algo_id (int), selected_algo (str), best_x (float)
        """

        selected_algo_id = selected_algo = best_x = None

        strategy_dict = {
            "min_best_pred_y": self.strategy_min_best_pred_y,
            "model_quality": self.strategy_model_quality,
        }

        selected_algo_id, selected_algo, best_x = strategy_dict[strategy]()

        return selected_algo_id, selected_algo, best_x

    def send_point_from_initial_design(self):
        """ Sends the next point from the initial design as message """
        id = self.nr_of_iterations
        self.send_msg(
            topic="AB_new_x", data={"algorithm": "Initial design", "new_x": self.X[id]}
        )

    def calc_y_delta(self, row):
        return abs(row["y"] - row["pred_y"])

    def calc_avg(self, columns):
        result = 0
        for column in columns:
            result += column
        result = result / len(columns)

        return result

    def normalize_values(self, norm_source, norm_dest, invert):
        if invert:
            self.df_sim[norm_dest] = 1 - (
                (self.df_sim[norm_source] - self.df_sim[norm_source].min())
                / (self.df_sim[norm_source].max() - self.df_sim[norm_source].min())
            )
        else:
            self.df_sim[norm_dest] = (
                self.df_sim[norm_source] - self.df_sim[norm_source].min()
            ) / (self.df_sim[norm_source].max() - self.df_sim[norm_source].min())

    def assign_real_y(self, x, y):
        if self.df.empty is False:
            self.df.loc[self.df["x"] == x, "y"] = y
            self.df["y_delta"] = self.df.apply(self.calc_y_delta, axis=1)

    def process_application_results(self, msg):
        """Sends the new value for x to the adaption

        Incoming Avro Message:
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
        print("Processing application results from Optimizer on AB_application_results")
        new_appl_result = self.decode_msg(msg)

        adaption_data = {
            "algorithm": self.best_algorithm["algorithm"],
            "new_x": new_appl_result["x"],
        }

        self.send_msg(topic="AB_new_x", data=adaption_data)
        print(f"Sent application results to Adaption: x={new_appl_result['x']}")

        """ Processes incoming messages from the model application and normalizes the values
            to predict model quality and rate resource consumption.

        """
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
        """

    def process_monitoring(self, msg):
        """ Processes incoming messages from the production monitoring tool and
            sends data + instructions to the simulation module.

        Incoming Avro Message:
        "name": "Data",
        "fields": [
            {"name": "phase", "type": ["string"]},
            {"name": "id_x", "type": ["int"]},
            {"name": "x", "type": ["float"]},
            {"name": "y", "type": ["float"]}
            ]

        Outgoing Avro Message:
        {"type": "record",
        "name": "Simulation_Data",
        "fields": [
            {"name": "id", "type": ["int"]},
            {"name": "new_simulation", "type": ["bool"]},
            {"name": "x", "type": ["float"]},
            {"name": "y", "type": ["float"]}
            ]
            }
        """
        print("Processing monitoring data from Monitoring on AB_monitoring")
        new_monitoring = self.decode_msg(msg)

        # send initial design first
        if self.nr_of_iterations < self.N_INITIAL_DESIGN:

            self.send_point_from_initial_design()
            print(
                f"Sent next point from initial design x={self.X[self.nr_of_iterations]} to Adaption."
            )

        # then send new data points to simulation

        # \If{(nrIterations $\%\, \theta = 0 \vee \zeta = 1$)}
        new_simulation = False
        if self.nr_of_iterations % self.theta == 0 or self.zeta == 1:
            self.zeta = 0
            new_simulation = True
            print("Setting new_simulation=True")

        # send all data to simulation
        simulation_data = {
            "id": self.nr_of_iterations,
            "new_simulation": new_simulation,
            "x": new_monitoring["x"],
            "y": new_monitoring["y"],
        }

        self.send_msg(topic="AB_simulation_input", data=simulation_data)

        self.nr_of_iterations += 1

    def process_simulation_results(self, msg):
        """ Cognition selects best algorithm from simulation results
        """
        """
         "name": "Simulation_Result",
        "fields": [
            {"name": "selection_phase", "type": ["int"]},
            {"name": "algorithm", "type": ["string"]},
            {"name": "repetition", "type": ["int"]},
            {"name": "budget", "type": ["int"]},
            {"name": "x", "type": ["float"]},
            {"name": "y", "type": ["float"]},
            {"name": "CPU_ms", "type": ["float"]},
            {"name": "RAM", "type": ["float"]}
            ]
        """
        new_sim_results = self.decode_msg(msg)

        print(
            f"Processing simulation results from {new_sim_results['algorithm']} on AB_simulation_results"
        )

        # append to df_sim
        self.df_sim = self.df_sim.append(new_sim_results, ignore_index=True)

        print("df_sim:")
        print(self.df_sim)

        # compute rel performance, if baseline exists
        is_baseline = self.df_sim["algorithm"] == "baseline"
        row = self.df_sim[is_baseline].tail(1)  # [-1:]
        print("Simulation results selects baseline: ")
        print(row)
        print("for new Simulation results: ")
        print(new_sim_results)
        if len(row) > 0:
            self.df_sim["rel_y"] = self.df_sim["y"] / row["y"][0]
            self.df_sim["rel_CPU_ms"] = self.df_sim["CPU_ms"] / row["CPU_ms"][0]
            self.df_sim["rel_RAM"] = self.df_sim["RAM"] / row["RAM"][0]

            # normalize performance, if something to normalize exists
            if len(self.df_sim) > 1:
                self.normalize_values("rel_y", "norm_y", False)
                self.normalize_values("rel_CPU_ms", "norm_CPU_ms", True)
                self.normalize_values("rel_RAM", "norm_RAM", True)

                # aggregate
                self.df_sim["y_agg"] = np.vectorize(self.aggregatePerformance)(
                    cpu=self.df_sim["norm_CPU_ms"],
                    memory=self.df_sim["norm_RAM"],
                    y=self.df_sim["norm_y"],
                )
                # take max performance y_agg
                self.best_algorithm = self.df_sim.loc[self.df_sim["y_agg"].idxmax()]
                print("Best performing algorithm: " + self.best_algorithm["algorithm"])

                r = requests.patch(
                    url=self.URL, params={"value": self.best_algorithm["algorithm"]}
                )

    def process_apply_on_cpps(self, msg):
        new_appl_result = self.decode_msg(msg)

        adaption_data = {
            "algorithm": new_appl_result["algorithm"],
            "new_x": new_appl_result["new_x"],
        }

        self.send_msg(topic="AB_new_x", data=adaption_data)
        print(f"Sent application results to Adaption: x={new_appl_result['new_x']}")

