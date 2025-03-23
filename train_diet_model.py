import os
import pandas as pd
import joblib
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
from sklearn.preprocessing import LabelEncoder

# **🔹 Restrict CPU usage to prevent Joblib parallelization issues**
os.environ["LOKY_MAX_CPU_COUNT"] = "1"  

# **🔹 Load dataset efficiently**
dataset_path = os.path.join(os.getcwd(), "diet.csv")
if not os.path.exists(dataset_path):
    raise FileNotFoundError(f"❌ Dataset not found at {dataset_path}")

# **🔹 Load only necessary columns**
df = pd.read_csv(dataset_path, usecols=["Height", "Weight", "FCVC", "NCP", "FAF", "CH2O", "NObeyesdad"])

# **🔹 Compute BMI directly**
df["BMI"] = df["Weight"] / (df["Height"] ** 2)

# **🔹 Encode categorical labels (one-time transformation)**
encoder = LabelEncoder()
df["NObeyesdad"] = encoder.fit_transform(df["NObeyesdad"])

# **🔹 Select only necessary features**
X = df[["BMI", "FCVC", "NCP", "FAF", "CH2O"]].values  # Use `.values` to speed up NumPy processing

# **🔹 Reduce K range (Speeds up training)**
wcss = []
for i in range(2, 4):  # ⚡ Testing only K=2 & K=3 for best speed
    kmeans = KMeans(n_clusters=i, random_state=42, n_init=3, max_iter=20)  # ⚡ Lowered `n_init` & `max_iter`
    kmeans.fit(X)
    wcss.append(kmeans.inertia_)

# **🔹 Plot Elbow Curve**
plt.figure(figsize=(8, 5))
plt.plot(range(2, 4), wcss, marker="o", linestyle="-", color="b")
plt.xlabel("Number of Clusters (K)")
plt.ylabel("WCSS (Within-Cluster Sum of Squares)")
plt.title("Elbow Method for Optimal K")
plt.grid(True)
plt.show()

# **🔹 Select Best `K` Based on Elbow Graph**
optimal_k = 2  # Manually adjust this based on the graph

# **🔹 Train Final Model (Highly Optimized)**
kmeans = KMeans(n_clusters=optimal_k, random_state=42, n_init=3, max_iter=20)  # ⚡ Minimal settings for speed
df["Cluster"] = kmeans.fit_predict(X)

# **🔹 Save Trained Model**
model_path = os.path.join(os.getcwd(), "diet_kmeans.pkl")
joblib.dump(kmeans, model_path)

print(f"✅ Model trained in **FAST MODE** with {optimal_k} clusters and saved at: {model_path}")
