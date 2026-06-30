"""
Neural Network Risk Assessment Module
======================================
Trains a Random Forest classifier on synthetic Alzheimer's educational
risk data based on the 14 modifiable risk factors from the Lancet
Commission on Dementia Prevention (2024).

Uses SHAP TreeExplainer for feature attribution and XAI.
"""

from __future__ import annotations
import numpy as np
import shap
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split

FEATURES: list[dict] = [
    {"key": "age",              "label": "Age",                        "type": "numeric", "unit": "years"},
    {"key": "education_years",  "label": "Years of Education",         "type": "numeric", "unit": "years"},
    {"key": "hypertension",     "label": "Hypertension",               "type": "binary"},
    {"key": "obesity",          "label": "Obesity (BMI ≥ 30)",         "type": "binary"},
    {"key": "smoking",          "label": "Current / Former Smoker",    "type": "binary"},
    {"key": "depression",       "label": "History of Depression",      "type": "binary"},
    {"key": "physical_inactivity", "label": "Physically Inactive",    "type": "binary"},
    {"key": "diabetes",         "label": "Type 2 Diabetes",            "type": "binary"},
    {"key": "social_isolation", "label": "Social Isolation",           "type": "binary"},
    {"key": "hearing_loss",     "label": "Untreated Hearing Loss",     "type": "binary"},
    {"key": "excess_alcohol",   "label": "Excess Alcohol Consumption", "type": "binary"},
    {"key": "tbi_history",      "label": "History of TBI",             "type": "binary"},
    {"key": "high_cholesterol", "label": "High LDL Cholesterol",       "type": "binary"},
    {"key": "vision_loss",      "label": "Untreated Vision Loss",      "type": "binary"},
]

RISK_LABELS  = ["Low", "Moderate", "High"]
RISK_COLORS  = {"Low": "#22c55e", "Moderate": "#f59e0b", "High": "#ef4444"}
FEATURE_KEYS = [f["key"] for f in FEATURES]
FEATURE_LBLS = [f["label"] for f in FEATURES]


def _generate_synthetic_data(n: int = 2000, seed: int = 42):
    """
    Synthetic training data whose risk-score weights approximate the
    population-level effect sizes reported by the Lancet Commission 2024.
    """
    rng = np.random.default_rng(seed)

    age  = rng.integers(45, 90, n).astype(float)
    edu  = rng.integers(8, 22,  n).astype(float)

    hypertension = rng.binomial(1, 0.45, n)
    obesity      = rng.binomial(1, 0.35, n)
    smoking      = rng.binomial(1, 0.25, n)
    depression   = rng.binomial(1, 0.20, n)
    inactivity   = rng.binomial(1, 0.40, n)
    diabetes     = rng.binomial(1, 0.15, n)
    isolation    = rng.binomial(1, 0.25, n)
    hearing      = rng.binomial(1, 0.30, n)
    alcohol      = rng.binomial(1, 0.15, n)
    tbi          = rng.binomial(1, 0.10, n)
    cholesterol  = rng.binomial(1, 0.35, n)
    vision       = rng.binomial(1, 0.20, n)

    score = (
          0.07 * (age - 60)
        - 0.12 * (edu - 12)
        + 0.65 * hypertension
        + 0.45 * obesity
        + 0.55 * smoking
        + 0.72 * depression
        + 0.50 * inactivity
        + 0.65 * diabetes
        + 0.55 * isolation
        + 0.45 * hearing
        + 0.40 * alcohol
        + 0.35 * tbi
        + 0.40 * cholesterol
        + 0.35 * vision
        + rng.normal(0, 0.8, n)
    )

    lo = np.percentile(score, 40)
    hi = np.percentile(score, 75)
    labels = np.where(score < lo, 0, np.where(score < hi, 1, 2))

    X = np.column_stack([
        age, edu, hypertension, obesity, smoking, depression,
        inactivity, diabetes, isolation, hearing, alcohol, tbi,
        cholesterol, vision,
    ])
    return X, labels


class RiskAssessmentModel:
    """
    Random Forest classifier with SHAP TreeExplainer for XAI.
    Predicts educational risk category (Low / Moderate / High) from
    14 modifiable lifestyle and demographic features.
    """

    def __init__(self) -> None:
        self.model: RandomForestClassifier | None = None
        self.explainer: shap.TreeExplainer | None = None
        self._train()

    def _train(self) -> None:
        X, y = _generate_synthetic_data()
        X_tr, _, y_tr, _ = train_test_split(X, y, test_size=0.2, random_state=42)

        self.model = RandomForestClassifier(
            n_estimators=200,
            max_depth=8,
            min_samples_leaf=10,
            random_state=42,
            class_weight="balanced",
        )
        self.model.fit(X_tr, y_tr)
        self.explainer = shap.TreeExplainer(self.model)

    def predict(self, features: dict) -> dict:
        X = np.array([[
            float(features.get("age", 65)),
            float(features.get("education_years", 12)),
            int(bool(features.get("hypertension",        False))),
            int(bool(features.get("obesity",             False))),
            int(bool(features.get("smoking",             False))),
            int(bool(features.get("depression",          False))),
            int(bool(features.get("physical_inactivity", False))),
            int(bool(features.get("diabetes",            False))),
            int(bool(features.get("social_isolation",    False))),
            int(bool(features.get("hearing_loss",        False))),
            int(bool(features.get("excess_alcohol",      False))),
            int(bool(features.get("tbi_history",         False))),
            int(bool(features.get("high_cholesterol",    False))),
            int(bool(features.get("vision_loss",         False))),
        ]])

        proba      = self.model.predict_proba(X)[0]  # type: ignore[union-attr]
        pred_class = int(np.argmax(proba))
        risk_label = RISK_LABELS[pred_class]

        shap_values = self.explainer.shap_values(X)  # type: ignore[union-attr]
        # SHAP >= 0.45 returns ndarray (n_samples, n_features, n_classes);
        # older SHAP returns a list of (n_samples, n_features) per class.
        if isinstance(shap_values, list):
            class_shap = shap_values[pred_class][0]
        else:
            class_shap = shap_values[0, :, pred_class]

        attributions = sorted(
            [
                {
                    "feature":    FEATURE_LBLS[i],
                    "key":        FEATURE_KEYS[i],
                    "value":      float(X[0, i]),
                    "shap_value": float(class_shap[i]),
                    "impact":     "risk" if class_shap[i] > 0 else "protective",
                }
                for i in range(len(FEATURE_KEYS))
            ],
            key=lambda x: abs(x["shap_value"]),
            reverse=True,
        )

        return {
            "risk_category": risk_label,
            "risk_color":    RISK_COLORS[risk_label],
            "probabilities": {
                "Low":      round(float(proba[0]), 3),
                "Moderate": round(float(proba[1]), 3),
                "High":     round(float(proba[2]), 3),
            },
            "top_attributions": attributions[:8],
            "disclaimer": (
                "This is an educational risk-estimation tool, not a clinical diagnostic instrument. "
                "Categories are based on population-level modifiable risk factors identified by the "
                "Lancet Commission on Dementia Prevention (2024). Consult a healthcare professional "
                "for personalised medical advice."
            ),
        }


_risk_model: RiskAssessmentModel | None = None


def get_risk_model() -> RiskAssessmentModel:
    global _risk_model
    if _risk_model is None:
        _risk_model = RiskAssessmentModel()
    return _risk_model
