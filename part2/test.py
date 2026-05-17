from __future__ import annotations

import argparse

import numpy as np
from stable_baselines3 import PPO

from part2.drone_env import DroneRandomTargetEnv, RosDroneAdapter


class RealRosDroneAdapter(RosDroneAdapter):
    """TODO: implement ROS 2 communication for evaluation."""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate a trained drone policy.")
    parser.add_argument(
        "--model",
        default="part2/models/ppo_random_target.zip",
        help="Path to the trained Stable-Baselines3 model.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    env = DroneRandomTargetEnv(RealRosDroneAdapter())
    model = PPO.load(args.model)
    fixed_targets = [
        np.array([-2.0, 4.0, 1.5], dtype=np.float32),
        np.array([0.0, 0.0, 3.0], dtype=np.float32),
        np.array([3.0, -3.0, 2.0], dtype=np.float32),
    ]

    for target in fixed_targets:
        observation, info = env.reset(options={"target": target})
        terminated = truncated = False
        episode_reward = 0.0

        while not (terminated or truncated):
            action, _ = model.predict(observation, deterministic=True)
            observation, reward, terminated, truncated, info = env.step(action)
            episode_reward += reward

        print(
            f"target={target.tolist()} "
            f"success={info['is_success']} "
            f"distance={info['distance_to_target']:.3f} "
            f"reward={episode_reward:.2f}"
        )


if __name__ == "__main__":
    main()

