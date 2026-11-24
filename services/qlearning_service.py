import random
import logging
import numpy as np

logger = logging.getLogger(__name__)

class QLearningTrafficAgent:
    """
    Academic Reinforcement Learning Demonstration using tabular Q-Learning.
    Optimizes traffic signal green timing to minimize queue lengths and waiting delays.
    """
    ACTIONS = [
        "INCREASE_GREEN_10S",
        "DECREASE_GREEN_10S",
        "MAINTAIN_DURATION",
        "SWITCH_PHASE"
    ]

    def __init__(self, alpha=0.1, gamma=0.9, epsilon=0.15):
        self.alpha = alpha      # Learning rate
        self.gamma = gamma      # Discount factor
        self.epsilon = epsilon  # Exploration rate
        # 3 queue levels * 3 density levels * 3 wait levels = 27 states
        # 4 actions per state
        self.q_table = np.zeros((3, 3, 3, 4))
        self._pretrain_baseline()

    def _pretrain_baseline(self):
        """Pre-seeds the Q-table with rational traffic domain priors."""
        # When queue and density are high (state 2, 2, *), action 0 (INCREASE_GREEN) has positive expected reward
        for w in range(3):
            self.q_table[2, 2, w, 0] = 5.0   # Increase green
            self.q_table[2, 2, w, 1] = -8.0  # Decrease green is punished
            self.q_table[0, 0, w, 1] = 4.0   # When empty, decreasing green saves cycle time
            self.q_table[1, 1, w, 2] = 3.5   # Moderate states maintain steady timing

    def _discretize_state(self, queue_len: int, density_cat: str, wait_sec: int):
        # Queue discretizing: 0: 0-3, 1: 4-8, 2: 9+
        q_idx = 0 if queue_len <= 3 else (1 if queue_len <= 8 else 2)

        # Density: 0: LOW, 1: MODERATE, 2: HIGH/VERY HIGH
        d_map = {"LOW": 0, "MODERATE": 1, "HIGH": 2, "VERY HIGH": 2}
        d_idx = d_map.get(density_cat, 1)

        # Wait time: 0: <30s, 1: 30-60s, 2: >60s
        w_idx = 0 if wait_sec < 30 else (1 if wait_sec <= 60 else 2)

        return q_idx, d_idx, w_idx

    def choose_action(self, queue_len: int, density_cat: str, wait_sec: int):
        q, d, w = self._discretize_state(queue_len, density_cat, wait_sec)
        if random.random() < self.epsilon:
            return random.randint(0, 3)
        return int(np.argmax(self.q_table[q, d, w]))

    def compute_reward(self, prev_queue: int, new_queue: int, wait_sec: int):
        # Reward is higher when queue is reduced and wait times drop
        queue_delta = prev_queue - new_queue
        wait_penalty = -0.05 * wait_sec
        return (queue_delta * 2.0) + wait_penalty

    def run_comparison_simulation(self, initial_queue: int = 14, initial_density: str = "HIGH", steps: int = 25):
        """
        Runs an academic simulation comparing Fixed-Time Signal Control vs
        Q-Learning Adaptive Controller across multiple time intervals.
        """
        fixed_queues = []
        fixed_waits = []
        rl_queues = []
        rl_waits = []

        # 1. Fixed-Time Simulation (Static 35s green, fixed cycle)
        curr_q = initial_queue
        curr_w = 40
        for step in range(steps):
            arrivals = random.randint(2, 6)
            departures = 4  # fixed discharge rate per cycle
            curr_q = max(0, curr_q + arrivals - departures)
            curr_w = min(120, max(15, curr_w + (curr_q * 1.8) - 10))
            fixed_queues.append(curr_q)
            fixed_waits.append(round(curr_w, 1))

        # 2. Q-Learning Adaptive Simulation
        curr_q = initial_queue
        curr_w = 40
        current_green = 35
        for step in range(steps):
            q_state, d_state, w_state = self._discretize_state(curr_q, initial_density, int(curr_w))
            action_idx = int(np.argmax(self.q_table[q_state, d_state, w_state]))

            # Apply action
            if action_idx == 0:  # Increase green
                current_green = min(90, current_green + 10)
            elif action_idx == 1:  # Decrease green
                current_green = max(15, current_green - 10)

            arrivals = random.randint(2, 6)
            # More green = higher discharge
            departures = int(current_green / 7.0)
            next_q = max(0, curr_q + arrivals - departures)
            next_w = min(120, max(10, curr_w + (next_q * 1.2) - (current_green * 0.4)))

            # Update Q-table with reward
            reward = self.compute_reward(curr_q, next_q, int(next_w))
            next_q_s, next_d_s, next_w_s = self._discretize_state(next_q, initial_density, int(next_w))
            best_next_q = np.max(self.q_table[next_q_s, next_d_s, next_w_s])
            self.q_table[q_state, d_state, w_state, action_idx] += self.alpha * (
                reward + (self.gamma * best_next_q) - self.q_table[q_state, d_state, w_state, action_idx]
            )

            curr_q = next_q
            curr_w = next_w
            rl_queues.append(curr_q)
            rl_waits.append(round(curr_w, 1))

        avg_fixed_wait = round(sum(fixed_waits) / len(fixed_waits), 1)
        avg_rl_wait = round(sum(rl_waits) / len(rl_waits), 1)
        wait_reduction_pct = round(max(0, ((avg_fixed_wait - avg_rl_wait) / max(1, avg_fixed_wait)) * 100), 1)

        avg_fixed_q = round(sum(fixed_queues) / len(fixed_queues), 1)
        avg_rl_q = round(sum(rl_queues) / len(rl_queues), 1)
        queue_reduction_pct = round(max(0, ((avg_fixed_q - avg_rl_q) / max(1, avg_fixed_q)) * 100), 1)

        return {
            "disclaimer": "ACADEMIC REINFORCEMENT LEARNING SIMULATION – RESEARCH DEMONSTRATION",
            "steps": list(range(1, steps + 1)),
            "fixed_time": {
                "queues": fixed_queues,
                "waiting_times": fixed_waits,
                "avg_queue": avg_fixed_q,
                "avg_wait_sec": avg_fixed_wait
            },
            "q_learning": {
                "queues": rl_queues,
                "waiting_times": rl_waits,
                "avg_queue": avg_rl_q,
                "avg_wait_sec": avg_rl_wait
            },
            "improvements": {
                "waiting_time_reduction_percent": wait_reduction_pct,
                "queue_length_reduction_percent": queue_reduction_pct
            }
        }
