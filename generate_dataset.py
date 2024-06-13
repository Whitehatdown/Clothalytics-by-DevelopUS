import pandas as pd
import numpy as np
import random
from faker import Faker

# Initialize Faker
fake = Faker()

# Set random seed for reproducibility
random.seed(42)
np.random.seed(42)

# Generate synthetic raw dataset
def generate_raw_cloth_sales_dataset(n_records=1000):
    # Define product names and categories
    product_names = ["T-Shirt", "Jeans", "Jacket", "Dress", "Skirt", "Blouse", "Sweater", "Shorts", "Pants", "Coat"]
    product_categories = ["Men", "Women", "Children", "Unisex"]
    
    # Define store names
    store_names = ["Store A", "Store B", "Store C", "Store D", "Store E"]
    
    # Generate records
    data = {
        "Date Sold": [fake.date_between(start_date='-1y', end_date='today') for _ in range(n_records)],
        "Product Name": [random.choice(product_names) for _ in range(n_records)],
        "Product Category": [random.choice(product_categories) for _ in range(n_records)],
        "Quantity": np.random.randint(1, 20, size=n_records),
        "Sell Price": [round(random.uniform(5.0, 100.0), 2) for _ in range(n_records)],
        "Store Name": [random.choice(store_names) for _ in range(n_records)]
    }
    
    # Calculate Revenue based on Quantity and Sell Price
    data["Revenue"] = [data["Quantity"][i] * data["Sell Price"][i] for i in range(n_records)]
    
    # Create DataFrame
    df = pd.DataFrame(data)
    
    return df

# Generate the raw dataset
raw_cloth_sales_dataset = generate_raw_cloth_sales_dataset()

# Save the raw dataset to a CSV file
raw_cloth_sales_dataset.to_csv("raw_cloth_sales_dataset.csv", index=False)

print("Synthetic raw cloth sales dataset generated and saved as 'raw_cloth_sales_dataset.csv'")
