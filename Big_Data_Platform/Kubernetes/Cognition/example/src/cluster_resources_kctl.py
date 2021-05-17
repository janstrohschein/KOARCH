#!/usr/bin/env python3

""" This script executes the command kubectl describe nodes and outputs the node name, cpu stats & memory stats in
     a json file. Author https://github.com/prasadjjoshi """


import os
import json

DESCRIBE_COMMAND_OUTPUT_FILE = 'nodes.log'
node_properties = {}
ALLOCATED_RESOURCES = 'Allocated resources'
props_to_read = ('Name', ALLOCATED_RESOURCES)
node_name_dict = {}
node_name = ""

def get_name():
    global line, node_name, node_name_dict
    line = line.split(":")
    node_name = line[1].strip()
    if not node_properties.__contains__(node_name):
        node_properties[node_name] = None
    node_name_dict = {line[0].strip(): line[1].strip()}


def get_cpu():
    global line, cpu_res
    line = line.split()
    cpu = line[0]
    cpu_res = {
        cpu:
            {requests_key: line[1] + " " + line[2], limits_key: line[3] + " " + line[4]}
    }


def get_memory():
    global line, mem_res
    line = line.split()
    mem = line[0]
    mem_res = {
        mem:
            {requests_key: line[1] + " " + line[2], limits_key: line[3] + " " + line[4]}
    }


def get_allocated_resources():
    global line, cpu_res, mem_res, requests_key, limits_key
    line = lines.__next__()
    resources = ""
    cpu_res = {}
    mem_res = {}
    requests_key = ""
    limits_key = ""
    while not line.startswith("Events"):

        if line.strip().startswith("Resource"):
            line = line.split()
            resource_key = line[0]
            requests_key = line[1]
            limits_key = line[2]

        elif line.strip().startswith('cpu'):
            get_cpu()

        elif line.strip().startswith('memory'):
            get_memory()

        line = lines.__next__()  # iterating till events to get all resources


def kubectl_describe_nodes():
    global lines, line
    # kubectl command to execute & outputting in nodes.log file in cwd
    myCmd = 'kubectl describe nodes > ' + DESCRIBE_COMMAND_OUTPUT_FILE
    os.system(myCmd)
    describe_command_output_file = os.getcwd() + '/' + DESCRIBE_COMMAND_OUTPUT_FILE
    # Iterating through command's output in nodes.log and reading values
    lines = open(describe_command_output_file, "r")
    if lines.__sizeof__() > 0:
        for line in lines:
            if line.startswith("Name"):
                get_name()

            elif line.startswith(ALLOCATED_RESOURCES):
                get_allocated_resources()

                all_props_of_node = [node_name_dict, cpu_res, mem_res]
                node_properties[node_name] = all_props_of_node
    print(node_properties)
    # r = json.dumps(node_properties, indent=2)
    # print(r)
    # Outputting in output.json file in cwd
    # with open('output.json', 'w') as outfile:
    #     json.dump(node_properties, outfile, indent=2)


if __name__ == '__main__':
    kubectl_describe_nodes()
