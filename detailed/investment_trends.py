import pandas as pd
import dash
import dash_bootstrap_components as dbc
from dash import html, dcc
import plotly.express as px

# Load data
df_deals = pd.read_csv("cleaned_data/cleaned_deals.csv")
df_eco = pd.read_csv("cleaned_data/cleaned_ecosystem.csv")

# Group by year and sum the investment amount
investment_trends = df_deals.groupby('year')['amount'].sum().reset_index()
fig_investment = px.line(investment_trends, x='year', y='amount', markers=True,
                         title='Total Investment in Canadian Startups (2019-2024)')

# Count number of deals per year
deal_volume = df_deals.groupby('year')['id'].count().reset_index()
deal_volume.rename(columns={'id': 'num_deals'}, inplace=True)
fig_deals = px.bar(deal_volume, x='year', y='num_deals',
                   title='Number of Investment Deals Per Year (2019-2024)', color='num_deals')

# Define deal size categories
def categorize_deal(amount):
    if amount < 100000:
        return '<$100K'
    elif 1000000 <= amount < 5000000:
        return '$1M-$5M'
    elif amount >= 100000000:
        return '$100M+'
    else:
        return 'Other'

df_deals['deal_size_category'] = df_deals['amount'].apply(categorize_deal)

deal_size_trends = df_deals.groupby(['year', 'deal_size_category'])['amount'].sum().reset_index()
deal_size_pivot = deal_size_trends.pivot(index='year', columns='deal_size_category', values='amount')
fig_deal_size = px.bar(deal_size_trends, x='year', y='amount', color='deal_size_category',
                        title='Investment Distribution by Deal Size (2019-2024)', barmode='stack')

# Merge deals with ecosystems
df_deals_regions = df_deals.merge(df_eco, on='ecosystemName', how='left')
region_trends = df_deals_regions.groupby(['year', 'province'])['amount'].sum().reset_index()
fig_region = px.line(region_trends, x='year', y='amount', color='province', markers=True,
                      title='Investment Trends by Region (2019-2024)')

# Dash App
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

app.layout = html.Div([
    html.H1("Investment Trends Dashboard"),
    dcc.Tabs([
        dcc.Tab(label='Total Investment', children=[dcc.Graph(figure=fig_investment)]),
        dcc.Tab(label='Deal Volume', children=[dcc.Graph(figure=fig_deals)]),
        dcc.Tab(label='Deal Size Distribution', children=[dcc.Graph(figure=fig_deal_size)]),
        dcc.Tab(label='Regional Trends', children=[dcc.Graph(figure=fig_region)])
    ])
])

if __name__ == '__main__':
    app.run_server(debug=True)
