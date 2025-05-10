document.addEventListener('DOMContentLoaded', function () {
  const elements = JSON.parse(document.getElementById('cy-data').textContent);
  var cy = cytoscape({
    container: document.getElementById('cy'),
    elements: elements,
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
      {
        selector: 'node[central = "true"]',
        style: {
          'background-color': '#7BFF63',  // central (searched/selected) nodes are blue
          'border-width': 3,
          'border-color': '#000000'
        }
      },
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

  // Hide the graph container before layout starts
  document.getElementById('cy').classList.add('hidden');

  // Listens for when the layout finishes
  cy.on('layoutstop', () => {
    document.getElementById('cy').classList.remove('hidden');
  });

  cy.nodes().ungrabify();  // Prevents user dragging nodes (while unlike autolock doesn't mess with layout)

  /*
  // Compute degree centrality and set it on each node
  cy.nodes().forEach(function (node) {
    const degree = node.degree();  // Number of connections
    node.data('centralityScore', degree); // Attach to node data
  });
  */

  // sets up the layout
  function applyLayout() {
    cy.layout({
      name: 'cose',
      nodeRepulsion: 2000,
      edgeElasticity: 200,
      gravity: .8,
      numIter: 1000,
      fit: true,
      padding: 30
    }).run();
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

  cy.on('tap', 'node', function(evt) {
    const node = evt.target;
    const case_id = node.id();

    if (!confirm(`Expand citations for case "${node.data('case_name')}"?`)) return;

    node.data('central', 'true');

    fetch("/expand-case", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({
        case_id: case_id,
        // excludes the id from which the new graph is being generated to avoid duplication
        existing_ids: cy.nodes().map(node => node.id()).filter(id => id !== case_id)
      })
    })
      .then(response => response.json())
      .then(newElements => {
        cy.add(newElements);
        applyLayout();
      })
      .catch(err => console.error("Error expanding case:", err));
  });

  cy.fit(); // Ensures full graph is visible in the viewport
});

  