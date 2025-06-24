#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jun 12 11:30:06 2025

@author: kostre
"""

import numpy as np
import pandas as pd
import sqlite3
from collections import defaultdict
import matplotlib.pyplot as plt
from collections import Counter
import json

"""
Simulates how users discover restaurants based on:
- Price 
- Category
We assign to each review one user. Furthermore, for each restaurant each user
cannot give  more than 1 review.
"""
# Load database
conn = sqlite3.connect("cleaned_yelp_data.db")
cursor = conn.cursor()

# Preview
cursor.execute("SELECT * FROM cleaned_restaurants LIMIT 200;")
rows = cursor.fetchall()

for row in rows:
    print(row)

restaurant_info = {
    row[0]: {'price': row[4], 'cleaned_category': row[7], 'rating':row[2]}
    for row in rows
}


number_of_reviews = sum(row[3] for row in rows)
number_of_users = 1050   # select total number of users (modellign parameter)

#%% Assign number of reviews for each user assuming Poisson distribution
users = []
reviews_left = number_of_reviews
i = 0  # user index, gives number of users who already got their reviews
avg_reviews=20
while reviews_left > 0 and i < number_of_users:
    avg_reviews = 25
    num_reviews_u = np.random.poisson(avg_reviews)  
    max_possible = min(num_reviews_u, reviews_left)  
   
    users.append({
        'user_id': f"user_{i}",
        'num_reviews': num_reviews_u
    })
    
    reviews_left = reviews_left-num_reviews_u   # update number of left reviews
  
    i += 1                                      # move to the next user 
    
# Test


total_reviews = sum(user['num_reviews'] for user in users)
print(total_reviews,number_of_reviews )   # prints how many reviews were assigned versus the total number

#%% Build a map from restaurant_id to how many reviews are available


restaurant_review_capacity = {row[0]: row[3] for row in rows}
restaurant_id_list = [row[0] for row in rows]


#%% Assign restaurant to users by their preferences, the first restaurant is chosen randomly the second choice prefers
#restaurant with similar price and category

for user in users:
    number = user['num_reviews']
    if number == 0:
        user['reviewed_restaurants'] = []
        continue

    assigned = []
    visited_prices = defaultdict(int)  # dictionary which tracks number of visits of this user per price
    visited_categories = defaultdict(int) # dictionary which tracks number of visits of this user per categroy

    # First restaurant: random
    available_restaurants = [rid for rid in restaurant_id_list if restaurant_review_capacity[rid] > 0]
    if not available_restaurants:
        user['reviewed_restaurants'] = []
        continue

    first_choice = np.random.choice(available_restaurants)
    assigned.append(first_choice)
    restaurant_review_capacity[first_choice] -= 1

    info = restaurant_info[first_choice]  # get info of this restaurant
    visited_prices[info['price']] += 1
    visited_categories[info['cleaned_category']] += 1  # update dict
   
    # Choose next restaurant accoring to dict visited_prices and visited_categories
    for _ in range(number - 1):
        available_restaurants = [
            rid for rid in restaurant_id_list
            if restaurant_review_capacity[rid] > 0 and rid not in assigned
        ]
        if not available_restaurants:
            break
        # score the restaurants accoring to the visits
        scores = []
        for rid in available_restaurants:
            info = restaurant_info[rid]
            price_score = visited_prices[info['price']] # give the same score as in the dict
            category_score = visited_categories[info['cleaned_category']]  # give the same score as in the dict
            score = price_score*1.5 + category_score  # 1.5 means we are weightining price more than category
            scores.append(score)
        
        # transform to a weight vector
        weights = np.array(scores, dtype=float)
        

        # Prevent all-zero weights: if no match at all, fall back to uniform
        if weights.sum() == 0:
            weights = np.ones(len(weights)) / len(weights)
        else:
            weights /= weights.sum()

        chosen = np.random.choice(available_restaurants, p=weights)
        assigned.append(chosen)
        restaurant_review_capacity[chosen] -= 1

        # Update dict and restaurants pool
        info = restaurant_info[chosen]
        visited_prices[info['price']] += 1
        visited_categories[info['cleaned_category']] += 1
      

    user['reviewed_restaurants'] = assigned




#%% Example: preference of one users


# Global dictionaries to hold total preferences
user_price_counts = defaultdict(int)
user_category_counts = defaultdict(int)


user=users[9]
for rid in user.get('reviewed_restaurants', []):
    info = restaurant_info[rid]
    price = info['price']
    category = info['cleaned_category']

    user_price_counts[price] += 1
    user_category_counts[category] += 1

# Print summary
print("User Price Preferences:")
for price, count in sorted(user_price_counts.items(), key=lambda x: -x[1]):
    print(f"  {price}: {count}")

print("User Category Preferences:")
for cat, count in sorted(user_category_counts.items(), key=lambda x: -x[1]):
    print(f"  {cat}: {count}")
    
    
#%% Save users

with open("users.json", "w") as f:
    json.dump(users, f, indent=4)
