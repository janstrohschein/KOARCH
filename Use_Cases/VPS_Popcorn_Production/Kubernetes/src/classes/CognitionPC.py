from datetime import datetime
from typing import Tuple
import requests
import json
from time import sleep

import pandas as pd
import numpy as np

import traceback

from Big_Data_Platform.Kubernetes.Kafka_Client.Confluent_Kafka_Python.src.classes.CKafkaPC import KafkaPC
from Big_Data_Platform.Kubernetes.Cognition.example.src.classes.KubeAPI import KubeAPI, Deployment, ConfigMap
from Use_Cases.VPS_Popcorn_Production.Kubernetes.src.classes.caai_util import ObjectiveFunction

pd.set_option("display.max_columns", None)
pd.options.display.float_format = "{:.3f}".format


class CognitionPC(KafkaPC):
    def __init__(self, config_path, config_section):
        super().__init__(config_path, config_section)

        # QUESTION Resources DF, job_id and algorithm_name?
        df_res_columns = [
            "job_id",
            "algorithm_name",
            "CPU_ms",
            "RAM",
            "CPU_perc",
            "RAM_perc",
        ]

        df_sim_columns = [
            "selection_phase",
            "algorithm",
            ""
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

        # df_columns = [
        #     "phase",
        #     "model_name",
        #     "id_x",
        #     "n_data_points",
        #     "id_start_x",
        #     "model_size",
        #     "x",
        #     "pred_y",
        #     "pred_y_norm",
        #     "y",
        #     "y_norm",
        #     "y_delta",
        #     "y_delta_norm",
        #     "rmse",
        #     "rmse_norm",
        #     "mae",
        #     "rsquared",
        #     "CPU_ms",
        #     "CPU_norm",
        #     "RAM",
        #     "RAM_norm",
        #     "pred_quality",
        #     "real_quality",
        #     "resources",
        #     "timestamp",
        # ]
        self.df_sim = pd.DataFrame(columns=df_sim_columns)
        # self.df = pd.DataFrame(columns=df_columns)
        self.df_res = pd.DataFrame(columns=df_res_columns)
        API_URL = self.config["API_URL"]
        ENDPOINT = "/production_parameter/algorithm"
        self.production_parameter_url = API_URL + ENDPOINT
        self.nr_of_iterations = 0
        self.selection_phase = 0
        self.theta = 25
        self.zeta = 1
        self.best_algorithm = "baseline"
        self.k_api = KubeAPI()
        self.k_api.init_kube_connection()
        self.current_alg_dep = None
        API_URL = "http://api-knowledge-service.default:80"
        ENDPOINT_USER_INPUT = "/use_case/"
        self.user_input_url = API_URL + ENDPOINT_USER_INPUT

        ENDPOINT_FEASIBLE_PIPELINES = "/knowledge/feasible_pipelines/"
        self.feasible_pipelines_url = API_URL + ENDPOINT_FEASIBLE_PIPELINES

        ENDPOINT_ALGORITHM = "/knowledge/algorithm/"
        self.algorithm_url = API_URL + ENDPOINT_ALGORITHM

        self.generate_initial_design()
        # maps topics and functions, which process the incoming data
        self.func_dict = {
            "AB_apply_on_cpps": self.process_apply_on_cpps,
            "AB_application_results": self.process_application_results,
            "AB_monitoring": self.process_monitoring,
            "AB_simulation_results": self.process_simulation_results,
            "AB_cluster_monitoring": self.process_cluster_monitoring,
        }

    def get_from_API(self, URL, parameters=None):
        result = ()

        try:
            api_request = requests.get(url=URL, params=parameters)
            result = json.loads(api_request.content)
        except Exception as e:
            print(f"Could not retrieve from API: {e}")

        return result

    def instantiate_best_alg(self):
        user_input = self.get_from_API(self.user_input_url)
        algorithm = {"algorithm": self.best_algorithm}
        api_info = {**user_input, **algorithm}
        alg_info = self.get_from_API(self.algorithm_url, api_info)

        name = self.best_algorithm
        image = alg_info["container"]["Image"]
        version = alg_info["container"]["Version"]

        cm_list = []
        for cm in alg_info["container"]["Config_Maps"]:
            cm_list.append(ConfigMap(**cm))

        best_alg_dep = Deployment(name=name, image=image,
                                  version=version, config_maps=cm_list)

        dep_obj = self.k_api.kube_create_deployment_object(
            best_alg_dep)
        self.k_api.kube_create_deployment(dep_obj)

        return best_alg_dep

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

    def send_point_from_initial_design(self):
        """ Sends the next point from the initial design as message """
        id = self.nr_of_iterations
        self.send_msg(
            topic="AB_new_x",
            message={"algorithm": "Initial design", "new_x": self.X[id]},
        )

    def calc_y_delta(self, row):
        return abs(row["y"] - row["pred_y"])

    def calc_avg(self, columns):
        result = 0
        for column in columns:
            result += column
        result = result / len(columns)

        return result

    def normalize_values(self, selection_phase, norm_source, norm_dest, invert):

        con_phase = self.df_sim['selection_phase'] == selection_phase
        con_al = self.df_sim['algorithm'] != 'baseline'

        value_minus_min = (self.df_sim.loc[con_phase & con_al, norm_source] -
                           self.df_sim.loc[con_phase & con_al, norm_source].min())

        max_minus_min = (self.df_sim.loc[con_phase & con_al, norm_source].max() -
                         self.df_sim.loc[con_phase & con_al, norm_source].min())

        if max_minus_min == 0:
            res = 0
        else:
            res = value_minus_min / max_minus_min

        if invert:
            res = 1 - res

        self.df_sim.loc[con_phase & con_al, norm_dest] = res

        # if invert:
        #     self.df_sim.loc[con_phase & con_al, norm_dest] = 1 - (
        #         (self.df_sim.loc[con_phase & con_al, norm_source] -
        #          self.df_sim.loc[con_phase & con_al, norm_source].min())
        #         / (self.df_sim.loc[con_phase & con_al, norm_source].max() -
        #             self.df_sim.loc[con_phase & con_al, norm_source].min()))
        # else:
        #     self.df_sim.loc[con_phase & con_al, norm_dest] = (self.df_sim.loc[con_phase & con_al, norm_source] -
        #                                                       self.df_sim.loc[con_phase & con_al, norm_source].min()) / \
        #         (self.df_sim.loc[con_phase & con_al, norm_source].max() -
        #          self.df_sim.loc[con_phase & con_al, norm_source].min())

        # print(self.df_sim.loc[con_phase & con_al, norm_dest])

    def process_application_results(self, msg):
        """Sends the new value for x to the adaption

        Incoming Avro Message:
        "name": "Model_Application",
        "fields": [
            {"name": "phase", "type": ["enum"],
                "symbols": ["init", "observation"]},
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
            "algorithm": self.best_algorithm,
            "new_x": new_appl_result["x"],
        }

        self.send_msg(topic="AB_new_x", message=adaption_data)
        print(
            f"Sent application results to Adaption: x={new_appl_result['x']}")

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
            {"name": "selection_phase", "type": ["int"]},
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
            self.selection_phase += 1
            print("Setting new_simulation=True")

            if self.k_api.has_capacity():
                # get feasible pipelines based on user input
                user_input = self.get_from_API(self.user_input_url)
                feasible_pipelines = self.get_from_API(
                    self.feasible_pipelines_url, user_input)

                # create jobs for each module in the pipelines
                job_list = self.k_api.get_jobs_from_pipelines(
                    feasible_pipelines)
                # instantiate the jobs on K8s
                for job in job_list:
                    self.k_api.kube_create_job(job)

                    # add the algorithm to the df
                    job_info = {"selection_phase": self.selection_phase,
                                "algorithm": job.name}
                    job_series = pd.Series(job_info)
                    self.df_sim = self.df_sim.append(
                        job_series, ignore_index=True)
            else:
                print("Waiting for resources..")

        # send all data to simulation
        simulation_data = {
            "id": self.nr_of_iterations,
            "selection_phase": self.selection_phase,
            "new_simulation": new_simulation,
            "x": new_monitoring["x"],
            "y": new_monitoring["y"],
        }

        self.send_msg(topic="AB_simulation_input", message=simulation_data)
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
        try:
            new_sim_results = self.decode_msg(msg)

            print(
                f"Processing simulation results from {new_sim_results['algorithm']} on AB_simulation_results"
            )

            # current iteration of algorithm-selection
            selection_phase = new_sim_results["selection_phase"]

            # conditions for df
            con_phase = self.df_sim['selection_phase'] == selection_phase
            con_not_base = self.df_sim['algorithm'] != "baseline"
            con_al = self.df_sim['algorithm'] == new_sim_results["algorithm"]

            # append to df_sim
            in_df = self.df_sim[con_phase & con_al].index.tolist()
            if len(in_df) == 0:
                self.df_sim = self.df_sim.append(
                    new_sim_results, ignore_index=True)
            else:
                new_sim_series = pd.Series(new_sim_results)
                new_in_df = self.df_sim[con_phase & con_al].index.tolist()[0]
                self.df_sim.iloc[new_in_df] = new_sim_series

            print(self.df_sim)

            # subselect data of current "selection_phase"
            baseline = self.df_sim.loc[(self.df_sim['selection_phase'] == selection_phase) & (
                self.df_sim["algorithm"] == "baseline")]
            # baseline = self.df_sim.loc[con_phase & con_base]

            # compute rel performance, if baseline exists
            print("Baseline Simulation results: ")
            print(baseline)
            print("New Simulation results: ")
            print(new_sim_results)

            newNotBaseline = new_sim_results["algorithm"] != "baseline"

            if len(baseline) > 0 and newNotBaseline is True:
                baseline_y = baseline["y"].item()
                baseline_cpu = baseline["CPU_ms"].item()
                baseline_ram = baseline["RAM"].item()

                # performance y relative to baseline
                # self.df_sim.loc[(self.df_sim['selection_phase'] == selection_phase) and (self.df_sim['algorithm'] != "baseline"), "rel_y"] = (
                #     baseline_y - self.df_sim.loc[(self.df_sim['selection_phase'] == selection_phase) and (self.df_sim['algorithm'] != "baseline"), "y"]) / baseline_y
                self.df_sim.loc[con_phase & con_al, "rel_y"] = (
                    baseline_y - self.df_sim.loc[con_phase & con_al, "y"]) / baseline_y

                # CPU cons. relative to baseline
                # self.df_sim.loc[(self.df_sim['selection_phase'] == selection_phase) and (self.df_sim['algorithm'] != "baseline"), "rel_CPU_ms"] = self.df_sim.loc[(
                #     self.df_sim['selection_phase'] == selection_phase) and (self.df_sim['algorithm'] != "baseline"), "CPU_ms"] / baseline_cpu
                self.df_sim.loc[con_phase & con_al,
                                "rel_CPU_ms"] = self.df_sim.loc[con_phase & con_al, "CPU_ms"] / baseline_cpu

                # RAM cons. relative to baseline
                # self.df_sim.loc[(self.df_sim['selection_phase'] == selection_phase) & (self.df_sim['algorithm'] != "baseline"), "rel_RAM"] = self.df_sim.loc[(
                #     self.df_sim['selection_phase'] == selection_phase) and (self.df_sim['algorithm'] != "baseline"), "RAM"] / baseline_ram
                self.df_sim.loc[con_phase & con_al,
                                "rel_RAM"] = self.df_sim.loc[con_phase & con_al, "RAM"] / baseline_ram

                # normalize performance, if something to normalize exists
                if len(self.df_sim.loc[con_phase & con_not_base]) > 0:
                    self.normalize_values(
                        selection_phase, "rel_y", "norm_y", False)
                    self.normalize_values(
                        selection_phase, "rel_CPU_ms", "norm_CPU_ms", True)
                    self.normalize_values(
                        selection_phase, "rel_RAM", "norm_RAM", True)
                    # aggregate
                    self.df_sim.loc[con_phase & con_al, "y_agg"] = np.vectorize(self.aggregatePerformance)(
                        cpu=self.df_sim.loc[con_phase & con_al,
                                            "norm_CPU_ms"],
                        memory=self.df_sim.loc[con_phase & con_al,
                                               "norm_RAM"],
                        y=self.df_sim.loc[con_phase & con_al, "norm_y"]
                    )

                    print("Performance results: ")
                    print(self.df_sim.loc[con_phase])

                    # take max performance y_agg
                    id = self.df_sim.loc[con_phase & con_al,
                                         "y_agg"].idxmax()
                    self.best_algorithm = self.df_sim.loc[con_phase,
                                                          "algorithm"][id]
                    print("Best performing algorithm: " +
                          self.best_algorithm)

                    # TODO instantiate best performing algorithm

                    if self.current_alg_dep is not None:
                        self.k_api.kube_delete_deployment(self.current_alg_dep)
                    sleep(1)
                    best_alg_dep = self.instantiate_best_alg()

                    self.current_alg_dep = best_alg_dep

                    r = requests.patch(
                        url=self.production_parameter_url, params={
                            "value": self.best_algorithm}
                    )

        except Exception as e:
            print(f"Error determining next best algorithm: {repr(e)}")
            print(traceback.format_exc())

    def process_apply_on_cpps(self, msg):
        new_appl_result = self.decode_msg(msg)
        if new_appl_result["algorithm"] == self.best_algorithm:
            adaption_data = {
                "algorithm": new_appl_result["algorithm"],
                "new_x": new_appl_result["new_x"],
            }

            self.send_msg(topic="AB_new_x", message=adaption_data)
            print(
                f"Sent application results to Adaption: x={new_appl_result['new_x']}")
        else:
            print(
                f"Apply on CPPS receives from {new_appl_result['algorithm']} but current best algo is {self.best_algorithm}")

    def process_cluster_monitoring(self, msg):
        # TODO save resources into self.df_sim
        # TODO adjust config to listen on AB_cluster_monitoring
        pass
