import mesa
from mesa import Model
from mesa.space import NetworkGrid
from mesa.datacollection import DataCollector
import networkx as nx
from agents import ConsumerAgent, State

# Define helper functions for DataCollector

def count_state(model, state):
    return sum(1 for a in model.grid.get_all_cell_contents() if a.state is state)

def number_indifferent(model):
    return count_state(model, State.INDIFFERENT)

def number_interested(model):
    return count_state(model, State.INTERESTED)

def number_active(model):
    return count_state(model, State.ACTIVE)

def number_successful(model):
    return count_state(model, State.SUCCESSFUL)

def number_failed(model):
    return count_state(model, State.FAILED)


class ScarcityModel(Model):
    # define initiation
    def __init__(
        self,
        num_nodes=100,
        avg_node_degree=6,
        network_type="random",
        friend_ratio=0.3,
        influencer_ratio=0.05,
        initial_enthusiast_ratio=0.1,
        threshold_mean=0.6,
        threshold_std=0.15,
        initial_supply=40,
        restock_rate=0.2,
        restock_interval=5,
        seed=None,
    ):
        if seed is not None:
            seed = int(seed)
        super().__init__(rng=seed)

        # set up parameters/network
        self.num_nodes = num_nodes
        self.network_type = network_type
        self.friend_ratio = friend_ratio
        self.influencer_ratio = influencer_ratio
        self.initial_enthusiast_ratio = initial_enthusiast_ratio
        self.threshold_mean = threshold_mean
        self.threshold_std = threshold_std
        self.initial_supply = initial_supply
        self.supply = initial_supply   # current stock (decremented on purchase)
        self.restock_rate = restock_rate
        self.restock_interval = restock_interval
        self.step_count = 0

        # build network
        prob = avg_node_degree / num_nodes

        if network_type == "random":
            # Erdos-Renyi: connections form with uniform probability
            self.G = nx.erdos_renyi_graph(n=num_nodes, p=prob)
        elif network_type == "clustered":
            # Watts-Strogatz: locally clustered small-world network
            # k must be even: round up to nearest even number
            k = max(2, avg_node_degree + avg_node_degree % 2)
            self.G = nx.watts_strogatz_graph(n=num_nodes, k=k, p=0.1)
        else:
            raise ValueError("network_type must be 'random' or 'clustered'")
        
        # assign tie type and weight to each edge
        # friend -> strong ties carry full influence, stranger -> weak ties carry reduce influence
        for u, v in self.G.edges():
            if self.random.random() < friend_ratio:
                self.G.edges[u, v]["tie_type"] = "friend"
                self.G.edges[u, v]["tie_weight"] = 1.0
            else:
                self.G.edges[u, v]["tie_type"] = "stranger"
                self.G.edges[u, v]["tie_weight"] = 0.2

        # influencer nodes: highest degree nodes
        n_influencers = int(num_nodes * influencer_ratio)
        degree_sorted = sorted(self.G.nodes(), key=lambda n:self.G.degree(n), reverse=True)
        influencer_nodes = set(degree_sorted[:n_influencers])

        # list of edge weights and node positions; used for visualization
        self.position = nx.spring_layout(self.G, seed=42, k=0.5)
        self.weights = [self.G[u][v]["tie_weight"] * 2 for u, v in self.G.edges()]

        # create grid from network object
        self.grid = NetworkGrid(self.G)

        # create agents
        for node in self.G.nodes():
            is_influencer = node in influencer_nodes

            # influencers and a random seed of enthusiasts start with high interest
            if is_influencer or self.random.random() < initial_enthusiast_ratio:
                interest = max(0.0, min(1.0, self.random.gauss(0.85, 0.08)))
            else:
                # most agents start with low interest
                interest = max(0.0, min(1.0, self.random.gauss(0.15, 0.1)))

            # heterogeneous thresholds: some people need more social proof than others
            threshold = max(0.1, min(0.95, self.random.gauss(threshold_mean, threshold_std)))

            agent = ConsumerAgent(self, interest, threshold, is_influencer)
            self.grid.place_agent(agent, node)

        # define datacollector
        self.datacollector = DataCollector(
            model_reporters={
                "Indifferent": number_indifferent,
                "Interested": number_interested,
                "Active": number_active,
                "Successful": number_successful,
                "Failed": number_failed,
                "Supply": lambda m: m.supply,
                # Cascade size = agents who are currently wanting or have successfully bought
                "Cascade_Size": lambda m: number_active(m) + number_successful(m),
            }
        )
        
        self.running = True
        self.datacollector.collect(self)

    # restock method: add fixed proportion of initial supply back to stock
    def restock(self):
        restock_amount = int(self.initial_supply * self.restock_rate)
        # cap at initial supply to avoid unbounded growth
        self.supply = min(self.initial_supply, self.supply + restock_amount)

    # agents take a step
    def step(self):
        self.step_count += 1
        # restock supply at regular interval
        if self.step_count % self.restock_interval == 0:
            self.restock()
        # random order: first come first serve
        self.agents.shuffle_do("step")
        # collect data after all agents acted
        self.datacollector.collect(self)
        # stopping simulation: when cascade fully resolved that no agents still deciding
        still_deciding = number_active(self) + number_interested(self)
        if still_deciding == 0:
            self.running = False