import os
from classes.CKafkaPC import KafkaPC


def plot_monitoring(msg):
    """
    localhost:8003/plotData/
    """
    msgdata = new_c.decode_msg(msg)

    # plot tells if message is send as topic for plotData or plotMultipleData
    # x_label is the label of xaxis
    # x_data is data of xaxis
    # x_int_to_date: set it True if your x_data is an integer-value, but you want to convert it to datetime
    # y - yaxis-Data
    new_data_point = {
        "plot": "single",
        "x_label": "id",
        "source": "monitoring",
        "x_data": msgdata["id"],
        "x_int_to_date": False,
        "y": {"x": msgdata["x"], "y": msgdata["y"]},
    }

    new_c.send_msg(new_data_point)
    print("monitoring message sent")


def plot_model_evaluation_multi(msg):
    """
    localhost:8003/plotMultipleData/
    """

    msgdata = new_c.decode_msg(msg)
    splitData = msgdata["algorithm"].split("(")

    # plot tells if message is send as topic for plotData or plotMultipleData
    # x_label is the label of xaxis
    # x_data is data of xaxis
    # x_int_to_date: set it True if your x_data is an integer-value, but you want to convert it to datetime
    # y - yaxis-Data
    new_data_point = {
        "plot": "multi",
        "multi_filter": "algorithm",
        "source": "model_evaluation",
        "x_label": "id",
        "x_data": msgdata["id"],
        "x_int_to_date": False,
        "y": {"new_x": msgdata["new_x"], "algorithm": splitData[0]},
    }

    new_c.send_msg(new_data_point)
    print("model evaluation message sent")


def plot_model_application(msg):
    """
    localhost:8003/plotData/
    """

    msgdata = new_c.decode_msg(msg)

    new_data_point = {
        "plot": "single",
        "source": "model_application",
        "x_label": "id",
        "x_data": msgdata["id"],
        "x_int_to_date": False,
        "y": {
            "pred_y": msgdata["pred_y"],
            "rmse": msgdata["rmse"],
            "CPU_ms": msgdata["CPU_ms"],
            "RAM": msgdata["RAM"],
        },
    }

    new_c.send_msg(new_data_point)
    print("model application message sent")


def plot_model_application_multi(msg):

    msgdata = new_c.decode_msg(msg)

    new_data_point = {
        "plot": "multi",
        "multi_filter": "model_name",
        "source": "model_application",
        "x_label": "id",
        "x_data": msgdata["id"],
        "x_int_to_date": False,
        "y": {
            "model_name": msgdata["model_name"],
            "pred_y": msgdata["pred_y"],
            "rmse": msgdata["rmse"],
            "CPU_ms": msgdata["CPU_ms"],
            "RAM": msgdata["RAM"],
        },
    }

    new_c.send_msg(new_data_point)
    print("model application message sent")


env_vars = {
    "config_path": os.getenv("config_path"),
    "config_section": os.getenv("config_section"),
}

new_c = KafkaPC(**env_vars)

plot_dict = new_c.config["PLOT_TOPIC"]
try:
    while True:
        msg = new_c.consumer.poll(0.1)

        if msg is None:
            continue

        elif msg.error() is not None:
            print(f"Error occured: {str(msg.error())}")

        else:
            # tests if msg.topic is in plot_dict and calls function from dict
            try:
                if plot_dict.get(msg.topic()) is not None:
                    eval(plot_dict[msg.topic()])(msg)
            except Exception as e:
                print(
                    f"Processing Topic: {msg.topic()} with Function: {plot_dict[msg.topic()]}\n Error: {e}"
                )
            

except KeyboardInterrupt:
    pass

finally:
    new_c.consumer.close()
