#!/usr/bin/python3
import sys
import json
import numbers

# Using plotly.express
import plotly.graph_objects as go
from datetime import datetime

# sys.argv[1] = data (all database data)
# sys.argv[2] = xaxis (name of datetime column in database)
# sys.argv[3] = userName (name of userName column in database)

try:
    # get data from sys.argv[1] and convert them into python dictionary
    userData = json.loads(sys.argv[1])
    # get keys from python dictionary in dataRowNames variable
    dataRowNames = userData[0].keys()
    # get dateRowName from sys.argv[2]
    idRowName = sys.argv[2]
except IndexError:
    sys.stderr.write("Wrong amount of arguments in sys.argv or no data")
    exit(1)
except json.JSONDecodeError:
    sys.stderr.write("Data is not a JSON-String")
    exit(2)

# format, in which date should be converted later
dateFormat = "%Y-%m-%d %H:%M:%S"

# list of dates. Need this later to get the borders of graph (min/max)
idList = []
for data in userData:
    try:
        idList.append(data[idRowName])
    except KeyError:
        sys.stderr.write("Given rowname of id in sys.argv[2] doesnt exist in data")
        exit(4)


# get dataRowNames that should be plotted
dynamicNav = ""
defaultDataRowname = ""
for dataRowName in dataRowNames:
    if dataRowName != idRowName and (len(sys.argv) < 4 or dataRowName != sys.argv[3]):
        if defaultDataRowname == "":
            defaultDataRowname = dataRowName
        dynamicNav += '<li id="navElement-' + dataRowName + '" class="navElement"'
        dynamicNav += (
            """ onclick="showPlot('"""
            + dataRowName
            + """');">"""
            + dataRowName
            + """</li>"""
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
<input id="checkbox" type="checkbox" name="autoRefresh">
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

    document.getElementById(plotKey).style.display='block';
    window.dispatchEvent(new Event('resize'));
}

</script>
"""
)


# create layout function
def createLayout(x_axisTitle, y_axisTitle):
    return go.Layout(xaxis=dict(title=x_axisTitle), yaxis=dict(title=y_axisTitle))


# plot one User
def plotData(userData, dataRowNames, idRowName, idList):

    for dataRowName in dataRowNames:

        if dataRowName != idRowName:

            x_axisData = []
            y_axisData = []
            hoverData = []
            for data in userData:

                id = data[idRowName]
                if isinstance(id, basestring):
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
                    not isinstance(data[dataRowName], numbers.Number)
                    and data[dataRowName] is not None
                ):
                    sys.stderr.write("Cannot plot non-numerical data.")
                    exit(6)
                y_axisData.append(data[dataRowName])
                hoverString = ""
                # fill hoverString with data that should be shown when mousehover a value in the graph
                for key, value in data.items():
                    hoverString += str(key) + ": " + str(value) + "<br>"
                # <extra> is used to define a title for hovered data. If not empty, default is name of trace
                hoverData.append(hoverString + "<extra></extra>")

            # create layout with given titles
            layout = createLayout(idRowName, dataRowName)

            # create graph
            fig = go.Figure(
                data=[
                    go.Scatter(
                        x=x_axisData,
                        y=y_axisData,
                        hovertemplate=hoverData,
                        mode="markers",
                    )
                ],
                layout=layout,
            )

            # print the graph as html
            print(
                '<div id="'
                + dataRowName
                + '" class="visibleElements" style="display: none;">'
            )
            print(fig.to_html())
            print("</div>")


# plot multiple users in one Graph
def plotMultipleData(userData, dataRowNames, idRowName, idList):

    # get rowname of username column
    userRowName = sys.argv[3]
    userNames = set()

    # fill the set with all usernames, no duplicates
    for data in userData:
        try:
            userNames.add(data[userRowName])
        except KeyError:
            sys.stderr.write(
                "Given rowname of username in sys.argv[3] doesnt exist in data"
            )
            exit(5)

    for dataRowName in dataRowNames:

        if dataRowName != idRowName and dataRowName != userRowName:

            layout = createLayout(idRowName, dataRowName)

            # create empty layout
            fig = go.Figure(layout=layout)

            for userName in userNames:
                x_axisData = []
                y_axisData = []
                hoverData = []

                for data in userData:
                    # check if data belongs to current username
                    if data[userRowName] == userName:
                        id = data[idRowName]
                        # fill x_axisData with associated values and convert them into datetime object
                        x_axisData.append(id)
                        # fill y_axisData with associated values
                        if (
                            not isinstance(data[dataRowName], numbers.Number)
                            and data[dataRowName] is not None
                        ):
                            sys.stderr.write("Cannot plot non-numerical data.")
                            exit(6)
                        y_axisData.append(data[dataRowName])
                        hoverString = ""
                        # fill hoverString with data that should be shown when mousehover a value in the graph
                        for key, value in data.items():
                            hoverString += str(key) + ": " + str(value) + "<br>"
                        # <extra> is used to define a title for hovered data. If not empty, default is name of trace
                        hoverData.append(hoverString + "<extra></extra>")

                # add trace to graph
                fig.add_trace(
                    go.Scatter(
                        x=x_axisData,
                        y=y_axisData,
                        mode="markers",
                        name=userName,
                        hovertemplate=hoverData,
                    )
                )

            # print the graph as html
            print(
                '<div id="'
                + dataRowName
                + '" class="visibleElements" style="display: none; width:100%;">'
            )
            print(fig.to_html())
            print("</div>")


if len(sys.argv) == 3:
    plotData(userData, dataRowNames, idRowName, idList)
if len(sys.argv) == 4:
    plotMultipleData(userData, dataRowNames, idRowName, idList)

print(
    """<script src="/socket.io/socket.io.js"></script>
<script>
if (sessionStorage.getItem(window.location.href) === null) {
    showPlot('"""
    + defaultDataRowname
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
});
</script>"""
)
print("</body>")
print("</html>")
