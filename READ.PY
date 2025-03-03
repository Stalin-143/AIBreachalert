import os
import pandas as pd

DATA_DIR = "data"  # Root directory containing subdirectories with text files

def load_data_from_txt():
    """Recursively reads all text files from the data directory and creates a DataFrame."""
    data = []

    if not os.path.exists(DATA_DIR):
        print(f"❌ Error: Data directory '{DATA_DIR}' does not exist.")
        return pd.DataFrame(columns=["email", "other_data"])  # Return an empty DataFrame

    # Walk through all directories and subdirectories
    for root, _, files in os.walk(DATA_DIR):
        for filename in files:
            file_path = os.path.join(root, filename)

            if filename.endswith(".txt") and os.path.isfile(file_path):
                with open(file_path, "r", encoding="utf-8", errors="ignore") as file:
                    for line in file:
                        parts = line.strip().split(",")  # Adjust if the data format is different
                        if len(parts) >= 2:
                            email = parts[0].strip()
                            other_data = ",".join(parts[1:]).strip()
                            data.append({"email": email, "other_data": other_data})

    return pd.DataFrame(data)

# Load data
df = load_data_from_txt()

# Check if data is loaded
if df.empty:
    print("❌ No data found in the text files.")
else:
    print("✅ Data successfully loaded:", df.head())

    # ✅ Save the DataFrame to a CSV file
    df.to_csv("breach_data.csv", index=False, encoding="utf-8")
    print("✅ Data successfully saved as breach_data.csv")
