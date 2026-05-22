from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
from stable_baselines3 import PPO
from stable_baselines3.common.callbacks import CheckpointCallback
from stable_baselines3.common.monitor import Monitor
from stable_baselines3.common.utils import set_random_seed

from part2.drone_env import DroneHoverConfig, DroneHoverEnv
from part2.ros_adapter import RealRosDroneAdapter


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Train a PPO agent for Part 2 Task A drone hovering."
    )
    parser.add_argument("--timesteps", type=int, default=5_000)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--device", default="auto")
    parser.add_argument("--namespace", default="/simple_drone")

    parser.add_argument("--target-x", type=float, default=0.0)
    parser.add_argument("--target-y", type=float, default=0.0)
    parser.add_argument("--target-z", type=float, default=2.0)
    parser.add_argument("--episode-horizon", type=int, default=400)
    parser.add_argument("--control-dt", type=float, default=0.1)
    parser.add_argument("--takeoff-settle-time", type=float, default=1.0)
    parser.add_argument("--reset-start-height", type=float, default=1.0)
    parser.add_argument("--reset-climb-speed", type=float, default=0.5)
    parser.add_argument("--reset-climb-timeout", type=float, default=8.0)
    parser.add_argument("--reset-settle-time", type=float, default=0.5)
    parser.add_argument("--max-linear-speed", type=float, default=1.0)
    parser.add_argument("--success-radius", type=float, default=0.25)
    parser.add_argument("--success-speed", type=float, default=0.2)
    parser.add_argument("--success-hold-steps", type=int, default=50)
    parser.add_argument("--progress-weight", type=float, default=1.0)
    parser.add_argument("--distance-weight", type=float, default=2.0)
    parser.add_argument("--velocity-weight", type=float, default=0.4)
    parser.add_argument("--control-weight", type=float, default=0.05)
    parser.add_argument("--smoothness-weight", type=float, default=0.1)
    parser.add_argument("--hover-bonus", type=float, default=0.1)
    parser.add_argument("--success-bonus", type=float, default=200.0)
    parser.add_argument("--failure-penalty", type=float, default=500.0)

    parser.add_argument("--learning-rate", type=float, default=3e-4)
    parser.add_argument("--n-steps", type=int, default=256)
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--log-std-init", type=float, default=-2.0)
    parser.add_argument("--gamma", type=float, default=0.99)
    parser.add_argument("--gae-lambda", type=float, default=0.95)
    parser.add_argument("--clip-range", type=float, default=0.2)
    parser.add_argument("--ent-coef", type=float, default=0.0)
    parser.add_argument("--vf-coef", type=float, default=0.5)

    parser.add_argument("--log-dir", type=Path, default=Path("part2/logs"))
    parser.add_argument("--model-dir", type=Path, default=Path("part2/models"))
    parser.add_argument("--run-name", default="ppo_hover_task_a")
    parser.add_argument("--checkpoint-freq", type=int, default=1_000)
    parser.add_argument("--resume", type=Path, default=None)
    parser.add_argument("--preflight-steps", type=int, default=3)
    return parser.parse_args()


def build_config(args: argparse.Namespace) -> DroneHoverConfig:
    return DroneHoverConfig(
        target_position=(args.target_x, args.target_y, args.target_z),
        episode_horizon=args.episode_horizon,
        control_dt=args.control_dt,
        takeoff_settle_time=args.takeoff_settle_time,
        reset_start_height=args.reset_start_height,
        reset_climb_speed=args.reset_climb_speed,
        reset_climb_timeout=args.reset_climb_timeout,
        reset_settle_time=args.reset_settle_time,
        max_linear_speed=args.max_linear_speed,
        success_radius=args.success_radius,
        success_speed=args.success_speed,
        success_hold_steps=args.success_hold_steps,
        progress_weight=args.progress_weight,
        distance_weight=args.distance_weight,
        velocity_weight=args.velocity_weight,
        control_weight=args.control_weight,
        smoothness_weight=args.smoothness_weight,
        hover_bonus=args.hover_bonus,
        success_bonus=args.success_bonus,
        failure_penalty=args.failure_penalty,
    )


def build_env(args: argparse.Namespace) -> Monitor:
    adapter = RealRosDroneAdapter(namespace=args.namespace)
    env = DroneHoverEnv(adapter=adapter, config=build_config(args), seed=args.seed)
    return Monitor(
        env,
        filename=str(args.log_dir / args.run_name),
        info_keywords=(
            "is_success",
            "is_failure",
            "failure_reason",
            "distance_to_target",
            "speed",
            "stable_steps",
        ),
    )


def run_preflight(env: Monitor, steps: int) -> None:
    if steps <= 0:
        return

    observation, info = env.reset()
    print("Preflight reset OK")
    print("  observation shape:", observation.shape)
    print("  distance:", round(float(info["distance_to_target"]), 4))
    print("  position:", np.round(info["position"], 4))
    print("  velocity:", np.round(info["velocity"], 4))
    print("  failure:", info["is_failure"], info["failure_reason"])

    for step_index in range(steps):
        action = np.zeros(env.action_space.shape, dtype=np.float32)
        observation, reward, terminated, truncated, info = env.step(action)
        print(
            f"  step {step_index + 1}: "
            f"reward={reward:.4f}, "
            f"distance={float(info['distance_to_target']):.4f}, "
            f"speed={float(info['speed']):.4f}, "
            f"terminated={terminated}, truncated={truncated}, "
            f"failure_reason={info['failure_reason']}"
        )
        if terminated or truncated:
            observation, info = env.reset()
            print("  preflight episode reset; new observation shape:", observation.shape)


def build_model(args: argparse.Namespace, env: Monitor) -> PPO:
    if args.resume is not None:
        print(f"Loading model from {args.resume}")
        return PPO.load(args.resume, env=env, device=args.device)

    return PPO(
        policy="MlpPolicy",
        env=env,
        learning_rate=args.learning_rate,
        n_steps=args.n_steps,
        batch_size=args.batch_size,
        gamma=args.gamma,
        gae_lambda=args.gae_lambda,
        clip_range=args.clip_range,
        ent_coef=args.ent_coef,
        vf_coef=args.vf_coef,
        seed=args.seed,
        verbose=1,
        tensorboard_log=str(args.log_dir),
        device=args.device,
        policy_kwargs={"log_std_init": args.log_std_init},
    )


def main() -> None:
    args = parse_args()
    set_random_seed(args.seed)
    args.log_dir.mkdir(parents=True, exist_ok=True)
    args.model_dir.mkdir(parents=True, exist_ok=True)

    env = build_env(args)
    try:
        run_preflight(env, args.preflight_steps)
        model = build_model(args, env)
        checkpoint_callback = CheckpointCallback(
            save_freq=args.checkpoint_freq,
            save_path=str(args.model_dir),
            name_prefix=f"{args.run_name}_checkpoint",
            save_replay_buffer=False,
            save_vecnormalize=False,
        )

        print(f"Training PPO for {args.timesteps} timesteps")
        model.learn(
            total_timesteps=args.timesteps,
            callback=checkpoint_callback,
            tb_log_name=args.run_name,
            reset_num_timesteps=args.resume is None,
        )

        final_model_path = args.model_dir / f"{args.run_name}_final"
        model.save(final_model_path)
        print(f"Saved final model to {final_model_path}.zip")
    finally:
        env.close()


if __name__ == "__main__":
    main()
