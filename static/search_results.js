// waits unti the document is loaded
document.addEventListener('DOMContentLoaded', function () {
  // gets raw data for the citation graph from a JSON passed in by the backend
  const elements = JSON.parse(document.getElementById('cy-data').textContent);
  // defines the cytoscape graph
  var cy = cytoscape({
    // tells cytoscape where to render the graph
    container: document.getElementById('cy'),
    // provides cytoscape the graph data
    elements: elements,
    // defines the graph styling (note: not intended for mobile)
    style: [
      {
        selector: 'node',
        style: {
          shape: 'ellipse',
          width: '100px',
          height: '100px',
          'background-color': '#eee',
          'border-color': '#000000',
          'border-width': 2,
          label: 'data(case_name)',
          'text-wrap': 'wrap',
          'text-max-width': '80px',
          'text-valign': 'center',
          'text-halign': 'center',
          'font-size': 13,
          'color': '#000'
        }
      },
      // styles central nodes differently to increase their distinctiveness
      {
        selector: 'node[central = "true"]',
        style: {
          'background-color': '#7BFF63', 
          'border-width': 4,
          'border-color': '#000000'
        }
      },
      // styles edges, with triangles indicating citation direction
      {
        selector: 'edge',
        style: {
          width: 2,
          'line-color': '#444444',
          'curve-style': 'bezier',
          'target-arrow-shape': 'triangle',
          'target-arrow-color': '#444444'
        }
      }
    ]
  });

  // Hide the graph container before the layout starts
  document.getElementById('cy').classList.add('hidden');

  // Listens for when the layout finishes, and only unhides the graph then
  // (the graph-building animation is distracting and annoying)
  cy.on('layoutstop', () => {
    document.getElementById('cy').classList.remove('hidden');
  });

  // Prevents user dragging nodes (while unlike autolock doesn't mess with layout)
  cy.nodes().ungrabify();  

  // not used with the current graph layout type (cose)
  /*
  // Compute degree centrality and set it on each node
  cy.nodes().forEach(function (node) {
    const degree = node.degree();  // Number of connections
    node.data('centralityScore', degree); // Attach to node data
  });
  */

  // sets up the layout
  // cose produces nice-looking but very unstable graphs
  function applyLayout() {
    cy.layout({
      name: 'cose',
      nodeRepulsion: 2000,
      edgeElasticity: 200,
      gravity: .8,
      numIter: 1500,
      fit: true,
      padding: 30
    }).run();

    // alternative layout to use with the degree centrality funciton
    // doesn't work well with more than one central case
    /*cy.layout( {
      name: 'concentric',
      concentric: function (node) {
        return node.data('central') ? 2 : 1; // cases the user searched for are centered
      },
      levelWidth: function () { return 1; }, // controls spacing between levels
      minNodeSpacing: 10,
      avoidOverlap: true,
      padding: 5,
      fit: true
    }).run();*/
  }
  applyLayout();

  // listens for node tapping
  cy.on('tap', 'node', function(evt) {
    const node = evt.target;
    const case_id = node.id();
    
    // no point expanding central nodes (all their citations already exist)
    if (node.data('central') === "true") return;
    // asks for confirmation
    if (!confirm(`Expand citations for case "${node.data('case_name')}"?`)) return;

    // the case is now a central case, yay!
    node.data('central', 'true');

    // adds all of the not previously included citations linked to the clicked case
    // to the graph
    fetch("/expand-case", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({
        case_id: case_id,
        // excludes the id of the node
        // from which the new graph is being generated to avoid duplication
        existing_ids: cy.nodes().map(node => node.id()).filter(id => id !== case_id)
      })
    })
    // then adds the new elements (edges and nodes) to the graph and recreates the graph
      .then(response => response.json())
      .then(newElements => {
        cy.add(newElements);
        applyLayout();
        cy.fit();
      })
      .catch(err => console.error("Error expanding case:", err));
  });

  // Ensures full graph is visible in the viewport
  cy.fit(); 
});

  