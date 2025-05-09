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
            'border-color': '#333',
            'border-width': 2,
            label: 'data(case_name)',
            'text-wrap': 'wrap',
            'text-max-width': '80px',
            'text-valign': 'center',
            'text-halign': 'center',
            'font-size': 12,
            'color': '#000'
          }
        },
        {
          selector: 'edge',
          style: {
            width: 2,
            'line-color': '#999',
            'curve-style': 'bezier',
            'target-arrow-shape': 'triangle',
            'target-arrow-color': '#999'
          }
        }
      ]
    });
    // Compute degree centrality and set it on each node
    cy.nodes().forEach(function (node) {
      const degree = node.degree();  // Number of connections
      node.data('centralityScore', degree); // Attach to node data
    });
    cy.layout( {
      name: 'concentric',
      concentric: function (node) {
        return node.data('centralityScore'); // Uses number of connections as score
      },
      levelWidth: function () { return 1; }, // controls spacing between levels
      minNodeSpacing: 80,
      avoidOverlap: true,
      padding: 10,
      fit: true
    }).run();
    cy.fit(); // Ensures full graph is visible in the viewport
});

  