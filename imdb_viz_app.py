from connect import Connect
import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.express as px
import pandas as pd
from dash.dependencies import Input, Output
from collections import OrderedDict
import json
import plotly.graph_objs as go
from dash.exceptions import PreventUpdate

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
server = app.server

NO_DATA_GRAPH = {
    'data': [],
    'layout': go.Layout(
        # title='NO DATA!',
        xaxis={'type': 'linear', 'title': ''},
        yaxis={'title': ''},
        margin={'l': 80, 'b': 70, 't': 50, 'r': 20},
        legend={'x': 0, 'y': 1},
        hovermode='closest'
    )
}

connection = Connect.get_connection()
print(connection.list_database_names())

# creating or accessing a new database
db = connection["imdb_database"]

category_dict = OrderedDict({
    'top_movies': 'Top Movies',
    'top_tvshows': 'Top TV Shows',
    'top_budgets': 'Top Movie Budgets',
    'top_revenues': 'Top Movie Revenues',
    'top_budgets_revenues': 'Top Movie Budgets and their Revenues',
    'top_revenues_budgets': 'Top Movie Revenues and their Budgets',
    'movies_count': 'Number of Movies per Year',
    'tvshows_count': 'Number of TV Shows per Year',
    'budgets_max': 'Highest Budget per Year',
    'revenues_max': 'Highest Revenue per Year'
})

category_dbs = {
    'top_movies': 'top_movies',
    'top_tvshows': 'top_tvshows',
    'top_budgets': 'top_budgets',
    'top_revenues': 'top_revenues',
    'top_budgets_revenues': 'top_budgets',
    'top_revenues_budgets': 'top_revenues',
    'movies_count': 'titles_count',
    'tvshows_count': 'titles_count',
    'budgets_max': 'top_budgets',
    'revenues_max': 'top_revenues'
}

category_fields = {
    'movies_count': 'movie',
    'tvshows_count': 'tvSeries',
    'top_budgets': 'budget',
    'top_revenues': 'revenue',
    'budgets_max': 'max_budget',
    'revenues_max': 'max_revenue'
}

app.layout = html.Div([
    html.Div([
        html.H3('IMDB Movie Explorer', style={'textAlign': 'center', 'fontWeight': '600'}),

        html.Div([
            html.Label('Select Chart', style={'fontWeight': '600'}),
            dcc.Dropdown(
                id='dropdown-category',
                options=[{'label': val, 'value': key} for key, val in category_dict.items()],
                value=list(category_dict.keys())[0]
            )
        ], style={'width': '30%', 'display': 'inline-block', 'marginRight': '5%'}),
        html.Div([
            html.Label('Sort By', style={'fontWeight': '600'}),
            dcc.Dropdown(
                id='dropdown-sort',
                value='relevance',
                searchable=False,
                clearable=False
            )
        ], id='dropdown-div', style={'width': '30%', 'display': 'inline-block'}),
        html.Div([
            html.Label(id='radio-label', style={'fontWeight': '600'}),
            dcc.RadioItems(
                id='radio-options',
                inputStyle={'marginRight': '10px'},
                labelStyle={'marginRight': '20px', 'display': 'inline-block'}
            )
        ], style={'width': '30%', 'float': 'right', 'display': 'inline-block'}),

        html.Div([dcc.Graph(id='movie-charts')]),

        html.Div([
            dcc.Slider(
                id='year-slider',
                step=None
            )
        ], id='slider-div'),

        html.Br(),
        html.P("© 2021 Ashish Kayastha. All rights reserved.", style={'textAlign': 'center'})
    ], style={'margin-left': '10%', 'margin-right': '10%'}),
    html.Div(id='intermediate-value', style={'display': 'none'})
])


# Dropdown Sort
@app.callback(
    Output('dropdown-div', 'style'),
    Input('dropdown-category', 'value')
)
def update_dropdown_sort(category_value):
    if category_value in ['movies_count', 'tvshows_count', 'budgets_max', 'revenues_max']:
        return {'display': 'none'}
    else:
        return {'width': '30%', 'display': 'inline-block'}


@app.callback(
    Output('dropdown-sort', 'options'),
    Input('dropdown-category', 'value'))
def update_sort_options(category_value):
    titles_options = OrderedDict({
        'relevance': 'Popularity: High to Low',
        'rating': 'Rating: High to Low',
        'votes': 'Votes: High to Low'
    })

    finance_options = OrderedDict({
        'relevance': 'Dollars: High to Low',
        'rating': 'Rating: High to Low',
        'votes': 'Votes: High to Low'
    })

    if category_value in ['top_movies', 'top_tvshows']:
        return [{'label': val, 'value': key} for key, val in titles_options.items()]
    elif category_value in ['top_budgets', 'top_revenues', 'top_budgets_revenues', 'top_revenues_budgets']:
        return [{'label': val, 'value': key} for key, val in finance_options.items()]
    else:
        raise PreventUpdate


# Year Slider
@app.callback(
    Output('intermediate-value', 'children'),
    Input('dropdown-category', 'value')
)
def get_years(category_value):
    if category_value in ['movies_count', 'tvshows_count', 'budgets_max', 'revenues_max']:
        no_data = {
            'min': 0,
            'max': 0,
            'marks': [0],
            'value': 0
        }

        return json.dumps(no_data)

    category_db = category_dbs[category_value]
    years_list = list(db[category_db].distinct('startYear'))
    sliced_list = years_list[-25:]
    print(sliced_list)

    slider_data = {
        'min': int(min(sliced_list)),
        'max': int(max(sliced_list)),
        'marks': sliced_list,
        'value': int(max(sliced_list))
    }

    return json.dumps(slider_data)


@app.callback(
    Output('year-slider', 'marks'),
    Input('intermediate-value', 'children')
)
def update_year_slider_marks(slider_json):
    slider_data = json.loads(slider_json)
    return {str(year): {'label': str(year), 'style': {'font-weight': 'bold'}} for year in slider_data['marks']}


@app.callback(
    Output('year-slider', 'min'),
    Input('intermediate-value', 'children')
)
def update_year_slider_min(slider_json):
    slider_data = json.loads(slider_json)
    return slider_data['min']


@app.callback(
    Output('year-slider', 'max'),
    Input('intermediate-value', 'children')
)
def update_year_slider_max(slider_json):
    slider_data = json.loads(slider_json)
    return slider_data['max']


@app.callback(
    Output('year-slider', 'value'),
    Input('intermediate-value', 'children')
)
def update_year_slider_value(slider_json):
    slider_data = json.loads(slider_json)
    return slider_data['max']


@app.callback(
    Output('radio-options', 'options'),
    Input('dropdown-category', 'value')
)
def update_radio_options(category_value):
    topk_dict = OrderedDict({
        10: 'Top 10',
        20: 'Top 20'
    })

    graph_dict = OrderedDict({
        'bar_graph': 'Bar Graph',
        'line_plot': 'Line Plot'
    })

    if category_value in ['movies_count', 'tvshows_count', 'budgets_max', 'revenues_max']:
        return [{'label': val, 'value': key} for key, val in graph_dict.items()]
    else:
        return [{'label': val, 'value': key} for key, val in topk_dict.items()]


@app.callback(
    Output('radio-options', 'value'),
    Input('radio-options', 'options')
)
def update_radio_value(available_options):
    return available_options[0]['value']


@app.callback(
    Output('radio-label', 'children'),
    Input('dropdown-category', 'value')
)
def update_radio_label(category_value):
    if category_value in ['movies_count', 'tvshows_count', 'budgets_max', 'revenues_max']:
        return 'Graph Type'
    else:
        return 'Show'


@app.callback(
    Output('slider-div', 'style'),
    Input('dropdown-category', 'value')
)
def update_slider(category_value):
    if category_value in ['movies_count', 'tvshows_count', 'budgets_max', 'revenues_max']:
        return {'display': 'none'}
    else:
        return {}


@app.callback(
    Output('movie-charts', 'figure'),
    [Input('dropdown-category', 'value'),
     Input('dropdown-sort', 'value'),
     Input('radio-options', 'value'),
     Input('year-slider', 'value')]
)
def update_figure(category_value, sort_value, options_value, selected_year):
    df = get_dataframe(category_value, sort_value, options_value, selected_year)
    print(df.head())
    fig = get_figure(df, category_value, options_value, selected_year)

    return fig


def get_dataframe(category, sort_type, max_results, year):
    try:
        category_db = category_dbs[category]
    except KeyError:
        return pd.DataFrame()

    year_query = {'startYear': str(year)}
    ratings_projection = {'_id': 0, 'primaryTitle': 1, 'averageRating': 1, 'numVotes': 1, 'totalRatings': 1}
    finance_projection = {'_id': 0, 'primaryTitle': 1, 'averageRating': 1, 'numVotes': 1, 'budget': 1, 'revenue': 1}
    count_projection = {'_id': 0, 'startYear': 1, 'count': 1}
    highest_budgets_pipeline = [
        {'$group': {'_id': "$startYear", 'max_budget': {'$max': '$budget'}}},
        {'$sort': {'_id': 1}}
    ]
    highest_revenues_pipeline = [
        {'$group': {'_id': "$startYear", 'max_revenue': {'$max': '$revenue'}}},
        {'$sort': {'_id': 1}}
    ]

    def get_items(projection, sort_field):
        try:
            if sort_type == 'rating':
                return db[category_db].find(year_query, projection).limit(max_results).sort('averageRating', -1)
            elif sort_type == 'votes':
                return db[category_db].find(year_query, projection).limit(max_results).sort('numVotes', -1)
            else:
                return db[category_db].find(year_query, projection).limit(max_results).sort(sort_field, -1)
        except TypeError:
            return pd.DataFrame()

    if category == 'top_movies' or category == 'top_tvshows':
        items = get_items(ratings_projection, 'totalRatings')

    elif category == 'top_budgets' or category == 'top_budgets_revenues':
        items = get_items(finance_projection, 'budget')

    elif category == 'top_revenues' or category == 'top_revenues_budgets':
        items = get_items(finance_projection, 'revenue')

    elif category == 'budgets_max':
        items = db[category_db].aggregate(highest_budgets_pipeline)

    elif category == 'revenues_max':
        items = db[category_db].aggregate(highest_revenues_pipeline)

    else:
        items = db[category_db].find({'titleType': category_fields[category]}, count_projection).sort('startYear', 1)

    return pd.DataFrame(items)


def get_figure(df, category, option, year):
    if df.empty:
        return NO_DATA_GRAPH

    graph_title = f'{category_dict[category]} of {year}'

    if category == 'top_movies' or category == 'top_tvshows':
        fig = px.bar(df, x='primaryTitle', y='numVotes', text='numVotes', color="averageRating",
                     color_continuous_scale='blues')
        fig.update_traces(texttemplate='%{text:.2s}', textposition='outside')

        # Edit the layout
        fig.update_layout(title_text=graph_title,
                          xaxis_title='Movie',
                          yaxis_title='Number of Votes',
                          coloraxis_colorbar_title='Average Rating')

    elif category == 'top_budgets' or category == 'top_revenues':
        fig = px.bar(df, x="primaryTitle", y=category_fields[category], text=category_fields[category], color="averageRating",
                     color_continuous_scale='blues')
        fig.update_traces(texttemplate='%{text:.2s}', textposition='outside')

        # Edit the layout
        fig.update_layout(title_text=graph_title,
                          xaxis_title='Movie',
                          yaxis_title='Dollars ($)',
                          coloraxis_colorbar_title='Average Rating')

    elif category == 'top_budgets_revenues' or category == 'top_revenues_budgets':
        fig = go.Figure([
            go.Bar(
                x=df["primaryTitle"],
                y=df["budget"],
                name='Budget',
                marker_color='indianred'
            ),
            go.Bar(
                x=df["primaryTitle"],
                y=df["revenue"],
                name='Revenue',
                marker_color='rgb(27,158,119)'
                # marker_color='#00CC96'
            )
        ])

        # Edit the layout
        fig.update_layout(title_text=graph_title,
                          xaxis_title='Movie',
                          yaxis_title='Dollars ($)',
                          barmode='group')

    elif category == 'budgets_max' or category == 'revenues_max':
        if option == 'bar_graph':
            fig = px.bar(df, x='_id', y=category_fields[category])
        elif option == 'line_plot':
            fig = px.line(df, x='_id', y=category_fields[category])

        # Edit the layout
        try:
            fig.update_traces(marker_color='#3366CC')
            fig.update_layout(title_text=category_dict[category],
                              xaxis_title='Year',
                              yaxis_title='Dollars ($)')
        except UnboundLocalError:
            return NO_DATA_GRAPH

    else:
        if option == 'bar_graph':
            fig = px.bar(df, x='startYear', y='count')
        elif option == 'line_plot':
            fig = px.line(df, x='startYear', y='count')

        # Edit the layout
        try:
            fig.update_traces(marker_color='#3366CC')
            fig.update_layout(title_text=category_dict[category],
                              xaxis_title='Year',
                              yaxis_title='Number of Titles')
        except UnboundLocalError:
            return NO_DATA_GRAPH

    try:
        fig.update_layout(height=550)
    except UnboundLocalError:
        return NO_DATA_GRAPH

    return fig


if __name__ == '__main__':
    app.run_server(debug=True)
