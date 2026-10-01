import pandas as pd

df = pd.read_csv("dataset/user_data/stem_education_research_data.csv")

print("--- ANÁLISIS DE IMPACTO DE IA EN EDUCACIÓN STEM ---")
# Comparación de notas y ansiedad final por condición experimental
grouped = df.groupby("condition")[["final_exam_score", "course_grade", "final_stem_anxiety", "final_growth_beliefs", "study_hours_per_week"]].mean()
print(grouped)

print("\n--- CORRELACIÓN CON CALIFICACIÓN FINAL ---")
numeric_df = df.select_dtypes(include=["number"])
corrs = numeric_df.corr()["final_exam_score"].sort_values(ascending=False)
print("Top 5 correlaciones positivas con nota de examen final:")
print(corrs.head(6))
print("\nTop 3 correlaciones negativas (factores que reducen el rendimiento):")
print(corrs.tail(4))
