#!/usr/bin/python3
import sys
import json
import numbers
# Using plotly.express
import plotly.graph_objects as go
from datetime import datetime

# sys.argv[1] = data (all database data)

try:
    # get data from sys.argv[1] and convert them into python dictionary
    userData = json.loads(sys.argv[1])
except IndexError:
    sys.stderr.write("No data available")
    exit(1)

except json.JSONDecodeError:
    sys.stderr.write("Data is not a JSON-String")
    exit(2)

# format, in which date should be converted later
dateFormat = "%Y-%m-%d %H:%M:%S"

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
print(
    """<!DOCTYPE html>

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

<ul id="navi" style="display: grid; grid-template-columns: repeat(auto-fit, 226px);">"""
    + dynamicNav
    + """</ul>
<br><br>

<div>
<input id="checkbox" type="checkbox" name="autoRefresh" onclick="sessionStorage.setItem('autoRefresh', document.getElementById('checkbox').checked);">
<label for="checkbox">auto plot refresh</label>
</div>

<script>
function showPlot(plotKey) {

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
)


# create layout function
def createLayout(x_axisTitle, y_axisTitle):
    return go.Layout(xaxis=dict(title=x_axisTitle), yaxis=dict(title=y_axisTitle))


# plot one User
def plotData(userData):
    firstDataPoint = userData[userData.keys()[0]][0]
    isSingleData = firstDataPoint["multi_filter"] is None

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
            print(
                '<div id="graph-{}-{}" class="visibleElements" style="display: none;">'.format(
                    source, dataRowName
                )
            )
            print(fig.to_html())
            print("</div>")


firstDataPoint = userData[userData.keys()[0]][0]

plotData(userData)

if firstDataPoint["y"].keys()[0] == firstDataPoint["multi_filter"]:
    firstLabelIndex = 1
else:
    firstLabelIndex = 0


print(
    """<script src="/socket.io/socket.io.js"></script>
<script>
if (sessionStorage.getItem("autoRefresh") !== null) {
    document.getElementById("checkbox").checked = sessionStorage.getItem("autoRefresh");
}

if (sessionStorage.getItem(window.location.href) === null) {
    showPlot('"""
    + userData.keys()[0]
    + "-"
    + firstDataPoint["y"].keys()[firstLabelIndex]
    + """')

}
else {
    showPlot(sessionStorage.getItem(window.location.href));
}

var socket = io();

socket.on("refresh", () => {
    if (document.getElementById("checkbox").checked == true) {
        window.location.reload();
      }
    else {
        checkboxStorage = false;
    }
});
</script>"""
)
print("</body>")
print("</html>")
