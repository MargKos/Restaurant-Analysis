#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jun 12 10:54:09 2025

@author: kostre
"""

import sqlite3
import requests
from Key import API_KEY

# calls Yelp-API restaurants, extracts from json and saves as SQL database

# Configuration: specify location and type 

LOCATION = "Berlin"
TERM = "restaurant"
LIMIT = 50  # Yelp's per-request limit
HEADERS = {"Authorization": f"Bearer {API_KEY}"}  # API Key

# SQLite setup
conn = sqlite3.connect("yelp_data.db")
cursor = conn.cursor()

# Create table
cursor.execute("""
CREATE TABLE IF NOT EXISTS restaurants (
    id TEXT PRIMARY KEY,
    name TEXT,
    rating REAL,
    review_count INTEGER,
    price TEXT,
    category TEXT,
    city TEXT
)
""")


def fetch_yelp(offset=0):
    """Fetches Yelp businesses data for a given offset.
    Args:
        offset (int): Pagination offset for API results.
    Returns:
        List[dict]: List of business data (empty list on error).
    """
    ...
    url = "https://api.yelp.com/v3/businesses/search"
    params = {
        "location": LOCATION,
        "term": TERM,
        "limit": LIMIT,
        "offset": offset
    }
    response = requests.get(url, headers=HEADERS, params=params)

    if response.status_code != 200:
        print("Yelp API error:", response.status_code)
        print(response.text)
        return []  # return empty list if failed

    return response.json().get("businesses", [])




# Loop through multiple pages ( 200 businesses, split into 4 pages of 50)
for offset in range(0, 200, 50):
    for b in fetch_yelp(offset):  # b represents one business
        categories = ", ".join([c["title"] for c in b.get("categories", [])])
        price = b.get("price", "N/A")
        city = b["location"]["city"]
        #insert data into restaurants table
        cursor.execute("""
        INSERT OR IGNORE INTO restaurants (id, name, rating, review_count, price, category, city)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            b["id"],
            b["name"],
            b["rating"],
            b["review_count"],
            price,
            categories,
            city
        ))

conn.commit()  
#%% Test
    
# Connect to the database
conn = sqlite3.connect("yelp_data.db")  # data_base name
cursor = conn.cursor()

# Preiew
cursor.execute("SELECT * FROM restaurants LIMIT 200;")
rows = cursor.fetchall()

# Print results
for row in rows:
    print(row)


conn.close()
