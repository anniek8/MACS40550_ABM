import mesa
import math
import solara
import networkx as nx
from matplotlib.figure import Figure
from model import ScarcityModel, number_successful, number_failed
from agents import State
from mesa.visualization import (
    Slider, 
    SolaraViz, 
    make_plot_component)
from mesa.visualization.utils import update_counter

# define model parameters
model_params = {
    "seed": {
        "type": "InputText",
        "value": 42,
        "label": "Random Seed",
    },
    "num_nodes": Slider(
        label="Number of Agents",
        value=100, min=20, max=150, step=5,
    ),
    "avg_node_degree": Slider(
        label="Avg Node Degree",
        value=4, min=2, max=10, step=1,
    ),
    "network_type": {
        "type": "Select",
        "value": "random",
        "values": ["random", "clustered"],
        "label": "Network Type",
    },
    "friend_ratio": Slider(
        label="Friend (Strong) Tie Ratio",
        value=0.3, min=0.0, max=1.0, step=0.05,
    ),
    "influencer_ratio": Slider(
        label="Influencer Ratio",
        value=0.05, min=0.0, max=0.2, step=0.01,
    ),
    "initial_enthusiast_ratio": Slider(
        label="Initial Enthusiast Ratio",
        value=0.1, min=0.0, max=0.5, step=0.05,
    ),
    "threshold_mean": Slider(
        label="Threshold Mean",
        value=0.6, min=0.1, max=0.9, step=0.05,
    ),
    "threshold_std": Slider(
        label="Threshold Std",
        value=0.15, min=0.0, max=0.4, step=0.05,
    ),
    "initial_supply": Slider(
        label="Initial Supply",
        value=40, min=5, max=100, step=5,
    ),
    "restock_rate": Slider(
        label="Restock Rate (fraction of initial)",
        value=0.2, min=0.0, max=1.0, step=0.05,
    ),
    "restock_interval": Slider(
        label="Restock Interval (steps)",
        value=5, min=1, max=20, step=1,
    ),
}

# map colors to agent status
STATE_COLORS = {
    State.INDIFFERENT: "gray", # not yet interested
    State.INTERESTED: "orange", # interest rising
    State.ACTIVE: "blue", # threshold crossed, trying to buy
    State.SUCCESSFUL: "green", # successfully purchased
    State.FAILED: "red", # attempted but supply exhausted
}

def agent_color(agent):
    return STATE_COLORS[agent.state]


# create custom figure to plot the network graph
@solara.component
def NetPlot(model):
    """
    Draw the social network with nodes colored by agent state.
    Influencer nodes are drawn larger. Edge thickness reflects tie strength.
    """
    # set this to update every turn, define it as mpl figure
    update_counter.get()
    fig = Figure(figsize=(7, 5))
    ax  = fig.subplots()

    # build node color list
    color_map = [agent_color(model.grid.get_cell_list_contents([n])[0])
                 for n in model.G.nodes()]
    
    # influencers drawn larger to make them visually distinct
    size_map  = [150 if model.grid.get_cell_list_contents([n])[0].is_influencer else 40
                 for n in model.G.nodes()]
    
    # draw network graph based on colors here
    nx.draw(
        model.G,
        ax = ax,
        pos = model.position,
        node_color = color_map,
        node_size = size_map,
        width = model.weights,
        edge_color = "#e0e0e0",
    )

    # Legend
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor="gray", label="Indifferent"),
        Patch(facecolor="orange", label="Interested"),
        Patch(facecolor="blue", label="Active"),
        Patch(facecolor="green", label="Successful"),
        Patch(facecolor="red", label="Failed"),
    ]
    ax.legend(handles=legend_elements, loc="upper left", fontsize=7, framealpha=0.8)
    ax.set_title("Consumer Network", fontsize=10)

    solara.FigureMatplotlib(fig)

# helper function adding axis titles and legend to line plots
def post_process_state_plot(ax):
    ax.set_ylim(ymin=0)
    ax.set_ylabel("Number of agents")
    ax.set_xlabel("Step")
    ax.legend(bbox_to_anchor=(1.05, 1.0), loc="upper left")

def post_process_supply_plot(ax):
    ax.set_ylim(ymin=0)
    ax.set_ylabel("Units remaining")
    ax.set_xlabel("Step")
    ax.legend(bbox_to_anchor=(1.05, 1.0), loc="upper left")

# make line plot showing state breakdown over time
StatePlot = make_plot_component(
    {"Interested": "orange",
     "Active": "blue",
     "Successful": "green",
     "Failed": "red",
    },
    post_process=post_process_state_plot,
)

# cascade size (Active + Successful) over time
CascadePlot = make_plot_component(
    {"Cascade_Size": "steelblue"},
    post_process=lambda ax: (
        ax.set_ylabel("Cascade size (Active + Successful)"),
        ax.set_xlabel("Step"),
    ),
)

# remaining supply over time
SupplyPlot = make_plot_component(
    {"Supply": "slategray"},
    post_process=post_process_supply_plot,
)

# get and display as text
def get_summary(model):
    successful = number_successful(model)
    failed = number_failed(model)
    supply = model.supply
    total = model.num_nodes
    return solara.Markdown(
        f"**Successful purchases:** {successful} / {total} agents | "
        f"**Failed attempts:** {failed} | "
        f"**Supply remaining:** {supply}"
    )

# initialize model instance
scarcity_model = ScarcityModel()

# define page components
page = SolaraViz(
    scarcity_model,
    components=[
        NetPlot,
        StatePlot,
        CascadePlot,
        SupplyPlot,
        get_summary,
    ],
    model_params=model_params,
    name="Social Contagion of Desire: Scarcity Cascade Model"
)