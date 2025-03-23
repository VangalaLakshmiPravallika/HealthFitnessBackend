import os
import pandas as pd
import joblib
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
from sklearn.preprocessing import LabelEncoder

# Set max CPU count to avoid joblib warnings
os.environ["LOKY_MAX_CPU_COUNT"] = "4"  # Set this to your actual core count

# Load dataset
dataset_path = os.path.join(os.getcwd(), "diet.csv")  # Ensure this file exists
if not os.path.exists(dataset_path):
    raise FileNotFoundError(f"❌ Dataset not found at {dataset_path}")

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
for i in range(1, 11):  # Try cluster sizes from 1 to 10
    kmeans = KMeans(n_clusters=i, random_state=42, n_init=10)
    kmeans.fit(X)
    wcss.append(kmeans.inertia_)

# Plot Elbow Curve
plt.figure(figsize=(8, 5))
plt.plot(range(1, 11), wcss, marker="o", linestyle="-", color="b")
plt.xlabel("Number of Clusters (K)")
plt.ylabel("WCSS (Within-Cluster Sum of Squares)")
plt.title("Elbow Method for Optimal K")
plt.grid(True)
plt.show()

# ✅ Choose the best 'K' from the elbow graph (Manually select based on graph)
optimal_k = 3  # Change this value based on the graph

# Train final K-Means model
kmeans = KMeans(n_clusters=optimal_k, random_state=42, n_init=10)
df["Cluster"] = kmeans.fit_predict(X)

# Save trained model
model_path = os.path.join(os.getcwd(), "diet_kmeans.pkl")
joblib.dump(kmeans, model_path)

print(f"✅ Model trained successfully with {optimal_k} clusters and saved at: {model_path}")
