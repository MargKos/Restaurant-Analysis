#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jun 12 11:22:40 2025
@author: kostre
"""

import sqlite3
import pandas as pd

# Connect to .db
conn = sqlite3.connect("yelp_data.db")
cursor = conn.cursor()

# Preview
cursor.execute("SELECT * FROM restaurants LIMIT 200;")
print("Original Data")

for row in cursor.fetchall():
    print(row)


#%% Clean Data, by assigning proper categories

# Load data
df = pd.read_sql_query("SELECT * FROM restaurants", conn)

# Define  categories 
category_map = {
    'german': 'German',
    'swabian': 'German',
    'beer garden': 'German',
    'bavarian': 'German',
    'game meat': 'German',
    'schnitzel': 'German',
    'russian': 'Slavic',
    'ukrainian': 'Slavic',
    'modern european': 'European',
    'pan asian': 'Asian',
    'ramen': 'Korean',
    'korean': 'Korean',
    'american': 'American',
    'chinese': 'Chinese',
    'soup': 'Chinese',
    'coffee & tea': 'Cafe',
    'cafes': 'Cafe',
    'café': 'Cafe',
    'breakfast & brunch': 'Breakfast',
    'fast food': 'Fast Food',
    'burgers': 'Burgers',
    'thai': 'Thai',
    'mediterranean': 'Mediterranean',
    'japanese': 'Japanese',
    'barbeque': 'Japanese',
    'indonesian': 'Indonesian',
    'turkish': 'Turkish',
    'italian': 'Italian',
    'dim sum': 'Asian',
    'vietnamese': 'Vietnamese',
    'greek': 'Greek',
    'indian': 'Indian',
    'lebanese': 'Lebanese',
    'singaporean': 'Singaporean',
    'pizza': 'Pizza',
    'austrian': 'Austrian',
    'seafood': 'Seafood',
    'persian/iranian': 'Persian',
    'chocolatiers & shops': 'Chocolate Shop',
    'food stands': 'Fast Food',
    'wine bars': 'Bars',
    'gastropubs': 'Bars',
    'scottish, beer garden, tapas/small plates': 'Irish',
    'international, bars, breakfast & brunch': 'Breakfast',
    'mediterranean, caterers, breakfast & brunch': 'Breakfast',
    'breakfast & brunch, international': 'Breakfast',
    'gastropubs, cocktail bars': 'Bars',
    'breakfast & brunch, music venues': 'Breakfast',
    'ukrainian, international': 'Slavic',
    'tea rooms, taiwanese': 'Taiwan',
    'argentine': 'Argentine',
    'breweries, gastropubs': 'German',
    'steakhouses': 'American',
    'curry sausage': 'German',
    'breakfast & brunch, bakeries': 'Breakfast',
    'steakhouses, barbeque': 'American',
    'rhinelandian, pubs': 'German',
    'latin american': 'Latin',
    'breakfast & brunch, swabian, baden': 'Breakfast',
    'wine bars, delicatessen, georgian': 'Bars',
    'international, breakfast & brunch': 'Breakfast',
    'serbo croatian': 'Slavic',
    'asian fusion': 'Asian',
    'mexican, tex-mex, vegan': 'Vegan',
    'spanish, portuguese': 'Latin',
    'polish': 'Slavic',
    'french': 'French',
    'french, brasseries': 'French',
    'himalayan/nepalese': 'Nepalese',
    'cuban, cocktail bars, cajun/creole': 'Latin',
    'arabic, syrian': 'Arabic',
    'bulgarian': 'Bulgarian',
    'african': 'African',
    'scandinavian': 'Scandinavian',
    'sushi bars': 'Japanese',
    'syrian':'Syrian',
    'kebab':'Fast Food',
    'spanish, Tapas Bars':'Latin',
    'egan, Vegetarian':'Vegan',
    'tapas bars':'Latin',
    'arabic':'Arabic',
    'canteen':'German',
    'mexican':'Latin',
    'middle eastern':'Middle Eastern',
    'french brasseries':'French',
    'brasseries':'French',
    'peruvian':'Latin'
}



def clean_category(category_text):
    category_text = category_text.lower()  # Lowercase everything
    for key, label in category_map.items():
        if key.lower() in category_text:
            return label
    return "Unidentified"                  # if category is not found


# Apply cleaning
df["cleaned_category"] = df["category"].apply(clean_category)  # apply clean_categroy fct on table row 'category' define new category 'cleaned_category'

# Save to new DB
cleaned_conn = sqlite3.connect("cleaned_yelp_data.db")
df.to_sql("cleaned_restaurants", cleaned_conn, if_exists="replace", index=False)
cleaned_conn.commit()



#%% Preview

cursor2 = cleaned_conn.cursor()


cursor2.execute("SELECT * FROM cleaned_restaurants LIMIT 200;")
for row in cursor2.fetchall():
    print(row)


#%% show all with unidentified label

cursor2.execute("SELECT * FROM cleaned_restaurants WHERE cleaned_category = 'Unidentified';")
rows = cursor2.fetchall()

k=0
# Print each matching restaurant
for row in rows:
    print(row)
    k=k+1

conn.close()
