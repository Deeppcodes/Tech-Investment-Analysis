import pandas as pd
import dash
import dash_bootstrap_components as dbc
from dash import html
from dash import dcc
import plotly.express as px

df_comp = pd.read_csv("cleaned_data/cleaned_companies.csv")
df_di = pd.read_csv("cleaned_data/cleaned_dealInvestor.csv")
df_deals = pd.read_csv("cleaned_data/cleaned_deals.csv") 
df_invs = pd.read_csv("cleaned_data/cleaned_investor.csv")
df_eco = pd.read_csv("cleaned_data/cleaned_ecosystem.csv")   

# START OF EDA

# identify all possible categories
print(df_deals['primaryTag'].unique())

# clean categories
fix = { # with identification help from genAI
    "blochchain": "blockchain",
    "heatlhtech": "healthtech",
    "contructiontech": "constructiontech",
    "artificial intelligences": "ai",
    "electronic health record (ehr)": "healthtech",
    "pharmaceutical manufacturing": "pharmaceuticals",
    "medical device": "medtech",
    "biotechnology": "biotech",
    "machine learning": "ai",
    "communications infrastructure": "telecommunications",
    "real estate": "propertytech",
    "renewable energy": "cleantech",
    "r&d": "research",
    "crm": "saas",
    "insurance software": "insurtech",
    "environmental services": "cleantech",
    "energy efficiency": "greentech",
    "womens health": "healthtech",
    "biotechnology research": "biotech",
    'esphera synbio': "biotech",
    'retail recyclable materials &':'cleantech',
    'data analytics':'analytics',
    'online audio and video media':'entertainmenttech',
    'technology':'information technology',
    '3d printing':'3dtech'
}

def clean_cat(cat):
    cat = cat.split(',')[0]
    cat = cat.replace('-', ' ')
    cat = cat.strip() 
    cat = fix.get(cat, cat) 
    if ('manu' in cat):
        return 'manufacturing'
    if ('software' in cat):
        return 'software development'
    if ('health' in cat):
        return 'healthtech'
    if ('transportation' in cat):
        return 'transportation'
    return cat

# make categories clean for all the relevant dfs
df_deals['primaryTag'] = df_deals['primaryTag'].apply(clean_cat)
df_comp['primaryTag'] = df_comp['primaryTag'].apply(clean_cat)

# identify all possible ecosystems
print(df_deals['ecosystemName'].unique())
# put waterloo into waterloo region
def clean_eco(eco):
  if (eco == 'waterloo'):
    return 'waterloo region'
  else:
    return eco
df_deals['ecosystemName'] = df_deals['ecosystemName'].apply(clean_eco)
df_comp['ecosystemName'] = df_comp['ecosystemName'].apply(clean_eco)
df_di['ecosystemName'] = df_di['ecosystemName'].apply(clean_eco)

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

# identify all possible headquarters
print(df_deals['headquarters'].unique())

# clean headquarters data
fix = { 
    "montréal": "montreal",
    "québec": "quebec",
    "vanouver": "vancouver",
    "west vancouver": "vancouver",
    "kitchener/toronto": "toronto",
    "kitchener-waterloo" : "waterloo",
    "kitchener": "waterloo" # include kitchener in the waterloo data
}
def clean_hq(hq):
    hq = hq.split('&')[0] 
    hq = hq.split(',')[0]
    hq = hq.strip()
    hq = fix.get(hq, hq) 
    return hq

# make headquarters clean for all the relevant dfs
df_deals['headquarters'] = df_deals['headquarters'].apply(clean_hq)
df_di['headquarters'] = df_di['headquarters'].apply(clean_hq)

uni_hq = df_deals['headquarters'].unique()

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

map_e = px.scatter_map(
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

map_e.update_layout(
    mapbox_style='carto-positron',
    mapbox_center={"lat": 56, "lon": -106}, 
)



# Putting everything into a dashboard
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

app.layout = html.Div([
    html.H1("Regional Insights Dashboard"),
    
        dcc.Tabs([
            dcc.Tab(label='Categories Analysis', children=[
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
                ])
            ]),

        dcc.Tab(label='Headquarter Map', children=[
            html.Div([
                html.H3("Investment Trends by Major Headquarter Locations",style={'margin-top': '50px', 'margin-left': '50px'}),
                html.P("Hover over the headquarter to see information such as total investment funding for each category, and number of deals!",
                       style={'margin-left': '50px'}),
                dcc.Graph(
                    figure=map_e,
                    style={'width': '90%', 'height': '700px'}
                )
            ])
        ]),

        dcc.Tab(label='Regional Insights', children=[
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

if __name__ == '__main__':
    print("App is starting")
    app.run_server(debug=True)
