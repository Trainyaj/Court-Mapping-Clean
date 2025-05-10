from flask import Flask, render_template, request, jsonify
import sqlite3

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/search_results")
def search_results():
    case_name = request.args.get('name')
    if not case_name:
        return render_template("index.html", error="No case name provided.")
    try: 
        graph_elements = create_citation_graph({'case_name': case_name})
        return render_template("search_results.html", elements = graph_elements)
    except ValueError as e:
        print("error")
        print(str(e))
        return render_template("index.html", error=str(e))
    
@app.route("/credits")
def credits():
    return render_template("credits.html")
    
@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/autocomplete")
def autocomplete():
    search_term = request.args.get("term", "")
    if not search_term:
        return jsonify([])

    con = get_db_connection()
    cur = con.cursor()
    matches = cur.execute(
        "SELECT id, case_name FROM dockets WHERE case_name LIKE ? LIMIT 10",
        ('%' + search_term + '%',)
    ).fetchall()

    results = [{'id': row[0], 'name': row[1]} for row in matches]
    return jsonify(results)

# expands the citation network!
@app.route("/expand-case", methods=["POST"])
def expand_case():
    data = request.get_json()
    case_id = data["case_id"]
    existing_ids = data.get("existing_ids", [])
    # Get citing and cited cases, and return as JSON to add
    try:
        graph_elements = create_citation_graph({'case_id': case_id}, existing_ids)
        return jsonify(graph_elements)
    except ValueError as e:
        return jsonify({'error':str(e)}), 400

# key for me: list(G.adj[foo]) and/or list(G.neighbors(foo))

# citation options: 
# 1: judicial.csv + allcites.txt (upsides: I have it, downsides: getting data from .txt, 
# direction of citations unclear, goes to 2002)
# 2: use Count listener API's (upsides: much more comphrensive, much less SQL
# downsides: baffling API's, may get rate limited)

# creates a citation graph of all citations around the given case name, then returns it
def create_citation_graph(case_info, existing_ids = []):
    con = get_db_connection()
    cur = con.cursor()

    cases = get_case_info(cur, case_info)
        
    all_edges = []
    all_nodes = {}

    # a loop incase more then one case has the same name (quite common)
    for case_id, case_name in cases:
        full_citing_ids, full_cited_ids = get_opinion_ids(cur, case_id)
        # ignores citations already in the graph
        if existing_ids:
            # nicer to work with sets than list, plus need in integer form to be comparable
            existing_ids_set = set(int(i) for i in existing_ids)
            full_citing_ids = [id for id in full_citing_ids if id not in existing_ids_set]
            full_cited_ids = [id for id in full_cited_ids if id not in existing_ids_set]

        # gets names, removes any ids somehow not in the database
        citing_ids, citing_names = get_case_names(cur, full_citing_ids)
        cited_ids, cited_names = get_case_names(cur, full_cited_ids)

        # Build edges around central
        all_edges += build_edges(case_id, citing_ids, cited_ids)

        # Adds intra-neighbor citations (including from previously cited cases)
        neighbor_ids = set(citing_ids + cited_ids)
        extra_edges = get_crosslinked_edges(cur, neighbor_ids, existing_ids)
        all_edges += extra_edges
        
        # the central case are central in the graph!
        nodes = build_nodes(case_id, case_name, zip(citing_ids, citing_names), zip(cited_ids, cited_names))
        all_nodes.update(nodes) 

    node_list = [
        {'data': {'id': str(i), 'case_name': case_dict['case_name'], 'central': case_dict['central']}}
        for i, case_dict in all_nodes.items()
    ]

    print(all_edges)
    print(node_list)
    return all_edges + node_list

def get_db_connection():
    return sqlite3.connect("cases.db")

# gets all cases that match the given case info
def get_case_info(cur, case_info):
    if 'case_id' in case_info:
        case_id = case_info['case_id']
        case_name_row = cur.execute("SELECT case_name FROM dockets WHERE id = ?", (case_id,)).fetchone()
        if not case_name_row:
            raise ValueError(f"Case id '{case_id}' not found.")
        return [case_id], [case_name_row[0]]
    elif 'case_name' in case_info:
        case_name = case_info['case_name']
        # goes from inexact to exact name, finds id
        results = cur.execute(
                "SELECT case_name, id FROM dockets WHERE case_name LIKE ?", 
                ('%' + case_name + '%',)
            ).fetchall()
        if not results:
            raise ValueError(f"Case name '{case_name}' not found.")
        
        # unpack case_names and ids
        case_names = [row[0] for row in results]
        case_ids = [row[1] for row in results]
        # limited to 20 results for sanity's sake
        return zip(case_ids, case_names)[:20]
    else:
        raise ValueError("Missing required key in search input.")
    
def get_opinion_ids(cur, case_id):
    citing_ids = [row[0] for row in cur.execute(
        "SELECT citing_opinion_id FROM cl_citations2 WHERE cited_opinion_id = ?", (case_id,)
    ).fetchall()]

    cited_ids = [row[0] for row in cur.execute(
        "SELECT cited_opinion_id FROM cl_citations2 WHERE citing_opinion_id = ?", (case_id,)
    ).fetchall()]

    return citing_ids, cited_ids

def get_case_names(cur, case_ids):
    corrected_case_ids, names = [], []
    for case_id in case_ids:
        row = cur.execute("SELECT case_name FROM dockets WHERE id = ?", (case_id,)).fetchone()
        if row:
            corrected_case_ids.append(case_id)
            names.append(row[0])
    return corrected_case_ids, names

def build_edges(source_id, citing_ids, cited_ids):
    edges = []
    edges += [{'data': {'source': str(source_id), 'target': str(cid)}} for cid in citing_ids]
    edges += [{'data': {'source': str(cid), 'target': str(source_id)}} for cid in cited_ids]
    return edges

def build_nodes(case_id, case_name, citing_data, cited_data):
    nodes = {
        str(case_id): {'case_name': case_name, 'central': "true"}
    }
    for cid, cname in citing_data:
        nodes[str(cid)] = {'case_name': cname, 'central': "false"}
    for cid, cname in cited_data:
        nodes[str(cid)] = {'case_name': cname, 'central': "false"}
    return nodes

# gets edges between non-core cases
def get_crosslinked_edges(cur, neighbor_ids, existing_ids=None):
    """
    Returns edges between:
    1. Neighbor → Neighbor
    2. Neighbor ↔ Existing (in both directions)
    
    Always returns edges in the form: cited_opinion_id → citing_opinion_id
    """
    edges = []

    if not neighbor_ids:
        return edges

    # Intra-neighbor citations
    n_placeholders = ','.join('?' for _ in neighbor_ids)
    intra_query = f"""
        SELECT cited_opinion_id, citing_opinion_id
        FROM cl_citations2
        WHERE citing_opinion_id IN ({n_placeholders})
          AND cited_opinion_id IN ({n_placeholders})
    """
    edges += cur.execute(intra_query, list(neighbor_ids) * 2).fetchall()

    # Crosslinks: neighbor ↔ existing
    if existing_ids:
        e_placeholders = ','.join('?' for _ in existing_ids)

        # neighbor → existing
        n_to_e_query = f"""
            SELECT cited_opinion_id, citing_opinion_id
            FROM cl_citations2
            WHERE citing_opinion_id IN ({e_placeholders})
              AND cited_opinion_id IN ({n_placeholders})
        """
        edges += cur.execute(n_to_e_query, list(existing_ids) + list(neighbor_ids)).fetchall()

        # existing → neighbor
        e_to_n_query = f"""
            SELECT cited_opinion_id, citing_opinion_id
            FROM cl_citations2
            WHERE citing_opinion_id IN ({n_placeholders})
              AND cited_opinion_id IN ({e_placeholders})
        """
        edges += cur.execute(e_to_n_query, list(neighbor_ids) + list(existing_ids)).fetchall()

    # Return as edge dicts (cited → citing)
    return [{'data': {'source': str(cited_id), 'target': str(citing_id)}} for cited_id, citing_id in edges]

#create_citation_graph({'case_name': "Brown v. Board of Education"})

#runs the development server!
if __name__ == '__main__':
    app.run(debug=True)