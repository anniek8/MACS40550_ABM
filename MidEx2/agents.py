from mesa import Agent

class StandingAgent(Agent):
    # Initiate agent instance, inherit model trait from parent class
    def __init__(self, model, quality, threshold):
        super().__init__(model)
        # Set agent type
        self.quality = quality # "Let q_ij ∈ Q_ij = [0,1] represent the quality signal received by the audience member seated in the ith row and jth seat."
        self.threshold = threshold # "Each audience member possesses an exogenous threshold level"

        # period 0: based purely on personal quality assessment
        self.standing = self.quality >= self.threshold # "if q_ij >= T_ij, she stands immediately."
        # next_standing
        # a staging variable required for sync mode
        # all agents must compute their next state before anyone commits, so they all see the same world-state. Without this two-phase design,
        # earlier agents in the loop would affect later agents' decisions, violating the "update in unison" requirement.
        self.next_standing = self.standing 

    def get_neighbors(self):
        # two neighborhood types: five neighbors/cones
        x, y = self.pos
        w, h = self.model.grid.width, self.model.grid.height
        candidates = set()

        # both types include two side seats: left, right
        for dx in (-1, 1):
            nx = x + dx
            if 0 <= nx < w:
                candidates.add((nx, y))

        if self.model.neighborhood_type == "five":
            # three seats in single row directly ahead
            if y < h - 1:
                for dx in (-1, 0, 1):
                    nx = x + dx
                    if 0 <= nx < w:
                        candidates.add((nx, y + 1)) # y + 1 == toward stage, the paper did not specified

        elif self.model.neighborhood_type == "cone":
            # Row d ahead contributes seats centred on agent
            # cone diagram in paper: row 1 = 3, row 2 = 5, row 3 = 7 
            for d in range(1, h - y): 
                ny = y + d
                for dx in range(-d, d +1 ):
                    nx = x + dx
                    if 0 <= nx < w:
                        candidates.add((nx, ny))

        # agent objects from all valid positions
        neighbors = []
        for pos in candidates:
            neighbors.extend(self.model.grid.get_cell_list_contents(pos))
        return neighbors

    def decide_next_standing(self):
        # "Each audience member uses a majority rule heuristic—if a majority of the people that she sees are standing, she stands, if not she sits"
        neighbors = self.get_neighbors()

        if not neighbors:
            # no visible neighbours, hold current state
            self.next_standing = self.standing
            return
        
        n = sum(1 for n in neighbors if n.standing)
        total = len(neighbors)

        if n > total / 2:
            self.next_standing = True
        elif n < total / 2:
            self.next_standing = False
        else:
            # tie: equal probability
            self.next_standing = self.random.random() < 0.5

    def apply_decision(self):
        # commit stage decision to live state
        # called as second pass in sync after all agents have run decide_next_standing()to ensure the true simultaneous update
        # in async mode, called immediately after decide_next_standing() within same agent step()
        self.standing = self.next_standing

    def step(self):
        # for async_random and async_incentive
        # agent decide and commit before next one step
        self.decide_next_standing()
        self.apply_decision()