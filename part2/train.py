from __future__ import annotations

from pathlib import Path

from stable_baselines3 import PPO
from stable_baselines3.common.callbacks import CheckpointCallback
from stable_baselines3.common.monitor import Monitor

from part2.drone_env import DroneRandomTargetEnv, RosDroneAdapter


class RealRosDroneAdapter(RosDroneAdapter):
    """TODO: implement ROS 2 communication for training."""


def build_env() -> Monitor:
    adapter = RealRosDroneAdapter()
    return Monitor(DroneRandomTargetEnv(adapter))


def main() -> None:
    models_dir = Path("part2/models")
    logs_dir = Path("part2/logs")
    models_dir.mkdir(parents=True, exist_ok=True)
    logs_dir.mkdir(parents=True, exist_ok=True)

    env = build_env()
    checkpoint_callback = CheckpointCallback(
        save_freq=10_000,
        save_path=str(models_dir),
        name_prefix="ppo_random_target",
    )

    model = PPO(
        policy="MlpPolicy",
        env=env,
        learning_rate=3e-4,
        n_steps=2048,
        batch_size=64,
        gamma=0.99,
        verbose=1,
        tensorboard_log=str(logs_dir / "tensorboard"),
    )
    model.learn(total_timesteps=300_000, callback=checkpoint_callback)
    model.save(models_dir / "ppo_random_target")


if __name__ == "__main__":
    main()

