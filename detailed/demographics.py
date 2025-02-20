import os
import pandas as pd
import dash
from dash import dcc, html, dash_table
import plotly.express as px

# Initialize Dash app
app = dash.Dash(__name__)
server = app.server

# File paths
file_paths = {
    "deals": "cleaned_data/cleaned_deals.csv",
    "dealInvestor": "cleaned_data/cleaned_dealInvestor.csv",
    "investors": "cleaned_data/cleaned_investor.csv",
    "ecosystems": "cleaned_data/cleaned_ecosystem.csv",
    "companies": "cleaned_data/cleaned_companies.csv"
}

# Load data
dfs = {name: pd.read_csv(path) for name, path in file_paths.items()}

# Investment firm demographics
investors_df = dfs["investors"].copy()
investors_df["country_grouped"] = investors_df["country"].apply(
    lambda x: x if x == "usa" else ("canada" if x == "canada" else "other International")
)
investor_counts = investors_df.groupby("country_grouped").size().reset_index(name="count")
fig1 = px.bar(investor_counts, x="country_grouped", y="count", title="Investment Firm Demographics")

# Average deal size per stage
deal_size_by_stage = dfs["deals"].groupby("roundType")["amount"].mean().reset_index(name="avg_deal_size")
fig2 = px.bar(deal_size_by_stage, x="roundType", y="avg_deal_size", title="Average Deal Size Per Funding Stage")

# Top lead investors per stage
lead_investors_per_stage = dfs["dealInvestor"].groupby(["roundType", "investorName"]).agg(
    lead_count=("leadInvestorFlag", "sum"), total_deals=("dealId", "count")
).reset_index()
top_lead_investors = lead_investors_per_stage.sort_values(
    by=["roundType", "lead_count", "total_deals"], ascending=[True, False, False]
).groupby("roundType").head(3)
fig3 = px.bar(top_lead_investors, x="investorName", y="lead_count", color="roundType",
              title="Top Lead Investors per Stage")

# Dash Layout
app.layout = html.Div([
    html.H1("Investor Demographics & Behavior Analysis"),
    dcc.Graph(figure=fig1),
    dcc.Graph(figure=fig2),
    dcc.Graph(figure=fig3)
])

# Run the app
if __name__ == "__main__":
    app.run_server(debug=True)
