from mesa import Agent

class SchellingAgent(Agent):
    # Initiate agent instance, inherit model trait from parent class
    def __init__(self, model, agent_type):
        super().__init__(model)
        # Set agent type
        self.type = agent_type

        # Modification: assign a life stage randomly to each agent at initialization
        # "family": househoulds with children, prefer family-dense neighborhood
        # "young": young adults without children, prefer same group (original rule)
        # "elderly": retirees, prefer quiet, less-crowded areas
        self.life_stage = self.random.choice(["family", "young", "elderly"])

    # Define decision rule - varies by different life stages
    def move(self):
        # Get list of neighbors within range of sight
        neighbors = self.model.grid.get_neighbors(
            self.pos, moore = True, radius = self.model.radius, include_center = False)

        valid_neighbors = len(neighbors)

        # Compute satisfaction score [0,1] for each life stage
        if self.life_stage == "family":
            # family agents want to live near other families as well
            # score = 0: no family neighbors, score =1: all neighbors are families
            if valid_neighbors > 0:
                family_neighbors = len(
                    [n for n in neighbors if n.life_stage == "family"]
                )
                score = family_neighbors / valid_neighbors
            else:
                score = 0 # if no neighbors at all then it is 0

        elif self.life_stage == "young":
            # young agents is same as the original schelling rule that they prefer same agent type
            # baseline = unmodified model
            if valid_neighbors > 0:
                similar_neighbors = len(
                    [n for n in neighbors if n.type == self.type]
                )
                score = similar_neighbors / valid_neighbors
            else:
                score = 0

        else: 
            # means elderly, prefer low-density and more quiet surroundings
            # score = 1 - occupancy_rate: fewer neighbors meaning higher satisfaction
            # max_possible: total number of cells in Moore neighborhood
            max_possible = (2 * self.model.radius + 1) ** 2 - 1
            density = valid_neighbors / max_possible
            score = 1 - density # high density -> lower score -> more likely to move

        # unified decision rule
        # if score is below model threshold, move to random empty cell, otherwise count as happy
        if score < self.model.desired_score:
            self.model.grid.move_to_empty(self)
        else:
            self.model.happy += 1