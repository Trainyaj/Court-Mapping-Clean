from flask import Flask, render_template, request, jsonify
# used to access my citation database, cases.db
import sqlite3

app = Flask(__name__)

#renders the main page (index.html)
@app.route("/")
def index():
    return render_template("index.html")

# renders the citation graph
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
    
# renders the (static) credits.html template
@app.route("/credits")
def credits():
    return render_template("credits.html")
    
# renders the (static) about.html template
@app.route("/about")
def about():
    return render_template("about.html")

# provides autocomplete case name suggestions, which are passively added below the 
# search bar (inspired by class word-autocomplete)
@app.route("/autocomplete")
def autocomplete():
    search_term = request.args.get("term", "")
    if not search_term:
        return jsonify([])
    con = get_db_connection()
    cur = con.cursor()
    try:
        # gets possible matches
        matches = get_case_info(cur, {'case_name': search_term})
        results = [{'id': row[0], 'name': row[1]} for row in matches]
        cur.close()
        con.close()
        # then returns them for javascript to display
        return jsonify(results)
    except ValueError:
        # if no results are found, return an empty list of results
        cur.close()
        con.close()
        return jsonify([])

# expands the citation network to include citations around a new case
@app.route("/expand-case", methods=["POST"])
def expand_case():
    data = request.get_json()
    case_id = data["case_id"]
    existing_ids = data.get("existing_ids", [])
    # Gets citing and cited cases, and return as JSON to add to the cytoscape graph
    try:
        graph_elements = create_citation_graph({'case_id': case_id}, existing_ids)
        return jsonify(graph_elements)
    # This error shouldn't ever occur unless the user manually messes with 
    # values of the data in the front-end cytoscape graph (in which case that is their fault)
    except ValueError as e:
        return jsonify({'error':str(e)}), 400

# creates a citation graph of all citations around the given case name, then returns it
def create_citation_graph(case_info, existing_ids = []):
    con = get_db_connection()
    cur = con.cursor()

    cases = get_case_info(cur, case_info)
        
    all_edges = []
    all_nodes = {}

    # loops in case more then one case is found by the fuzzy string matching
    for case_id, case_name in cases:
        full_citing_ids, full_cited_ids = get_opinion_ids(cur, case_id)
        # ignores citations already in the graph
        if existing_ids:
            # nicer to work with sets than list, plus need in integer form to be comparable
            # (cytoscape stores ids as strings)
            existing_ids_set = set(int(i) for i in existing_ids)
            full_citing_ids = [id for id in full_citing_ids if id not in existing_ids_set]
            full_cited_ids = [id for id in full_cited_ids if id not in existing_ids_set]

        # gets case names, removes any ids somehow not in the database
        citing_ids, citing_names = get_case_names(cur, full_citing_ids)
        cited_ids, cited_names = get_case_names(cur, full_cited_ids)

        # Build edges around central
        all_edges += build_edges(case_id, citing_ids, cited_ids)

        # Adds intra-neighbor citations (including from previously cited cases)
        neighbor_ids = set(citing_ids + cited_ids)
        extra_edges = get_noncore_edges(cur, neighbor_ids, existing_ids)
        all_edges += extra_edges
        
        # the central case are central in the graph!
        nodes = build_nodes(case_id, case_name, zip(citing_ids, citing_names), zip(cited_ids, cited_names))
        all_nodes.update(nodes) 

    # formats the nodes in a dictionary readable by cytoscape
    node_list = [
        {'data': {'id': str(i), 
                  'case_name': case_dict['case_name'], 'central': case_dict['central']}}
        for i, case_dict in all_nodes.items()
    ]

    cur.close()
    con.close()

    return all_edges + node_list

# connects to the database
def get_db_connection():
    return sqlite3.connect("cases.db")

# gets all cases that match the given case info (a dictionary with case_id and case_name)
def get_case_info(cur, case_info):
    # as case_id is more exact than case_name, checks for it first
    if 'case_id' in case_info:
        case_id = case_info['case_id']
        case_name_row = cur.execute(
            "SELECT case_name FROM dockets WHERE id = ?", (case_id,)).fetchone()
        if not case_name_row:
            raise ValueError(f"Case id '{case_id}' not found.")
        # doesn't need to be limited because each id should only have one row in the DB
        return [(case_id, case_name_row[0])]
    elif 'case_name' in case_info:
        case_name = case_info['case_name']
        # goes from inexact to exact name, finds corresponding ids
        # limited to 20 results for performance
        results = cur.execute(
                "SELECT case_name, id FROM dockets WHERE case_name LIKE ? LIMIT 20", 
                ('%' + case_name + '%',)
            ).fetchall()
        if not results:
            raise ValueError(f"Case name '{case_name}' not found.")
        
        # unpack case names and ids
        case_names = [row[0] for row in results]
        case_ids = [row[1] for row in results]
        return zip(case_ids, case_names)
    else:
        raise ValueError("Missing required key in search input.")
    
# given a case_id (usually of the central case), returns the cases 
# cited by and citing it
def get_opinion_ids(cur, case_id):
    citing_ids = [row[0] for row in cur.execute(
        "SELECT citing_opinion_id FROM cl_citations2 WHERE cited_opinion_id = ?", (case_id,)
    ).fetchall()]

    cited_ids = [row[0] for row in cur.execute(
        "SELECT cited_opinion_id FROM cl_citations2 WHERE citing_opinion_id = ?", (case_id,)
    ).fetchall()]

    return citing_ids, cited_ids

# returns the names of the cases with the given case_ids
# Necessary because search is implemented using (somewhat) fuzzy string matching 
def get_case_names(cur, case_ids):
    corrected_case_ids, case_names = [], []
    for case_id in case_ids:
        row = cur.execute("SELECT case_name FROM dockets WHERE id = ?",
                           (case_id,)).fetchone()
        if row :
            corrected_case_ids.append(case_id)
            case_names.append(row[0])
    return corrected_case_ids, case_names

# builds the citation edges (mapping) between the central case (source_id)
# and the cases it cites and is cited by
def build_edges(source_id, citing_ids, cited_ids):
    edges = []
    edges += [{'data': {'source': str(source_id), 'target': str(cid)}} for cid in citing_ids]
    edges += [{'data': {'source': str(cid), 'target': str(source_id)}} for cid in cited_ids]
    return edges

# builds the citatation graph around a central case (case_id plus case_name)
def build_nodes(source_id, case_name, citing_data, cited_data):
    # the central case is central (this allows cytoscape to format it differently)
    nodes = {
        str(source_id): {'case_name': case_name, 'central': "true"}
    }
    for cid, cname in citing_data:
        nodes[str(cid)] = {'case_name': cname, 'central': "false"}
    for cid, cname in cited_data:
        nodes[str(cid)] = {'case_name': cname, 'central': "false"}
    return nodes

# finds and builds the 
# edges between non-core cases (between cases that haven't been searched for
# or clicked for)
def get_noncore_edges(cur, neighbor_ids, existing_ids=None):
    """
    Returns edges between:
    1. Neighbor → Neighbor
    2. Neighbor ↔ Existing

    Does not return edges between:
    Existing → Existing (those already exist)
    
    Always returns edges in the form: cited_opinion_id → citing_opinion_id
    """
    edges = []

    # if there aren't any Neighbors, no edges are created 
    if not neighbor_ids:
        return edges

    # Intra-neighbor citations
    neighbor_placeholders = ','.join('?' for _ in neighbor_ids)
    intra_query = f"""
        SELECT cited_opinion_id, citing_opinion_id
        FROM cl_citations2
        WHERE citing_opinion_id IN ({neighbor_placeholders})
          AND cited_opinion_id IN ({neighbor_placeholders})
    """
    edges += cur.execute(intra_query, list(neighbor_ids) * 2).fetchall()

    # Crosslinks: neighbor ↔ existing (if there are existing_ids)
    if existing_ids:
        existing_placeholders = ','.join('?' for _ in existing_ids)

        # neighbor → existing
        n_to_e_query = f"""
            SELECT cited_opinion_id, citing_opinion_id
            FROM cl_citations2
            WHERE citing_opinion_id IN ({existing_placeholders})
              AND cited_opinion_id IN ({neighbor_placeholders})
        """
        edges += cur.execute(n_to_e_query, 
                             list(existing_ids) + list(neighbor_ids)).fetchall()

        # existing → neighbor
        e_to_n_query = f"""
            SELECT cited_opinion_id, citing_opinion_id
            FROM cl_citations2
            WHERE citing_opinion_id IN ({neighbor_placeholders})
              AND cited_opinion_id IN ({existing_placeholders})
        """
        edges += cur.execute(e_to_n_query, 
                             list(neighbor_ids) + list(existing_ids)).fetchall()

    # Return edges as a list of dicts (cited → citing)
    return [{'data': {'source': str(cited_id), 'target': str(citing_id)}} 
            for cited_id, citing_id in edges]


#runs my development server (using flask)
# e.g. is the key line in my code, lol
if __name__ == '__main__':
    app.run(debug=True)