import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error
import numpy as np

# Load the data
df_deals = pd.read_csv("cleaned_data_v2/cleaned_deals.csv")
df_eco = pd.read_csv("cleaned_data_v2/cleaned_ecosystem.csv")

# Merge df_deals with df_eco to get province information
df_deals = df_deals.merge(df_eco[['ecosystemName', 'province']], on='ecosystemName', how='left')

# Preprocessing for the Linear Regression Model
df_deals = df_deals[df_deals['year'].notnull()]
df_deals['year'] = df_deals['year'].astype(int)

# One-hot encode categorical variables
df_deals_encoded = pd.get_dummies(df_deals[['year', 'roundType', 'province']], drop_first=True)

# Feature matrix (X) and target vector (y)
X = df_deals_encoded
y = df_deals['amount']

# Split the data into training and test sets
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Initialize the model and fit it
model = LinearRegression()
model.fit(X_train, y_train)

# Predict on the test data
y_pred = model.predict(X_test)

# Evaluate the model
mae = mean_absolute_error(y_test, y_pred)
mse = mean_squared_error(y_test, y_pred)
rmse = np.sqrt(mse)  # Manually calculate RMSE

# Print evaluation metrics
print(f"Mean Absolute Error: {mae}")
print(f"Mean Squared Error: {mse}")
print(f"Root Mean Squared Error: {rmse}")

# Function for making predictions on new input data (you can call this in Dash later)
def predict_investment(year, round_type, province):
    # Prepare the input data for prediction
    input_data = pd.DataFrame([[year, round_type, province]], columns=['year', 'roundType', 'province'])
    input_data_encoded = pd.get_dummies(input_data, drop_first=True)
    prediction = model.predict(input_data_encoded)
    return prediction[0]

# Test prediction with an example
example_year = 2023
example_round_type = 'Seed'
example_province = 'Ontario'
predicted_investment = predict_investment(example_year, example_round_type, example_province)

print(f"Predicted Investment for {example_year}, {example_round_type} round in {example_province}: ${predicted_investment:,.2f}")
