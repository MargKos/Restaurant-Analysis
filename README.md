# Restaurant-Analyis
This project builds a graph-theoretic model of restaurant co-visitation behavior using Yelp data to explore the difference between rating and popularity.

We analyze a network where:

    Nodes represent restaurants.

    Edges connect restaurants that were visited by the same users.

    Weights on edges represent co-visit frequency, adjusted by restaurant ratings.

    A Markov chain defines transition probabilities between restaurants based on user flow and rating-dependent probabilities.

This helps us uncover:

    Differences between popularity (being visited often) and quality (high rating).

    The stationary distribution of a user randomly navigating the restaurant landscape.

    Category-level insights: which cuisines keep users coming back, and which fade out.




# Folder Strucutre
 users.json                  # Synthetic or anonymized user review data
cleaned_yelp_data.db       # Cleaned SQLite DB of restaurant metadata
Transition_Network.py         # Main Python script with network and Markov modeling
Fake_Users.py    		# creates fake users
Database.py # cleans Yelp data
fetch_data.py. # fetches yelp internet data


# Hot to Run

# Results


# Data Ethics


Due to terms of service, original Yelp data is not included. All user data is anonymized or synthetically generated. Restaurant names are optionally pseudonymized for publishing.


MIT License. Use and modify freely, but please respect data privacy if you adapt this for real-world datasets.