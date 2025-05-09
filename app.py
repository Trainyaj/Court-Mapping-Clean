from flask import Flask, render_template, request
import sqlite3

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/search_results")
def search_results():
    case_name = request.args.get("name")
    print("Received case name:", case_name)
    graph_elements = create_citation_graph(case_name)
    print(graph_elements)
    return render_template("search_results.html", elements = graph_elements)

# key for me: list(G.adj[foo]) and/or list(G.neighbors(foo))

# citation options: 
# 1: judicial.csv + allcites.txt (upsides: I have it, downsides: getting data from .txt, 
# direction of citations unclear, goes to 2002)
# 2: use Count listener API's (upsides: much more comphrensive, much less SQL
# downsides: baffling API's, may get rate limited)

# creates a citation graph of all citations around the given case name, then returns it
def create_citation_graph(case_name):
    con = sqlite3.connect("cases2.db")
    cur = con.cursor()
    # Get all case ids with the given name
    case_rows = [row[0] for row in cur.execute(
        "SELECT id FROM dockets WHERE case_name = ?", (case_name,)
    ).fetchall()]
    if not case_rows:
        raise ValueError(f"Case name '{case_name}' not found.")
        
    all_edges = []
    all_nodes = set()

    for case_id in case_rows:
        # Get all citing cases
        full_citing_opinion_ids = cur.execute(
            "SELECT citing_opinion_id FROM citation_map WHERE cited_opinion_id = ?",
            (case_id,)
        ).fetchall()
        full_citing_opinion_ids = [n[0] for n in full_citing_opinion_ids]

        # Get all cited cases
        full_cited_opinion_ids = cur.execute(
            "SELECT cited_opinion_id FROM citation_map WHERE citing_opinion_id = ?",
            (case_id,)
        ).fetchall()
        full_cited_opinion_ids = [n[0] for n in full_cited_opinion_ids]

        citing_opinion_ids = []
        citing_opinion_names = []
        for citing_id in full_citing_opinion_ids:
            row = cur.execute("SELECT case_name FROM dockets WHERE id = ?", (citing_id,)).fetchone()
            # only appends supreme court cases
            if row:
                citing_opinion_ids.append(citing_id)
                citing_opinion_names.append(row[0])

        cited_opinion_ids = []
        cited_opinion_names = []
        for cited_id in full_cited_opinion_ids:
            row = cur.execute("SELECT case_name FROM dockets WHERE id = ?", (cited_id,)).fetchone()
            if row:
                cited_opinion_ids.append(cited_id)
                cited_opinion_names.append(row[0])

        # Build edges and nodes
        for citing_id in citing_opinion_ids:
            all_edges.append({'data': {'source': case_id, 'target': citing_id}})
        for cited_id in cited_opinion_ids:
            all_edges.append({'data': {'source': cited_id, 'target': case_id}})

        all_nodes.add((case_id, case_name))
        all_nodes.update(zip(citing_opinion_ids, citing_opinion_names))
        all_nodes.update(zip(cited_opinion_ids, cited_opinion_names))

    nodes = [{'data': {'id': i, 'case_name': c}} for i, c in all_nodes]

    print(all_edges)
    print(nodes)
    return all_edges + nodes

create_citation_graph("Brown v. Board of Education")

# runs the development server!$
#if __name__ == '__main__':
#    app.run(debug=True)