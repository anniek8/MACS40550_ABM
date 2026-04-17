import solara
from model import SchellingModel
from mesa.visualization import (  
    SolaraViz,
    make_space_component,
    make_plot_component,
)
from mesa.visualization.components import AgentPortrayalStyle

## Define agent portrayal: color, shape, and size
# Modification: agent color reflect different life stage rather than agent type
# easier to visualize the pattern by life stage
def agent_portrayal(agent):
    if agent.life_stage == "family":
        color = "forestgreen"
    elif agent.life_stage == "young":
        color = "royalblue"
    else: #elderly
        color = "darkorange"
    return AgentPortrayalStyle(
        color = color,
        marker= "s",
        size= 75,
    )

## Enumerate variable parameters in model: seed, grid dimensions, population density, agent preferences, vision, and relative size of groups.
model_params = {
    "seed": {
        "type": "InputText",
        "value": 42,
        "label": "Random Seed",
    },
    "width": {
        "type": "SliderInt",
        "value": 30,
        "label": "Width",
        "min": 5,
        "max": 100,
        "step": 1,
    },
    "height": {
        "type": "SliderInt",
        "value": 30,
        "label": "Height",
        "min": 5,
        "max": 100,
        "step": 1,
    },
    "density": {
        "type": "SliderFloat",
        "value": 0.7,
        "label": "Population Density",
        "min": 0,
        "max": 1,
        "step": 0.01,
    },
    # Modification: new slider shows the unified desired_score threshold.
    # higher values mean agents are harder to satisfy and move more often
    "desired_score": {
        "type": "SliderFloat",
        "value": 0.5,
        "label": "Desired Score Threshold",
        "min": 0,
        "max": 1,
        "step": 0.01,
    },
    "group_one_share": {
        "type": "SliderFloat",
        "value": 0.7,
        "label": "Share Type 1 Agents",
        "min": 0,
        "max": 1,
        "step": 0.01,
    },
    "radius": {
        "type": "SliderInt",
        "value": 1,
        "label": "Vision Radius",
        "min": 1,
        "max": 5,
        "step": 1,
    },
}

## Instantiate model
schelling_model = SchellingModel()

## Define happiness over time plot
HappyPlot = make_plot_component({"share_happy": "tab:green"})

## Define space component
SpaceGraph = make_space_component(agent_portrayal, draw_grid=False)

## Instantiate page inclusing all components
# Modify name
page = SolaraViz(
    schelling_model,
    components=[SpaceGraph, HappyPlot],
    model_params=model_params,
    name="Schelling Segregation Model - Life Stage",
)
## Return page
page
    
