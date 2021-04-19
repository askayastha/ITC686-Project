from connect import Connect
import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.express as px
import pandas as pd
from dash.dependencies import Input, Output
from collections import OrderedDict
import json

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

connection = Connect.get_connection()
print(connection.list_database_names())

# creating or accessing a new database
db = connection["imdb_database"]

category_dict = OrderedDict({
    'top_movies': 'Top Movies',
    'top_tvshows': 'Top TV Shows',
    'top_budgets': 'Top Movie Budgets',
    'top_revenues': 'Top Movie Revenues',
    'movies_count': 'Number of Movies per Year',
    'tvshows_count': 'Number of TV Shows per Year',
    'budgets_max': 'Highest Budget per Year',
    'revenues_max': 'Highest Revenue per Year'
})

title_values = {
    'movies_count': 'movie',
    'tvshows_count': 'tvSeries'
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
        ], style={'width': '30%', 'display': 'inline-block'}),
        html.Div([
            html.Label('Sort By', style={'fontWeight': '600'}),
            dcc.Dropdown(
                id='dropdown-sort',
                options=[
                    {'label': 'Relevance: High to Low', 'value': 'relevance'},
                    {'label': 'Rating: High to Low', 'value': 'rating'},
                    {'label': 'Votes: High to Low', 'value': 'votes'}
                ],
                value='relevance',
                searchable=False,
                clearable=False
            )
        ], id='dropdown-div', style={'width': '30%', 'display': 'inline-block'}),
        html.Div([
            html.Label(id='radio-label', style={'fontWeight': '600'}),
            dcc.RadioItems(
                id='radio-options',
                # options=[{'label': f'Top {i}', 'value': i} for i in [10, 20]],
                # value=10,
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
        ], id='slider-div')
    ], style={'margin-left': '10%', 'margin-right': '10%'}),
    html.Div(id='intermediate-value', style={'display': 'none'})
])


@app.callback(
    Output('intermediate-value', 'children'),
    Input('dropdown-category', 'value'))
def get_years(category_value):
    years_list = list(db[category_value].distinct('startYear'))
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
    Output('dropdown-div', 'style'),
    Input('dropdown-category', 'value')
)
def update_dropdown_sort(category_value):
    if category_value in ['movies_count', 'tvshows_count']:
        return {'display': 'none'}
    else:
        return {'width': '30%', 'display': 'inline-block'}


@app.callback(
    Output('year-slider', 'marks'),
    Input('intermediate-value', 'children'))
def update_year_slider_marks(slider_json):
    slider_data = json.loads(slider_json)
    return {str(year): str(year) for year in slider_data['marks']}


@app.callback(
    Output('year-slider', 'min'),
    Input('intermediate-value', 'children'))
def update_year_slider_min(slider_json):
    slider_data = json.loads(slider_json)
    return slider_data['min']


@app.callback(
    Output('year-slider', 'max'),
    Input('intermediate-value', 'children'))
def update_year_slider_max(slider_json):
    slider_data = json.loads(slider_json)
    return slider_data['max']


@app.callback(
    Output('year-slider', 'value'),
    Input('intermediate-value', 'children'))
def update_year_slider_value(slider_json):
    slider_data = json.loads(slider_json)
    return slider_data['max']


@app.callback(
    Output('radio-options', 'options'),
    Input('dropdown-category', 'value'))
def update_radio_options(category_value):
    topk_dict = OrderedDict({
        10: 'Top 10',
        20: 'Top 20'
    })

    graph_dict = OrderedDict({
        'bar_graph': 'Bar Graph',
        'line_plot': 'Line Plot'
    })

    if category_value in ['movies_count', 'tvshows_count']:
        return [{'label': val, 'value': key} for key, val in graph_dict.items()]
    else:
        return [{'label': val, 'value': key} for key, val in topk_dict.items()]


@app.callback(
    Output('radio-options', 'value'),
    Input('radio-options', 'options'))
def update_radio_value(available_options):
    return available_options[0]['value']


@app.callback(
    Output('radio-label', 'children'),
    Input('dropdown-category', 'value')
)
def update_radio_label(category_value):
    if category_value in ['movies_count', 'tvshows_count']:
        return 'Graph Type'
    else:
        return 'Show'


@app.callback(
    Output('slider-div', 'style'),
    Input('dropdown-category', 'value')
)
def update_slider(category_value):
    if category_value in ['movies_count', 'tvshows_count']:
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
    year_query = {'startYear': str(selected_year)}
    ratings_projection = {'_id': 0, 'primaryTitle': 1, 'averageRating': 1, 'numVotes': 1, 'totalRatings': 1}
    finance_projection = {'_id': 0, 'primaryTitle': 1, 'averageRating': 1, 'numVotes': 1, 'budget': 1, 'revenue': 1}
    count_projection = {'_id': 0, 'startYear': 1, 'count': 1}

    graph_title = f'{category_dict[category_value]} of {selected_year}'

    if category_value in ['movies_count', 'tvshows_count']:
        title_counts = db['titles_count'].find({'titleType': title_values[category_value]}, count_projection).sort('startYear', 1)
        df = pd.DataFrame(title_counts)
        print(df.head())
        fig = get_figure(df, options_value, category_value)

        return fig
    elif category_value in ['top_budgets', 'top_revenues']:
        top_items = db[category_value].find(year_query, finance_projection).limit(options_value).sort('revenue', -1)

        df = pd.DataFrame(list(top_items))
        print(df.head())
        fig = px.bar(df, x="primaryTitle", y="revenue", color="averageRating", title=graph_title,
                     color_continuous_scale='purples')
        fig.update_layout(height=500)

        return fig
    else:
        if sort_value == 'rating':
            top_items = db[category_value].find(year_query, ratings_projection).limit(options_value).sort('averageRating', -1)
        elif sort_value == 'votes':
            top_items = db[category_value].find(year_query, ratings_projection).limit(options_value).sort('numVotes', -1)
        else:
            top_items = db[category_value].find(year_query, ratings_projection).limit(options_value).sort('totalRatings', -1)

        df = pd.DataFrame(list(top_items))
        print(df.head())
        title = f'{category_dict[category_value]} of {selected_year}'
        fig = px.bar(df, x="primaryTitle", y="numVotes", color="averageRating", title=graph_title,
                     color_continuous_scale='purples')
        fig.update_layout(height=500)

        return fig


def get_figure(df, options_value, category_value):
    if options_value == 'bar_graph':
        fig = px.bar(df, x="startYear", y="count", title=category_dict[category_value])
    elif options_value == 'line_plot':
        fig = px.line(df, x="startYear", y="count", title=category_dict[category_value])
    fig.update_layout(height=500)

    return fig


if __name__ == '__main__':
    app.run_server(debug=True)
