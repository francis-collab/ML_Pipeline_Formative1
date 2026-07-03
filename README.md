# Group6 Formative1 MLPipeline

# Task1 - Stock Market Price Movement Prediction

## Project Overview
Time-series Preprocessing, Exploratory Analysis & Modeling for a multivariate stock market dataset. The goal is to predict daily price movement (Up/Down/Stable) using technical indicators and temporal features.

**Contribution (Task 1)**: Full EDA, analytical questions, feature engineering, model experiments (3 classical ML models), visualizations, and best model selection.

## Repo Structure
```bash
ML_Pipeline_Formative1/
├── data/
│   └── stock_dataset.csv                           # Original dataset
├── notebooks/
│   └── Group6_Formative1_MLPipeline_Task1.ipynb    # Task 1 notebook
├── src/
│   ├── database_setup.py                           # (For Task 2)
│   ├── api.py                                      # (For Task 3)
│   ├── predict.py                                  # (For Task 4)
│   └── utils.py                                    # Reusable functions
├── models/
│   └── best_model.pkl                              # Best Tuned XGBoost model
├── reports/
│   ├── experiments.csv                             # Experiment table
│   
├── database/                                       # (For Task 2)
│   ├── erd_diagram.png
│   └── queries_results.md
├── README.md
└── .gitignore
```

## How to Run Task 1 Notebook
1. Upload `stock_dataset.csv` to Colab `data/` folder.
2. Open `Group6_Formative1_MLPipeline_Task1.ipynb`.
3. Run cells sequentially (Imports → EDA → Feature Engineering → Experiments → Testing).

## Key Results (Task 1)
- **Best Model**: Tuned XGBoost (Accuracy ~0.845, F1 ~0.820 on cross-validation)
- **Test Set Performance**: Accuracy 0.858, F1 0.818 on unseen data
- Strong performance on Up/Down movements; Stable class is harder due to market noise (expected).

## Next Tasks (For Colleagues)
- **Task 2**: Databases (SQL + MongoDB) using the same dataset
- **Task 3**: FastAPI CRUD endpoints + time-series queries
- **Task 4**: Prediction script integrating API + model

---
