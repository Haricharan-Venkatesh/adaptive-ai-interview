from pydantic import BaseModel, Field


class BKTParams(BaseModel):
    p_l0: float = Field(default=0.1, description="Probability of initial mastery")
    p_t: float = Field(default=0.1, description="Probability of transitioning to mastery after an opportunity")
    p_g: float = Field(default=0.2, description="Probability of a correct guess despite non-mastery")
    p_s: float = Field(default=0.1, description="Probability of a mistake (slip) despite mastery")


class BKTModel:
    def __init__(self, params: BKTParams):
        self.params = params

    def update(self, p_l: float, is_correct: bool) -> float:
        """
        Calculates the posterior probability of mastery after an observation.
        P(L_n) = P(L_{n-1} | obs) + (1 - P(L_{n-1} | obs)) * P(T)
        """
        if is_correct:
            p_obs_given_l = 1.0 - self.params.p_s
            p_obs_given_not_l = self.params.p_g
        else:
            p_obs_given_l = self.params.p_s
            p_obs_given_not_l = 1.0 - self.params.p_g

        # Marginal probability of the observation
        p_obs = (p_obs_given_l * p_l) + (p_obs_given_not_l * (1.0 - p_l))
        
        # Avoid division by zero (edge case if p_G = 0 and p_S = 0)
        p_l_given_obs = 0.0 if p_obs == 0.0 else (p_obs_given_l * p_l) / p_obs

        # Transition equation
        p_l_next = p_l_given_obs + (1.0 - p_l_given_obs) * self.params.p_t
        return p_l_next

    def predict(self, p_l: float) -> float:
        """
        Predicts the probability of a correct response on the next question.
        """
        return p_l * (1.0 - self.params.p_s) + (1.0 - p_l) * self.params.p_g


class BKTKnowledgeTracer:
    def __init__(self, default_params: BKTParams | None = None, skill_params: dict[str, BKTParams] | None = None):
        self.default_params = default_params or BKTParams()
        self.skill_params = skill_params or {}
        
    def get_params(self, skill_id: str) -> BKTParams:
        return self.skill_params.get(skill_id, self.default_params)
        
    def get_model(self, skill_id: str) -> BKTModel:
        return BKTModel(self.get_params(skill_id))
        
    def update(self, skill_id: str, current_mastery: float, is_correct: bool) -> float:
        model = self.get_model(skill_id)
        return model.update(current_mastery, is_correct)
        
    def predict(self, skill_id: str, current_mastery: float) -> float:
        model = self.get_model(skill_id)
        return model.predict(current_mastery)
