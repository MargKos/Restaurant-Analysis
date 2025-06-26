#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jun 26 10:20:14 2025

@author: kostre
"""
import networkx as nx
import sqlite3


# Connect to Database
conn = sqlite3.connect("cleaned_yelp_data.db")
cursor = conn.cursor()

# Fetch the first few rows
cursor.execute("SELECT * FROM cleaned_restaurants LIMIT 200;")
rows = cursor.fetchall()

restaurant_info = {row[0]: row for row in rows}
restaurant_info = {str(row[0]): row for row in rows}

# load network

G_dir = nx.read_graphml("restaurant_network.graphml")


# Person 'A' and 'B' want to open a restaurant. They can choose location, or categoryor price. 



# A selects category and price

cat_A='Fast Food'
price_A='€'



# B selects category and price

cat_B='Italian'
price_B='€€'



# print all restaurants of G_dir of vairant A

restaurants_possible_connections_A = []

for rid in G_dir.nodes:
    info = restaurant_info.get(rid)
 
    if info[7] == cat_A and info[4] == price_A:
        restaurants_possible_connections_A.append(rid)

# Print matching restaurant names
for rid in restaurants_possible_connections_A:
    info = restaurant_info[rid]
    print(f"{info[1]} ({info[7]}, {info[4]}) - Review: {info[3]}")

# print all restaurants of G_dir of vairant B

restaurants_possible_connections_B = []

for rid in G_dir.nodes:
    info = restaurant_info.get(rid)

    if info[7] == cat_B and info[4] == price_B:
        restaurants_possible_connections_B.append(rid)

# Print matching restaurant names
for rid in restaurants_possible_connections_B:
    info = restaurant_info[rid]
    print(f"{info[1]} ({info[7]}, {info[4]}) - Review: {info[3]}")

#%%
# now they add the restraunt to the netowk, for example by choosing a location close to the existing restaurants or
# by cooperate on social media
# for a fair comparison let them choose restaurants with similar number of reviews
# both restaurants will have a connection strength of 0.005 (one can play aroudn with this value)
def add_restaurant_version(G, name, rating, category, price, connection_id, weight=0.005):
    """
    Adds a new restaurant node to the graph and connects it bidirectionally
    to an existing node with given weight.
    """
    G.add_node(name)
    G.nodes[name]["rating"] = rating
    G.nodes[name]["category"] = category
    G.nodes[name]["price"] = price

    G.add_edge(name, connection_id, weight=weight)
    G.add_edge(connection_id, name, weight=weight)

    # Recalculate stationary distribution
    stationary = nx.pagerank(G, alpha=1, weight='weight')
    return stationary.get(name, 0.0)

# === Version A ===
restaurant_A = "new_restaurant_A"
stationary_A = add_restaurant_version(
    G_dir,
    name=restaurant_A,
    rating=3.5,  # average rating of a restaurant on google, plays no role for the result
    category=cat_A,
    price=price_A,
    connection_id=restaurants_possible_connections_A[2]
)
print(f"Stationary probability of '{restaurant_A}': {stationary_A:.5f}")

# === Version B ===
restaurant_B = "new_restaurant_B"
stationary_B = add_restaurant_version(
    G_dir,
    name=restaurant_B,
    rating=3.5,
    category=cat_B,
    price=price_B,
    connection_id=restaurants_possible_connections_B[2]
)
print(f"Stationary probability of '{restaurant_B}': {stationary_B:.5f}")

