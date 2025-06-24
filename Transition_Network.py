#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jun 19 11:26:54 2025
@author: kostre
"""

#%% Load Data 
import networkx as nx
from collections import defaultdict
import itertools
import sqlite3
import json
import matplotlib.pyplot as plt
import numpy as np
import string
import matplotlib.colors as colors
import random
import matplotlib.patches as mpatches


# Connect to Database
conn = sqlite3.connect("cleaned_yelp_data.db")
cursor = conn.cursor()

# Fetch the first few rows
cursor.execute("SELECT * FROM cleaned_restaurants LIMIT 200;")
rows = cursor.fetchall()

with open("users.json", "r") as f:
    users = json.load(f)

# Calculate for each pair of restaurant number of co-visits
co_visits = defaultdict(int)

for user in users:
    visited = user.get("reviewed_restaurants", [])
    for r1, r2 in itertools.combinations(sorted(visited), 2):
        pair = tuple(sorted((r1, r2)))
        co_visits[pair] += 1

# Connected all restaurant with at least 1 co visit
G = nx.Graph()

boundary=10 # number of co-visitors for two restuarants to be connected

# Only add edges with ≥boundary shared users
for (r1, r2), count in co_visits.items():
    if count >= boundary:  
        G.add_edge(r1, r2, weight=count)

# get information of restaurants

cursor.execute("SELECT id, name, rating, review_count, price, category, cleaned_category, city FROM cleaned_restaurants;")
rows = cursor.fetchall()

restaurant_info = {row[0]: row for row in rows}

#%% Construct Transition Network
rating_dict = {rid: info[2] for rid, info in restaurant_info.items() if rid in G.nodes}
nx.set_node_attributes(G, rating_dict, name="rating") # the rating is the node value

# Compute total transitions per restaurant (for normalization)



total_transitions = defaultdict(float)
for (u, v), count in co_visits.items():
    if count >= boundary:
        total_transitions[u] += count
        total_transitions[v] += count

#  Calulate transition probability from u to v
G_dir = nx.DiGraph()

for u, v, data in G.edges(data=True):
    weight = data.get("weight", 1) # weight= number of visits by some users between res. u and v
    rating_u = restaurant_info.get(u, [None, None, 0])[2] 
    rating_v = restaurant_info.get(v, [None, None, 0])[2]

    p_u = 1 - (rating_u - 1) / 4  # leaving probability is linear and anti-proportional to rating
    p_v = 1 - (rating_v - 1) / 4

    norm_u = weight / total_transitions[u] # transition probability from u to v
    norm_v = weight / total_transitions[v] # transition probability from v to u

    G_dir.add_edge(u, v, weight=norm_u * p_u) # update edges
    G_dir.add_edge(v, u, weight=norm_v * p_v)


#%% Plot Graph


# Group nodes by cleaned category
category_to_nodes = defaultdict(list)
for node in G_dir.nodes:
    category = restaurant_info.get(node, [None]*7)[6]  # cleaned_category
    category_to_nodes[category].append(node)

# Select categories to visualize
selected_categories = ['Middle Eastern','American','European']

nodes_per_category = 10

sample_nodes = []
for cat in selected_categories:
    nodes = category_to_nodes.get(cat, [])
    if len(nodes) < nodes_per_category:
        print(f"⚠️ Not enough restaurants in '{cat}': only {len(nodes)} available.")
    sample = random.sample(nodes, min(nodes_per_category, len(nodes)))
    sample_nodes.extend(sample)

G_sample = G_dir.subgraph(sample_nodes)

# Filter out weak edges (weight < 0.001)
edges_to_keep = [(u, v) for u, v, d in G_sample.edges(data=True) if d["weight"] > 0.001]
G_sample = G_sample.edge_subgraph(edges_to_keep).copy()

# Compute visual properties
p_u_values = {}
category_labels = {}
category_colors = {}

categories = list(set(restaurant_info.get(n, [""]*7)[6] for n in G_sample.nodes))
cmap_nodes = plt.cm.get_cmap("Dark2", len(categories))
cat_color_map = {cat: cmap_nodes(i) for i, cat in enumerate(categories)}

for node in G_sample.nodes:
    info = restaurant_info.get(node)
    rating = info[2]
    category = info[6]
    name = info[1]
    category_labels[node] = f"{name}\n({rating})"
    category_colors[node] = cat_color_map[category]

# Get edge weights
edge_weights = [data["weight"] for u, v, data in G_sample.edges(data=True)]

# Create figure with extra width for legend
fig, ax = plt.subplots(figsize=(20, 12))

# Assign categories for layout
for node in G_sample.nodes:
    G_sample.nodes[node]["subset"] = restaurant_info[node][6]

# Generate multipartite layout
pos = nx.multipartite_layout(G_sample)

# Draw network
nx.draw_networkx_nodes(
    G_sample, pos, 
    node_size=800,
    node_color=[category_colors[n] for n in G_sample.nodes],
    alpha=0.8,
    ax=ax
)


edge_vmin = 0
edge_vmax = np.percentile(edge_weights, 95)  # Use 95th percentile as max to prevent outlier distortion


nx.draw_networkx_edges(
    G_sample,
    pos,
    edge_color=edge_weights,
    edge_cmap=plt.cm.Blues,
    edge_vmin=edge_vmin,
    edge_vmax=edge_vmax,  # This ensures darkest blue is used
    width=2,
    arrows=True,                # Ensure arrows are visible
    arrowstyle='-|>',           # Standard arrow
    arrowsize=40,               # Larger arrowhead
    connectionstyle='arc3,rad=0.2',  # Gentle curves   
    ax=ax
    
)


sm = plt.cm.ScalarMappable(
    norm=colors.Normalize(vmin=edge_vmin, vmax=edge_vmax),
    cmap=plt.cm.Blues
)


nx.draw_networkx_labels(
    G_sample, pos, 
    labels=category_labels, 
    font_size=20,
    ax=ax
)

# Create legend
legend_handles = [
    mpatches.Patch(color=cat_color_map[cat], label=cat)
    for cat in sorted(set(restaurant_info[node][6] for node in G_sample.nodes))
]



# Add flattened legend
legend = plt.legend(
    handles=legend_handles,
    fontsize=24,
    bbox_to_anchor=(0, 1),
    loc='upper left',
    ncol=3,  # Adjust number of columns as needed
    frameon=False,
    handletextpad=0.3,
    columnspacing=0.8
)

# Add colorbar

cbar = plt.colorbar(sm, ax=ax, shrink=0.7)
cbar.set_label("Transition Probability", fontsize=24)
cbar.ax.tick_params(labelsize=24)

# Adjust layout

plt.tight_layout(rect=[0, 0, 0.9, 1])  # Leave 10% space on right for legend

plt.show()

#%% Anonymous Version



# Group nodes by cleaned category
category_to_nodes = defaultdict(list)
for node in G_dir.nodes:
    category = restaurant_info.get(node, [None]*7)[6]  # cleaned_category
    category_to_nodes[category].append(node)

# Select categories to visualize
selected_categories = ['Middle Eastern','American','European']

nodes_per_category = 10

sample_nodes = []
for cat in selected_categories:
    nodes = category_to_nodes.get(cat, [])
    if len(nodes) < nodes_per_category:
        print(f"⚠️ Not enough restaurants in '{cat}': only {len(nodes)} available.")
    sample = random.sample(nodes, min(nodes_per_category, len(nodes)))
    sample_nodes.extend(sample)

G_sample = G_dir.subgraph(sample_nodes)

# Filter out weak edges (weight < 0.001)
edges_to_keep = [(u, v) for u, v, d in G_sample.edges(data=True) if d["weight"] > 0.001]
G_sample = G_sample.edge_subgraph(edges_to_keep).copy()

# Compute visual properties
p_u_values = {}
category_labels = {}
category_colors = {}

categories = list(set(restaurant_info.get(n, [""]*7)[6] for n in G_sample.nodes))

cmap_nodes = plt.cm.get_cmap("Dark2", len(categories))
cat_color_map = {cat: cmap_nodes(i) for i, cat in enumerate(categories)}

for node in G_sample.nodes:
    info = restaurant_info.get(node)
    rating = info[2]
    category = info[6]
    name = info[1]
    category_colors[node] = cat_color_map[category]

# Get edge weights
edge_weights = [data["weight"] for u, v, data in G_sample.edges(data=True)]

# Create figure with extra width for legend
fig, ax = plt.subplots(figsize=(20, 12))

# Assign categories for layout
for node in G_sample.nodes:
    G_sample.nodes[node]["subset"] = restaurant_info[node][6]

# Generate multipartite layout
pos = nx.multipartite_layout(G_sample)

# Draw network
nx.draw_networkx_nodes(
    G_sample, pos, 
    node_size=800,
    node_color=[category_colors[n] for n in G_sample.nodes],
    alpha=0.8,
    ax=ax
)


edge_vmin = 0
edge_vmax = np.percentile(edge_weights, 95)  # Use 95th percentile as max to prevent outlier distortion


category_code_map = {
    'Middle Eastern': 'W',
    'American': 'A',
    'European': 'J'
}


legend_handles = [
    mpatches.Patch(color=cat_color_map[cat], label=code)
    for cat, code in category_code_map.items()
]


plt.legend(
    handles=legend_handles,
    title="Category Codes",
    fontsize=12,
    bbox_to_anchor=(1.05, 1),
    frameon=False
)

nx.draw_networkx_edges(
    G_sample,
    pos,
    edge_color=edge_weights,
    edge_cmap=plt.cm.Blues,
    edge_vmin=edge_vmin,
    edge_vmax=edge_vmax,  # This ensures darkest blue is used
    width=2,
    arrows=True,                # Ensure arrows are visible
    arrowstyle='-|>',           # Standard arrow
    arrowsize=40,               # Larger arrowhead
    connectionstyle='arc3,rad=0.2',  # Gentle curves   
    ax=ax
    
)


sm = plt.cm.ScalarMappable(
    norm=colors.Normalize(vmin=edge_vmin, vmax=edge_vmax),
    cmap=plt.cm.Blues
)


nx.draw_networkx_labels(
    G_sample, pos, 
    labels=category_labels, 
    font_size=20,
    ax=ax
)





# Add flattened legend
legend = plt.legend(
    handles=legend_handles,
    fontsize=24,
    bbox_to_anchor=(0, 1),
    loc='upper left',
    ncol=3,  # Adjust number of columns as needed
    frameon=False,
    handletextpad=0.3,
    columnspacing=0.8
)

# Add colorbar

cbar = plt.colorbar(sm, ax=ax, shrink=0.7)
cbar.set_label("Transition Probability", fontsize=24)
cbar.ax.tick_params(labelsize=24)

# Adjust layout

plt.tight_layout(rect=[0, 0, 0.9, 1])  # Leave 10% space on right for legend

plt.savefig('TransitionNW')


#%% Calculates Page Rank
stationary = nx.pagerank(G_dir,alpha=1, weight='weight')
sorted_nodes = sorted(stationary.items(), key=lambda x: x[1], reverse=True)

fig = plt.figure(figsize=(8, 5))
plt.plot(np.sort(list(stationary.values())), 'o')
plt.xlabel('Restautan_ID',fontsize=15 )
plt.ylabel('Stationary Distribution',fontsize=15 )
plt.xticks(fontsize=15)
plt.yticks(fontsize=15)
plt.grid('True')
plt.tight_layout()
plt.show()

#%% Test

nodes = list(G_dir.nodes())
# Build stochastic matrix with damping, here alpha=1
P = nx.google_matrix(G_dir, alpha=1, nodelist=nodes, weight='weight')
P = np.array(P)
pi = np.array([stationary[node] for node in nodes])  # shape (n,)

# Check deviation
pi_diff = pi @ P - pi

print("Deviation from stationary:", np.linalg.norm(pi_diff)) # almost 0 meanes P has good properties


#%% Print Top 22 Restaurants

# from the above plot one can determine which restaurants are the most outstanding

print(" Top 22 Restaurants by Stationary Distribution:\n")
for i, (rest_id, score) in enumerate(sorted_nodes[:22], 1):
    info = restaurant_info.get(rest_id)
    if info:
        print(f"{i:2d}. {info[1]} ({info[7]})")
        print(f"    → Rating: {info[2]}")
        print(f"    → Reviews: {info[3]}")
        print(f"    → Price: {info[4]}")
        print(f"    → Category: {info[6]}")
        print(f"    → Stationary Probability: {score:.5f}")
        print("-" * 60)

#%% Print Worse 10 Restaurants

sorted_nodes_by_stationary = sorted(stationary.items(), key=lambda x: x[1])

print("😞 Worse 10 Restaurants by Stationary Distribution:\n")
for i, (rest_id, score) in enumerate(sorted_nodes_by_stationary[:10], 1):
    info = restaurant_info.get(rest_id)
    if info:
        print(f"{i:2d}. {info[1]} ({info[7]})")
        print(f"    → Rating: {info[2]}")
        print(f"    → Reviews: {info[3]}")
        print(f"    → Price: {info[4]}")
        print(f"    → Category: {info[6]}")
        print(f"    → Stationary Probability: {score:.5f}")
        print("-" * 60)

#%% Stationary Distribution and Rating  per Category

# Group stationary distribution values and ratings by category
category_stationary = defaultdict(list)
category_ratings = defaultdict(list)

for rest_id, prob in stationary.items():
    info = restaurant_info.get(rest_id)
    if info:
        category = info[6]  # cleaned category
        rating = info[2]    # rating
        category_stationary[category].append(prob)
        category_ratings[category].append(rating)

# Compute averages
avg_stationary = {cat: np.mean(vals) for cat, vals in category_stationary.items()}
avg_rating = {cat: np.mean(vals) for cat, vals in category_ratings.items()}

#%%
plt.figure(figsize=(10, 6))

for cat in avg_stationary:
    x = avg_rating.get(cat, 0)
    y = avg_stationary[cat]
    if x > 0 and y > 0:  # log scale requires positive values
        plt.scatter(x, y)
        plt.annotate(cat, (x, y), fontsize=12, alpha=0.8)

plt.xscale("log")
plt.yscale("log")

plt.xlabel('Average Rating (log scale)', fontsize=15)
plt.ylabel('Stationary Distribution (log scale)', fontsize=15)
plt.xticks(fontsize=12)
plt.yticks(fontsize=12)
plt.title("Category Rating vs Stationary Probability (Log-Log Scale)", fontsize=15)
plt.grid(True, which="both", linestyle='--', linewidth=0.5)
plt.tight_layout()
plt.show()

# print results

print(avg_stationary)

#%%

# Generate label list: A, B, ..., Z, AA, AB, ..., ZZ
def generate_labels():
    letters = string.ascii_uppercase
    for size in range(1, 3):  # 1-letter and 2-letter combos
        for combo in itertools.product(letters, repeat=size):
            yield ''.join(combo)

labels_gen = generate_labels()
label_map = {cat: label for cat, label in zip(sorted(avg_stationary.keys()), labels_gen)}

# Plot
plt.figure(figsize=(10, 6))

for cat in sorted(avg_stationary.keys()):
    x = avg_rating.get(cat, 0)
    y = avg_stationary.get(cat, 0)
    if x > 0 and y > 0:
        plt.scatter(x, y)
        plt.annotate(label_map[cat], (x, y), fontsize=13, alpha=0.8)

plt.xlabel('Average Rating', fontsize=25)
plt.ylabel('Stationary Distribution', fontsize=25)
plt.xticks(fontsize=25)
plt.yticks(fontsize=25)
plt.title("Category Rating vs Stationary Distribution", fontsize=25)
plt.grid(True, which="both", linestyle='--', linewidth=0.5)
plt.tight_layout()
plt.savefig('Result.png')




