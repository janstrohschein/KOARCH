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

selection_phase = 0
name = "baseline"
job_info = {"selection_phase": selection_phase, "algorithm": name}
job_df = pd.Series(job_info)
df_sim = df_sim.append(job_df, ignore_index=True)

selection_phase = 0
name = "RF"
job_info = {"selection_phase": selection_phase, "algorithm": name}
job_df = pd.Series(job_info)
df_sim = df_sim.append(job_df, ignore_index=True)

selection_phase = 1
name = "baseline"
job_info = {"selection_phase": selection_phase, "algorithm": name,
            "repetition": 10, "budget": 10, "x": 4500, "y": 0.1, "CPU_ms": 200, "RAM": 200}
job_df = pd.Series(job_info)
df_sim = df_sim.append(job_df, ignore_index=True)

selection_phase = 1
name = "RF"
job_info = {"selection_phase": selection_phase, "algorithm": name}
job_df = pd.Series(job_info)
df_sim = df_sim.append(job_df, ignore_index=True)

print(df_sim)

new_sim_results = {"selection_phase": selection_phase, "algorithm": name,
                   "repetition": 10, "budget": 10, "x": 5000, "y": 0.2, "CPU_ms": 100, "RAM": 100}
new_sim_series = pd.Series(new_sim_results)
# this way you can combine several conditions
con_phase = df_sim['selection_phase'] == selection_phase
con_base = df_sim['algorithm'] == "baseline"
con_al = df_sim['algorithm'] == new_sim_results["algorithm"]

con_imp = df_sim["algorithm"] == "impossible"
in_df = df_sim[con_phase & con_imp].index.tolist()
# append to df_sim
new_in_df = df_sim[con_phase & con_al].index.tolist()[0]
# df_sim.loc[new_in_df[0]] = new_sim_df
df_sim.iloc[new_in_df] = new_sim_series


# subselect data of current "selection_phase"
# baseline = df_sim.loc[(df_sim['selection_phase'] == selection_phase) and
#                       (df_sim["algorithm"] == "baseline")]
baseline = df_sim[con_phase & con_base]
print(baseline)


new_not_baseline = new_sim_results["algorithm"] != "baseline"

print(new_not_baseline)

if len(baseline) > 0 and new_not_baseline is True:
    baseline_y = baseline["y"].item()
    baseline_cpu = baseline["CPU_ms"].item()
    baseline_ram = baseline["RAM"].item()

    df_sim.loc[con_phase & con_al, "rel_y"] = (
        baseline_y - df_sim.loc[con_phase & con_al, "y"]) / baseline_y

    print(df_sim)
