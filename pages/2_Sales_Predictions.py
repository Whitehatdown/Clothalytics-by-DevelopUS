import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
import statsmodels.api as sm
from sklearn.model_selection import train_test_split
from statsmodels.tsa.stattools import adfuller
from statsmodels.graphics.tsaplots import plot_acf, plot_pacf
from sklearn.metrics import mean_absolute_error, mean_squared_error
from pmdarima import auto_arima

# Set page title and icon
st.set_page_config(
    page_title="Sales Predictions",
    page_icon="💰",
)

# Main content
st.title("Sales Predictions 💰")
st.markdown(
    """
    Pharmalitics uses the SARIMA model to generate sales predictions based on your uploaded dataset. 
    This advanced technique captures seasonal and trend patterns in the data to forecast future trends.

    To ensure efficiency and practicality, our app focuses on predicting sales for the top 30 most sold products 
    in FirstMed Pharmacy and leverages the power of Auto ARIMA for predicting sales. By automating the model 
    fitting process, we eliminate the need for manual selection and comparison of different models. 
    
    This streamlined 
    approach enables us to provide forecasts for the key items driving the pharmacy's revenue, This automated process 
    saves time and resources, allowing us to focus on delivering reliable sales predictions while leaving room for 
    future expansion and inclusion of additional products.
"""
)

st.sidebar.header("Sales Predictions")

# Load the preprocessed dataset and stop if it doesn't exist
preprocessed_dataset_path = "preprocessed_dataset.csv"
if not os.path.exists(preprocessed_dataset_path):
    st.warning("Dataset not uploaded. Please upload a dataset first in the Home page.")
    st.stop()

preprocessed_dataset = pd.read_csv(preprocessed_dataset_path, parse_dates=["Date Sold"], index_col="Date Sold")

# Create containers to group codes together
top_30_products_adf_exp = st.expander("See ADF Test Results")
top_30_products_pred_con = st.container()

# Get the minimum and maximum dates from the filtered dataset and set to beginning and end of the months respectively
min_date = pd.Timestamp(preprocessed_dataset.index.min().date())
max_date = preprocessed_dataset.index.max().date()

# Time interval (daily, weekly, monthly)
time_interval = "W-MON"

# Create a date range from min_date to max_date
date_range = pd.date_range(start=min_date, end=max_date, freq=time_interval)

with top_30_products_adf_exp:
    # Create an empty list to store the ADF test results
    adf_results = []

    # Get the top 30 most sold products
    top_30_products = preprocessed_dataset.groupby("Product Name")["Quantity"].sum().nlargest(30).index

    # Iterate through each product
    for product in top_30_products:
        product_data = preprocessed_dataset[preprocessed_dataset["Product Name"] == product]
        resampled_data = product_data.drop(["Product Name", "Sell Price", "Product Category"], axis=1).resample("W-MON").sum().reindex(date_range, fill_value=0).reset_index()
        resampled_data = resampled_data.set_index("index")

        # Perform the ADF test
        adf_result = adfuller(resampled_data['Quantity'])
        
        # Calculate total sales
        total_sales = product_data['Quantity'].sum()
        
        # Determine if sales are non-stationary
        is_non_stationary = adf_result[1] > 0.05
        
        # Append the result to the list
        adf_results.append({
            'Product': product,
            'Total Sales': total_sales,
            'ADF Statistic': adf_result[0],
            'p-value': adf_result[1],
            'Critical Values': adf_result[4],
            'Is Non-Stationary': is_non_stationary
        })

    # Convert the list to a DataFrame
    adf_results_df = pd.DataFrame(adf_results)
    adf_results_df.index += 1

    # Output the DataFrame
    st.subheader("Top 30 Most Sold Products ADF Test Results")
    st.dataframe(adf_results_df)

    # Count the non-stationary products
    non_stationary_count = adf_results_df['Is Non-Stationary'].sum()

    # Calculate the ratio of non-stationary products to the total number of products
    ratio_non_stationary = non_stationary_count / len(adf_results_df)

    # Output the counts and ratio
    st.write("Non-stationary products out of total:", non_stationary_count, "/", len(adf_results_df))
    st.write("Ratio of non-stationary products:", ratio_non_stationary)

with top_30_products_pred_con:
    st.subheader("Sales Predictions")

    unique_product_names = top_30_products.unique().tolist()
    product_to_predict = st.selectbox("Select Product to Apply Sales Predictions", unique_product_names)

    # Get the data for the selected product
    pred_product_data = preprocessed_dataset[preprocessed_dataset["Product Name"] == product_to_predict]
    pred_resampled_data = pred_product_data.drop(["Product Name", "Sell Price", "Product Category"], axis=1).resample(time_interval).sum().reindex(date_range, fill_value=0).reset_index()
    pred_resampled_data = pred_resampled_data.set_index("index")

    extra_info_expander = st.expander("See Extra Information")
    with extra_info_expander:        
        st.write("**Product Sales Aggregated Dataset**")
        st.dataframe(pred_resampled_data)
        
        # Perform ACF and PACF analysis
        fig, ax = plt.subplots(2, 1, figsize=(10, 8))
        plot_acf(pred_resampled_data['Quantity'], lags=20, ax=ax[0])
        plot_pacf(pred_resampled_data['Quantity'], lags=10, ax=ax[1])
        ax[0].set_title(f"ACF Plot - {product_to_predict}")
        ax[1].set_title(f"PACF Plot - {product_to_predict}")
        plt.tight_layout()
        st.write("**ACF and PCF Plot**")
        st.pyplot(fig)

    # Split data into train and test sets
    train_data, test_data = train_test_split(pred_resampled_data, test_size=0.2, shuffle=False)

    # Add train and test set details to extra_info_expander
    extra_info_expander.write("Train Set")
    extra_info_expander.dataframe(train_data)
    extra_info_expander.write("Test Set")
    extra_info_expander.dataframe(test_data)

    # Use auto-SARIMA to determine the order and seasonal order
    model = auto_arima(train_data['Quantity'], seasonal=True, m=4)
    order = model.order
    seasonal_order = model.seasonal_order

    # Train the SARIMA model
    sarima_model = sm.tsa.SARIMAX(train_data['Quantity'], order=order, seasonal_order=seasonal_order)
    sarima_model_fit = sarima_model.fit()

    # Generate predictions on the test set
    predictions = sarima_model_fit.predict(start=test_data.index[0], end=test_data.index[-1])

    # Calculate accuracy statistics
    mae = mean_absolute_error(test_data['Quantity'], predictions)
    mse = mean_squared_error(test_data['Quantity'], predictions)
    rmse = np.sqrt(mse)

    col1, col2 = st.columns(2)

    # Plot actual vs predicted
    with col1:
        st.write("**Actual vs Predicted**")
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.plot(pred_resampled_data.index, pred_resampled_data['Quantity'], label='Actual')
        ax.plot(predictions.index, predictions, label='Predicted')
        ax.set_xlabel("Date")
        ax.set_ylabel("Quantity")
        ax.legend()
        ax.set_title(f"Sales Predictions - {product_to_predict}")
        plt.xticks(rotation=70)
        plt.tight_layout()
        st.pyplot(fig)

    with col2:
        st.write("**What the predictions should look like in final app**")
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.plot(train_data.index, train_data['Quantity'], label='Actual')
        ax.plot(predictions.index, predictions, label='Predicted')
        ax.set_xlabel("Date")
        ax.set_ylabel("Quantity")
        ax.legend()
        ax.set_title(f"Sales Predictions - {product_to_predict}")
        plt.xticks(rotation=70)
        plt.tight_layout()
        st.pyplot(fig)
    
    st.write("**Accuracy Results**")
    st.write("MAE: ", mae)
    st.write("RMSE: ", rmse)
    st.write("**Auto-ARIMA parameters**")
    st.write("Order: ", order)
    st.write("Seasonal Order: ", seasonal_order)

