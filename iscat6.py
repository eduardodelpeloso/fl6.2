import dash
from jupyter_dash import JupyterDash
from dash import dcc
from dash import html
from dash.dependencies import Input, Output, State
import plotly.graph_objs as go
import pandas as pd
import base64
import io

app = JupyterDash(__name__)

app.layout = html.Div([
    html.H1("Scatter Plot with Binning"),

    dcc.Upload(
        id='upload-data',
        children=html.Div([
            'Drag and Drop or ',
            html.A('Select a CSV File')
        ]),
        style={
            'width': '100%',
            'height': '60px',
            'lineHeight': '60px',
            'borderWidth': '1px',
            'borderStyle': 'dashed',
            'borderRadius': '5px',
            'textAlign': 'center',
            'margin': '10px'
        },
        multiple=False
    ),

    dcc.Input(id='bin-size', type='number', value=1.0, placeholder='Enter bin size'),

    dcc.Dropdown(
        id='y-column-selector',
        options=[],
        value=None
    ),

    dcc.Checklist(
        id='log-scale',
        options=[
            {'label': 'Log X', 'value': 'x'},
            {'label': 'Log Y', 'value': 'y'}
        ],
        value=[]
    ),

    html.Button('Update Plot', id='submit-button'),

    dcc.Graph(id='scatter-plot')
])

@app.callback(
    Output('y-column-selector', 'options'),
    [Input('upload-data', 'contents')]
)
def update_dropdown_options(uploaded_content):
    if uploaded_content is not None:
        content_type, content_string = uploaded_content.split(',')
        decoded = base64.b64decode(content_string)
        try:
            data = pd.read_csv(io.StringIO(decoded.decode('utf-8')))
            return [{'label': col, 'value': idx} for idx, col in enumerate(data.columns) if idx != 0]
        except Exception as e:
            return [{'label': 'Error', 'value': 'Error'}]

    return []

@app.callback(
    Output('scatter-plot', 'figure'),
    [Input('submit-button', 'n_clicks')],
    [State('bin-size', 'value'),
     State('y-column-selector', 'value'),
     State('log-scale', 'value'),
     State('upload-data', 'contents')]
)
def update_plot(n_clicks, bin_value, y_col, log_values, uploaded_content):
    if log_values is None:
        log_values = []

    if uploaded_content is None:
        return go.Figure()

    content_type, content_string = uploaded_content.split(',')
    decoded = base64.b64decode(content_string)
    data = pd.read_csv(io.StringIO(decoded.decode('utf-8')))

    if data is None:
        return go.Figure()

    x_data = data[data.columns[0]]
    y_data = data.iloc[:, y_col]

    if bin_value and bin_value > 0:
        bins = pd.interval_range(start=x_data.min(), end=x_data.max(), freq=bin_value)
        grouped_data = y_data.groupby(pd.cut(x_data, bins)).mean()
        x_data_binned = [interval.mid for interval in grouped_data.index]
        y_data_binned = grouped_data.values
    else:
        x_data_binned = x_data
        y_data_binned = y_data

    fig = go.Figure(go.Scatter(x=x_data_binned, y=y_data_binned, mode='markers'))

    fig.update_layout(
        title="Scatter Plot with Binning",
        xaxis_title=data.columns[0],
        yaxis_title=data.columns[y_col],
        xaxis_type='log' if 'x' in log_values else 'linear',
        yaxis_type='log' if 'y' in log_values else 'linear'
    )

    return fig

if __name__ == "__main__":
    app.run_server(mode="inline")
