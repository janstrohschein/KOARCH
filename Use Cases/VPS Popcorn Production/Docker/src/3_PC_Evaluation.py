import os
from time import sleep
from datetime import datetime

import pandas as pd
import numpy as np

from classes.KafkaPC import KafkaPC
from classes.util import ObjectiveFunction

pd.set_option('display.max_columns', None)
pd.options.display.float_format = '{:.3f}'.format

"""
- bekommt die y_pred beider Algorithmen
- wertet beide gegen die Zielfunktion aus, Delta berechnen
- Ergebnisse in Tabelle vorhalten
- besseren Wert an Adaption schicken (bessere Vorhersage)
"""

env_vars = {'kafka_broker_url': os.getenv('KAFKA_BROKER_URL'),
            'in_topic': os.getenv('IN_TOPIC'),
            'in_group': os.getenv('IN_GROUP'),
            'in_schema_file': os.getenv('IN_SCHEMA_FILE'),
            'out_topic': os.getenv('OUT_TOPIC'),
            'out_schema_file': os.getenv('OUT_SCHEMA_FILE')}
"""
env_vars = {'in_topic': 'AB_model_application',
            'in_group': 'evaluation',
            'in_schema_file': './schema/model_appl.avsc',
            'out_topic': 'AB_model_evaluation',
            'out_schema_file': './schema/new_x.avsc'
            }
"""

df_columns = ['phase', 'model_name', 'n_data_points', 'id_start_x', 'model_size', 'best_x', 'best_pred_y',
              'y', 'y_delta', 'rmse', 'mae', 'rsquared', 'CPU_ms', 'RAM', 'timestamp']

df = pd.DataFrame(columns=df_columns)

new_pc = KafkaPC(**env_vars)

MAX_DATA_POINTS = 50
current_data_point = 1

"""initialize objective function"""
new_objective = ObjectiveFunction()
new_objective.load_data()
new_objective.fit_model()


"""generate initial design"""
N_INITIAL_DESIGN = 5
X_MIN = 4000.
X_MAX = 10100.
# equally spaced X between X_MIN, X_MAX
X = np.linspace(X_MIN, X_MAX, num=N_INITIAL_DESIGN)

print('Creating initial design of the system by applying '+ str(N_INITIAL_DESIGN)+ ' equal distributed values x over the whole working area of the CPPS.')

for x in X:
    """
    "name": "New X",
    "fields": [
         {"name": "phase", "type": ["enum"], "symbols": ["init", "observation"]},
         {"name": "id_x", "type": ["int"]},
         {"name": "new_x", "type": ["float"]}
     ]
    """

    new_x = {'phase': 'init',
             'id_x': current_data_point,
             'new_x': x}
    current_data_point += 1

    new_pc.send_msg(new_x)
    print(f'Sent x={new_x["new_x"]}')


"""evaluation"""
#print('Done sending initial design, now receiving results')
print('Initialization phase is completed. Now, the algorithms are applied.')
for msg in new_pc.consumer:
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

    new_model_appl = new_pc.decode_avro_msg(msg)
    best_pred_y = new_model_appl['best_pred_y']
    y = new_objective.get_objective(new_model_appl['best_x'])
    y_delta = abs(y - best_pred_y) # absoluter Wert?

    new_model_appl['y'] = y
    new_model_appl['y_delta'] = y_delta
    new_model_appl['timestamp'] = datetime.now()


    df = df.append(new_model_appl, ignore_index=True)

    min_best_pred_y = df.loc[df['best_pred_y'].idxmin()]
    new_x = min_best_pred_y.best_x
  #  print(df[['model_name', 'n_data_points', 'id_start_x', 'best_x', 'best_pred_y', 'rmse', 'rsquared', 'CPU_ms', 'RAM']] .sort_values(by=['best_pred_y']))
    print(df[['model_name', 'best_x', 'best_pred_y', 'rmse', 'rsquared', 'CPU_ms', 'RAM']].iloc[-1:])

    """
    "name": "New X",
    "fields": [
        {"name": "phase", "type": ["string"]},
        {"name": "id_x", "type": ["int"]},
        {"name": "new_x", "type": ["float"]}
        ]
    """
    new_x = {'phase': 'observation',
             'id_x': current_data_point,
             'new_x': new_x}

    if current_data_point > MAX_DATA_POINTS:
        continue

    current_data_point += 1
   
    print('The x value of the algorithm '+str(min_best_pred_y['model_name'])+' is applied to the CPPS, since the lowest y is expected (y='+str(min_best_pred_y['best_pred_y'])+').')

    new_pc.send_msg(new_x)
