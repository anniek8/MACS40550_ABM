from mesa import Model
from mesa.space import SingleGrid
from agents import StandingAgent
from mesa.datacollection import DataCollector

class StandingOvationModel(Model):
    # mesa singlegrid: width x height
    def __init__(self, width=20, height=20,
                 quality_mean=0.5, quality_std=0.2, threshold=0.5,
                 neighborhood_type="five", update_type="sync", 
                 seed=None):
        # ensure integer and inherit RNG from parent class
        if seed is not None:
            seed = int(seed)
        super().__init__(rng=seed)

        self.width = width
        self.height = height
        self.neighborhood_type = neighborhood_type # "five" or "cone"
        self.update_type = update_type # sync / async_random / async_incentive

        # Create grid
        # torus=False: auditorium has wall that edge agent cannot wrap around to other side
        self.grid = SingleGrid(width, height, torus = False)

        ## Define data collector
        # standing: raw count S^t notation
        # pct_standing: plot across grid size
        self.datacollector = DataCollector(
            model_reporters = {
                "standing" : "n_standing",
                "pct_standing" : lambda m : (m.n_standing / len(m.agents)) * 100
                if len(m.agents) > 0
                else 0
            }
        )

        ## Place agents randomly around the grid, randomly assigning them to agent types.
        # MODIFICATION: paper states quality lies in [0,1] but does not specify the distribution. 
        # Use N(quality_mean, quality_std) clipped to [0,1] to allow heterogeneity controlled by the user via sliders.
        for _, pos in self.grid.coord_iter():
            q = max(0, min(1, self.random.gauss(quality_mean, quality_std)))
            agent = StandingAgent(self, q, threshold)
            self.grid.place_agent(agent, pos)

        # total number of standing agents for data collection
        self.n_standing = 0
        # period 0 standing count before first data collection
        self._update_standing_count()

        ## Initialize datacollector
        # collect period 0 state before any stepping
        self.datacollector.collect(self)

    def _update_standing_count(self):
        # recount after stepping
        self.n_standing = sum(1 for a in self.agents if a.standing)

    def _pressure(self, agent):
        # “agents surrounded by agents taking the opposite action are the first to update"
        # pressure = | own_state - fraction_of_neighbors_standing|
        # perfectly aligned with neighborhood: 0.0, completely opposite to neighborhood: 1.0
        # higher pressure -> agents update first in async_incentive
        neighbors = agent.get_neighbors()
        if not neighbors:
            return 0.0
        frac = sum(1 for n in neighbors if n.standing) / len(neighbors)
        own = 1.0 if agent.standing else 0.0
        return abs(frac - own)
    
    def step(self):
        if self.update_type == "sync":
            # "At the start of each discrete time period, all agents update in unison."
            # every agent compute next state from current grid
            # every agent commit simultaneously
            # ensure no agent see partially update scenario
            self.agents.do("decide_next_standing")
            self.agents.do("apply_decision")

        elif self.update_type == "async_random":
            # "Within each discrete time period, the agents are permuted into a random order and updated in that order."
            # each agent decide and apply before next one is update
            # later agent see decision of the earlier agents
            self.agents.shuffle_do("step")

        elif self.update_type == "async_incentive":
            # "Within each discrete time period, the agents update one at a time based on an explicit ordering rule 
            # that has agents who are least like the people that surround them move first."
            # agents sorted by descending pressure
            ordered = sorted(self.agents, key=self._pressure, reverse=True)
            for agent in ordered:
                agent.step()

        # update standing count and record data
        self._update_standing_count()
        self.datacollector.collect(self)