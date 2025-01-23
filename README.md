# Unusual Pricing
 
This project will focus on estimating appropriate pricing for virtual items in the Team 
Fortress 2 video game, which has one of the oldest existing game item trading economies. 

### Background:

TF2 is one of the first [randomized-lootbox games](https://en.wikipedia.org/wiki/Team_Fortress_2#Items_and_economy).
In any given "crate", some items drop commonly, others more rarely. All differences
between the most valuable items are entirely cosmetic, from rare weapons with varying
patterns to our topic, "unusual"-quality clothing items with a small visual effect that
appears above the player. Unlike most current games, players have been able to freely 
trade items with other players since 2010, which has led to the development of 
third-party sites that estimate the value of in-game items. 

This project focuses on the pricing available through https://backpack.tf/, which has
become the dominant pricing source over the 15 years since the trading economy began. 
It has an API which allows anyone who registers to download the current price database
as a json object. 

## Project structure:

Environment: Default Anaconda3

Currently working on: 2-i

1. Collect and perform initial data preparation
   1. Download data using personal API key
   2. Store JSON object
   3. Parse data to focus only on items classified as "unusual" quality
   4. Convert to dataframe which provides item properties, price, and date
   5. Repeat steps 3 and 4 for any previously-stored JSON objects, keeping differences

2. Model preprocessing and pipeline
   1. One-hot encode our categorical variables
   2. Log-transform price (keeping it basic)
   3. Generate time-weighting variable
   4. Fit model (weighted to focus on recent prices

