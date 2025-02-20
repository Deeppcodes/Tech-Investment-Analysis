import pandas as pd
import dash
import dash_bootstrap_components as dbc
from dash import html, dcc
import plotly.express as px

# Load datasets
df_deals = pd.read_csv("cleaned_data/cleaned_deals.csv")

# Clean and prepare data
def clean_stage(stage):
    mapping = {
        "pre-seed": "Pre-Seed",
        "seed": "Seed",
        "series a": "Series A",
        "series b": "Series B",
        "series c": "Series C",
        "series d": "Series D+",
        "series e": "Series D+",
        "series f": "Series D+",
        "growth": "Growth",
        "ipo": "IPO"
    }
    return mapping.get(stage.lower(), "Other")

df_deals["roundType"] = df_deals["roundType"].astype(str).apply(clean_stage)

# Proportion of Deals per Investment Stage
# Count the number of deals at each funding stage
stage_counts = df_deals['roundType'].value_counts(normalize=True) * 100  # Convert to percentage
stage_counts = stage_counts.reset_index()  # Reset index to turn it into a DataFrame
stage_counts.columns = ['Funding Stage', 'Proportion']  # Rename columns for clarity

# Create a pie chart
fig_stage_proportion = px.pie(stage_counts, 
                               names='Funding Stage', 
                               values='Proportion',
                               title='Proportion of Deals at Each Investment Stage',
                               color_discrete_sequence=px.colors.qualitative.Prism)




# Average Deal Size per Stage Over Time
deal_size = df_deals.groupby(["year", "roundType"])['amount'].mean().reset_index()
fig_avg_deal_size = px.line(deal_size, x='year', y='amount', color='roundType',
                            title='Average Deal Size Per Stage Over Time',
                            labels={'amount': 'Average Deal Size ($)', 'year': 'Year'})

# Trends in Number and Size of Deals per Stage Over Years
deal_trends = df_deals.groupby(["year", "roundType"]).agg({"id": "count", "amount": "sum"}).reset_index()
deal_trends.rename(columns={"id": "num_deals"}, inplace=True)
fig_deal_trends = px.bar(deal_trends, x='year', y='num_deals', color='roundType',
                         title='Trends in Number of Deals Per Stage Over Years',
                         labels={'num_deals': 'Number of Deals', 'year': 'Year'},
                         barmode='stack', color_discrete_sequence=px.colors.qualitative.Dark24)



# Dash App
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.layout = html.Div([
    html.H1("Funding Stages Analysis Dashboard"),
    dcc.Tabs([
        dcc.Tab(label='Proportion of Deals', children=[dcc.Graph(figure=fig_stage_proportion)]),
        dcc.Tab(label='Average Deal Size Over Time', children=[dcc.Graph(figure=fig_avg_deal_size)]),
        dcc.Tab(label='Deal Trends Over Years', children=[dcc.Graph(figure=fig_deal_trends)])
    ])
])

if __name__ == '__main__':
    app.run_server(debug=True)
