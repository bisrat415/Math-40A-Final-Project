# This program provides the population distribution of the strategies over generations
# A mutation rate is introduced to the population to simulate the evolution of strategies

import random
from statistics import mean

# Adjustable parameters
MAX_MOVES = 10
P_INJURY = 0.1        # Probability of serious injury from a single D act
TIME_BONUS_START = 20
TIME_BONUS_DECREMENT = 2
CONTESTS_PER_MATCHUP = 2000     # Increase for more stable averages in non-evolution runs
POPULATION_SIZE = 200           # Number of individuals in the evolving population
GENERATIONS = 50                # Number of generations to simulate
MUTATION_RATE = 0.01            # Probability of a mutant strategy appearing
PROBE_PROB = 0.05               # Probability that Prober-Retaliator probes on first move

# Payoffs
WIN_PAYOFF = 60        # Payof for winning (without time bonus)
SERIOUS_INJURY = -100
SCRATCH = -2

# Base Strategy Class
class Strategy:
    def reset(self):
        pass
    def choose_move(self, my_history, opp_history):
        raise NotImplementedError

# Example of a more complex strategy that looks at the full history
class Mouse(Strategy):
    def __init__(self):
        self.reset()
    def reset(self):
        self.opponent_d_played = False
    def choose_move(self, my_history, opp_history):
        if 'D' in opp_history:
            self.opponent_d_played = True
        if len(my_history) < MAX_MOVES and not self.opponent_d_played:
            return 'C'
        else:
            return 'R'

class Hawk(Strategy):
    def reset(self):
        pass
    def choose_move(self, my_history, opp_history):
        return 'D'

class Bully(Strategy):
    def __init__(self):
        self.reset()
    def reset(self):
        self.first_move = True
        self.d_streak = 0
    def choose_move(self, my_history, opp_history):
        if self.first_move:
            self.first_move = False
            return 'D'
        if len(opp_history) > 0 and opp_history[-1] == 'D':
            self.d_streak += 1
        else:
            self.d_streak = 0
        if self.d_streak >= 2:
            return 'R'
        return 'C'

class Retaliator(Strategy):
    def __init__(self):
        self.reset()
    def reset(self):
        self.state = 'C'
        self.move_count = 0
    def choose_move(self, my_history, opp_history):
        self.move_count += 1
        if self.move_count > MAX_MOVES:
            return 'R'
        if len(opp_history) > 0 and opp_history[-1] == 'D':
            return 'D'
        return 'C'

class ProberRetaliator(Strategy):
    def __init__(self):
        self.reset()
    def reset(self):
        self.move_count = 0
        self.has_probed = False
    def choose_move(self, my_history, opp_history):
        self.move_count += 1
        if self.move_count > MAX_MOVES:
            return 'R'
        # Attempt a probe on the first move with certain probability
        if not self.has_probed and len(my_history) == 0:
            if random.random() < PROBE_PROB:
                self.has_probed = True
                return 'D'
        # If opponent was dangerous last turn, cooperate to appear non-threatening
        if len(opp_history) > 0 and opp_history[-1] == 'D':
            return 'C'
        # Otherwise, if we have probed before, continue to be dangeros
        if self.has_probed:
            return 'D'
        return 'C'

# New, more complex strategy that looks further back in history
class LongRetaliator(Strategy):
    def __init__(self):
        self.reset()
    def reset(self):
        self.move_count = 0
    def choose_move(self, my_history, opp_history):
        self.move_count += 1
        if self.move_count > MAX_MOVES:
            return 'R'
        # If the opponent has been dangerous in any of the last two moves, retaliate now
        if len(opp_history) >= 2 and ('D' in opp_history[-2:]):
            return 'D'
        # Else cooperate
        return 'C'

def play_contest(strategyA, strategyB):
    strategyA.reset()
    strategyB.reset()
    A_history, B_history = [], []
    A_score, B_score = 0, 0

    for moves in range(MAX_MOVES):
        A_move = strategyA.choose_move(A_history, B_history)
        B_move = strategyB.choose_move(B_history, A_history)
        A_history.append(A_move)
        B_history.append(B_move)

        # Check retreats
        if A_move == 'R' and B_move == 'R':
            return (A_score, B_score)
        elif A_move == 'R':
            time_bonus = TIME_BONUS_START - TIME_BONUS_DECREMENT * moves
            return (A_score, B_score + WIN_PAYOFF + max(time_bonus, 0))
        elif B_move == 'R':
            time_bonus = TIME_BONUS_START - TIME_BONUS_DECREMENT * moves
            return (A_score + WIN_PAYOFF + max(time_bonus, 0), B_score)

        # Handle dangerous acts
        if A_move == 'D':
            if random.random() < P_INJURY:
                # B injured, A wins
                time_bonus = TIME_BONUS_START - TIME_BONUS_DECREMENT * moves
                return (A_score + WIN_PAYOFF + max(time_bonus, 0), B_score + SERIOUS_INJURY)
            else:
                B_score += SCRATCH

        if B_move == 'D':
            if random.random() < P_INJURY:
                # A injured, B wins
                time_bonus = TIME_BONUS_START - TIME_BONUS_DECREMENT * moves
                return (A_score + SERIOUS_INJURY, B_score + WIN_PAYOFF + max(time_bonus, 0))
            else:
                A_score += SCRATCH

    # If reached here, draw with no one retreating or injured
    return (A_score, B_score)

def average_payoff(strategyA_class, strategyB_class, contests=CONTESTS_PER_MATCHUP):
    # Only return average payoff to strategyA for static tests
    A_payoffs = []
    for _ in range(contests):
        A = strategyA_class()
        B = strategyB_class()
        A_score, B_score = play_contest(A, B)
        A_payoffs.append(A_score)
    return mean(A_payoffs)

def evolutionary_simulation(strategies, initial_distribution, generations=GENERATIONS, population_size=POPULATION_SIZE):
    """
    Run an evolutionary simulation:
    - strategies: list of strategy classes
    - initial_distribution: list of frequencies summing to 1.0 for each strategy
    - generations: number of generations to run
    - population_size: number of individuals per generation
    """
    # Current distribution of strategies in population
    # Represent population as a list of tuples (StrategyClass, frequency)
    population = [(s, f) for s, f in zip(strategies, initial_distribution)]

    for gen in range(generations):
        # Create a list of individuals based on the current population distribution
        individuals = []
        for strat, freq in population:
            count = int(freq * population_size)
            individuals.extend([strat() for _ in range(count)])
        
        # If due to rounding we have fewer or more than population_size, adjust randomly
        while len(individuals) < population_size:
            # Add a random individual
            chosen_strat = random.choices(strategies, weights=[f for _, f in population])[0]
            individuals.append(chosen_strat())
        while len(individuals) > population_size:
            # Remove a random individual
            individuals.pop()

        # Pair individuals randomly and let them compete
        random.shuffle(individuals)
        payoffs = [0]*population_size
        for i in range(0, population_size, 2):
            A = individuals[i]
            B = individuals[i+1]
            A_score, B_score = play_contest(A, B)
            payoffs[i] += A_score
            payoffs[i+1] += B_score

        # Compute total payoff by strategy class
        strat_payoffs = {s: 0 for s in strategies}
        strat_counts = {s: 0 for s in strategies}
        for ind, payoff in zip(individuals, payoffs):
            # Identify strategy class of individual
            for s in strategies:
                if isinstance(ind, s):
                    strat_payoffs[s] += payoff
                    strat_counts[s] += 1
                    break
        
        # Compute average payoffs and update frequencies
        new_population = []
        total_fitness = 0.0
        for s in strategies:
            if strat_counts[s] > 0:
                avg_pay = strat_payoffs[s] / strat_counts[s]
            else:
                avg_pay = 0
            # Fitness function could be a positive transform of payoff
            fitness = max(avg_pay + 100, 0.01)  # shift payoff by +100 to avoid negatives
            new_population.append((s, fitness))
            total_fitness += fitness

        # Normalize frequencies
        population = [(s, f/total_fitness) for s, f in new_population]

        # Mutation step: With some probability, introduce a random strategy
        if random.random() < MUTATION_RATE:
            mut_index = random.randrange(len(population))
            s, freq = population[mut_index]
            # Shift some frequency to another strategy (e.g., Hawk)
            # Let's say we introduce randomness by shifting some frequency to Hawk if not s
            if s is not Hawk:
                # shift a small portion of freq to Hawk
                mutation_amount = min(freq*0.1, 0.05)  # up to 5% of population
                # reduce s by mutation_amount, increase Hawk by mutation_amount
                population[mut_index] = (s, freq - mutation_amount)
                # Find Hawk's index
                for i, (st, fr) in enumerate(population):
                    if st is Hawk:
                        population[i] = (st, fr + mutation_amount)
                        break

        # Print generation info
        print(f"Generation {gen+1}:")
        for s, freq in population:
            print(f"  {s.__name__}: {freq*100:.2f}%")
        print()

    return population

if __name__ == "__main__":
    # Define strategies
    strategies = [Mouse, Hawk, Bully, Retaliator, ProberRetaliator, LongRetaliator]
    strategy_names = [s.__name__ for s in strategies]

    # Example: Run evolutionary simulation
    # Initial distribution: equal frequencies
    initial_distribution = [1.0/len(strategies)]*len(strategies)
    final_population = evolutionary_simulation(strategies, initial_distribution, generations=GENERATIONS, population_size=POPULATION_SIZE)

    print("Final population distribution after evolutionary simulation:")
    for s, freq in final_population:
        print(f"{s.__name__}: {freq*100:.2f}%")
