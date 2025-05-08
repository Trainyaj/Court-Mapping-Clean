document.addEventListener('DOMContentLoaded', function () {
  const elements = JSON.parse(document.getElementById('cy-data').textContent);
    var cy = cytoscape({
      container: document.getElementById('cy'),
      elements: elements,
      style: [
        {
          selector: 'node',
          style: {
            shape: 'hexagon',
            'background-color': 'red',
            label: 'data(case_name)'
          }
        }
      ],
      layout: {
        name: 'grid'
      }
    });
});
  