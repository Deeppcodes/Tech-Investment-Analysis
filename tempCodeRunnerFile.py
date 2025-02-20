df_deals_regions = df_deals.merge(df_eco, on='ecosystemName', how='left')
# region_trends = df_deals_regions.groupby(['year', 'province'])['amount'].sum().reset_index()
# fig_region = px.line(region_trends, x='year', y='amount', color='province', markers=True,
#                       title='Investment Trends by Region (2019-2024)')
