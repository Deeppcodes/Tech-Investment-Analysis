import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.ensemble import RandomForestRegressor
from sklearn.ensemble import RandomForestClassifier
from sklearn.neighbors import KNeighborsClassifier
from sklearn.svm import SVC
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, accuracy_score, classification_report, r2_score
from sklearn.preprocessing import StandardScaler

df_deals = pd.read_csv("cleaned_data_v2/cleaned_deals.csv") 

# creates a new dataframe of categories (sectors) with associated total investments and number of deals per year
cat_trends = df_deals.groupby(['primaryTag', 'year']).agg(
    totalInv=('amount', 'sum'), 
    numDeals=('amount', 'count')
).reset_index()

# calculates growth rate for both number of deals and investment amount
cat_trends['invGrowth'] = cat_trends.groupby('primaryTag')['totalInv'].pct_change()
cat_trends['dealGrowth'] = cat_trends.groupby('primaryTag')['numDeals'].pct_change()

cat_trends.replace([np.inf, -np.inf], np.nan, inplace=True)
cat_trends = cat_trends.dropna(subset=['invGrowth', 'dealGrowth']) # drop the first years where theres no growth rate indicators
# target of high growth sectors is a sector with more than 50% investment growth and no decrease of deals from the prev year
cat_trends['hiGrowth'] = ((cat_trends['invGrowth'] > 0.5) & (cat_trends['dealGrowth'] >= 0)).astype(int)
print(cat_trends)
cat_trends['hiGrowth'].value_counts().plot(kind='bar', color=['blue', 'orange'], title='Class Distribution')
plt.show()

X = cat_trends.drop(columns=['hiGrowth', 'primaryTag'])
y = cat_trends['hiGrowth']

# text split and standardize
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
scaler = StandardScaler()
X_train = scaler.fit_transform(X_train)
X_test = scaler.transform(X_test)

# test different models
models = {
    'Random Forest': RandomForestClassifier(n_estimators=100, random_state=42),
    'K-Nearest Neighbors': KNeighborsClassifier(n_neighbors=5),
    'Support Vector Machine': SVC(gamma="auto")
}
results = {}

# train and evaluate models
for name, model in models.items():
    print(f"Training {name}...")
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    
    acc = accuracy_score(y_test, y_pred)
    results[name] = acc
    
    print(f"Accuracy for {name}: {acc:.4f}")
    print(classification_report(y_test, y_pred))

best_model = max(results, key=results.get)
print(f"Best model: {best_model} with accuracy {results[best_model]:.4f}")

plt.figure(figsize=(8, 5))
plt.bar(results.keys(), results.values(), color=['blue', 'green', 'red'])
plt.xlabel('Model')
plt.ylabel('Accuracy')
plt.title('Model Comparison')
plt.ylim([0.5, 1.0])
plt.show()

# model - random forest classification
mod = RandomForestClassifier(n_estimators=100, random_state=42)
mod.fit(X_train, y_train)
pred = []
# uses model to predict whether each sector (category) will be high growth or low growth in 2025
for sector in cat_trends['primaryTag'].unique():
    last_row = cat_trends[cat_trends['primaryTag'] == sector].iloc[-1]
    prev_year = last_row['year'] 
    prev_inv = last_row['totalInv']
    prev_deals = last_row['numDeals']
    prev_inv_growth = last_row['invGrowth']
    prev_deals_growth = last_row['dealGrowth']
    X_future = pd.DataFrame([[prev_year, prev_inv, prev_deals, prev_inv_growth, prev_deals_growth]],
                            columns=['year', 'totalInv', 'numDeals', 'invGrowth', 'dealGrowth'])
    X_future = X_future.to_numpy()
    hi_or_lo = mod.predict(X_future)[0]
    pred.append((sector, 2025, hi_or_lo))

future_df = pd.DataFrame(pred, columns=['primaryTag', 'year', 'hiGrowth'])
# sectors that are likely to be high growth in 2025
hg_sectors = future_df[future_df['hiGrowth'] == 1]
print(hg_sectors)

# model - random forest regression, investment amount prediction
cat_trends = df_deals.groupby(['primaryTag', 'year']).agg(
    totalInv=('amount', 'sum'), 
    numDeals=('amount', 'count')
).reset_index()

cat_trends['invGrowth'] = cat_trends.groupby('primaryTag')['totalInv'].pct_change()
cat_trends['dealGrowth'] = cat_trends.groupby('primaryTag')['numDeals'].pct_change()
cat_trends.replace([np.inf, -np.inf], np.nan, inplace=True)
cat_trends = cat_trends.dropna(subset=['invGrowth', 'dealGrowth']) 

X = cat_trends.drop(columns=['totalInv', 'primaryTag'])
y = cat_trends['totalInv']
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
mod = RandomForestRegressor(n_estimators=100, random_state=42)
mod.fit(X_train, y_train)
y_pred = mod.predict(X_test)

mae = mean_absolute_error(y_test, y_pred)
print(mae)
# 198173046.42679608
range = cat_trends['totalInv'].max() - cat_trends['totalInv'].min()
print(range)
# 2481721091
r2 = r2_score(y_test, y_pred)
print(r2)

# predicts the investment amount of each sector for 2025
predictions = []
for sector in cat_trends['primaryTag'].unique():
    last = cat_trends[cat_trends['primaryTag'] == sector].iloc[-1] 
    prev_year = last['year']
    prev_deals = last['numDeals']
    prev_dg = last['dealGrowth']
    prev_ig = last['invGrowth']
    X_future = pd.DataFrame([[prev_year, prev_deals, prev_ig, prev_dg]], 
                            columns=['year', 'numDeals', 'invGrowth', 'dealGrowth'])
    future_pred = mod.predict(X_future)[0]
    predictions.append((sector, 2025, future_pred))
    prev_inv = future_pred

future_df = pd.DataFrame(predictions, columns=['primaryTag', 'year', 'predInv'])
# top 10 predicted sectors with the most investments in 2025
print(future_df.sort_values(by='predInv', ascending=False).head(10))