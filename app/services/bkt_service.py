# app/services/bkt_service.py
import math

def update_pknow(prior: float, is_correct: bool,
                 slip: float = 0.1, guess: float = 0.2, transit: float = 0.3) -> float:
    """
    Bayesian Knowledge Tracing update with adaptive learning rate.
    Used for both user- and adventure-level mastery.
    """
    # Clamp to [0,1]
    prior = max(0.0, min(1.0, prior))

    if is_correct:
        num = prior * (1 - slip)
        den = num + (1 - prior) * guess
    else:
        num = prior * slip
        den = num + (1 - prior) * (1 - guess)

    posterior = num / (den + 1e-9)

    # Adaptive transition
    if is_correct:
        scaled_T = transit * (1 - prior)
        next_prior = posterior + (1 - posterior) * scaled_T
    else:
        unlearn_rate = 0.05 + (0.15 * prior)
        next_prior = posterior * (1 - unlearn_rate)

    return max(0.0, min(1.0, next_prior))