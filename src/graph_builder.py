# TCL Graph Core - Ojo LGA Influence Map
# Finds kingmakers in Ojo via network analysis

import networkx as nx
from pyvis.network import Network
import pandas as pd
from.sheets_client import get_sheet

def build_ojo_graph():
    print("Building Ojo influence graph...")

    # Load data from your sheet
    try:
        ws = get_sheet("raw_posts")
        data = ws.get_all_records()
        df = pd.DataFrame(data)
        print(f"Loaded {len(df)} posts from sheet")
    except Exception as e:
        print(f"Sheet empty, using demo Ojo data: {e}")
        # Demo Ojo data so you can test graph today
        df = pd.DataFrame([
            {"author": "Alaba Market Leader", "ward": "Ojo Ward 1", "text": "Traders angry about levy"},
            {"author": "LASU SUG President", "ward": "Ojo Ward 3", "text": "Students need road"},
            {"author": "Iba Baale", "ward": "Iba LCDA", "text": "Support Alaba Leader"},
            {"author": "Okokomaiko Youth Chair", "ward": "Ojo Ward 9", "text": "Youth with LASU SUG"},
            {"author": "Alaba Market Leader", "ward": "Ojo Ward 1", "text": "Meeting with Iba Baale"},
            {"author": "Mama Nkechi Ojo", "ward": "Ojo Ward 5", "text": "Women support Alaba"},
        ])

    if df.empty:
        print("No data yet - run scraper first")
        return

    G = nx.Graph()

    # Add nodes = influencers in Ojo
    for _, row in df.iterrows():
        author = str(row.get('author', 'Unknown'))[:35]
        ward = str(row.get('ward', 'Unknown'))
        # Size = how many times they appear
        if G.has_node(author):
            G.nodes[author]['size'] = G.nodes[author].get('size', 10) + 5
        else:
            G.add_node(author, ward=ward, size=15, title=f"{author} - {ward}")

    # Add edges = people in same ward or mentioned together
    authors = list(G.nodes())
    for i in range(len(authors)):
        for j in range(i+1, len(authors)):
            # Same ward = connection
            if G.nodes[authors[i]].get('ward') == G.nodes[authors[j]].get('ward'):
                if G.has_edge(authors[i], authors[j]):
                    G[authors[i]][authors[j]]['weight'] += 1
                else:
                    G.add_edge(authors[i], authors[j], weight=1)

    # Find kingmaker for Ojo
    if len(G.nodes()) >= 3:
        centrality = nx.betweenness_centrality(G)
        kingmaker = max(centrality, key=centrality.get)
        print(f"\n*** OJO KINGMAKER FOUND: {kingmaker} ***")
        print(f"Centrality: {centrality[kingmaker]:.3f} - This person connects different wards")
        print(f"Top 3 influencers in Ojo:")
        for person, score in sorted(centrality.items(), key=lambda x: x[1], reverse=True)[:3]:
            print(f" - {person}: {score:.3f}")
    else:
        print("Too few influencers - need more data from scraper")

    # Save interactive graph - open this in browser
    net = Network(height="650px", width="100%", bgcolor="#ffffff", font_color="#0A1931")
    net.from_nx(G)
    # Color by ward
    for node in net.nodes:
        ward = G.nodes[node['id']].get('ward', '')
        if 'Ward 1' in ward or 'Alaba' in str(node['id']):
            node['color'] = '#185ADB' # Blue for Alaba area
        elif 'LASU' in str(node['id']):
            node['color'] = '#FF6B00' # Orange for LASU

    net.save_graph("ojo_graph.html")
    print(f"\nGraph saved to ojo_graph.html")
    print(f"Double-click ojo_graph.html to open in Chrome - you will see Ojo network")

    return G

if __name__ == "__main__":
    build_ojo_graph()