import pandas as pd

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

df_sim = pd.DataFrame(columns=df_sim_columns)

job_info = {"selection_phase": 0,
            "algorithm": "Kriging"}
job_series = pd.Series(job_info)
df_sim = df_sim.append(job_series, ignore_index=True)

job_info = {"selection_phase": 1,
            "algorithm": "Kriging",
            "x": 5,
            "y": 12}
job_series = pd.Series(job_info)
df_sim = df_sim.append(job_series, ignore_index=True)

new_sim_results = {"algorithm": "Kriging",
                   "CPU_ms": 0.123,
                   "RAM": 1.234}

# find max selection_phase
selection_phase = df_sim['selection_phase'].max()
# conditions for df
con_phase = df_sim['selection_phase'] == selection_phase
con_al = df_sim['algorithm'] == new_sim_results["algorithm"]

# append to df_sim
in_df = df_sim[con_phase & con_al].index.tolist()
if len(in_df) == 0:
    df_sim = df_sim.append(
        new_sim_results, ignore_index=True)
else:
    new_sim_series = pd.Series(new_sim_results)
    df_sim.iloc[in_df[0]]['CPU_ms'] = new_sim_results["CPU_ms"]
    df_sim.iloc[in_df[0]]['RAM'] = new_sim_results["RAM"]

print(df_sim)
