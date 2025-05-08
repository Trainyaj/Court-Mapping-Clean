from flask import Flask, render_template, request
import sqlite3

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/search_results")
def search_results():
    case_name = request.args.get("name")
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
    con = sqlite3.connect("cases.db")
    cur = con.cursor()
    case_id = cur.execute(
        "SELECT caseid FROM judicial WHERE (parties = ?)", (case_name,)).fetchone()
    # gets all citing cases (all cases citing the requested case)
    citing_case_ids = cur.execute(
        "SELECT citing_case_id FROM citations WHERE (cited_case_id = ?)",
          case_id).fetchall()
    # gets all cited cases
    cited_case_ids = cur.execute(
        "SELECT cited_case_id FROM citations WHERE (citing_case_id = ?)",
          case_id).fetchall()
    # TODO: looks up names of found cases, connects to passed in case name
    # as list of tuples
    citing_case_names = []
    for case_id in citing_case_ids:
        citing_case_names.append(cur.execute(
        "SELECT parties FROM judicial WHERE (caseid = ?)", case_id).fetchone()[0])
    cited_case_names = []
    for case_id in cited_case_ids:
        cited_case_names.append(cur.execute(
        "SELECT parties FROM judicial WHERE (caseid = ?)", case_id).fetchone()[0])
    # creates a list of edges (tuples) between cases
    case_citation_tuples = []
    for citing_case_name in citing_case_names:
        case_citation_tuples.append((case_name, citing_case_name))
    for cited_case_name in cited_case_names:
        case_citation_tuples.append((cited_case_name, case_name))

    # get data into useable form for cytoscape
    edges = [{'data': {'source': s, 'target': t}} for s, t in case_citation_tuples]
    all_cases = [case_name] + citing_case_names + cited_case_names
    # removes duplicates from all_cases (case cans both cite and be cited)
    all_cases = list(set(all_cases))
    nodes = [{'data': {'id': n, 'case_name': n}} for n in all_cases]
    print(edges)
    print(nodes)
    return edges + nodes

#create_citation_graph("Flexner v. Farson")

# runs the development server!$
if __name__ == '__main__':
    app.run(debug=True)