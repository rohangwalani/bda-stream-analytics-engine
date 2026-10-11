import random
from datetime import datetime, timedelta

PAGES = ["/home", "/product", "/search", "/cart", "/checkout", "/about", "/blog", "/support"]
PAGE_WEIGHTS = [30, 25, 15, 10, 6, 5, 5, 4]
ACTIONS = ["view", "click", "add_to_cart", "login", "purchase"]
ACTION_WEIGHTS = [55, 25, 10, 7, 3]


def generate_stream(num_events=50000, num_users=100000, zipf_s=1.0, seed=42, start=None):
    """Yield time-ordered synthetic clickstream events.

    User activity follows a Zipf distribution (a few heavy users, a long tail),
    which is far more realistic than uniform sampling and gives the
    Count-Min Sketch something meaningful to find. Seeded, so runs are reproducible.
    """
    rng = random.Random(seed)
    user_weights = [1 / (rank ** zipf_s) for rank in range(1, num_users + 1)]
    users = rng.choices(range(num_users), weights=user_weights, k=num_events)
    pages = rng.choices(PAGES, weights=PAGE_WEIGHTS, k=num_events)
    actions = rng.choices(ACTIONS, weights=ACTION_WEIGHTS, k=num_events)

    t = start or datetime(2026, 1, 1)
    for i in range(num_events):
        t += timedelta(milliseconds=rng.expovariate(1 / 500))
        yield {
            "log_id": i,
            "user_id": f"user_{users[i]:06d}",
            "timestamp": t,
            "action": actions[i],
            "page": pages[i],
        }
