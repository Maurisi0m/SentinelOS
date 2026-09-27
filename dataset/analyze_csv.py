import pandas as pd

csv_path = "dataset/user_data/stem_education_research_data.csv"
df = pd.read_csv(csv_path)

print("=== ANÁLISIS DE DATASET EXTRAÍDO ===")
print("Total de filas (muestras):", len(df))
print("Total de columnas:", len(df.columns))
print("\nDistribución por tipo de curso:")
print(df["course_type"].value_counts())
print("\nCondición experimental (Uso de IA / Mindset):")
print(df["condition"].value_counts())
print("\nEstadísticas clave:")
print(df[["final_exam_score", "course_grade", "perceived_ai_usefulness", "study_hours_per_week"]].describe())
