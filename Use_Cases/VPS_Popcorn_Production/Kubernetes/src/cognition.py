import json
import pydash
import pandas as pd
import numpy as np
import rpy2.robjects as robjects
from rpy2.robjects import pandas2ri
from rpy2.robjects.conversion import localconverter
from sklearn import preprocessing
import os

##### mocking some methods here first, replace them by message driven module processing later 
def generate_initial_design(X_MIN, X_MAX, N_INITIAL_DESIGN):
    """ number n_initial_design equally spaced X between X_MIN, X_MAX """
    x = np.linspace(X_MIN, X_MAX, num=N_INITIAL_DESIGN)
    return x

def normalize_values(df, norm_source, norm_dest):
        df[norm_dest] = (df[norm_source] - df[norm_source].min()) /\
                (df[norm_source].max()-df[norm_source].min())

def applyToCPPS(x):
    # fit model
    # apply predict
    y = 1.0 * x
    return y

def get_goal():
    """
    returns goal in 4-stage-format:

    1. Use case
    2. Signal(s)
    3. Aggregation / Feature
    4. Goal

    """
    pass

def load_knowledge(path):
    with open(path) as f:
        return json.load(f)


def get_from_knowledge(knowledge, search_base, search):

    result = None

    search_string = search_base + '.' + search

    try:
        result = pydash.get(knowledge, search_string)
    except:
        print(f'Error while searching: {search_string}')

    return result


def get_pipelines(knowledge, search_base, search, parent=None, pipelines=[]):

    result = get_from_knowledge(knowledge, search_base, search)

    if result is None:
        return pipelines

    for key, values in result.items():
        pipeline = (key, values)

        if parent is not None:
            pipeline = (pipeline, *parent)
        else:
            pipeline = (pipeline,)

        if values['input'] == 'raw data':
            pipelines.append(pipeline)
        else:
            pipelines = get_pipelines(knowledge, search_base, values['input'], pipeline, pipelines)

    return pipelines


def print_pipelines(pipelines):
    """ prints the feasible, complete pipelines

    :param pipelines: list of pipelines
    """
    for i, pipeline in enumerate(pipelines):
        print(f'Pipeline {i + 1}')
        print(pipeline)

# Evaluation of benchmark experiment according to weighted performance
def evaluate_benchmark(e, sequence):
    best = e[e.y_agg == e.y_agg.max()]['algorithm'][0]
    return best

def aggregatePerformance(cpu, memory, y):
    # TODO adjusted weights? get from Knowledge?
    # compute weighted aggregation
    weightY = 0.8
    weightC = 0.1
    weightM = 0.1
    return (weightY * y) + (weightC * cpu) + (weightM * memory)

def pipelineSelectionProcess(s, theta, knowledge, g, r, dH):
    """ 
    s: init design size
    theta: pipeline selection frequency
    knowledge: knowledge base (algorithms etc.)
    g: goal
    r: available resources
    dH: historical data (if any)
    """
    print("Init variables")
    cycle = 0
    etha = 0 # controls reinstanciation of pipelines
    e = pd.DataFrame() # evaluation list
    # e = None
    d = list() # list of current data 
    pR = list() # pipeline resource consumptions
    x = float # control parameter 
    
    if dH is None:
        l = generate_initial_design(X_MIN=X_MIN, X_MAX=X_MAX,N_INITIAL_DESIGN=N_INITIAL_DESIGN) # get initial set of control parameters to evaluate
        for param in l: 
            d.append(applyToCPPS(param))
            x = param
    else:
        d = dH

    # counter algorithm selection sequence
    sequence = 1

    # starting from here, look each theta cycles and evaluate optimizers
    etha = 1 # for convenience, enforce algorithm selection right now, as sufficient data is there
    while (cycle < MAX_PRODUCTION_CYCLES):
        if 0 == (cycle % theta) or 1 == etha: # 
            print('Cycle: ' + str(cycle))
            etha = 0

            # sample candidate pipelines according to available resources r
            # d data points
            # g goal
            # r available ressources
            # e evaluation list            
            new_e = simulateAndBenchmark(d, g, r, e, sequence) # should use previously grabbed feasiblePipelines inside R

            # compute weighted aggregated performance
            new_e['y_agg'] = np.vectorize(aggregatePerformance)(cpu = new_e['relCpuNorm'], memory = new_e['relMemoryNorm'], y = new_e['relYNorm'])
            print(new_e)

            # get p_best from e
            best = evaluate_benchmark(new_e, sequence)
            ## TODO apply best on CPPS
            print("best optimizer: " + best)

            # append new_e to e
            e.append(new_e)

            # increment sequence
            sequence = sequence + 1            
        else: 
            print("No selection required")
        cycle = cycle + 1

#### everything below is executed
# CONSTANTS ARE UPPERCASE

NUMBER_OF_SIMULATION_CYCLES = 5 # Cognition is allowed to adjust this
MIN_NUMBER_OF_PRODUCTION_CYCLES = 5 # Cognition is allowed to adjust this

MIN_SIMULATION_PIPELINES = 3 # Cognition is allowed to adjust this
MAX_SIMULATION_PIPELINES = 8 # Cognition is allowed to adjust this

MIN_PRODUCTION_PIPELINES = 3 # Cognition is allowed to adjust this
MAX_PRODUCTION_PIPELINES = 8 # Cognition is allowed to adjust this

MIN_CYCLES_BEFORE_ALGORITHM_SWITCH = 20

N_INITIAL_DESIGN = 10
MAX_PRODUCTION_CYCLES = 50
X_MIN = 4000.0
X_MAX = 10100.0 

user_input = {'use_case': 'Optimization',
              'goal': 'minimize',
              'feature': 'minimum',
              'sensor': 'l_rPower' # target_variable at last spot?, how to handle multiple criteria?
              }

# os.path.dirname(os.path.abspath(__file__))

# user_input = get_goal()
#knowledge = load_knowledge('data/knowledge.yaml')

# make search_base and algorithm selection dynamic
search_base = f'{user_input["use_case"]}.{user_input["goal"]}.{user_input["feature"]}'
algorithm_selection = 'algorithms'

#recursively builds pipelines from knowledge, stops at "raw_data"
#pipelines = get_pipelines(knowledge, search_base, algorithm_selection)

#print_pipelines(pipelines)
    
########## call cognition stuff from r scripts starts here ############
def getHistoricalData(name):
    """ load process data from database/knowledge
        at the moment: load previous extracted features? by name
    """
    path = "data" + os.path.sep + name
    # path = ".." + os.path.sep + "data" + os.path.sep + name
    result = pd.read_csv(path, sep=';', decimal=',')
    print(result.shape)
    # now chose unique rows (by yAgg)
    

    return(result)

# rpy2 r objects access
r = robjects.r
# source R file of cognition implementation
r.source('cognition.R')

# r data.frame to pandas conversion 
# pandas2ri.activate()
pandas2ri.activate()

# get R function interface of simulation and generation and benchmark experiments
simulateAndBenchmark = robjects.r["simulateAndBenchmark"]

# vpsFeatures_It2_AlterMais.csv 
# vpsFeatures_It2_Premium.csv
# vpsFeatures_It1_20191220.csv
dataPoints = getHistoricalData("vpsFeatures.csv") 


""" 
s: init design size
theta: pipeline selection frequency
knowledge: knowledge base (algorithms etc.)
g: goal
r: available resources
dH: historical data (if any)
"""
s = N_INITIAL_DESIGN
theta = MIN_CYCLES_BEFORE_ALGORITHM_SWITCH
knowledge = ""
r = 3
dH = robjects.DataFrame(dataPoints) # 

g = robjects.ListVector(user_input) # 

print(" --- Start pipeline selection process --- ")
pipelineSelectionProcess(s, theta, knowledge, g, r, dH)


print(" --- Finish pipeline selection process --- ")


