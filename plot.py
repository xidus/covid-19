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

nearest = alt.selection(
    type='single',
    nearest=True,
    on='mouseover',
    fields=['infected_accum'],
    empty='none',
)

base_weekly = alt.Chart(g).encode(
    x=alt.X('infected_accum:Q', scale=alt.Scale(type='log')),
    y=alt.X('infected_this_week_so_far:Q', scale=alt.Scale(type='log')),
).properties(width=700, height=400)

selectors_weekly = alt.Chart(g).mark_point().encode(
    x=alt.X('infected_accum:Q'),
    opacity=alt.value(0),
).add_selection(
    nearest,
)

line_weekly = base_weekly.mark_line()
points_weekly = base_weekly.mark_point().encode(
    opacity=alt.condition(nearest, alt.value(1), alt.value(0.5)),
)
text_data = [
    'yearweek:N',
    'infected_accum:Q',
    'infected_this_week_so_far:Q',
]
text_weekly = base_weekly.mark_text(align='right', valign='bottom', dx=5, dy=-5).encode(
    text=alt.condition(nearest, text_data, alt.value(' '))
)
rule_weekly = base_weekly.mark_rule(color='gray').encode(
    x=alt.X('infected_accum:Q'),
    tooltip=[
        'yearweek:N',
        'infected_accum:Q',
        'infected_this_week_so_far:Q',
    ],
).transform_filter(
    nearest
)

weekly = (line_weekly + selectors_weekly + points_weekly + rule_weekly + text_weekly).interactive()

base_daily = alt.Chart(df).encode(
    x=alt.X('infected_accum:Q'),
    y=alt.X('infected_today:Q'),
).properties(width=700, height=400)

selectors_daily = alt.Chart(df).mark_point().encode(
    x=alt.X('infected_accum:Q'),
    opacity=alt.value(0),
).add_selection(
    nearest,
)

line_daily = base_daily.mark_line()
points_daily = base_daily.mark_point().encode(
    opacity=alt.condition(nearest, alt.value(1), alt.value(0.5)),
)
text_daily = base_daily.mark_text(align='left', dx=5, dy=-5).encode(
    text=alt.condition(nearest, 'infected_today:Q', alt.value(' ')),
)
rule_daily = base_daily.mark_rule(color='gray').encode(
    x=alt.X('infected_accum:Q'),
    tooltip=[
        'yearweek:N',
        'infected_accum:Q',
        'infected_today:Q',
    ],
).transform_filter(
    nearest
)

daily = (line_daily + selectors_daily + points_daily + rule_daily + text_daily).interactive()

chart = weekly & daily
chart.save('index.html')
