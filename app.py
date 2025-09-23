import streamlit as st
import pandas as pd
import plotly.express as px

# Load data
CSV_FILE = 'data/league_results.csv'
df = pd.read_csv(CSV_FILE)

# Get relative league rank
df['league_rank'] = df.groupby('gameweek')['total_points'] \
                      .rank(method='min', ascending=False) \
                      .astype(int)

# Select managers
managers = df['manager'].unique()
selected_managers = st.sidebar.multiselect(
    'Select Manager(s)',
    managers,
    default=managers
)
df_filtered = df[df['manager'].isin(selected_managers)]

# Rank progress over time
st.subheader('League Rank Progress')
fig_rank = px.line(
    df_filtered,
    x='gameweek',
    y='league_rank',
    color='manager',
    markers=True,
    title='League Rank Over Time'
)
fig_rank.update_layout(width=1000, height=600)

# Plot rank 1 at top
fig_rank.update_yaxes(autorange='reversed')
st.plotly_chart(fig_rank)

# Latest table
latest_gw = df['gameweek'].max()
st.subheader(f'Latest Gameweek ({latest_gw}) Standings')
latest_df = df[df['gameweek'] == latest_gw].sort_values('league_rank')
st.dataframe(
    latest_df[['manager', 'team', 'points', 'total_points', 'league_rank']]
)
