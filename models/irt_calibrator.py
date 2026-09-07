"""
2PL IRT Calibration

Estimates:
    - learner ability (theta)
    - item difficulty (b)
    - item discrimination (a)

Method:
    Joint Maximum Likelihood Estimation (JMLE)
    using L-BFGS-B.

Synthetic ground-truth parameters are used ONLY for
post-calibration reference/validation and are NOT used
by the optimizer.
"""

import json
import os

import numpy as np
import pandas as pd
from scipy.optimize import minimize


# ============================================================
# PATHS
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

RESPONSE_PATH = os.path.join(
    BASE_DIR,
    "synthetic_data",
    "data",
    "irt_response_matrix.csv"
)

ITEM_REFERENCE_PATH = os.path.join(
    BASE_DIR,
    "synthetic_data",
    "data",
    "irt_item_params.csv"
)

OUTPUT_PATH = os.path.join(
    BASE_DIR,
    "models",
    "irt_item_params.json"
)


# ============================================================
# 2PL IRT MODEL
# ============================================================

class IRT2PL:
    """
    Two-Parameter Logistic IRT model.

    P(X=1 | theta) =
        1 / (1 + exp(-a(theta-b)))

    theta = learner ability
    a     = item discrimination
    b     = item difficulty
    """

    def __init__(
        self,
        discrimination_a=1.0,
        difficulty_b=0.0
    ):
        if discrimination_a <= 0:
            raise ValueError(
                "Discrimination parameter 'a' must be > 0."
            )

        self.a = float(
            discrimination_a
        )

        self.b = float(
            difficulty_b
        )

    def probability(
        self,
        theta
    ):
        """
        Calculate probability of a correct response.
        """

        theta = np.asarray(
            theta,
            dtype=float
        )

        z = self.a * (
            theta - self.b
        )

        return stable_sigmoid(z)

    def predict(
        self,
        theta,
        threshold=0.5
    ):
        """
        Predict response.

        1 = correct
        0 = incorrect
        """

        probability = self.probability(
            theta
        )

        return (
            probability >= threshold
        ).astype(int)

    def information(
        self,
        theta
    ):
        """
        Fisher information:

            I(theta) = a^2 P(1-P)
        """

        probability = self.probability(
            theta
        )

        return (
            self.a ** 2
            * probability
            * (1.0 - probability)
        )

    def parameters(self):
        """
        Return model parameters.
        """

        return {
            "discrimination_a": self.a,
            "difficulty_b": self.b
        }


# ============================================================
# STABLE SIGMOID
# ============================================================

def stable_sigmoid(
    x
):
    """
    Numerically stable sigmoid.
    """

    x = np.asarray(
        x,
        dtype=float
    )

    return np.where(
        x >= 0,
        1.0 / (
            1.0 + np.exp(-x)
        ),
        np.exp(x) / (
            1.0 + np.exp(x)
        )
    )


# ============================================================
# LOAD RESPONSE DATA
# ============================================================

def load_response_data():
    """
    Load and validate the synthetic IRT response data.
    """

    if not os.path.exists(
        RESPONSE_PATH
    ):
        raise FileNotFoundError(
            f"Response data not found: "
            f"{RESPONSE_PATH}"
        )

    df = pd.read_csv(
        RESPONSE_PATH
    )

    required_columns = {
        "learner_id",
        "item_id",
        "response",
        "data_source"
    }

    missing = (
        required_columns
        - set(df.columns)
    )

    if missing:
        raise ValueError(
            f"Missing required columns: "
            f"{sorted(missing)}"
        )

    # --------------------------------------------------------
    # Sandbox validation
    # --------------------------------------------------------

    if not (
        df["data_source"]
        == "[SANDBOX DATA]"
    ).all():

        raise ValueError(
            "IRT calibration requires "
            "sandbox response data only."
        )

    # --------------------------------------------------------
    # Response validation
    # --------------------------------------------------------

    if not (
        df["response"].isin(
            [0, 1]
        )
    ).all():

        raise ValueError(
            "Responses must contain only 0 or 1."
        )

    # --------------------------------------------------------
    # Duplicate validation
    # --------------------------------------------------------

    duplicates = df.duplicated(
        subset=[
            "learner_id",
            "item_id"
        ]
    )

    if duplicates.any():
        raise ValueError(
            "Duplicate learner-item response "
            "pairs detected."
        )

    return df


# ============================================================
# RESPONSE MATRIX
# ============================================================

def prepare_matrix(
    responses
):
    """
    Convert long-format responses into:

        rows    = learners
        columns = items
        values  = responses
    """

    required_columns = {
        "learner_id",
        "item_id",
        "response"
    }

    missing = (
        required_columns
        - set(responses.columns)
    )

    if missing:
        raise ValueError(
            f"Missing columns for matrix preparation: "
            f"{sorted(missing)}"
        )

    matrix = responses.pivot(
        index="learner_id",
        columns="item_id",
        values="response"
    )

    if matrix.isna().any().any():
        raise ValueError(
            "Response matrix contains missing values."
        )

    return matrix.astype(float)


# ============================================================
# NEGATIVE LOG LIKELIHOOD
# ============================================================

def negative_log_likelihood(
    params,
    response_matrix
):
    """
    Calculate 2PL negative log likelihood.

    Parameter vector:

        [theta_1 ... theta_N,
         b_1 ... b_M,
         log(a_1) ... log(a_M)]
    """

    matrix = response_matrix.to_numpy(
        dtype=float
    )

    n_learners, n_items = (
        matrix.shape
    )

    expected_length = (
        n_learners
        + n_items
        + n_items
    )

    if len(params) != expected_length:
        raise ValueError(
            "Parameter vector has incorrect length."
        )

    # --------------------------------------------------------
    # Extract parameters
    # --------------------------------------------------------

    theta = params[
        :n_learners
    ]

    difficulty = params[
        n_learners:
        n_learners + n_items
    ]

    log_discrimination = params[
        n_learners + n_items:
    ]

    discrimination = np.exp(
        log_discrimination
    )

    # --------------------------------------------------------
    # Model probability
    # --------------------------------------------------------

    z = (
        theta[:, None]
        - difficulty[None, :]
    )

    z = (
        discrimination[None, :]
        * z
    )

    probabilities = stable_sigmoid(
        z
    )

    probabilities = np.clip(
        probabilities,
        1e-9,
        1.0 - 1e-9
    )

    # --------------------------------------------------------
    # Log likelihood
    # --------------------------------------------------------

    log_likelihood = (
        matrix
        * np.log(probabilities)
        +
        (1.0 - matrix)
        * np.log(
            1.0 - probabilities
        )
    )

    return float(
        -np.sum(
            log_likelihood
        )
    )


# ============================================================
# ANALYTICAL GRADIENT
# ============================================================

def negative_log_likelihood_gradient(
    params,
    response_matrix
):
    """
    Analytical gradient of the 2PL negative log likelihood.

    Parameter vector:

        [theta,
         b,
         log(a)]

    For:

        P = sigmoid(a(theta-b))

    and:

        error = P - X

    Gradients:

        dNLL/dtheta_i
            = sum_j a_j(P_ij - X_ij)

        dNLL/db_j
            = -sum_i a_j(P_ij - X_ij)

        dNLL/dlog(a_j)
            = sum_i a_j(theta_i-b_j)(P_ij-X_ij)
    """

    matrix = response_matrix.to_numpy(
        dtype=float
    )

    n_learners, n_items = (
        matrix.shape
    )

    expected_length = (
        n_learners
        + n_items
        + n_items
    )

    if len(params) != expected_length:
        raise ValueError(
            "Parameter vector has incorrect length."
        )

    # --------------------------------------------------------
    # Extract parameters
    # --------------------------------------------------------

    theta = params[
        :n_learners
    ]

    difficulty = params[
        n_learners:
        n_learners + n_items
    ]

    log_discrimination = params[
        n_learners + n_items:
    ]

    discrimination = np.exp(
        log_discrimination
    )

    # --------------------------------------------------------
    # Probability
    # --------------------------------------------------------

    z = (
        discrimination[None, :]
        *
        (
            theta[:, None]
            -
            difficulty[None, :]
        )
    )

    probabilities = stable_sigmoid(
        z
    )

    # --------------------------------------------------------
    # Residual
    # --------------------------------------------------------

    residual = (
        probabilities
        - matrix
    )

    # --------------------------------------------------------
    # Gradient for theta
    # --------------------------------------------------------

    gradient_theta = np.sum(
        residual
        *
        discrimination[None, :],
        axis=1
    )

    # --------------------------------------------------------
    # Gradient for difficulty b
    # --------------------------------------------------------

    gradient_difficulty = -np.sum(
        residual
        *
        discrimination[None, :],
        axis=0
    )

    # --------------------------------------------------------
    # Gradient for log(a)
    #
    # Because:
    #
    # a = exp(log_a)
    #
    # dNLL/dlog(a)
    #     =
    #     dNLL/da * a
    # --------------------------------------------------------

    gradient_log_discrimination = np.sum(
        residual
        *
        discrimination[None, :]
        *
        (
            theta[:, None]
            -
            difficulty[None, :]
        ),
        axis=0
    )

    # --------------------------------------------------------
    # Combine
    # --------------------------------------------------------

    gradient = np.concatenate(
        [
            gradient_theta,
            gradient_difficulty,
            gradient_log_discrimination
        ]
    )

    return gradient


# ============================================================
# INITIAL PARAMETERS
# ============================================================

def prepare_initial_parameters(
    matrix
):
    """
    Generate optimizer starting values.

    theta:
        logit learner accuracy

    b:
        negative logit item accuracy

    a:
        initialized to 1.0
    """

    n_learners, n_items = (
        matrix.shape
    )

    # --------------------------------------------------------
    # Learner theta
    # --------------------------------------------------------

    learner_mean = (
        matrix.mean(
            axis=1
        )
        .clip(
            0.01,
            0.99
        )
    )

    initial_theta = (
        np.log(
            learner_mean
            /
            (
                1.0
                - learner_mean
            )
        )
    ).to_numpy()

    # --------------------------------------------------------
    # Item difficulty
    # --------------------------------------------------------

    item_mean = (
        matrix.mean(
            axis=0
        )
        .clip(
            0.01,
            0.99
        )
    )

    initial_difficulty = (
        -np.log(
            item_mean
            /
            (
                1.0
                - item_mean
            )
        )
    ).to_numpy()

    # --------------------------------------------------------
    # Item discrimination
    # --------------------------------------------------------

    initial_discrimination = np.ones(
        n_items
    )

    # --------------------------------------------------------
    # Combine
    # --------------------------------------------------------

    initial_params = np.concatenate(
        [
            initial_theta,
            initial_difficulty,
            np.log(
                initial_discrimination
            )
        ]
    )

    return initial_params


# ============================================================
# CALIBRATION
# ============================================================

def calibrate_irt(
    response_matrix=None,
    max_iterations=200
):
    """
    Estimate learner abilities and 2PL item parameters.

    response_matrix:
        Optional pre-built learner x item matrix.

        If None, the complete response dataset is loaded.

    max_iterations:
        Maximum optimizer iterations.

    Returns:
        scipy OptimizeResult
    """

    print("=" * 70)
    print("2PL IRT CALIBRATION")
    print("=" * 70)

    # ========================================================
    # DATA
    # ========================================================

    if response_matrix is None:

        print(
            "Loading response data..."
        )

        responses = load_response_data()

        print(
            f"Responses: "
            f"{len(responses)}"
        )

        print(
            f"Learners: "
            f"{responses['learner_id'].nunique()}"
        )

        print(
            f"Items: "
            f"{responses['item_id'].nunique()}"
        )

        matrix = prepare_matrix(
            responses
        )

    else:

        print(
            "Using provided response matrix..."
        )

        if not isinstance(
            response_matrix,
            pd.DataFrame
        ):
            raise TypeError(
                "response_matrix must be "
                "a pandas DataFrame."
            )

        matrix = response_matrix.copy()

        if matrix.isna().any().any():
            raise ValueError(
                "Provided response matrix "
                "contains missing values."
            )

        if not matrix.isin(
            [0.0, 1.0]
        ).all().all():

            raise ValueError(
                "Provided response matrix "
                "must contain only 0 and 1."
            )

    # ========================================================
    # MATRIX INFO
    # ========================================================

    n_learners, n_items = (
        matrix.shape
    )

    print(
        f"Matrix shape: "
        f"{n_learners} x {n_items}"
    )

    # ========================================================
    # INITIAL PARAMETERS
    # ========================================================

    print(
        "Preparing initial parameters..."
    )

    initial_params = (
        prepare_initial_parameters(
            matrix
        )
    )

    # ========================================================
    # BOUNDS
    # ========================================================

    bounds = (
        [(-4.0, 4.0)] * n_learners
        +
        [(-4.0, 4.0)] * n_items
        +
        [
            (
                np.log(0.3),
                np.log(3.0)
            )
        ] * n_items
    )

    # ========================================================
    # INITIAL NLL
    # ========================================================

    initial_nll = (
        negative_log_likelihood(
            initial_params,
            matrix
        )
    )

    print(
        f"Initial negative log-likelihood: "
        f"{initial_nll:.4f}"
    )

    # ========================================================
    # OPTIMIZATION
    # ========================================================

    print(
        "Starting optimization..."
    )

    result = minimize(
        negative_log_likelihood,
        initial_params,
        args=(matrix,),
        jac=negative_log_likelihood_gradient,
        method="L-BFGS-B",
        bounds=bounds,
        options={
            "maxiter": max_iterations,
            "ftol": 1e-9,
            "gtol": 1e-5,
            "maxls": 50
        }
    )

    # ========================================================
    # RESULTS
    # ========================================================

    print(
        f"Optimization success: "
        f"{result.success}"
    )

    print(
        f"Optimizer message: "
        f"{result.message}"
    )

    print(
        f"Iterations: "
        f"{result.nit}"
    )

    print(
        f"Function evaluations: "
        f"{result.nfev}"
    )

    print(
        f"Gradient evaluations: "
        f"{result.njev}"
    )

    print(
        f"Final negative log-likelihood: "
        f"{result.fun:.4f}"
    )

    return result


# ============================================================
# EXTRACT PARAMETERS
# ============================================================

def extract_calibrated_parameters(
    result,
    matrix
):
    """
    Extract calibrated theta, b and a.
    """

    n_learners, n_items = (
        matrix.shape
    )

    params = result.x

    theta = params[
        :n_learners
    ]

    difficulty = params[
        n_learners:
        n_learners + n_items
    ]

    log_discrimination = params[
        n_learners + n_items:
    ]

    discrimination = np.exp(
        log_discrimination
    )

    return (
        theta,
        difficulty,
        discrimination
    )


# ============================================================
# SAVE OUTPUT
# ============================================================

def save_calibration_output(
    result,
    matrix
):
    """
    Save calibrated parameters to JSON.

    Reference parameters from the synthetic generator
    are included only for validation.
    """

    (
        theta,
        difficulty,
        discrimination
    ) = extract_calibrated_parameters(
        result,
        matrix
    )

    # --------------------------------------------------------
    # Reference item data
    # --------------------------------------------------------

    reference = None

    if os.path.exists(
        ITEM_REFERENCE_PATH
    ):
        reference = pd.read_csv(
            ITEM_REFERENCE_PATH
        )

    # --------------------------------------------------------
    # Item records
    # --------------------------------------------------------

    items = []

    item_ids = list(
        matrix.columns
    )

    for index, item_id in enumerate(
        item_ids
    ):

        record = {
            "item_id": str(
                item_id
            ),
            "calibrated_difficulty_b": float(
                difficulty[index]
            ),
            "calibrated_discrimination_a": float(
                discrimination[index]
            ),
            "data_source": "[SANDBOX DATA]"
        }

        if reference is not None:

            ref_rows = reference[
                reference["item_id"].astype(str)
                == str(item_id)
            ]

            if not ref_rows.empty:

                ref = ref_rows.iloc[0]

                if "difficulty_b" in ref:

                    record[
                        "reference_difficulty_b"
                    ] = float(
                        ref["difficulty_b"]
                    )

                if "discrimination_a" in ref:

                    record[
                        "reference_discrimination_a"
                    ] = float(
                        ref["discrimination_a"]
                    )

                if "competency" in ref:

                    record[
                        "competency"
                    ] = str(
                        ref["competency"]
                    )

        items.append(
            record
        )

    # --------------------------------------------------------
    # Learner records
    # --------------------------------------------------------

    learners = []

    learner_ids = list(
        matrix.index
    )

    for index, learner_id in enumerate(
        learner_ids
    ):

        learners.append(
            {
                "learner_id": str(
                    learner_id
                ),
                "theta": float(
                    theta[index]
                ),
                "data_source": "[SANDBOX DATA]"
            }
        )

    # --------------------------------------------------------
    # Output
    # --------------------------------------------------------

    output = {
        "model": "2PL IRT",
        "estimation_method": (
            "Joint Maximum Likelihood Estimation"
        ),
        "optimizer": "L-BFGS-B",
        "analytical_gradient": True,
        "converged": bool(
            result.success
        ),
        "optimizer_message": str(
            result.message
        ),
        "iterations": int(
            result.nit
        ),
        "function_evaluations": int(
            result.nfev
        ),
        "gradient_evaluations": int(
            result.njev
        ),
        "negative_log_likelihood": float(
            result.fun
        ),
        "n_learners": int(
            len(learners)
        ),
        "n_items": int(
            len(items)
        ),
        "data_source": "[SANDBOX DATA]",
        "items": items,
        "learners": learners
    }

    os.makedirs(
        os.path.dirname(
            OUTPUT_PATH
        ),
        exist_ok=True
    )

    with open(
        OUTPUT_PATH,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            output,
            file,
            indent=2,
            ensure_ascii=False
        )

    print(
        f"Saved calibration output: "
        f"{OUTPUT_PATH}"
    )

    return output


# ============================================================
# FULL CALIBRATION PIPELINE
# ============================================================

def run_full_calibration(
    max_iterations=200
):
    """
    Run complete calibration on all response data.
    """

    responses = load_response_data()

    matrix = prepare_matrix(
        responses
    )

    result = calibrate_irt(
        response_matrix=matrix,
        max_iterations=max_iterations
    )

    if not result.success:

        raise RuntimeError(
            "IRT calibration did not converge: "
            f"{result.message}"
        )

    output = save_calibration_output(
        result,
        matrix
    )

    return output


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    run_full_calibration(
        max_iterations=200
    )