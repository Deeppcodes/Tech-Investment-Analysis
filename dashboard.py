import pandas as pd
import dash
import dash_bootstrap_components as dbc
from dash import html
from dash import dcc, Input, Output
import plotly.express as px

df_comp = pd.read_csv("cleaned_data/cleaned_companies.csv")
df_di = pd.read_csv("cleaned_data/cleaned_dealInvestor.csv")
df_deals = pd.read_csv("cleaned_data/cleaned_deals.csv") 
df_invs = pd.read_csv("cleaned_data/cleaned_investor.csv")
df_eco = pd.read_csv("cleaned_data/cleaned_ecosystem.csv")   

#------------------------------------ INVESTMENTS OVER TIME ------------------------------------
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

# Data cleaning
valid_deals = df_deals_regions [(df_deals_regions ['roundType'] != 'Unknown') & (~df_deals_regions['province'].isna())]
valid_deals['date'] = pd.to_datetime(valid_deals['date'])
valid_deals['year'] = valid_deals['date'].dt.year
valid_deals = valid_deals[valid_deals['year'] != 2025]


# Get dropdown options
year_options = sorted(valid_deals['year'].unique())
province_options = sorted(valid_deals['province'].dropna().unique())
stage_options = sorted(valid_deals['roundType'].unique())
stage_options = [stage for stage in stage_options if stage.lower() != 'unknown']

#------------------------------------ FUNDING STAGES  ------------------------------------

def clean_stage(stage):
    mapping = {
        "pre seed": "Pre-Seed",
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

#------------------------------------ INVESTOR BEHAVIOUR ------------------------------------

# Categorize countries: Keep US & Canada, group others as 'Other International'
df_invs["country_grouped"] = df_invs["country"].apply(
    lambda x: x if x == "usa" else ("canada" if x == "canada" else "other International")
)

# Count number of investment firms by country group
investor_counts = df_invs.groupby("country_grouped").size().reset_index(name="count")

# Visualize Investment Firm Demographics with Plotly
fig1 = px.bar(
    investor_counts,
    x="country_grouped",
    y="count",
    title="Investment Firm Demographics",
    labels={"country_grouped": "Country Group", "count": "Number of Investment Firms"},
    color="country_grouped",  # Optional: color by country group
    color_discrete_sequence=px.colors.sequential.Viridis  # Optional: use 'Viridis' color palette
)

# Assuming the dataframe 'df_invs' is already defined
investment_counts = df_invs.explode("stages").groupby(["country", "stages"]).size().reset_index(name="count")

# Filtering out insignificant data (threshold of at least 5 firms per category)
investment_counts = investment_counts[investment_counts["count"] >= 5]

# Pivoting for better visualization
investment_pivot = investment_counts.pivot(index="country", columns="stages", values="count").fillna(0)

# Plot the heatmap using Plotly
fig2 = px.imshow(
    investment_pivot,
    title="Number of Significant Investments per Funding Stage by Country",
    labels={"x": "Funding Stage", "y": "Country", "color": "Number of Firms"},
    color_continuous_scale="Blues",  # Optional: change color scale
)

# Adjust layout for better presentation
fig2.update_xaxes(tickangle=45, tickmode='array')
fig2.update_layout(
    xaxis_title="Funding Stage",
    yaxis_title="Country",
    xaxis=dict(tickmode='array'),
    yaxis=dict(tickmode='array'),
    coloraxis_colorbar=dict(title="Number of Firms")
)

# Assuming the dataframe 'df_deals' is already defined
deal_size_by_stage = df_deals.groupby("roundType")["amount"].mean().reset_index(name="avg_deal_size")

# Plot the bar chart using Plotly with Cividis color palette
fig3 = px.bar(
    deal_size_by_stage,
    x="roundType",
    y="avg_deal_size",
    title="Average Deal Size Per Funding Stage",
    labels={"roundType": "Funding Stage", "avg_deal_size": "Average Deal Size"},
    color="roundType",  # Optional: color by funding stage for better visualization
    color_continuous_scale="Cividis"  # Set color scale to Cividis
)

# Assuming the dataframe 'df_di' and 'df_deals' are already defined
# Identify leading investors per stage
lead_investors_per_stage = df_di.groupby(["roundType", "investorName"]).agg(
    lead_count=("leadInvestorFlag", "sum"),
    total_deals=("dealId", "count")
).reset_index()

# Sort and select top investors per stage
top_lead_investors = lead_investors_per_stage.sort_values(
    by=["roundType", "lead_count", "total_deals"], ascending=[True, False, False]
).groupby("roundType").head(3)  # Top 3 investors per stage

# Influence on funding success
funding_data = df_deals.merge(df_di, on="id", how="left")
investor_funding = funding_data.groupby("investorName").agg(
    total_funding=("amount", "sum"),
    avg_funding=("amount", "mean"),
    total_deals=("id", "count")
).reset_index()

# Filter for leading investors
top_investors = investor_funding[investor_funding["investorName"].isin(top_lead_investors["investorName"])]

# Plot using Plotly
fig4 = px.bar(
    top_investors.sort_values("total_funding", ascending=False),
    x="investorName",
    y="total_funding",
    color="total_deals",
    title="Top Lead Investors and their Funding Influence",
    labels={"investorName": "Investor Name", "total_funding": "Total Funding Received"},
    color_continuous_scale="Inferno_r"
)

# Adjust layout for better readability
fig4.update_layout(
    xaxis_title="Investor Name",
    yaxis_title="Total Funding Received",
    xaxis_tickangle=45,
    legend_title="Total Deals"
)

# ------------------------------------ REGIONAL INSIGHTS ------------------------------------
# top investment categories
cats = df_deals.groupby('primaryTag').agg({'amount': 'sum'}).reset_index()
cats = cats.sort_values(by='amount', ascending=False)
cats = cats.head(10) # top 10
top10_cats = px.bar(cats,
             x='amount', y='primaryTag', 
             color = 'primaryTag',
             title='Top 10 Investment Categories by Amount',
             labels={'primaryTag': 'Investment Category', 'amount': 'Total Investment ($)'},
             color_discrete_sequence=px.colors.qualitative.Prism,)
top10_cats.update_layout(showlegend=False)  

# average deal size
avg_deal = df_deals.groupby('ecosystemName')['amount'].mean().reset_index()
avg_reg = px.bar(avg_deal, x='ecosystemName', y='amount', 
             labels={'ecosystemName':'Region', 'amount':'Average Investment Volume'},
             title='Average Deal Size by Region',)
avg_reg.update_xaxes(categoryorder='total descending')

# total investment vol and category
cat_pref = df_deals.groupby(['ecosystemName', 'primaryTag'])['amount'].sum().reset_index()
cat_pref = cat_pref.sort_values(by='amount', ascending=False)
top20 = df_deals.groupby('primaryTag')['amount'].sum().sort_values(ascending=False)
top20 = top20.head(25).index
cat_pref = cat_pref[cat_pref['primaryTag'].isin(top20)]

inv_reg = px.bar(cat_pref, x='ecosystemName', y='amount', color='primaryTag',
             labels={'ecosystemName':'Region', 'amount':'Investment Volume', 'primaryTag':'Categories (Top 25)'},
             title='Category Preferences and Investment Volume by Region', barmode='stack',
             color_discrete_sequence=px.colors.qualitative.Dark24,)
inv_reg.update_xaxes(categoryorder='total descending')

# map visualisation by key headquarter regions
# longitude and latitude of major regions of interest
hq_loc = {
    'toronto': [43.6511, -79.3470],
    'montreal': [45.5019, -73.5674],
    'waterloo': [43.4643, -80.5204],
    'ottawa': [45.4235, -75.6979],
    'quebec': [46.8131, -71.2075],
    'vancouver': [49.2827, -123.1207],
    'calgary': [51.0447, -114.0719],
    'edmonton': [53.5461, -113.4937],
    'winnipeg': [49.8954, -97.1385],
}

df_loc = pd.DataFrame(hq_loc).T.reset_index()
df_loc.columns = ['headquarters', 'lat', 'lon']

# grabs a subset of deals with relevant headquarters, finds its total investment vol and top inv categories
hq_trends = df_deals.groupby(['headquarters', 'primaryTag'])['amount'].sum().reset_index()

# finds top 3 categories for each major headquarter location
top_cats = []
for hq in hq_trends['headquarters']:
        hq_data = hq_trends[hq_trends['headquarters'] == hq]
        top4 = hq_data.sort_values(by='amount', ascending=False).head(4)
        top_cats.append(top4)
top4_df = pd.concat(top_cats, ignore_index=True)

hq_trends = top4_df.merge(df_loc, on='headquarters', how='left')
num_deals = df_deals.groupby('headquarters').size().reset_index(name='num_deals') # counts number of deals for each hq
hq_trends = hq_trends.merge(num_deals, on='headquarters', how='left')
hq_trends = hq_trends.dropna(subset=['lat', 'lon']) # drops irrelevant headquarter locations
hq_trends = hq_trends.sort_values(by="amount", ascending=False)

map_hq = px.scatter_map(
    hq_trends,
    lat='lat',
    lon='lon',
    size='amount',  # bubble size represents investment volume
    color="primaryTag", # color represents top category
    hover_name='headquarters',
    hover_data={'primaryTag': True, "amount": True, 'num_deals': True, "lat": False, "lon":False},
    labels={'amount':'Investment Volume by Category', 'primaryTag':'Top Investment Categories',
            'num_deals': 'Total Number of Deals for Headquarter'},
    color_discrete_sequence=px.colors.qualitative.Prism,
    size_max=60, 
    zoom=3
)

map_hq.update_layout(
    mapbox_style='carto-positron',
    mapbox_center={"lat": 56, "lon": -106}, 
)

# ------------------------- Putting everything into a dashboard -------------------------
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

app.layout = html.Div([
    html.H1("Canadian Tech Investments Dashboard"),
        dcc.Tabs([
            dcc.Tab(label='Investment Trends Over Time', children=[
                html.Div([
                    html.H3("Investment Trends Over Time", style={'margin-top': '50px', 'margin-left': '50px'}),
                    html.P([
                        "Analyze total tech investment per year (2019-2024), identifying major shifts.",
                        html.Br(),
                        "Examine deal volume and funding size trends over time.",
                        html.Br(),
                        "Investigate how investment has changed across different deal sizes."
                    ], style={'margin-left': '50px'}),
                    
                    dbc.Row([
                        dbc.Col([
                            html.Label("Select Year"),
                            dcc.Dropdown(
                                id='year-dropdown', 
                                options=[{'label': str(y), 'value': y} for y in year_options],
                                multi=True, value=[year_options[-1]]
                            ),
                            
                            html.Label("Select Province", style={'margin-top': '20px'}),
                            dcc.Dropdown(
                                id='province-dropdown', 
                                options=[{'label': p, 'value': p} for p in province_options],
                                multi=True, value=province_options
                            ),
                            
                            html.Label("Select Funding Stage", style={'margin-top': '20px'}),
                            dcc.Dropdown(
                                id='stage-dropdown', 
                                options=[{'label': s, 'value': s} for s in stage_options],
                                multi=True, value=stage_options
                            )
                        ], width=3, style={'padding': '20px'}),
                        dbc.Col([
                            dcc.Graph(
                                id='investment-bar-chart', 
                                style={'width': '100%', 'height': '600px'}
                            )
                        ], width=9)  # Graph takes more space
                    ], justify='start', style={'margin-left': '80px', 'margin-right': '80px'}),
                ]),
                dcc.Tab(label='Total Investment', children=[dcc.Graph(figure=fig_investment,style={'width': '80%', 'height': '500px', 'margin': 'auto'})]),
                dcc.Tab(label='Deal Volume', children=[dcc.Graph(figure=fig_deals,style={'width': '80%', 'height': '500px', 'margin': 'auto'})]),
                dcc.Tab(label='Deal Size Distribution', children=[dcc.Graph(figure=fig_deal_size,style={'width': '80%', 'height': '500px', 'margin': 'auto'})]),
                dcc.Tab(label='Regional Trends', children=[dcc.Graph(figure=fig_region,style={'width': '80%', 'height': '500px', 'margin': 'auto'})])
            ]),
            dcc.Tab(label=' Funding Stages Analysis', children=[
                dcc.Tab(label='Proportion of Deals', children=[dcc.Graph(figure=fig_stage_proportion)]),
                dcc.Tab(label='Average Deal Size Over Time', children=[dcc.Graph(figure=fig_avg_deal_size)]),
                dcc.Tab(label='Deal Trends Over Years', children=[dcc.Graph(figure=fig_deal_trends)])
            ]),
            dcc.Tab(label='Investor Demographics & Behavior', children=[
                html.Div([
                    dcc.Graph(
                        figure=fig1,
                        style={'width': '90%', 'height': '700px'}
                    ),
                    dcc.Graph(
                        figure=fig2,
                        style={'width': '90%', 'height': '700px'}
                    ),
                    dcc.Graph(
                        figure=fig3,
                        style={'width': '90%', 'height': '700px'}
                    ),
                    dcc.Graph(
                        figure=fig4,
                        style={'width': '90%', 'height': '700px'}
                    ),
                ]),
            
            ]),
            dcc.Tab(label='Regional Insights', children=[
                html.Div([
                    html.H3("Sectoral & Regional Insights",style={'margin-top': '50px', 'margin-left': '50px'}),
                    html.P(["Identify the top investment categories nationally (e.g., SaaS, FinTech, HealthTech, AI, Blockchain).",
                           html.Br(),
                           "Compare investment trends across key Canadian regions (Toronto, Vancouver, Montreal, Calgary, Waterloo, etc.).",
                           html.Br(),
                           "Examine regional differences in investment volume, deal sizes, and category preferences."],
                    style={'margin-left': '50px'}),
                    dcc.Graph(figure=top10_cats,
                            style={'width': '90%', 'height': '700px', 'margin': 'auto'})
                ]),
                html.Div([
                    html.H3("Investment Trends by Major Headquarter Locations",style={'margin-top': '50px', 'margin-left': '50px'}),
                    html.P("Hover over the headquarter to see information such as total investment funding for each category, and number of deals!",
                        style={'margin-left': '50px'}),
                    dcc.Graph(
                        figure=map_hq,
                        style={'width': '90%', 'height': '700px'}
                    )
                ]),
                html.Div([
                    dcc.Graph(figure=inv_reg,
                            style={'width': '80%', 'height': '500px', 'margin': 'auto'},
                    ),
                    dcc.Graph(figure=avg_reg,
                            style={'width': '80%', 'height': '500px', 'margin': 'auto'},
                    )
                ])
            ]),
        ])
])

# Callbacks
@app.callback(
    Output('investment-bar-chart', 'figure'),
    Input('year-dropdown', 'value'),
    Input('province-dropdown', 'value'),
    Input('stage-dropdown', 'value')
)
def update_graph(selected_years, selected_provinces, selected_stages):
    filtered_df = valid_deals[
        (valid_deals['year'].isin(selected_years)) &
        (valid_deals['province'].isin(selected_provinces)) &
        (valid_deals['roundType'].isin(selected_stages))
    ]
    
    summary = filtered_df.groupby(['province'])['amount'].sum().reset_index()
    fig = px.bar(summary, x='province', y='amount', title='Investment Amount by Province',
                 labels={'province': 'Province', 'amount': 'Total Investment ($)'},
                 color='province', color_discrete_sequence=px.colors.qualitative.Prism,)
    fig.update_xaxes(categoryorder='total descending')
    return fig

if __name__ == '__main__':
    print("App is starting")
    app.run_server(debug=True)
