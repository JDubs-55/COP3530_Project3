
function drawGraph(data) {
                
    var width = 200 + window.innerWidth * 0.5, height = window.innerHeight * 0.9;
    
    var color = d3.scaleOrdinal(d3.schemeCategory20);

    var simulation = d3.forceSimulation()
        .force("link", d3.forceLink().id(function (d) { return d.id; }))
        .force("charge", d3.forceManyBody().strength(-500))
        .force("center", d3.forceCenter(width / 2, height / 2));
    
    
    const svg = d3.select("#graph").append("svg")
        .attr("width", "100%").attr("height", "100%")
        .attr("pointer-events", "all");


    
    var link = svg.append("g")
        .attr("class", "links")
        .selectAll("line")
        .data(data.links)
        .enter().append("line")
        .attr("stroke-width", function (d) { return Math.sqrt(d.value); });

    var node = svg.append("g")
        .attr("class", "nodes")
        .selectAll("circle")
        .data(data.nodes)
        .enter().append("circle")
        .attr("r", 10)
        .attr("fill", function (d) { return color(d.group); })
        .call(d3.drag()
            .on("start", dragstarted)
            .on("drag", dragged)
            .on("end", dragended));

    node.append("title")
        .text(function (d) { return d.id; });

    simulation
        .nodes(data.nodes)
        .on("tick", ticked);

    simulation.force("link")
        .links(data.links);

    function ticked() {
        link
            .attr("x1", function (d) { return d.source.x; })
            .attr("y1", function (d) { return d.source.y; })
            .attr("x2", function (d) { return d.target.x; })
            .attr("y2", function (d) { return d.target.y; });

        node
            .attr("cx", function (d) { return d.x; })
            .attr("cy", function (d) { return d.y; });
    }
    

    function dragstarted(d) {
        if (!d3.event.active) simulation.alphaTarget(0.3).restart();
        d.fx = d.x;
        d.fy = d.y;
    }

    function dragged(d) {
        d.fx = d3.event.x;
        d.fy = d3.event.y;
    }

    function dragended(d) {
        if (!d3.event.active) simulation.alphaTarget(0);
        d.fx = null;
        d.fy = null;
    }
}

//Mine above, saving if messup. 













function myGraph() {

    // Add and remove elements on the graph object
    this.addNode = function (id) {
        nodes.push({"id": id});
        update();
    };

    this.removeNode = function (id) {
        var i = 0;
        var n = findNode(id);
        while (i < links.length) {
            if ((links[i]['source'] == n) || (links[i]['target'] == n)) {
                links.splice(i, 1);
            }
            else i++;
        }
        nodes.splice(findNodeIndex(id), 1);
        update();
    };

    this.removeLink = function (source, target) {
        for (var i = 0; i < links.length; i++) {
            if (links[i].source.id == source && links[i].target.id == target) {
                links.splice(i, 1);
                break;
            }
        }
        update();
    };

    this.removeallLinks = function () {
        links.splice(0, links.length);
        update();
    };

    this.removeAllNodes = function () {
        nodes.splice(0, links.length);
        update();
    };

    this.addLink = function (source, target, value) {
        links.push({"source": findNode(source), "target": findNode(target), "value": value});
        update();
    };

    var findNode = function (id) {
        for (var i in nodes) {
            if (nodes[i]["id"] === id) return nodes[i];
        }
        ;
    };

    var findNodeIndex = function (id) {
        for (var i = 0; i < nodes.length; i++) {
            if (nodes[i].id == id) {
                return i;
            }
        }
        ;
    };

    // set up the D3 visualisation in the specified element
    var width = 200 + window.innerWidth * 0.5, height = window.innerHeight * 0.9;

    var color = d3.scaleOrdinal(d3.schemeCategory20);

    var vis = d3.select("body")
            .append("svg")
            .attr("width", width)
            .attr("height", height)
            .attr("id", "graph")
            .attr("pointer-events", "all");

    //var force = d3.layout.force();
    
    var simulation = d3.forceSimulation();

    var nodes = force.nodes();
    var links = force.links();

    var update = function () {

        var link = vis.selectAll("g.links")
                .data(links, function(d) {
                    return d.source;
                });

        link.enter().append("g")
            .attr("class", "links")
            .selectAll("line")
            .data(data.links)
            .enter().append("line")
            .attr("stroke-width", function (d) { return Math.sqrt(d.value); });
        
        link.exit().remove();
        
        
        // var link = vis.selectAll("line")
        //         .data(links, function (d) {
        //             return d.source.id + "-" + d.target.id;
        //         });

        // link.enter().append("line")
        //         .attr("id", function (d) {
        //             return d.source.id + "-" + d.target.id;
        //         })
        //         .attr('marker-end','url(#arrowhead)')
        //         .style("stroke","#ccc")
        //         .style("pointer-events", "none");

        // link.exit().remove();


        //Mine
        var node = svg.append("g")
            .attr("class", "nodes")
            .selectAll("circle")
            .data(data.nodes)
            .enter().append("circle")
            .attr("r", 10)
            .attr("fill", function (d) { return color(d.group); })
            .call(d3.drag()
                .on("start", dragstarted)
                .on("drag", dragged)
                .on("end", dragended));
        
        var node = vis.selectAll("g.node")
                .data(nodes, function (d) {
                    return d.id;
                });

        var nodeEnter = node.enter().append("g")
                .attr("class", "nodes")
                .call(force.drag);

        nodeEnter.append("svg:circle")
                .attr("r", 12)
                .attr("id", function (d) {
                    return "Node;" + d.id;
                })
                .attr("class", "nodeStrokeClass")
                .attr("fill", function(d) { return color(d.id); });

        nodeEnter.append("svg:text")
                .attr("class", "textClass")
                .attr("x", 14)
                .attr("y", ".31em")
                .text(function (d) {
                    return d.id;
                });

        node.exit().remove();


        force.on("tick", function () {

            node.attr("transform", function (d) {
                return "translate(" + d.x + "," + d.y + ")";
            });

            link.attr("x1", function (d) {
                return d.source.x;
            })
            .attr("y1", function (d) {
                return d.source.y;
            })
            .attr("x2", function (d) {
                return d.target.x;
            })
            .attr("y2", function (d) {
                return d.target.y;
            });

        });

        // Restart the force layout.
        force
            .gravity(.01)
            .charge(-80000)
            .friction(0)
            .linkDistance( function(d) { return d.value * 10 } )
            .size([w, h])
            .start();
    };

    // Make it all go
    update();
}

function drawGraph() {

    graph = new myGraph("#graph");


    graph.addNode('Sophia');
    graph.addNode('Ryan');
    graph.addNode('Alex');
    graph.addNode('Daniel');
    graph.addNode('Too');

    graph.addLink('Alex', 'Ryan', '20');
    graph.addLink('Sophia', 'Ryan', '20');
    graph.addLink('Daniel', 'Ryan', '20');
    graph.addLink('Daniel', 'Too', '20');

    keepNodesOnTop();

}

drawGraph();

// because of the way the network is created, nodes are created first, and links second,
// so the lines were on top of the nodes, this just reorders the DOM to put the svg:g on top
function keepNodesOnTop() {
    $(".nodeStrokeClass").each(function( index ) {
        var gnode = this.parentNode;
        gnode.parentNode.appendChild(gnode);
    });
}