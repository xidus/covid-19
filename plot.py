import datetime as dt

import pandas as pd
import altair as alt

conv = {
    1: lambda s: dt.datetime.strptime(s, '%Y-%m-%d'),
}
lkw = dict(
    converters=conv,
)
df = pd.read_csv('covid19-data-denmark.csv', **lkw)
# df = pd.read_csv('covid19-data-denmark.csv')

n = df.copy()
years = n.date.dt.year
weeks = n.date.dt.isocalendar().week
n['yearweek'] = years.astype(str) + '-' + weeks.map(lambda w: f'{w:02d}')
aggregates = {
    # Take the latest total number of cases at the end of the period
    'infected_accum': 'last',
    # Sum all new cases to get the rate for the period
    'infected_today': 'sum',
}
# BAD: g = n.groupby('yearweek')[['infected_accum', 'infected_today']].mean()
g = n.groupby('yearweek').agg(aggregates)
# g.tail()

# Make index a regular column so that it can be included in the plot.
g = g.reset_index('yearweek')
# g = g.iloc[:-1]

# Rename columns after aggregation
g = g.rename(columns=dict(infected_today='infected_this_week_so_far'))

highlight = alt.selection(
    type='single',
    on='mouseover',
    fields=['symbol'],
    nearest=True,
)

base_weekly = alt.Chart(g).encode(
    x=alt.X('infected_accum:Q', scale=alt.Scale(type='log')),
    y=alt.X('infected_this_week_so_far:Q', scale=alt.Scale(type='log')),
).properties(width=700, height=400).interactive()
weekly = base_weekly.mark_circle().encode(
    opacity=alt.value(0)
).add_selection(
    highlight
)
weekly += base_weekly.mark_line()
weekly += base_weekly.mark_point(
    size=alt.condition(~highlight, alt.value(1), alt.value(3)),
    tooltip=[
        'yearweek:N',
        'infected_accum:Q',
        'infected_this_week_so_far:Q',
    ],
)

base_daily = alt.Chart(df).encode(
    x=alt.X('infected_accum:Q'),
    y=alt.X('infected_today:Q'),

).properties(width=700, height=400).interactive()
daily = base_daily.mark_circle().encode(
    opacity=alt.value(0)
).add_selection(
    highlight
)
daily += base_daily.mark_line()
daily += base_daily.mark_point(
    size=alt.condition(~highlight, alt.value(1), alt.value(3)),
    tooltip=[
        'yearweek:N',
        'infected_accum:Q',
        'infected_today:Q',
    ],
)

chart = weekly & daily
chart.save('index.html')
