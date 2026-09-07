import math


class IRT2PL:
    """
    Two-Parameter Logistic Item Response Theory model.

    The 2PL model estimates the probability that a learner
    answers an item correctly based on:

        theta = learner ability
        a     = item discrimination
        b     = item difficulty

    Formula:

        P(X=1) = 1 / (1 + exp(-a * (theta - b)))
    """

    def __init__(
        self,
        discrimination=1.0,
        difficulty=0.0
    ):
        """Initialize a 2PL item."""

        if discrimination <= 0:
            raise ValueError(
                "Discrimination parameter must be greater than 0."
            )

        self.discrimination = float(discrimination)
        self.difficulty = float(difficulty)


    def probability(
        self,
        theta
    ):
        """
        Calculate probability of a correct response.

        Parameters
        ----------
        theta : float
            Learner ability.

        Returns
        -------
        float
            Probability between 0 and 1.
        """

        theta = float(theta)

        exponent = (
            -self.discrimination
            * (theta - self.difficulty)
        )

        # Prevent numerical overflow in exp()
        exponent = max(
            min(exponent, 700),
            -700
        )

        return 1.0 / (
            1.0 + math.exp(exponent)
        )


    def predict(
        self,
        theta,
        threshold=0.5
    ):
        """
        Predict whether the learner will answer correctly.

        Returns:
            1 for predicted correct
            0 for predicted incorrect
        """

        probability = self.probability(theta)

        return int(
            probability >= threshold
        )


    def information(
        self,
        theta
    ):
        """
        Calculate Fisher information provided by an item.

        For the 2PL model:

            I(theta) = a^2 * P(theta) * (1 - P(theta))

        Higher information means the item is more useful
        for estimating learner ability at that theta.
        """

        probability = self.probability(theta)

        return (
            self.discrimination ** 2
            * probability
            * (1.0 - probability)
        )


    def parameters(self):
        """Return item parameters as a dictionary."""

        return {
            "discrimination_a": self.discrimination,
            "difficulty_b": self.difficulty
        }