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
import matplotlib.pyplot as plt
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

# Only add edges with ≥1 shared users
for (r1, r2), count in co_visits.items():
    if count >= 1:  
        G.add_edge(r1, r2, weight=count)

# get information of restaurants

# Connect to DB and build ID→info mapping
cursor.execute("SELECT id, name, rating, review_count, price, category, cleaned_category, city FROM cleaned_restaurants;")
rows = cursor.fetchall()

restaurant_info = {row[0]: row for row in rows}

#%% Construct Transition Network
rating_dict = {rid: info[2] for rid, info in restaurant_info.items() if rid in G.nodes}
nx.set_node_attributes(G, rating_dict, name="rating") # the rating is the node value

# Compute total transitions per restaurant (for normalization)
total_transitions = defaultdict(float)
for (u, v), count in co_visits.items():
    if count >= 1:
        total_transitions[u] += count
        total_transitions[v] += count

#  Calulate transition probability from u to v
G_dir = nx.DiGraph()

for u, v, data in G.edges(data=True):
    weight = data.get("weight", 1)
    rating_u = restaurant_info.get(u, [None, None, 0])[2] 
    rating_v = restaurant_info.get(v, [None, None, 0])[2]

    p_u = 1 - (rating_u - 1) / 4  # leaving probability is linear and anti-proportional to rating
    p_v = 1 - (rating_v - 1) / 4

    norm_u = weight / total_transitions[u] # transition probability from u to v
    norm_v = weight / total_transitions[v] # transition probability from v to u

    G_dir.add_edge(u, v, weight=norm_u * p_u) # update edges
    G_dir.add_edge(v, u, weight=norm_v * p_v)

#%% Calculate Stationary Distribution
stationary = nx.pagerank(G_dir, weight='weight')
sorted_nodes = sorted(stationary.items(), key=lambda x: x[1], reverse=True)

fig = plt.figure(figsize=(8, 5))
plt.plot(np.sort(list(stationary.values())))
plt.grid(True)
plt.tight_layout()
plt.show()
#%% Print Top 40 Restaurants
print("\U0001F3C6 Top 40 Restaurants by Stationary Distribution:\n")
for i, (rest_id, score) in enumerate(sorted_nodes[:40], 1):
    info = restaurant_info.get(rest_id)
    if info:
        print(f"{i:2d}. {info[1]} ({info[7]})")
        print(f"    → Rating: {info[2]}")
        print(f"    → Reviews: {info[3]}")
        print(f"    → Price: {info[4]}")
        print(f"    → Category: {info[6]}")
        print(f"    → Stationary Probability: {score:.5f}")
        print("-" * 60)

#%% Average Stationary and Rating  per Category

# Group stationary values and ratings by category
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

# Plot
plt.figure(figsize=(10, 6))

for cat in avg_stationary:
    x = avg_rating.get(cat, 0)
    y = avg_stationary[cat]
    plt.scatter(x, y)
    plt.annotate(cat, (x, y), fontsize=8, alpha=0.8)

plt.xlabel("Average Rating per Category")
plt.ylabel("Average Stationary Probability per Category")
plt.title("Category Rating vs Stationary Distribution")
plt.grid(True)
plt.tight_layout()
plt.show()
