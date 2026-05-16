from enum import Enum
from mesa import Agent

#Define enumeration of susceptibility state
class State(Enum):
    INDIFFERENT = 0 # low interest, not yet influenced enough
    INTERESTED = 1 # interest rising but below purchase threshold
    ACTIVE = 2 # threshold crossed, attempting to purchase
    SUCCESSFUL = 3 # successfully purchased the product
    FAILED = 4 # attempted to purchase but supply was exhausted

class ConsumerAgent(Agent):
    """
    Represent individual consumer in the social network.
    Each agents had a continuous interest level and personal threshold.
    When observed neighbor interest exceeds threshold, agents join the purchasing queue.
    The tie strength for friend vs. stranger weights how much each neighbor's signal matters.
    """
    # define initiation of agents
    def __init__(
            self,
            model,
            initial_interest,
            threshold,
            is_influencer=False
    ):
        super().__init__(model)

        self.interest = initial_interest # continuous interest level [0, 1]
        self.threshold = threshold # personal threshold to become ACTIVE
        self.is_influencer = is_influencer # influencers have higher initial interest and more connections
        # assign initial state based on interest and threshold
        self._update_state()

    # map continuous interest to discrete state label
    def _update_state(self):
        if self.state_is_terminal():
            return
        if self.interest >= self.threshold:
            self.state = State.ACTIVE
        elif self.interest >= 0.3:
            self.state = State.INTERESTED
        else:
            self.state = State.INDIFFERENT

    # return True if agent has already bought or failed
    def state_is_terminal(self):
        return hasattr(self, "state") and self.state in (State.SUCCESSFUL, State.FAILED)
        
    # core behavior of agents
    def get_weighted_neighbor_signal(self):
        """
        Calculate the weighted average interest signal from all neighbors.
        """
        neighbors_nodes = self.model.grid.get_neighborhood(self.pos, include_center=False)
        neighbors = self.model.grid.get_cell_list_contents(neighbors_nodes)

        if not neighbors:
            return 0.0
            
        total_weight = 0.0
        weighted_signal = 0.0

        for neighbor in neighbors:
            # retrieve tie strength assigned at initialization stage
            edge_data = self.model.G.edges[self.pos, neighbor.pos]
            tie_weight = edge_data.get("tie_weight", 0.2)
            # map neighbor state to numeric signal
            if neighbor.state in (State.ACTIVE, State.SUCCESSFUL):
                signal = 1.0 # strong positive signal: visibly wanting/buying
            elif neighbor.state == State.FAILED:
                signal = -0.2 # small negative signal: visible failure discourages
            else:
                signal = neighbor.interest # intermediate signal: raw interest level

            weighted_signal += tie_weight * signal
            total_weight += tie_weight

            return weighted_signal / total_weight if total_weight > 0 else 0.0

    def update_interest(self):
        signal = self.get_weighted_neighbor_signal()
        learning_rate = 0.3
        self.interest = max(0.0, min(1.0,
                                        self.interest + learning_rate * (signal - self.interest)))
        self._update_state()

    def try_purchase(self):
        """
        ACTIVE agents attempt to buy. 
        Supply is shared across all agents and decremented first-come-first-served in the shuffled step order.
        """
        if self.model.supply > 0:
            self.model.supply -= 1
            self.state = State.SUCCESSFUL
        else:
            self.state = State.FAILED

    # agent step
    def step(self):
        # terminal agents do not act further
        if self.state_is_terminal():
            return
        # observe neighbors and update interest level
        self.update_interest()
        # if interest cross threshold, attempt to purchase
        if self.state == State.ACTIVE:
            self.try_purchase()