from ..classes import ml_util


def test_objective_function():
    new_objective = ml_util.ObjectiveFunction()
    new_objective.load_data(path="Use Cases/VPS Popcorn Production/Docker/src/data/vpsFeatures.csv")
    new_objective.fit_model()
    prediction = new_objective.get_objective(4000)
    assert prediction == 0.6553353728953759
