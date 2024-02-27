#!/usr/bin/env python3
#
# Generate an animated version of the locks
# of a query. Input data is the JSON output of
# pg_lock_tracker.
#
# Current limitations:
# * Only lock traces of one query are supported.
##########################

import os
import json
import argparse

import igraph
import graphviz

from pg_lock_tracer import __version__
from pg_lock_tracer.helper import PostgreSQLLockHelper

# See https://github.com/magjac/d3-graphviz/blob/master/examples/basic-unpkg-worker.html
HTML_TEMPLATE = """
<!DOCTYPE html>
<meta charset="utf-8">
<body>
<script src="https://d3js.org/d3.v7.js"></script>
<script src="https://unpkg.com/@hpcc-js/wasm@2/dist/graphviz.umd.js"></script>
<script src="https://unpkg.com/d3-graphviz@5/build/d3-graphviz.js"></script>

<style>
.frame_div {
   display: inline-block;
}

#frame_control {
   background-color: lightgray;
   height: 24px;
   margin-bottom: 5px;
   padding-left: 5px;
}

#pause_control {
   padding-left: 20px;
}

input, output {
  vertical-align: middle;
}
</style>
<div id="frame_control">
  Frame <input type="range" id="active_frame_slider" min="0" max="100" value="0" oninput="updateSlider(this.value);" onchange="render();">
  <div id="frames" class="frame_div">
     (<div id="cur_frame" class="frame_div"></div> of <div id="total_frame" class="frame_div"></div>)
  </div>
  <div id="pause_control" class="frame_div">
    <input type="checkbox" id="render_active" name="render_active" value="active" checked onclick="render();">
     <label for="render_active" style="vertical-align: bottom;">&#9658; Play</label>
    </input>
  </div>
</div>

<div id="graph" style="text-align: center;"></div>

<script>
var dotIndex = 0;

var graphviz = d3.select("#graph").graphviz()
    .attributer(attributer)
    .transition(function () {
        return d3.transition("main")
            .ease(d3.easeLinear)
            .delay(500)
            .duration(1500);
    })
    .logEvents(true)
    .engine('circo')
    .on("initEnd", render);

function render() {
    var dotLines = dots[dotIndex];
    var dot = dotLines.join('');
    graphviz
        .renderDot(dot)
        .on("end", function () {
            if (! document.getElementById('render_active').checked) {
                return;
            }
            dotIndex = (dotIndex + 1) % dots.length;
            updateFrames();
            document.getElementById("active_frame_slider").value = dotIndex;
            render();
        })
        .zoom(true);
}

function updateFrames() {
    document.getElementById("cur_frame").innerHTML = dotIndex;
    document.getElementById("total_frame").innerHTML = dots.length;
}

function updateSlider(newValue) {
    dotIndex = Number(newValue);
    updateFrames();
}

function initSlider() {
    document.getElementById("active_frame_slider").value = dotIndex;
    document.getElementById("active_frame_slider").max = dots.length;
}

function attributer(datum, index, nodes) {
    marginWidth = 20; // to avoid scrollbars
    marginHeight = 40;
    var selection = d3.select(this);
    if (datum.tag == "svg") {
        var width = window.innerWidth;
        var height = window.innerHeight;
        datum.attributes.width = width - marginWidth;
        datum.attributes.height = height - marginHeight;
    }
}


%%DOT_TEMPLATE%%

updateFrames();
initSlider();

</script>
"""

EXAMPLES = """

usage examples:

# Read events from 'test_trace.json' and generate 'test.html'
animate_lock_graph.py -i test_trace.json -o test.html
"""

parser = argparse.ArgumentParser(
    description="",
    formatter_class=argparse.RawDescriptionHelpFormatter,
    epilog=EXAMPLES,
)
parser.add_argument(
    "-V",
    "--version",
    action="version",
    version=f"{parser.prog} ({__version__})",
)
parser.add_argument("-v", "--verbose", action="store_true", help="be verbose")
parser.add_argument(
    "-o",
    "--output",
    type=str,
    dest="output_file",
    default=None,
    help="write the trace into output file",
    required=True,
)
parser.add_argument(
    "-i",
    "--input",
    type=str,
    dest="input_file",
    default=None,
    help="the input file with the events",
    required=True,
)
parser.add_argument(
    "-f",
    "--force",
    action="store_true",
    help="overwrite the output file if it already exists",
)


class DOTModel:
    def __init__(self, input_file, verbose) -> None:
        self.input_file = input_file
        self.verbose = verbose
        self.dot_graphs = []
        self.graph = igraph.Graph(directed=True)
        self.calculate_graphs()

    def calculate_graphs(self):
        """
        Calculate the dot graphs for each line of the input
        """
        with open(self.input_file, "r", encoding="utf-8") as input_file_handle:
            for line in input_file_handle:
                json_data = json.loads(line)
                self.handle_json(json_data)

    def handle_json(self, event):
        """
        Handle the JSON encoded graph event
        """
        vertex_name_query = f"query_{event['pid']}"

        if event["event"] == "QUERY_BEGIN":
            self.graph.add_vertex(vertex_name_query, type="query", label=event["query"])
            self.generate_graph()
            return

        if event["event"] == "LOCK_GRANTED_LOCAL":
            if self.verbose:
                print(f"Processing {event}")

            tablename = StringHelper.get_tablename(event)
            lock_type = event["lock_type"]

            if not self.graph.vs.select(label_eq=tablename):
                self.graph.add_vertex(tablename, label=tablename)

            # Get numeric value of lock
            lock_numeric_value = PostgreSQLLockHelper.lock_type_to_int(lock_type)

            # Get existing edge to this table
            edge_id = self.graph.get_eid(vertex_name_query, tablename, error=False)

            # If not exist, create
            if edge_id == -1:
                lock_value = PostgreSQLLockHelper.encode_locks_into_value(
                    [lock_numeric_value]
                )
                self.graph.add_edge(vertex_name_query, tablename, lock_value=lock_value)
                self.generate_graph()
                return

            # Else, modify edge and add lock
            edge = self.graph.es[edge_id]
            decoded_lock_value = PostgreSQLLockHelper.decode_locks_from_value(
                edge["lock_value"]
            )
            decoded_lock_value.append(lock_numeric_value)
            edge["lock_value"] = PostgreSQLLockHelper.encode_locks_into_value(
                decoded_lock_value
            )

            return

        if event["event"] == "LOCK_UNGRANTED_LOCAL":
            if self.verbose:
                print(f"Processing {event}")

            tablename = StringHelper.get_tablename(event)
            lock_type = event["lock_type"]
            lock_numeric_value = PostgreSQLLockHelper.lock_type_to_int(lock_type)

            edge_id = self.graph.get_eid(vertex_name_query, tablename)
            edge = self.graph.es[edge_id]

            decoded_lock_value = PostgreSQLLockHelper.decode_locks_from_value(
                edge["lock_value"]
            )

            if lock_numeric_value in decoded_lock_value:
                decoded_lock_value.remove(lock_numeric_value)
            else:
                print(
                    f"Lock {lock_numeric_value} for table {tablename} removed but not requested"
                )

            edge["lock_value"] = PostgreSQLLockHelper.encode_locks_into_value(
                decoded_lock_value
            )

            # Delete the edge if not locks hold
            if len(decoded_lock_value) == 0:
                self.graph.delete_edges(edge)

            # Is the vertex unconnected (degree == 0) after we deleted the edge?
            vertex = self.graph.vs.select(label_eq=tablename)
            if self.graph.degree(vertex)[0] == 0:
                # self.graph.delete_vertices(tablename)
                self.graph.delete_vertices(vertex)

            self.generate_graph()
            return

    def generate_graph(self):
        """
        Generate a DOT graph based on the igraph
        """
        vertices = self.graph.vs
        edges = self.graph.es

        # Reduce space if more nodes are present
        if len(vertices) > 15:
            mindist = "0.2"
        elif len(vertices) > 10:
            mindist = "0.4"
        elif len(vertices) > 6:
            mindist = "0.75"
        elif len(vertices) > 4:
            mindist = "1.0"
        else:
            mindist = "1.7"

        dot = graphviz.Digraph("lock-graph", graph_attr={"mindist": mindist})

        for vertex in vertices:
            if vertex["type"] == "query":
                dot.node(
                    vertex["name"], vertex["label"], fillcolor="gray", style="filled"
                )
            else:
                display_name = vertex["label"]
                display_name = StringHelper.split_string(display_name, 20)
                dot.node(
                    vertex["name"],
                    display_name,
                    shape="box",
                    fillcolor="lightgray",
                    style="filled",
                )

        for edge in edges:
            # Decode graph lock value into list of lock values
            decoded_lock_value = PostgreSQLLockHelper.decode_locks_from_value(
                edge["lock_value"]
            )

            # Convert numeric lock values into a string values and join them into a single string
            label = ",".join(
                map(PostgreSQLLockHelper.lock_type_to_str, decoded_lock_value)
            )

            # Add edge to dot graph
            dot.edge(
                vertices[edge.source]["name"],
                vertices[edge.target]["name"],
                label=label,
            )

        # Convert Dot graph into string.
        # Every line needs to be quoted and line breaks need a ",""
        #
        # For example:
        #
        # ['digraph "lock-graph" {',
        # '       query_171379 [label="select count(*) from sensor_data ;"]',
        # '       "public.sensor_data" [label="public.sensor_data"]',
        # '       query_171379 -> "public.sensor_data"',
        # '}'],
        lines = dot.source.split("\n")
        lines = [f"'{line}'" for line in lines if line]
        lines = ",\n".join(lines)

        # Add dot string to list of graphs
        self.dot_graphs.append(f"[{lines}]")

    def get_html(self):
        """
        Convert all dot graphs into a single string
        """
        result = "var dots = [\n"
        graphs = ",\n".join(self.dot_graphs)
        result += graphs
        result += "];\n"
        return result


# pylint: disable=too-few-public-methods
class StringHelper:
    @staticmethod
    def split_string(mystring, max_length):
        """
        Add linebreaks to the string after max_length chars at
        the next dot or underscore.
        """

        result = ""
        chars_without_break = 0
        for element in mystring:
            result += element
            chars_without_break += 1

            if chars_without_break > max_length and element in (".", "_"):
                chars_without_break = 0
                result += "\\n"

        return result

    @staticmethod
    def get_tablename(event):
        """
        Get the tablename or the Oid of the event.
        """
        if "table" in event:
            return event["table"]

        return f"Oid {event['oid']}"


def main():
    """
    Entry point for the animate_lock_graph script
    """
    args = parser.parse_args()

    if not os.path.exists(args.input_file):
        raise ValueError(f"Input file does not exist {args.input_file}")

    if os.path.exists(args.output_file) and not args.force:
        raise ValueError(f"Output file already exists {args.output_file}")

    # Create a new dot model, process the events in the input file
    # and generate the HTML output
    dot_model_instance = DOTModel(args.input_file, args.verbose)

    with open(args.output_file, "w", encoding="utf-8") as output:
        dots = dot_model_instance.get_html()
        output_html = HTML_TEMPLATE.replace("%%DOT_TEMPLATE%%", dots)
        output.write(output_html)


if __name__ == "__main__":
    main()
