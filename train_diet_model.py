import pandas as pd
import joblib
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
from sklearn.preprocessing import LabelEncoder
import os

# Load dataset
dataset_path = os.path.join(os.getcwd(), "diet.csv")  # Ensure the file is in backend/
df = pd.read_csv(dataset_path)

# Ensure required columns exist
required_columns = ["Height", "Weight", "FCVC", "NCP", "FAF", "CH2O", "NObeyesdad"]
for col in required_columns:
    if col not in df.columns:
        raise ValueError(f"❌ Missing required column: {col}")

# Calculate BMI
df["BMI"] = df["Weight"] / (df["Height"] ** 2)

# Encode categorical target variable
encoder = LabelEncoder()
df["NObeyesdad"] = encoder.fit_transform(df["NObeyesdad"])  # Encoding obesity category

# Select features for clustering
X = df[["BMI", "FCVC", "NCP", "FAF", "CH2O"]]

# Find optimal number of clusters using Elbow Method
wcss = []
for i in range(1, 10):
    kmeans = KMeans(n_clusters=i, random_state=42, n_init=10)
    kmeans.fit(X)
    wcss.append(kmeans.inertia_)

# Plot Elbow Curve
plt.plot(range(1, 10), wcss, marker="o")
plt.xlabel("Number of Clusters")
plt.ylabel("WCSS (Within-Cluster Sum of Squares)")
plt.title("Elbow Method for Optimal K")
plt.show()

# Choose optimal K (e.g., 3 based on elbow point)
optimal_k = 3
kmeans = KMeans(n_clusters=optimal_k, random_state=42, n_init=10)
df["Cluster"] = kmeans.fit_predict(X)

# Save trained model
model_path = os.path.join(os.getcwd(), "diet_kmeans.pkl")
joblib.dump(kmeans, model_path)

print(f"✅ Model trained and saved at: {model_path}")
