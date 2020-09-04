# Cognition
Cognitive capabilities allow to make decisions and adapt to new situations. 
The usage of these capabilities for the selection of AI algorithms enables the system to learn over time and choose suitable algorithms by itself.
This can be a key feature to reach a high degree of autonomy and efficiency in cyber-physical production systems (CPPS). 

Process pipelines are defined as sequence of processing modules, e.g., a preprocessing module, followed by a modelling module wrapped up by an optimization module to find an optimum of the model. 
The purpose of the pipelines is the optimization of the production process.

The cognition module evaluates the pipelines' quality, and switches to promising pipelines during the operational phase if necessary, e.g., if they are likely more efficient w.r.t. accuracy or resource consumption (or both). 

The Cognition in its current state implements the following functionality:
- Initializes the objective function with historic data. The user defines the parameters for the objective function in `./src/configurations/config.yml` :
  ```
  Objective_Function:
  data_path: ./data/vpsFeatures.csv
  x_columns:
    conveyorRuntimeMean: float
  y_columns:
    yAgg: float
  ```
- Generate the initial design based on the number of samples and the use case constraints. The user defines the parameters for the initial design in `./src/configurations/config.yml` :
  ```
  Initial_Design:
  N_INITIAL_DESIGN: 5
  MAX_PRODUCTION_CYCLES: 50
  X_MIN: 4000.0
  X_MAX: 10100.0 
  ```
- Processes incoming messages from the model application module and normalizes the values, predicts model quality and rates the resource consumption.
  - predicted model quality:\
  `avg(normalized_predicted_y, normalized_rmse)`
  - resource consumption:\
  `avg(normalized_CPU, normalized_RAM)`
- Processes incoming messages from the monitoring module and selects the parameters for the next production cycle
  - use production information to assign the real y-value to the algorithm
  - calculate the real model quality as:\
  `avg(normalized_y, normalyzed_y_delta, normalyzed_rmse)`
  - selects the best algorithm and the according x-value for the next cycle
    - uses the real model quality if available, otherwise uses the predicted model quality
    - considers the resource consumption and the user weights for quality / resource consumption
  
    ```
    model_quality = real_model_quality if real_model_quality is not None else pred_model_quality
    best_algorithm = min(model_quality * user_weight + resources * user_weight)
    ```
  - sends the new parameters to the adaption module

The Cognition depends on several other modules and can not be isolated easily. 
Therefore it is easier to show the capabilities of the cognitive module through a use case.
The VPS use case implementation with detailed explanations and a demonstration of the Cognition can be found [here](../../../Use_Cases/VPS_Popcorn_Production/Docker/readme.md).
