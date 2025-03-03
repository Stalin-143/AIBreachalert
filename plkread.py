import pickle
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer

# Sample training data (Replace with actual breach-related email data)
emails = ["user1@example.com", "hacked@mail.com", "safe@email.com", "compromised@site.com"]
labels = [1, 1, 0, 1]  # 1 = Breached, 0 = Safe

# Convert emails to vectorized form
vectorizer = TfidfVectorizer()
X = vectorizer.fit_transform(emails)

# Train a Random Forest model
rf_model = RandomForestClassifier(n_estimators=100, random_state=42)
rf_model.fit(X, labels)

# Save the trained model and vectorizer
with open("random_forest.pkl", "wb") as f:
    pickle.dump(rf_model, f)
with open("vectorizer.pkl", "wb") as f:
    pickle.dump(vectorizer, f)

print("Model training complete. Files saved as 'random_forest.pkl' and 'vectorizer.pkl'.")
