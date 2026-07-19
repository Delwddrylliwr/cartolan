# Stale model weights

These weights were trained against the pre-refactor Beginner/Regular/Advanced
rules. The game rules, editions, and observation space have since been aligned
to the official rulebooks (LiteWinds/ShadyRoutes/SilkRoads), so these models
need retraining before they will play sensibly. See
`cartolan/players/ann.py`.
