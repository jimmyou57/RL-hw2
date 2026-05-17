from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Plot reward curve from Monitor CSV.")
    parser.add_argument(
        "--monitor-csv",
        required=True,
        help="Path to Stable-Baselines3 Monitor CSV output.",
    )
    parser.add_argument(
        "--output",
        default="part2/logs/training_curve.png",
        help="Output path for the reward curve figure.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    source = Path(args.monitor_csv)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)

    data = pd.read_csv(source, comment="#")
    rewards = data["r"].rolling(window=20, min_periods=1).mean()

    plt.figure(figsize=(8, 4.5))
    plt.plot(data.index, data["r"], alpha=0.25, label="episode reward")
    plt.plot(data.index, rewards, linewidth=2, label="20-episode mean")
    plt.xlabel("Episode")
    plt.ylabel("Reward")
    plt.title("Training Curve")
    plt.legend()
    plt.tight_layout()
    plt.savefig(output, dpi=160)


if __name__ == "__main__":
    main()

