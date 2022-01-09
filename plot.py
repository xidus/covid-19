import datetime as dt

import pandas as pd
import altair as alt


def make_chart(df: pd.DataFrame, y: str = None, loglog: bool = False) -> alt.Chart:

    nearest = alt.selection(
        type='single',
        nearest=True,
        on='mouseover',
        fields=['infected_accum'],
        empty='none',
    )

    base_kwargs = dict()
    if loglog is True:
        base_kwargs.update(scale=alt.Scale(type='log'))
    base = alt.Chart(df).encode(
        x=alt.X('infected_accum:Q', **base_kwargs),
        y=alt.Y(y, **base_kwargs),
        color='year(date):N',
    ).properties(width=700, height=400)

    selectors = alt.Chart(df).mark_point().encode(
        x=alt.X('infected_accum:Q'),
        opacity=alt.value(0),
    ).add_selection(
        nearest,
    )

    line = base.mark_line()

    if 'yearweek' in df:
        tooltip_base = ['yearweek:N']
    else:
        tooltip_base = ['date:T']
    tooltip = tooltip_base + [
        'infected_accum:Q',
        y,
    ]
    points = base.mark_point().encode(
        opacity=alt.condition(nearest, alt.value(1), alt.value(0.5)),
        tooltip=tooltip,
    )
    text = base.mark_text(align='right', baseline='bottom', dx=5, dy=-5).encode(
        text=alt.condition(nearest, y, alt.value(' '))
    )
    rule = base.mark_rule(color='gray').encode(
        x=alt.X('infected_accum:Q'),
    ).transform_filter(
        nearest
    )

    return (line + selectors + points + rule + text).interactive()


def main():

    conv = {
        1: lambda s: dt.datetime.strptime(s, '%Y-%m-%d'),
    }
    lkw = dict(
        converters=conv,
    )
    df = pd.read_csv('covid19-data-denmark.csv', **lkw)
    # df = pd.read_csv('covid19-data-denmark.csv')

    n = df.copy()
    years = n.date.dt.isocalendar().year
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

    weekly = make_chart(df=g, y='infected_this_week_so_far:Q', loglog=True)
    daily = make_chart(df=df, y='infected_today:Q')
    chart = weekly & daily
    chart.save('index.html')


if __name__ == '__main__':
    main()
