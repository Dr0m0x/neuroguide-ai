## NeuroGuide AI – Baseline Alzheimer's Risk Prediction Model
## Overview

This repository contains the baseline machine learning component developed for NeuroGuide AI, a graduate capstone project for the Master of Science in Artificial Intelligence program at the University of the Cumberlands.

The purpose of this model is to estimate educational Alzheimer's disease risk levels using established dementia risk factors identified by the 2024 Lancet Commission. The model serves as one component of a larger Explainable AI platform that combines machine learning, Retrieval-Augmented Generation (RAG), and a multi-agent architecture to provide evidence-based cognitive health education.

This model is intended for educational purposes only and is not designed to diagnose Alzheimer's disease.

## Project Objectives
Develop an interpretable baseline risk prediction model
Utilize evidence-based Alzheimer's risk factors
Support explainable AI through SHAP feature interpretation
Integrate with a multi-agent RAG educational platform
Provide personalized educational risk assessments
Dataset

## Alzheimer's Prediction Dataset (Global)

Source: Kaggle
Author: Ankush Panday (2025)
Records: 74,283
Features: 25

## Dataset:
https://www.kaggle.com/datasets/ankushpanday1/alzheimers-prediction-dataset-global

## Selected Features

The baseline model uses twelve evidence-based predictors aligned with the 2024 Lancet Commission recommendations.

Age
Years of Education
APOE-ε4 Status
Hypertension
BMI (Obesity)
Smoking Status
Depression
Physical Activity
Diabetes
Social Isolation
Alcohol Consumption
Hypercholesterolemia
Model

## Algorithm

Random Forest Classifier
Parameters
200 Decision Trees
Maximum Depth: 8
Balanced Class Weights
Train/Test Split: 80/20
Five-Fold Cross Validation
Risk Categories

## Instead of predicting a clinical diagnosis, NeuroGuide AI predicts educational risk levels:

Low Risk
Moderate Risk
High Risk

These categories are derived from Alzheimer's diagnosis labels and cognitive assessment scores to improve interpretability for educational use.

Baseline Performance
Metric	Score
Accuracy	0.516
Weighted Precision	0.544
Weighted Recall	0.516
Weighted F1	0.519
ROC-AUC	0.718
5-Fold CV F1	0.525 ± 0.006
Explainability

The model incorporates SHAP (SHapley Additive exPlanations) to improve transparency by identifying the most influential features contributing to each prediction.

Future Improvements
Hyperparameter optimization
Feature engineering
Probability calibration
Gradient Boosting comparison
XGBoost and LightGBM benchmarking
Improved Moderate-risk classification
Additional lifestyle and environmental predictors
Integration into the NeuroGuide AI multi-agent system
Repository Structure
├── week3_risk_model.ipynb
├── Week3_Baseline_Model_Report.pdf
├── README.md
└── requirements.txt
Technologies
Python
Pandas
NumPy
Scikit-learn
SHAP
Matplotlib
Jupyter Notebook
Capstone Project

This repository represents the baseline machine learning component of the larger NeuroGuide AI platform.

## The complete platform combines:

Random Forest Risk Prediction
Retrieval-Augmented Generation (RAG)
Multi-Agent AI Architecture
Evidence-Based Medical Knowledge
Explainable Artificial Intelligence (XAI)
Personalized Cognitive Health Education
Disclaimer

## NeuroGuide AI is intended solely for educational and research purposes. It is not a medical device and should not be used to diagnose, treat, or replace professional medical advice.

## References

Breiman, L. (2001). Random forests. Machine Learning, 45(1), 5–32.

Livingston, G., et al. (2024). Dementia prevention, intervention, and care: 2024 report of the Lancet standing Commission. The Lancet.

Lundberg, S. M., & Lee, S.-I. (2017). A Unified Approach to Interpreting Model Predictions.

Panday, A. (2025). Alzheimer's Prediction Dataset (Global). Kaggle.

## Author

Moriah Holland

Master of Science in Artificial Intelligence
University of the Cumberlands

## Capstone Project (MSAI 699)
