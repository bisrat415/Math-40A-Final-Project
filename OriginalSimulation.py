# This program is the implementation of the orginial simulation described on the paper

import random
from statistics import mean

# Adjustable parameters
MAX_MOVES = 10
P_INJURY = 0.1        # Probability of serious injury from a single D act
TIME_BONUS_START = 20
TIME_BONUS_DECREMENT = 2
CONTESTS_PER_MATCHUP = 5000   # Increase for more stable averages

# Payoffs
WIN_PAYOFF = 60        # Payoff for winning (without time bonus)
SERIOUS_INJURY = -100
SCRATCH = -2

PROBE_PROB = 0.05       # Probability that Prober-Retaliator probes first move

class Strategy:
    def reset(self):
        pass
    def choose_move(self, my_history, opp_history):
        raise NotImplementedError

class Mouse(Strategy):
    def __init__(self):
        self.reset()
    def reset(self):
        self.opponent_d_played = False
    def choose_move(self, my_history, opp_history):
        if opp_history and opp_history[-1] == 'D':
            self.opponent_d_played = True
        if self.opponent_d_played:
            return 'R'
        if len(my_history) < MAX_MOVES:
            return 'C'
        else:
            return 'R'

class Hawk(Strategy):
    def choose_move(self, my_history, opp_history):
        return 'D'

class Bully(Strategy):
    def __init__(self):
        self.reset()
    def reset(self):
        self.first_move = True
        self.d_streak = 0
    def choose_move(self, my_history, opp_history):
        # Try adjusting Bully's logic to match original outcomes more closely
        if self.first_move:
            self.first_move = False
            return 'D'
        if opp_history and opp_history[-1] == 'D':
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
        if opp_history:
            if opp_history[-1] == 'D':
                self.state = 'D'
            else:
                self.state = 'C'
        return self.state

class ProberRetaliator(Strategy):
    def __init__(self):
        self.reset()
    def reset(self):
        self.state = 'C'
        self.move_count = 0
        self.has_probed = False
    def choose_move(self, my_history, opp_history):
        self.move_count += 1
        if self.move_count > MAX_MOVES:
            return 'R'
        # Attempt probe on first move
        if not self.has_probed and len(my_history) == 0:
            if random.random() < PROBE_PROB:
                self.has_probed = True
                self.state = 'D'
                return 'D'
        if opp_history:
            if opp_history[-1] == 'D':
                self.state = 'C'
            else:
                if self.has_probed and self.state == 'D':
                    self.state = 'D'
                else:
                    self.state = 'C'
        return self.state

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
            return (A_score, B_score + WIN_PAYOFF + max(time_bonus,0))
        elif B_move == 'R':
            time_bonus = TIME_BONUS_START - TIME_BONUS_DECREMENT * moves
            return (A_score + WIN_PAYOFF + max(time_bonus,0), B_score)

        # Handle dangerous acts
        if A_move == 'D':
            if random.random() < P_INJURY:
                # B injured, A wins
                time_bonus = TIME_BONUS_START - TIME_BONUS_DECREMENT * moves
                return (A_score + WIN_PAYOFF + max(time_bonus,0), B_score + SERIOUS_INJURY)
            else:
                B_score += SCRATCH

        if B_move == 'D':
            if random.random() < P_INJURY:
                # A injured, B wins
                time_bonus = TIME_BONUS_START - TIME_BONUS_DECREMENT * moves
                return (A_score + SERIOUS_INJURY, B_score + WIN_PAYOFF + max(time_bonus,0))
            else:
                A_score += SCRATCH

    # If reached here, draw with no one retreating or injured
    return (A_score, B_score)

def average_payoff(strategyA_class, strategyB_class, contests=CONTESTS_PER_MATCHUP):
    # Only return average payoff to strategyA
    A_payoffs = []
    for _ in range(contests):
        A = strategyA_class()
        B = strategyB_class()
        A_score, B_score = play_contest(A, B)
        A_payoffs.append(A_score)
    return mean(A_payoffs)

if __name__ == "__main__":
    strategies = [Mouse, Hawk, Bully, Retaliator, ProberRetaliator]
    strategy_names = ["Mouse", "Hawk", "Bully", "Retaliator", "Prober-Retaliator"]

    payoff_matrix = []
    for row_strat in strategies:
        row_results = []
        for col_strat in strategies:
            avg_p = average_payoff(row_strat, col_strat, contests=CONTESTS_PER_MATCHUP)
            row_results.append(avg_p)
        payoff_matrix.append(row_results)

    print(" " * 20, end="")
    for name in strategy_names:
        print(f"{name:>20}", end="")
    print()
    for i, row in enumerate(payoff_matrix):
        print(f"{strategy_names[i]:<20}", end="")
        for val in row:
            print(f"{val:>20.1f}", end="")
        print()
