# Experiment 001: Bayesian Knowledge Tracing (BKT) Baseline

## Objective
Establish a baseline for candidate knowledge tracing using Bayesian Knowledge Tracing (BKT). This baseline will be compared against subsequent Deep Knowledge Tracing (DKT) and Graph Neural Network (GNN) models in terms of predictive accuracy (AUC) and adaptability.

## Methodology

### Mathematical Model
BKT models a candidate's knowledge state as a Hidden Markov Model (HMM) with two latent states (Mastered, Not Mastered) and two observable states (Correct, Incorrect).

Parameters:
- **$P(L_0)$**: Probability of prior mastery before the interview begins.
- **$P(T)$**: Probability of transitioning to mastery after an opportunity (answering a question).
- **$P(G)$**: Probability of guessing correctly without mastery.
- **$P(S)$**: Probability of slipping (answering incorrectly) despite mastery.

**Update Rule (Posterior):**
If the answer is correct:
$$ P(L_n | obs) = \frac{(1 - P(S)) \cdot P(L_{n-1})}{(1 - P(S)) \cdot P(L_{n-1}) + P(G) \cdot (1 - P(L_{n-1}))} $$

If the answer is incorrect:
$$ P(L_n | obs) = \frac{P(S) \cdot P(L_{n-1})}{P(S) \cdot P(L_{n-1}) + (1 - P(G)) \cdot (1 - P(L_{n-1}))} $$

**Transition Rule:**
$$ P(L_{n+1}) = P(L_n | obs) + (1 - P(L_n | obs)) \cdot P(T) $$

**Prediction Rule:**
$$ P(\text{Correct}_{n+1}) = P(L_{n+1}) \cdot (1 - P(S)) + (1 - P(L_{n+1})) \cdot P(G) $$

### Default Parameters
For the baseline, we assign uniform conservative parameters across all skills:
- $P(L_0) = 0.1$
- $P(T) = 0.1$
- $P(G) = 0.2$
- $P(S) = 0.1$

## Future Evaluation
The predictive performance of this model will be evaluated by its ability to predict $P(\text{Correct}_{n+1})$. We will log these predictions and calculate the ROC-AUC once we collect empirical interview data or simulate candidate interactions.
