import streamlit as st
import pandas as pd
import plotly.express as px
import os
import datetime

# FIXME make this configurable
CSV_FILE = 'data/league_results.csv'

# Load data
@st.cache_data(ttl=3600) # every hour
def load_data():
    df = pd.read_csv(CSV_FILE)

    # Get relative league rank
    df['league_rank'] = df.groupby('gameweek')['total_points'] \
                          .rank(method='min', ascending=False) \
                          .astype(int)

    df = df.sort_values(['manager', 'gameweek'])

    return df

def main():
    df = load_data()

    # Select managers
    managers = df['manager'].unique()
    selected_managers = st.sidebar.multiselect(
        'Select Manager(s)',
        managers,
        default=managers
    )
    df_filtered = df[df['manager'].isin(selected_managers)]

    # last updated timestamp
    mod_time = os.path.getmtime(CSV_FILE)
    last_updated = datetime.datetime.fromtimestamp(mod_time).strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    st.title('Fantasy Football League Tracker')
    st.markdown(f"**Last updated:** {last_updated}")

    # Rank progress over time
    latest_ranks = df_filtered.sort_values('gameweek').groupby('manager')['league_rank'].last().sort_values(ascending=True)
    order = latest_ranks.index.tolist()

    # common colour mapping
    colours = px.colors.qualitative.Light24
    manager_colours = {manager: colours[i % len(colours)] for i, manager in enumerate(order)}

    # Plot selection
    plot_choice = st.radio('Choose plot', ['League Rank Over Time', 'Total Points Over Time'])

    if plot_choice == 'League Rank Over Time':
        fig = px.line(
            df_filtered,
            x='gameweek',
            y='league_rank',
            color='manager',
            markers=True,
            hover_data=['team', 'manager'],
            title='League Rank Over Time',
            color_discrete_map=manager_colours,
            category_orders={'manager': order}
        )
        fig.update_yaxes(autorange='reversed')
        st.plotly_chart(fig, use_container_width=True)

    else:
        fig = px.line(
            df_filtered,
            x='gameweek',
            y='total_points',
            color='manager',
            markers=True,
            hover_data=['team', 'manager'],
            title='Total Points Over Time',
            color_discrete_map=manager_colours,
            category_orders={'manager': order}
        )
        st.plotly_chart(fig, use_container_width=True)

    # Latest table
    latest_gw = df['gameweek'].max()
    st.subheader(f'Latest Gameweek ({latest_gw}) Standings')
    latest_df = df[df['gameweek'] == latest_gw].sort_values('league_rank').reset_index()
    latest_df.index = latest_df['league_rank']
    st.dataframe(
        latest_df[['manager', 'team', 'total_points']]
    )

if __name__ == '__main__':
    main()

