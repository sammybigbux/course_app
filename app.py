import dash
from dash import dcc, html, no_update, dash_table
from dash.dependencies import Input, Output
import plotly.express as px
import pandas as pd
import dash_bootstrap_components as dbc
from ranker import Ranker
from functools import partial

# Sample data for the bar graphs
data = pd.DataFrame({
    "Category": ["A", "B", "C", "D"],
    "Value1": [10, 15, 7, 10],
    "Value2": [5, 3, 8, 12]
})

# Initialize the Dash app with a Bootstrap theme
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.SOLAR])

app.layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            html.Div([
                dcc.Markdown("""
                # Gen-AI Tool Recommender
                """, className="mb-3")
            ]),
            dcc.Tabs(id="tabs", value='tab-1', children=[
                dcc.Tab(label="About", value='tab-1', children=[
                    html.Div([
                        dcc.Markdown("""
                        ### How to Use This App

                        This application is designed to recommend a set of tools aimed at automating as much of your work as possible. To ensure the recommendations are tailored to your needs, please follow these steps:

                        1. **Budget Setup**: Navigate to the Budget tab. Input your budget constraints and indicate if you want the recommendations to include tools from the Copilot bundle. Press submit to confirm your settings.

                        2. **Automation Preferences**: Switch to the Automation tab. Here, you'll find questions regarding the amount of time you spend on various tasks each week. Your responses will help prioritize the types of tools that the app recommends for you.

                        3. **Quality Prioritization**: Visit the Quality tab. Fill out the questions regarding your priority for improving the quality of each area of work. This information is crucial for resolving tie-breakers among recommended tools.

                        4. **Review and Adjust**: After submitting all necessary information, return to the Budget tab to generate a report of your potential toolset. You can review and adjust your budget based on the recommendations provided.

                        5. **Results Analysis**: On the right side of the interface, you will see an analysis of the potential hours you can save by utilizing the recommended services. Below this, the quality scores for each recommended service are displayed, providing a qualitative measure of how much the product will improve the quality of your work.
                        """,
                        className="mb-3")
                    ])
                ]),
                dcc.Tab(label="Budget", value='tab-2', children=[
                    html.Div([
                        dcc.Markdown("""
                            ### Budget
                            """, className="mb-3"
                        ),
                        dbc.Label("What is your budget each month?"),
                        dbc.Input(id="budget", type="number", min=0, placeholder="Dollars per month", className="mb-2"),

                        dbc.Label("Copilot Pro (20$) contains several tools, would you like to consider this integration in the analysis?"),
                        dbc.Checkbox(id='checkbox', className='mb-2', label="Enable Copilot tools"),
                        html.Div(id='error-message', className='bg-danger'),
                        dbc.Button("Submit", id="submit-button-3", color="primary", n_clicks=0, className="mb-2"),
                        dbc.Button("Generate Report", id="generate-report-1", color="success", n_clicks=0, className="mb-2"),

                        html.Div(id='output-data-table', className='mb-2')
                    ])
                ]),
                dcc.Tab(label='Automation', value='tab-3', children=[
                    html.Div([
                        dcc.Markdown("""
                            ### How much time do you spend...
                            """, className="mb-3"
                        ),
                        dbc.Label("Reading or reviewing long documents"),
                        dbc.Input(id="input-1", type="number", min=0, placeholder="Hours per week", className="mb-2"),
                        
                        dbc.Label("Writing or reading through PowerPoints"),
                        dbc.Input(id="input-2", type="number", min=0, placeholder="Hours per week", className="mb-2"),

                        dbc.Label("Writing long texts (blog posts, emails, documents)"),
                        dbc.Input(id="input-3", type="number", min=0, placeholder="Hours per week", className="mb-2"),

                        dbc.Label("Scheduling and re-scheduling tasks or events"),
                        dbc.Input(id="input-4", type="number", min=0, placeholder="Hours per week", className="mb-2"),

                        dbc.Label("Recording, summarizing, or reviewing meeting notes"),
                        dbc.Input(id="input-5", type="number", min=0, placeholder="Hours per week", className="mb-2"),
                        
                        dbc.Label("Doing repetitive tasks that involve multiple web apps"),
                        dbc.Input(id="input-6", type="number", min=0, placeholder="Hours per week", className="mb-2"),

                        dbc.Button("Submit", id="submit-button", color="primary", n_clicks=0, className="mb-2"),
                    ])
                ]),
                dcc.Tab(label='Quality', value='tab-4', children=[
                    html.Div([
                        dcc.Markdown("""
                            ### How much do you...
                            """, className="mb-3"
                        ),
                        dbc.Label("Want to improve the quality of your understanding of long texts"),
                        dbc.Input(id="input-7", type="number", min=1, max=10, placeholder="Scale of 1-10", className="mb-2"),
                        
                        dbc.Label("Want to improve the quality of created PowerPoints"),
                        dbc.Input(id="input-8", type="number", min=1, max=10, placeholder="Scale of 1-10", className="mb-2"),

                        dbc.Label("Want to improve the quality of writing long texts (blog posts, emails, documents)"),
                        dbc.Input(id="input-9", type="number", min=1, max=10, placeholder="Scale of 1-10", className="mb-2"),

                        dbc.Label("Want to improve the quality of scheduling for tasks or events"),
                        dbc.Input(id="input-10", type="number", min=1, max=10, placeholder="Scale of 1-10", className="mb-2"),

                        dbc.Label("Want to improve the quality of recordings or summaries of meeting notes"),
                        dbc.Input(id="input-11", type="number", min=1, max=10, placeholder="Scale of 1-10", className="mb-2"),
                        
                        dbc.Label("Want to improve the quality of repetetive tasks that involve multiple web apps"),
                        dbc.Input(id="input-12", type="number", min=1, max=10, placeholder="Scale of 1-10", className="mb-2"),

                        dbc.Button("Submit", id="submit-button-2", color="primary", n_clicks=0, className="mb-2"),
                    ])
                ]),
            ]),
        ], width=5),
        
        dbc.Col([
            dcc.Graph(id="bar-graph-1"),
            dcc.Graph(id="bar-graph-2")
        ], width=7)
    ])
], fluid=True)

@app.callback(
    [Output("bar-graph-1", "figure"),
     Output("bar-graph-2", "figure"),
     Output('output-data-table', 'children'),
     Output('error-message', 'children')],
    [Input("submit-button", "n_clicks"), Input("submit-button-2", "n_clicks"),
     Input("submit-button-3", "n_clicks"), Input("generate-report-1", "n_clicks")],
    [dash.dependencies.State("input-1", "value"), dash.dependencies.State("input-2", "value"), 
     dash.dependencies.State("input-3", "value"), dash.dependencies.State("input-4", "value"),
     dash.dependencies.State("input-5", "value"), dash.dependencies.State("input-6", "value"),
     dash.dependencies.State("input-7", "value"), dash.dependencies.State("input-8", "value"),
     dash.dependencies.State("input-9", "value"), dash.dependencies.State("input-10", "value"),
     dash.dependencies.State("input-11", "value"), dash.dependencies.State("input-12", "value"),
     dash.dependencies.State("budget", "value"), dash.dependencies.State("budget", "value"),
     dash.dependencies.State('checkbox', 'value')]
)
def update_output(*args):
    ctx = dash.callback_context
    button_id = ctx.triggered[0]['prop_id'].split('.')[0] if ctx.triggered else None

    # Initialize custom layout
    custom_layout = {
        'height': 650,
        'plot_bgcolor': '#288cb4',
        'paper_bgcolor': '#002b36',
        'font': {'color': '#ffffff'},
        'title': {'x': 0.5},
        'xaxis': {'showgrid': False, 'gridcolor': '#666666'},
        'yaxis': {'showgrid': False, 'gridcolor': '#666666'}
    }

    # Initialize default data for graphs
    default_data_auto = pd.DataFrame({"Task": ["A"], "Hours saved": [0], "Remaining hours": [0]})
    default_data_qual = pd.DataFrame({"Service": ["A"], "Quality": [0]})

    # Initialize graphs with default data
    fig1 = px.bar(default_data_auto, x="Task", y=["Hours saved", "Remaining hours"], title="Time Saved", labels={"value": "Total Hours"})
    fig1.update_layout(**custom_layout)
    fig1.update_traces(marker=dict(line=dict(width=0)), texttemplate='%{y}', textposition='inside')
    fig1.update_layout(legend_title_text='')

    fig2 = px.bar(default_data_qual, x="Service", y="Quality", title="Quality Scores", labels={"Service": "Recommended Service"})
    fig2.update_layout(**custom_layout)

    default_report = 'Nothing to show'

    # Return early if no button was pressed yet
    if not ctx.triggered:
        return fig1, fig2, "No data submitted yet.", " "

    # Handling form inputs and button press
    keys = ["input-" + str(num) + ".value" for num in range(1,13)]
    input_n = [ctx.states[key] for key in keys]
    automation_vals, quality_vals = input_n[:len(input_n)//2], input_n[len(input_n)//2:]

    # Validation logic
    budget = ctx.states['budget.value']
    checkbox_checked = ctx.states['checkbox.value']
    error_message = " "
    if checkbox_checked and (budget is None or budget < 20):
        error_message = "If budget tracking is enabled, the budget must be at least $20."
        return fig1, fig2, "No data to display.", error_message

    elif checkbox_checked:
        budget -= 20

    # Process data and update graphs as necessary
    ranker = Ranker(budget, automation_vals, quality_vals, checkbox_checked)
    ranked_df = ranker.rank()
    ranked_df['Remaining hours'] = ranked_df['Hours spent'] - ranked_df['Hours saved']
    ranked_df.loc[ranked_df['selected'] == 0, 'Remaining hours'] = 0

    ranked_df['Hours saved'] = ranked_df['Hours saved'].apply(partial(round, ndigits=2))
    ranked_df['Remaining hours'] = ranked_df['Remaining hours'].apply(partial(round, ndigits=2))

    auto_bar = ranked_df[['Task', 'Hours saved', 'Remaining hours', 'selected']]
    qual_bar = ranked_df[['Service', 'Quality Score', 'selected']]

    def refine_auto_bar(df):
        # Initialize an empty list to store the indices of the rows to keep
        keep_indices = []
        
        # Group the DataFrame by 'Task'
        grouped = df.groupby('Task')
        
        for _, group in grouped:
            if len(group) == 1:
                # If there's only one entry for the task, keep it
                keep_indices.append(group.index[0])
            else:
                # If there are multiple entries for the task
                # Filter entries where 'Hours saved' > 0
                positive_hours_saved = group[group['Hours saved'] > 0]
                
                if not positive_hours_saved.empty:
                    # If there are entries with 'Hours saved' > 0, keep the first one
                    keep_indices.append(positive_hours_saved.index[0])
                else:
                    # If all entries have 'Hours saved' <= 0, keep the first one
                    keep_indices.append(group.index[0])
        
        # Create a new DataFrame with only the selected indices
        refined_df = df.loc[keep_indices].reset_index(drop=True)

        # Adding aggregate row
        refined_df = refined_df.append({'Task': 'Total',
            'Hours saved': df['Hours saved'].sum(),
            'Remaining hours': df['Remaining hours'].sum()},
            ignore_index=True)
        
        return refined_df
        
    def refine_quality_bar(df):
        df = df[df['selected']]
        return df[['Quality Score', 'Service']]

    auto_ready = refine_auto_bar(auto_bar)
    qual_ready = refine_quality_bar(qual_bar)

    default_report = "No data to show"

    if button_id in ["submit-button"]:
        fig1 = px.bar(auto_ready, x="Task", y=["Hours saved", "Remaining hours"], title="Time Saved", labels={"value": "Total Hours"})
        fig1.update_layout(**custom_layout)
        # Code for un-centering the title
        #   fig1.update_layout(
        #                     legend_title_text="",
        #                     yaxis_title="Total Hours",
        #                     title={
        #                         'text': 'Your Graph Title',
        #                         'x':0.45,  # Adjust this value to shift the title left (<0.5) or right (>0.5)
        #                         'xanchor': 'center',  # Ensures the title will still center at the new x position
        #                         'yanchor': 'top'
        #                     }
        #                 )

        return fig1, no_update, no_update, error_message
    elif button_id in ["submit-button-2"]:
        fig2 = px.bar(qual_ready, x="Service", y="Quality Score", title="Quality Scores", labels={"Service": "Recommended Service"})
        fig2.update_layout(**custom_layout)
        return no_update, fig2, no_update, error_message
    elif button_id in ['generate-report-1']:
        df = ranked_df[['Service', 'Hours saved', 'Remaining hours', 'Quality Score', 'selected']]
        df = df[df['selected']]
        df.drop('selected', axis=1, inplace=True)
        default_report = dash_table.DataTable(
            data=df.to_dict('records'),
            columns=[{"name": i, "id": i} for i in df.columns],
            style_table={
                'overflowX': 'auto',
                'width': '100%',  # Ensure the table uses the full width of its container
                'minWidth': '100%'
            },
            page_size=10,  # Add pagination
            page_action='native',  # Enables server-side pagination
            style_cell={
                'overflow': 'hidden',
                'textOverflow': 'ellipsis',
                'maxWidth': 0,
                'padding': '10px',  # Add padding for content inside cells for better readability
                'backgroundColor': '#343a40',  # Dark background for each cell
                'color': '#f8f9fa',  # Light text for readability
                'border': '1px solid #444'  # Slightly lighter border for subtle contrast
            },
            style_header={
                'backgroundColor': '#495057',  # Slightly lighter than cell background for distinction
                'fontWeight': 'bold',
                'color': '#f8f9fa',  # White text color for the header
                'border': '1px solid #444'
            },
            style_data={  # Style for the table's data cells
                'border': '1px solid #444',
                'backgroundColor': '#343a40',  # Same as cell background for consistency
                'color': '#f8f9fa'
            },
            style_as_list_view=True,  # Styles the table like a list view without vertical grid lines
        )

        return no_update, no_update, default_report, no_update
    
    else:
        fig1 = px.bar(auto_ready, x="Task", y=["Hours saved", "Remaining hours"], title="Time Saved", labels={"value": "Total Hours"})
        fig1.update_layout(**custom_layout)
        # Code for un-centering the title
        #   fig1.update_layout(
        #                     legend_title_text="",
        #                     yaxis_title="Total Hours",
        #                     title={
        #                         'text': 'Your Graph Title',
        #                         'x':0.45,  # Adjust this value to shift the title left (<0.5) or right (>0.5)
        #                         'xanchor': 'center',  # Ensures the title will still center at the new x position
        #                         'yanchor': 'top'
        #                     }
        #                 )
        fig2 = px.bar(qual_ready, x="Service", y="Quality Score", title="Quality Scores", labels={"Service": "Recommended Service"})
        fig2.update_layout(**custom_layout)
        return fig1, fig2, no_update, error_message

# Run the app
if __name__ == '__main__':
    app.run(debug=True)
