# dp.py

import csv
import attr
import numpy as np


class BudgetDepletedError(Exception):
    pass


@attr.s
class Rating:
    """Movie rating."""
    user = attr.ib()
    movie = attr.ib()
    date = attr.ib()
    stars = attr.ib()

# Unsure what Rating this? It is a convenient alternative to namedtuple.

class DpQuerySession:
    """
    Respond to database queries with differential privacy.

    Args:
        db (str): Path to the ratings database csv-file.
        privacy_budget (float): Total differential privacy epsilon for the session.
    """

    def __init__(self, db, privacy_budget):

        self.db = db
        self.privacy_budget = privacy_budget
        self._load_db()
        self.epsilons = []
        self.output_history = {}

    def _load_db(self):
        """Load the rating database from a csv-file."""
        self._entries = []
        with open(self.db) as f:
            reader = csv.reader(f, quotechar='"', delimiter=",")
            for email, movie, date, stars in reader:
                self._entries.append(
                    Rating(user=email, movie=movie, date=date, stars=int(stars))
                )

    @property
    def remaining_budget(self):
        """
        Calculate the remaining privacy budget.

        Returns:
            float: The remaining privacy budget.
        """
        return self.privacy_budget - sum(self.epsilons)

    def get_count(self, movie_name, rating_threshold, epsilon):
        """
        Get the number of ratings where a given movie is rated at least as high as threshold.

        Args:
            movie_name (str): Movie name.
            rating_threshold (int): Rating threshold (number between 1 and 5).
            epsilon: Differential privacy epsilon to use for this query.

        Returns:
            float: The count with differentially private noise added.

        Raises:
            BudgetDepletedError: When query would exceed the total privacy budget.
        """
        # WARNING: Do not convert the response to positive integers. Leave as a
        # possibly negative float. This is a requirement for our verification.
        #
        # Question: Converting to a positive integer does not affect privacy. Why?

        # Compute privacy noise
        if (movie_name, rating_threshold) in self.output_history:
            return self.output_history[movie_name, rating_threshold]

        # Check for enough credit
        self.epsilons.append(epsilon)
        if self.remaining_budget < 0.0 :
            raise BudgetDepletedError("Not enough privacy budget to run such a intrusive query")

        delta_f = 1 # for count agg function, it's always 1
        loc, scale = 0, delta_f / epsilon
        noise = np.random.laplace(loc, scale, 1)[0]

        # Compute count value from the db
        count = 0
        for entry in self._entries:
            if (entry.movie == movie_name) and (entry.stars >= rating_threshold):
                count += 1

        # Save the value to prevent further attacking 
        output = count + noise
        self.output_history[movie_name, rating_threshold] = output

        return output



if __name__ == '__main__':
    querier = DpQuerySession("imdb-dp.csv", privacy_budget=1.0)
    count = querier.get_count("Seven Samurai", rating_threshold=3, epsilon=0.25)
    print(count)