import streamlit as st
import pandas as pd
import numpy as np
import os

# Set page title and icon
st.set_page_config(
    page_title="Home",
    page_icon="🏠",
)

# Main content
st.title("Welcome to Clothalytics!")
st.markdown(
    """
    Clothalytics is a sales prediction system developed for analyzing cloth sales across different stores using the **SARIMA** model.
    ### Instructions
    1. Upload the cloth sales dataset below.
        - Requirements: CSV file format, Column Headers [Product Name (string), Quantity (int), Sell Price (int), 
        Date Sold (datetime: dd-mm-yyyy), Product Category (string), Store Name (string)]
    2.  👈 Select Analytics or Predictions from the sidebar
        - To gain insights into the dataset, click on the "Analytics" option. 
        This will provide you with a comprehensive overview and analysis of the sales data, 
        including key statistics, trends, and visualizations.
        - To generate sales predictions, click on "Predictions" option.
        Clothalytics will employ the SARIMA (Seasonal Autoregressive Integrated Moving Average) model 
        to generate sales predictions based on the uploaded dataset.
"""
)

# Prompt to upload dataset
dataset = None
file = st.file_uploader("Upload Sales Dataset", type="csv")
if file:
    dataset = pd.read_csv(file, index_col=False)
    st.success("Dataset uploaded successfully!")
    st.write("**Dataset Preview:**")
    st.dataframe(dataset, width=700)

    dataset.to_csv("uploaded_dataset.csv", index=None)  # Save dataset to local machine
elif not os.path.exists("uploaded_dataset.csv") and not file:
    st.stop()

# Load the previously uploaded dataset (if exists)
if os.path.exists("uploaded_dataset.csv") and not file:
    dataset = pd.read_csv("uploaded_dataset.csv", index_col=None)
    st.write("**Uploaded Dataset:**")
    st.dataframe(dataset, width=700)

st.divider()

# Create containers to group codes together
pre_con = st.container()

with pre_con:
    if dataset is not None:
        # Drop the unnamed columns
        unnamed_columns = [col for col in dataset.columns if 'Unnamed' in col]
        dataset.drop(unnamed_columns, axis=1, inplace=True)

        # Replace all occurrences of "#REF!" with NaN (because of auto-fill category in Google Sheet)
        dataset.replace("#REF!", np.nan, inplace=True)

        # Drop all rows that contain NaN values (All rows that have a single NaN value will be dropped)
        dataset.dropna(inplace=True)

        cleaned_dataset = dataset.reset_index(drop=True)

        # Convert the "Date Sold" column to datetime format, handling various formats
        cleaned_dataset["Date Sold"] = pd.to_datetime(cleaned_dataset["Date Sold"], errors='coerce')

        # Check if there are any rows where date parsing failed
        invalid_dates = cleaned_dataset[cleaned_dataset["Date Sold"].isnull()]

        if not invalid_dates.empty:
            st.warning(f"Found {len(invalid_dates)} rows with invalid dates. These rows are dropped.")
            cleaned_dataset = cleaned_dataset.dropna(subset=["Date Sold"])

        # Create a new DataFrame with the dates as the index
        indexed_dataset = cleaned_dataset.set_index("Date Sold")

        # Show Preprocessed Dataset
        st.subheader("Data Pre-processing")
        st.markdown(
            """
            1. **Data Cleaning**: Rows and columns with empty cells are removed from the dataset.
            2. **Set DateTime Index**: Replace the index with a datetime index, enabling analysis and tracking of trends over time.
        """
        )
        st.write("**Preprocessed Dataset**")
        st.dataframe(indexed_dataset, width=700)

        indexed_dataset.to_csv("preprocessed_dataset.csv", date_format="%d-%m-%Y")  # Save preprocessed dataset to local machine
    else:
        st.warning("Please upload a dataset to proceed with preprocessing.")

# Additional container for analysis and optimization
analysis_con = st.container()

with analysis_con:
    st.subheader("Store Analysis and Inventory Optimization")
    
    if dataset is not None:
        # Group by store and category to analyze which store is best for selling each category of clothes
        sales_by_store_category = indexed_dataset.groupby(["Store Name", "Product Category"]).agg({
            "Quantity": "sum",
            "Sell Price": "mean"
        }).reset_index()

        st.markdown(
            """
            ### Best Store Analysis
            Below table shows the total quantity sold and average sell price for each product category in each store.
            """
        )
        st.dataframe(sales_by_store_category, width=700)

        # Determine the best store for each category
        best_store_for_category = sales_by_store_category.loc[sales_by_store_category.groupby("Product Category")["Quantity"].idxmax()]
        st.markdown(
            """
            ### Best Store for Each Category
            Below table shows the best store for each product category based on the total quantity sold.
            """
        )
        st.dataframe(best_store_for_category, width=700)

        # Optimizing inventory based on demand analysis
        st.markdown(
            """
            ### Inventory Optimization
            The following table shows the recommended inventory levels for each store and product category based on demand analysis.
            """
        )
        
        # Calculate recommended inventory (e.g., keeping stock level to meet 95th percentile of demand)
        recommended_inventory = indexed_dataset.groupby(["Store Name", "Product Category"]).agg({
            "Quantity": lambda x: np.percentile(x, 95)
        }).reset_index().rename(columns={"Quantity": "Recommended Inventory"})
        
        st.dataframe(recommended_inventory, width=700)

        # Save analysis results to CSV
        best_store_for_category.to_csv("best_store_for_category.csv", index=False)
        recommended_inventory.to_csv("recommended_inventory.csv", index=False)
    else:
        st.warning("Please upload a dataset to proceed with analysis and optimization.")
