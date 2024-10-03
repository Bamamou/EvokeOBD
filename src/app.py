# Install the required libraries if not already installed
# !pip install dash pandas dash-bootstrap-components
import dash
from dash import html, dcc, Input, Output, State
import pandas as pd
import io
import base64
import plotly.express as px
import plotly.graph_objs as go
import dash_bootstrap_components as dbc
from plotly.subplots import make_subplots
import numpy as np
import dash_daq as daq

# Initialize the Dash app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server
app.title ="EvokeOBD"
colors = {
    'background': '#202020',
    'papercolor': '#202020',
    'text': '#7FDBFF'
}
picker_style = {'float': 'left', 'margin': 'auto'}
drop_down_icon = html.I(className="bi bi-chevron-double-down me-2")
# Define the app layout
app.layout = html.Div([
    html.H1("Evoke Motorcycles OBD analyser", style={'textAlign': 'center', 'color': colors["text"]}, className="bg-primary text-white text-center p-3 h3 mb-2 "),
    dcc.Upload(
        id="upload-data",
        children=html.Div([
            "Drag and drop or click to select an OBD file"
        ]),
        style={
            "width": "50%",
            "height": "60px",
            "lineHeight": "60px",
            "borderWidth": "1px",
            "borderStyle": "dashed",
            "borderRadius": "5px",
            "textAlign": "center",
            "margin": "10px auto",
        },
        multiple=False
    ),
    dcc.Dropdown(
        id="column-dropdown",
        options=[],
        placeholder="Select a data",
        #drop_down_icon,  
       # color = "primary", className ="me-2",
        maxHeight=300,
        #multi=True,
        style={"width": "50%", "margin": "10px auto"," font-size": "16px"},
        clearable=True,
        searchable=True
    ),
    dcc.Graph(id="data-plot"),
    # Not critcal and can be remove the color picker is not needed
    dcc.Dropdown(
        id='dropdown',
        multi=True,
        style={"width": "50%", "margin": "10px auto"," font-size": "16px"},
        searchable=True
        ),
        
    dcc.Graph(id='subplot'),
    daq.ColorPicker(
        id='font', label='Font Color', size=150,
        style=picker_style, value=dict(hex='#1876AE')),
    daq.ColorPicker(
        id='title', label='Title Color', size=150,
        style=picker_style, value=dict(hex='#1876AE')),
])

# Define callback to handle file upload
@app.callback(
    Output("column-dropdown", "options"),
    Output("dropdown", "options"),
    Output("column-dropdown", "value"),
    Input("upload-data", "contents"),
    State("upload-data", "filename"),

)
def update_uploaded_file(contents, filename):
    if contents is None:
        return [], [], None

    # Read the uploaded CSV file
    content_type, content_string = contents.split(",")
    decoded = base64.b64decode(content_string)
    df = pd.read_csv(io.StringIO(decoded.decode("utf-8")))
       # Filter data based on the selected column
    block0_index = None
    for row_idx, row in df.iterrows():
        for col_idx, cell_value in enumerate(row):
            if isinstance(cell_value, str) and "block0" in cell_value.lower():
                block0_index = row_idx
                break
        if block0_index is not None:
            break

    if block0_index is not None:
            # Create a new DataFrame with data after 'block0'
        df = df.iloc[block0_index + 1:]


    for col in df.columns:
            df =df[col].str.split(';', expand=True)
    # keep only the colunm from 1 to 30
    df = df.iloc[:, 1:31] 
    # Remove all data where there is an empty space 
    df.dropna( 
            how='all',
            axis=0,
            inplace= True)
    def to_float(x):
        return float(x) if x != '' else np.nan
        # Apply the conversion function to the entire DataFrame
    df = df.map(to_float)
    #voltage convertion
   # df[13] =df[13].div(10)   # BMS pack voltgae 
    df[19] =df[10].div(19)   #ECU supply voltage
    df[14] =(df[14]+200).div(100) # Highest cell voltage 
    df[15] =(df[15]+200).div(100) # HLowestighest cell voltage 
    df.rename(columns = {1:'Odometer', 2:'Trip', 3:'Speed kmh', 4:'Is in Reverse', 5:'Riding Mode',  6:'MCU Current',  7:'BMS Current', 8:'Vehicle status byte1', 9:'Vehicle status byte2', 10:'Throttle',
                            11:'MCU Temp', 12:'Motor temp', 13:'Pack Voltage',  14: 'BMS Cell Highest Voltage value', 15: 'BMS Cell Lowest Voltage value', 16:'SOC', 17:'RPM', 18:'Avg MOSTFet temp', 19: '12V voltage', 20:'Charger Volt', 21:'Charger Current', 22: 'Num Ative ERROR', 23: 'Sum Active ERROR', 24: 'Input Head light', 25: 'Turn left', 26: 'Turn Right', 27:'Mode Switch', 27: 'Kick Stand', 28: 'Kill switch', 29:'Key', 30:'Brake'}, inplace = True)

    # Get column names for dropdown options
    column_options = [{"label": col, "value": col} for col in df.columns]
    column_option = [{"label": col, "value": col} for col in df.columns]

    return column_options, column_option, column_options[0]["value"]

# Define callback to filter data based on selected column
@app.callback(
    Output("data-plot", "figure"),
    Input("column-dropdown", "value"),
    State("upload-data", "contents"),
    # Can be removed if the color picker is not needed
    Input("font", 'value'),
    Input("title", 'value')
)
def update_plot(selected_column, contents, font_color, title_color):
    if contents is None:
        return {}

    # Read the uploaded CSV file
    content_type, content_string = contents.split(",")
    decoded = base64.b64decode(content_string)
    df = pd.read_csv(io.StringIO(decoded.decode("utf-8")))
       # Filter data based on the selected column
    block0_index = None
    for row_idx, row in df.iterrows():
        for col_idx, cell_value in enumerate(row):
            if isinstance(cell_value, str) and "block0" in cell_value.lower():
                block0_index = row_idx
                break
        if block0_index is not None:
            break
    
    if block0_index is not None:
            # Create a new DataFrame with data after 'block0'
        df = df.iloc[block0_index + 1:]


    for col in df.columns:
            df =df[col].str.split(';', expand=True)
    # keep only the colunm from 1 to 30
    df = df.iloc[:, 1:31] 
    # Remove all data where there is an empty space 
    df.dropna( 
            how='all',
            axis=0,
            inplace= True)
    def to_float(x):
        return float(x) if x != '' else np.nan
        # Apply the conversion function to the entire DataFrame
    df = df.map(to_float)
      #voltage convertion
   # df[13] =df[13].div(10)   # BMS pack voltgae 
    df[19] =df[10].div(19)   #ECU supply voltage
    df[14] =(df[14]+200).div(100) # Highest cell voltage 
    df[15] =(df[15]+200).div(100) # HLowestighest cell voltage 
    
    df.rename(columns = {1:'Odometer', 2:'Trip', 3:'Speed kmh', 4:'Is in Reverse', 5:'Riding Mode',  6:'MCU Current',  7:'BMS Current', 8:'Vehicle status byte1', 9:'Vehicle status byte2', 10:'Throttle',
                            11:'MCU Temp', 12:'Motor temp', 13:'Pack Voltage',  14: 'BMS Cell Highest Voltage value', 15: 'BMS Cell Lowest Voltage value', 16:'SOC', 17:'RPM', 18:'Avg MOSTFet temp', 19: '12V voltage', 20:'Charger Volt', 21:'Charger Current', 22: 'Num Ative ERROR', 23: 'Sum Active ERROR', 24: 'Input Head light', 25: 'Turn left', 26: 'Turn Right', 27:'Mode Switch', 27: 'Kick Stand', 28: 'Kill switch', 29:'Key', 30:'Brake'}, inplace = True)
 
    # Create a scatter plot
   # fig =  px.line(df, x="selected_column", y=selected_column)
    fig = px.line(df, x=df.index, y=selected_column, title= f"Plot of {selected_column} over time")
     # Let's give some color to our plot
    fig.update_layout(
    plot_bgcolor ='#121212',    # The bg of the plot
    paper_bgcolor = '#121212',  # The bg of the paper 
    font_color=font_color['hex'],
    title_font_color=title_color['hex'],
   # font_color = '#1876AE',      # The text on the plot (Inside the plot only)
    font_family="Times new roman", # font 
    font_size = 18
    )
   
           
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(showgrid=False)

    return fig

# ============================ Section of the subplots =============================

# Callback to update the subplot
@app.callback(
Output('subplot', 'figure'),
[Input("dropdown", "value")],
[State("upload-data", "contents")]
)
def update_subplot(selected_column, contents):
  
    if selected_column and contents:
        # Read the uploaded file
       # Read the uploaded CSV file
        content_type, content_string = contents.split(",")
        decoded = base64.b64decode(content_string)
        df = pd.read_csv(io.StringIO(decoded.decode("utf-8")))
        # Filter data based on the selected column
        block0_index = None
        for row_idx, row in df.iterrows():
            for col_idx, cell_value in enumerate(row):
                if isinstance(cell_value, str) and "block0" in cell_value.lower():
                    block0_index = row_idx
                    break
            if block0_index is not None:
                break
        
        if block0_index is not None:
                # Create a new DataFrame with data after 'block0'
            df = df.iloc[block0_index + 1:]


        for col in df.columns:
                df =df[col].str.split(';', expand=True)
        # keep only the colunm from 1 to 30
        df = df.iloc[:, 1:31] 
        # Remove all data where there is an empty space 
        df.dropna( 
                how='all',
                axis=0,
                inplace= True)
        def to_float(x):
            return float(x) if x != '' else np.nan
            # Apply the conversion function to the entire DataFrame
        df = df.map(to_float)
        #voltage convertion
    # df[13] =df[13].div(10)   # BMS pack voltgae 
        df[19] =df[10].div(19)   #ECU supply voltage
        df[14] =(df[14]+200).div(100) # Highest cell voltage 
        df[15] =(df[15]+200).div(100) # HLowestighest cell voltage 
        
        df.rename(columns = {1:'Odometer', 2:'Trip', 3:'Speed kmh', 4:'Is in Reverse', 5:'Riding Mode',  6:'MCU Current',  7:'BMS Current', 8:'Vehicle status byte1', 9:'Vehicle status byte2', 10:'Throttle',
                                11:'MCU Temp', 12:'Motor temp', 13:'Pack Voltage',  14: 'BMS Cell Highest Voltage value', 15: 'BMS Cell Lowest Voltage value', 16:'SOC', 17:'RPM', 18:'Avg MOSTFet temp', 19: '12V voltage', 20:'Charger Volt', 21:'Charger Current', 22: 'Num Ative ERROR', 23: 'Sum Active ERROR', 24: 'Input Head light', 25: 'Turn left', 26: 'Turn Right', 27:'Mode Switch', 27: 'Kick Stand', 28: 'Kill switch', 29:'Key', 30:'Brake'}, inplace = True)

    
        subplots = make_subplots(rows=4, cols=1, shared_xaxes=True, subplot_titles=selected_column, print_grid=False, horizontal_spacing=0.015,)

        for i, col in enumerate(selected_column[:4]):
            subplots.add_trace(go.Scatter(x=df.index, y=df[col], mode='lines', name=col),
                row=i+1, col=1
        )
    # Add empty subplots if fewer than 3 columns are selected
 # Add empty subplots if fewer than 3 columns are selected
        for i in range(len(selected_column), 1):
            subplots.add_trace(go.Scatter(x=[], y=[]), row=i+1, col=1)
            #subplots.update_layout( title_text="Subplot of Selected Columns", plot_bgcolor ='#121212',   paper_bgcolor = '#121212',  font_color = '#1876AE'  )
            subplots.update_layout(
                print_grid=False,
                height=1500,
                width=600,
                autosize=False,
                plot_bgcolor ='#121212',    # The bg of the plot
                paper_bgcolor = '#121212',  # The bg of the paper 
                # font_color=font_color['hex'],
                # title_font_color=title_color['hex'],
            # font_color = '#1876AE',      # The text on the plot (Inside the plot only)
                font_family="Times new roman", # font 
                font_size = 18 )
    
        return subplots
    else:
        return {}

if __name__ == "__main__":
    app.run_server(debug=True)
