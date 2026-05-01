import solara
from model import StandingOvationModel
from mesa.visualization import (  
    SolaraViz,
    make_space_component,
    make_plot_component,
)
from mesa.visualization.components import AgentPortrayalStyle

## Define agent portrayal: color, shape, and size
# Modification: lightblue = standing, lightpink = seated
def agent_portrayal(agent):
    return AgentPortrayalStyle(
        color = "lightblue" if agent.standing else "lightpink",
        marker= "s",
        size= 100,
    )

## Enumerate variable parameters in model: seed, grid dimensions, population density, agent preferences, vision, and relative size of groups.
model_params = {
    "seed": {
        "type": "InputText",
        "value": 42,
        "label": "Random Seed",
    },
    # "Agents are seated in a rectangular auditorium with R rows and C seats per row."
    "width": {
        "type": "SliderInt",
        "value": 20,
        "label": "Width",
        "min": 5,
        "max": 100,
        "step": 1,
    },
    "height": {
        "type": "SliderInt",
        "value": 20,
        "label": "Height",
        "min": 5,
        "max": 100,
        "step": 1,
    },
    # Modification: paper does not specify quality distribution.
    # We use N(mean, std) clipped to [0,1].
    "quality_mean": {
        "type": "SliderFloat",
        "value": 0.5,
        "label": "Quality Mean",
        "min": 0,
        "max": 1,
        "step": 0.05,
    },
    "quality_std": {
        "type": "SliderFloat",
        "value": 0.2,
        "label": "Quality Std",
        "min": 0,
        "max": 0.5,
        "step": 0.05,
    },
    # "Each individual has an identical standing threshold of 0.5." (Section 6)
    # Modification: exposed as slider to allow exploration beyond paper's fixed value.
    "threshold": {
        "type": "SliderFloat",
        "value": 0.5,
        "label": "Threshold",
        "min": 0,
        "max": 1,
        "step": 0.05,
    },
    # two different neighborhood structure
    # "Five Neighbors" and "Cones"
    "neighborhood_type": {
        "type": "Select",
        "value": "five",
        "values": ["five", "cone"],
        "label": "Neighborhood Type",
    },
    # three different updating protocols
    # "Synchronous", "Asynchronous-Random", "Asynchronous-Incentive-Based"
    "update_type": {
        "type": "Select",
        "value": "sync",
        "values": ["sync", "async_random", "async_incentive"],
        "label": "Update Mode",
    }
}

# Instantiate model
standing_model = StandingOvationModel()

# Define standing over time plot
# percentage of audience standing over time
StandingPlot = make_plot_component({"pct_standing": "tab:red"})

# Define space component
# grid visualization of auditorium
# blue = standing, pink = seated
SpaceGraph = make_space_component(agent_portrayal, draw_grid=False)

# Instantiate page including all components
page = SolaraViz(
    standing_model,
    components=[SpaceGraph, StandingPlot],
    model_params=model_params,
    name="Standing Ovation Model",
)
# Return page
page
    
