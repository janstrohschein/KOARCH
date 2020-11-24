import os
import json
import sys
import csv
from enum import Enum
import yaml
from fastapi import FastAPI
from fastapi.responses import JSONResponse, FileResponse, HTMLResponse
from pydantic import BaseModel
from collections import deque

import numbers
import requests
import os

# Using plotly.express
import plotly.graph_objects as go
from datetime import datetime


def read_config(config_path, config_section):
    config = {}
    if config_path is not None and config_section is not None:
        config_section = config_section.replace(" ", "").split(",")
    else:
        raise ValueError("Configuration requires config_path and config_section")
    try:
        with open(config_path, "r") as ymlfile:
            config = yaml.load(ymlfile, Loader=yaml.FullLoader)
            for section in config_section:
                for key, value in config[section].items():
                    config[key] = value
        return config

    except Exception as e:
        print(f"Failed to read the config: {repr(e)}")
        sys.exit()


config_path = os.getenv('config_path')
config_section = os.getenv('config_section')

print(config_path)
print(config_section)

config = read_config(config_path, config_section)

plot_api = FastAPI()
data = dict()
dataMultiple = dict()

 # format, in which date should be converted later
dateFormat = "%Y-%m-%d %H:%M:%S"

@plot_api.get("/getData")
async def get_data():
    return HTMLResponse(content=generateHTML(data), status_code=200)

@plot_api.get("/getDataMultiple")
async def get_data_multiple():
    return HTMLResponse(content=generateHTML(dataMultiple), status_code=200)

@plot_api.post("/postData")
async def post_result(decodedMessage: dict):
    source = decodedMessage["source"]
    if decodedMessage["multi_filter"] is not None:
        if source not in dataMultiple:
            dataMultiple[source] = deque(maxlen=config["WINDOW_SIZE"])

        dataMultiple[source].append(decodedMessage)
    else:
        if source not in data:
            data[source] = deque(maxlen=config["WINDOW_SIZE"])
        data[source].append(decodedMessage)

    return JSONResponse(decodedMessage, status_code=200)

def generateHTML(userData):

    # get dataRowNames that should be plotted
    dynamicNav = ""

    for source in userData:
        for dataRowName in userData[source][0]["y"]:
            if dataRowName == userData[source][0]["multi_filter"]:
                continue
            dynamicNav += '<li id="navElement-{}-{}" class="navElement"'.format(
                source, dataRowName
            )
            dynamicNav += """ onclick="showPlot('{}-{}');">{}-{}</li>""".format(
                source, dataRowName, source, dataRowName
            )

    # html-code of navbar
    html = """<!DOCTYPE html>

    <html>
    <head>
    <style>
    ul {
    list-style-type: none;
    margin: 0;
    padding: 0;
    overflow: hidden;
    background-color: #555;
    }

    li {
    float: left;
    display: block;
    color: white;
    text-align: center;
    padding: 14px 16px;
    text-decoration: none;
    }

    .active {
    background-color: #f1f1f1;
    color: black;
    }
    </style>
    </head>
    <body>

    <ul id="navi" style="display: grid; grid-template-columns: repeat(auto-fit, 226px);">""" + dynamicNav + """</ul>
    <br><br>

    <div>
    <input id="checkbox" type="checkbox" name="autoRefresh" onclick="sessionStorage.setItem('autoRefresh', document.getElementById('checkbox').checked);">
    <label for="checkbox">auto plot refresh</label>
    </div>

    <script>
    var currentSource = "";
    function showPlot(plotKey) {
        currentSource = plotKey.split("-")[0];
        sessionStorage.setItem(window.location.href, plotKey);
        var showElements = document.getElementsByClassName("visibleElements");
        for (var i = 0; i < showElements.length; i++) {
            showElements[i].style.display='none';
        }

        if (document.getElementsByClassName("active").length > 0) {
            var previousActiveNavbarElement = document.getElementsByClassName("active")[0];
            previousActiveNavbarElement.className = previousActiveNavbarElement.className.replace(" active", "");
        }
        var newActiveNavbarElement = document.getElementById(`navElement-${plotKey}`);
        newActiveNavbarElement.className += " active";

        document.getElementById(`graph-${plotKey}`).style.display='block';
        window.dispatchEvent(new Event('resize'));

    }

    </script>
    """

    firstDataPoint = userData[list(userData.keys())[0]][0]

    html += plotData(userData)

    if list(firstDataPoint["y"].keys())[0] == firstDataPoint["multi_filter"]:
        firstLabelIndex = 1
    else:
        firstLabelIndex = 0

    html += """<script src="/socket.io/socket.io.js"></script>
    <script>
    if (sessionStorage.getItem("autoRefresh") !== null) {
        document.getElementById("checkbox").checked = sessionStorage.getItem("autoRefresh");
    }

    if (sessionStorage.getItem(window.location.href) === null) {
        showPlot('""" + list(userData.keys())[0] + "-" + list(firstDataPoint["y"].keys())[firstLabelIndex] + """')

    }
    else {
        showPlot(sessionStorage.getItem(window.location.href));
    }

    var socket = io();
    var isReloading = false;
    socket.on("refresh", async function(source) {
        if (document.getElementById("checkbox").checked == true && source == currentSource) {
            await new Promise(r => setTimeout(r, 1000));
            if (document.getElementById("checkbox").checked == true) {
                if (!isReloading) {
                    isReloading = true;
                    window.location.reload();
                }
            }
        }
        else {
            checkboxStorage = false;
        }
    });
    </script>"""

    html += "</body>"
    html += "</html>"

    return html


# create layout function
def createLayout(x_axisTitle, y_axisTitle):
    return go.Layout(xaxis=dict(title=x_axisTitle), yaxis=dict(title=y_axisTitle))


# plot one User
def plotData(userData):
    firstDataPoint = userData[list(userData.keys())[0]][0]
    isSingleData = firstDataPoint["multi_filter"] is None

    plotHTML = ""

    for source in userData:
        filterSet = set()

        if not isSingleData:
            for dataPoint in userData[source]:
                filterSet.add(dataPoint["y"][dataPoint["multi_filter"]])
        else:
            filterSet.add("")

        for dataRowName in userData[source][0]["y"]:
            if dataRowName == userData[source][0]["multi_filter"]:
                continue

            # create layout with given titles
            layout = createLayout(userData[source][0]["x_label"], dataRowName)
            fig = go.Figure(layout=layout)

            for traceName in filterSet:

                x_axisData = []
                y_axisData = []
                hoverData = []

                for dataPoint in userData[source]:
                    if (
                        isSingleData
                        or dataPoint["y"][dataPoint["multi_filter"]] == traceName
                    ):
                        id = dataPoint["x_data"]
                        if isinstance(id, str):
                            try:
                                x_axisData.append(datetime.strptime(id, dateFormat))
                            except ValueError:
                                sys.stderr.write(
                                    "Given dates from date row doesnt match the format YYYY-MM-DD HH:MM:SS"
                                )
                                exit(3)
                        else:
                            x_axisData.append(id)
                        # fill y_axisData with associated values
                        if (
                            not isinstance(dataPoint["y"][dataRowName], numbers.Number)
                            and dataPoint["y"][dataRowName] is not None
                        ):
                            sys.stderr.write("Cannot plot non-numerical data.")
                            exit(6)
                        y_axisData.append(dataPoint["y"][dataRowName])
                        hoverString = ""
                        # fill hoverString with data that should be shown when mousehover a value in the graph
                        hoverString += (
                            str(dataPoint["x_label"])
                            + ": "
                            + str(dataPoint["x_data"])
                            + "<br>"
                        )
                        for key, value in dataPoint["y"].items():
                            hoverString += str(key) + ": " + str(value) + "<br>"
                        # <extra> is used to define a title for hovered data. If not empty, default is name of trace
                        hoverData.append(hoverString + "<extra></extra>")

                # create graph
                fig.add_trace(
                    go.Scatter(
                        x=x_axisData,
                        y=y_axisData,
                        mode="markers",
                        name=traceName,
                        hovertemplate=hoverData,
                    )
                )

            # print the graph as html
            plotHTML += '<div id="graph-{}-{}" class="visibleElements" style="display: none;">'.format(
                    source, dataRowName
                )

            plotHTML += fig.to_html()
            plotHTML += "</div>"
    return plotHTML
