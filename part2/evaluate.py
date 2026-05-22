from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
from stable_baselines3 import PPO

from part2.drone_env import DroneHoverConfig, DroneHoverEnv
from part2.ros_adapter import RealRosDroneAdapter


DEFAULT_MODEL = Path("part2/models/ppo_drone.zip")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Evaluate the final Task A hover policy and save report artifacts."
    )
    parser.add_argument("--model", type=Path, default=DEFAULT_MODEL)
    parser.add_argument("--output-dir", type=Path, default=Path("part2/evaluation/final_hover"))
    parser.add_argument("--episodes", type=int, default=10)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--namespace", default="/simple_drone")
    parser.add_argument("--deterministic", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--action-scale", type=float, default=0.5)
    parser.add_argument("--test-label", default="normal_hover")
    parser.add_argument("--disturbance-type", default="none")
    parser.add_argument("--motion-drift-noise", type=float, default=0.0)
    parser.add_argument("--motion-drift-noise-time", type=float, default=50.0)

    parser.add_argument("--target-x", type=float, default=0.0)
    parser.add_argument("--target-y", type=float, default=0.0)
    parser.add_argument("--target-z", type=float, default=2.0)
    parser.add_argument("--episode-horizon", type=int, default=160)
    parser.add_argument("--control-dt", type=float, default=0.1)
    parser.add_argument("--takeoff-settle-time", type=float, default=1.0)
    parser.add_argument("--reset-start-height", type=float, default=1.8)
    parser.add_argument("--reset-climb-speed", type=float, default=0.5)
    parser.add_argument("--reset-climb-timeout", type=float, default=8.0)
    parser.add_argument("--reset-settle-time", type=float, default=0.5)
    parser.add_argument("--max-linear-speed", type=float, default=0.1)
    parser.add_argument("--success-radius", type=float, default=0.25)
    parser.add_argument("--success-speed", type=float, default=0.2)
    parser.add_argument("--success-hold-steps", type=int, default=50)
    parser.add_argument("--distance-weight", type=float, default=3.0)
    parser.add_argument("--velocity-weight", type=float, default=2.0)
    parser.add_argument("--control-weight", type=float, default=0.7)
    parser.add_argument("--smoothness-weight", type=float, default=0.4)
    parser.add_argument("--hover-bonus", type=float, default=2.0)
    parser.add_argument("--success-bonus", type=float, default=300.0)
    parser.add_argument("--failure-penalty", type=float, default=500.0)
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
        distance_weight=args.distance_weight,
        velocity_weight=args.velocity_weight,
        control_weight=args.control_weight,
        smoothness_weight=args.smoothness_weight,
        hover_bonus=args.hover_bonus,
        success_bonus=args.success_bonus,
        failure_penalty=args.failure_penalty,
    )


def vector3(values: Any) -> np.ndarray:
    return np.asarray(values, dtype=np.float32).reshape(3)


def run_evaluation(args: argparse.Namespace) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    adapter = RealRosDroneAdapter(namespace=args.namespace)
    env = DroneHoverEnv(adapter=adapter, config=build_config(args), seed=args.seed)
    model = PPO.load(args.model, env=env, device=args.device)

    episode_rows: list[dict[str, Any]] = []
    trajectory_rows: list[dict[str, Any]] = []

    try:
        for episode_index in range(1, args.episodes + 1):
            observation, reset_info = env.reset(seed=args.seed + episode_index - 1)
            reset_position = vector3(reset_info["position"])
            reset_velocity = vector3(reset_info["velocity"])
            total_reward = 0.0
            min_distance = float(reset_info["distance_to_target"])
            max_stable_steps = int(reset_info["stable_steps"])
            final_info = reset_info
            final_reward = 0.0
            terminated = False
            truncated = False

            for step_index in range(1, args.episode_horizon + 1):
                raw_action, _ = model.predict(
                    observation,
                    deterministic=args.deterministic,
                )
                raw_action = np.asarray(raw_action, dtype=np.float32)
                action = np.clip(
                    raw_action * args.action_scale,
                    env.action_space.low,
                    env.action_space.high,
                ).astype(np.float32)

                observation, reward, terminated, truncated, info = env.step(action)
                position = vector3(info["position"])
                velocity = vector3(info["velocity"])
                total_reward += float(reward)
                final_reward = float(reward)
                final_info = info
                min_distance = min(min_distance, float(info["distance_to_target"]))
                max_stable_steps = max(max_stable_steps, int(info["stable_steps"]))

                trajectory_rows.append(
                    {
                        "episode": episode_index,
                        "step": step_index,
                        "time_sec": step_index * args.control_dt,
                        "raw_action_x": float(raw_action[0]),
                        "raw_action_y": float(raw_action[1]),
                        "raw_action_z": float(raw_action[2]),
                        "action_x": float(action[0]),
                        "action_y": float(action[1]),
                        "action_z": float(action[2]),
                        "x": float(position[0]),
                        "y": float(position[1]),
                        "z": float(position[2]),
                        "vx": float(velocity[0]),
                        "vy": float(velocity[1]),
                        "vz": float(velocity[2]),
                        "distance_to_target": float(info["distance_to_target"]),
                        "speed": float(info["speed"]),
                        "reward": float(reward),
                        "cumulative_reward": total_reward,
                        "stable_steps": int(info["stable_steps"]),
                        "is_success": bool(info["is_success"]),
                        "is_failure": bool(info["is_failure"]),
                        "failure_reason": info["failure_reason"] or "",
                        "terminated": bool(terminated),
                        "truncated": bool(truncated),
                    }
                )

                if terminated or truncated:
                    break

            final_position = vector3(final_info["position"])
            final_velocity = vector3(final_info["velocity"])
            episode_rows.append(
                {
                    "episode": episode_index,
                    "steps": step_index,
                    "total_reward": total_reward,
                    "final_reward": final_reward,
                    "is_success": bool(final_info["is_success"]),
                    "is_failure": bool(final_info["is_failure"]),
                    "failure_reason": final_info["failure_reason"] or "",
                    "terminated": bool(terminated),
                    "truncated": bool(truncated),
                    "reset_x": float(reset_position[0]),
                    "reset_y": float(reset_position[1]),
                    "reset_z": float(reset_position[2]),
                    "reset_vx": float(reset_velocity[0]),
                    "reset_vy": float(reset_velocity[1]),
                    "reset_vz": float(reset_velocity[2]),
                    "reset_distance_to_target": float(reset_info["distance_to_target"]),
                    "reset_speed": float(reset_info["speed"]),
                    "final_x": float(final_position[0]),
                    "final_y": float(final_position[1]),
                    "final_z": float(final_position[2]),
                    "final_vx": float(final_velocity[0]),
                    "final_vy": float(final_velocity[1]),
                    "final_vz": float(final_velocity[2]),
                    "final_distance_to_target": float(final_info["distance_to_target"]),
                    "final_speed": float(final_info["speed"]),
                    "min_distance_to_target": min_distance,
                    "max_stable_steps": max_stable_steps,
                }
            )

            print(
                f"episode={episode_index:02d} "
                f"success={bool(final_info['is_success'])} "
                f"steps={step_index} "
                f"final_distance={float(final_info['distance_to_target']):.4f} "
                f"final_speed={float(final_info['speed']):.4f} "
                f"max_stable={max_stable_steps} "
                f"total_reward={total_reward:.2f}",
                flush=True,
            )
    finally:
        env.close()

    return episode_rows, trajectory_rows


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    with path.open("w", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def build_summary(args: argparse.Namespace, episode_rows: list[dict[str, Any]]) -> dict[str, Any]:
    successes = [row for row in episode_rows if row["is_success"]]
    failures = [row for row in episode_rows if row["is_failure"]]
    timeouts = [
        row for row in episode_rows if not row["is_success"] and not row["is_failure"]
    ]

    def mean(key: str, rows: list[dict[str, Any]] = episode_rows) -> float | None:
        if not rows:
            return None
        return float(np.mean([float(row[key]) for row in rows]))

    def maximum(key: str, rows: list[dict[str, Any]] = episode_rows) -> float | None:
        if not rows:
            return None
        return float(np.max([float(row[key]) for row in rows]))

    return {
        "model": str(args.model),
        "episodes": args.episodes,
        "success_count": len(successes),
        "failure_count": len(failures),
        "timeout_count": len(timeouts),
        "success_rate": len(successes) / args.episodes if args.episodes else 0.0,
        "action_scale": args.action_scale,
        "deterministic": args.deterministic,
        "test_label": args.test_label,
        "disturbance_type": args.disturbance_type,
        "motion_drift_noise": args.motion_drift_noise,
        "motion_drift_noise_time": args.motion_drift_noise_time,
        "target_position": [args.target_x, args.target_y, args.target_z],
        "success_radius": args.success_radius,
        "success_speed": args.success_speed,
        "success_hold_steps": args.success_hold_steps,
        "control_dt": args.control_dt,
        "episode_horizon": args.episode_horizon,
        "mean_steps": mean("steps"),
        "mean_total_reward": mean("total_reward"),
        "mean_final_distance": mean("final_distance_to_target"),
        "mean_final_speed": mean("final_speed"),
        "mean_min_distance": mean("min_distance_to_target"),
        "mean_max_stable_steps": mean("max_stable_steps"),
        "max_final_distance": maximum("final_distance_to_target"),
        "max_final_speed": maximum("final_speed"),
        "success_mean_final_distance": mean("final_distance_to_target", successes),
        "success_mean_final_speed": mean("final_speed", successes),
        "success_mean_steps": mean("steps", successes),
        "failure_reasons": {
            reason: sum(1 for row in failures if row["failure_reason"] == reason)
            for reason in sorted({row["failure_reason"] for row in failures})
        },
    }


def plot_results(
    output_path: Path,
    args: argparse.Namespace,
    episode_rows: list[dict[str, Any]],
    trajectory_rows: list[dict[str, Any]],
) -> None:
    target = np.array([args.target_x, args.target_y, args.target_z], dtype=np.float32)
    episode_ids = sorted({int(row["episode"]) for row in trajectory_rows})

    fig = plt.figure(figsize=(12, 8))
    ax_3d = fig.add_subplot(2, 2, 1, projection="3d")
    ax_dist = fig.add_subplot(2, 2, 2)
    ax_speed = fig.add_subplot(2, 2, 3)
    ax_z = fig.add_subplot(2, 2, 4)

    for episode_id in episode_ids:
        rows = [row for row in trajectory_rows if int(row["episode"]) == episode_id]
        xs = [float(row["x"]) for row in rows]
        ys = [float(row["y"]) for row in rows]
        zs = [float(row["z"]) for row in rows]
        ts = [float(row["time_sec"]) for row in rows]
        distances = [float(row["distance_to_target"]) for row in rows]
        speeds = [float(row["speed"]) for row in rows]
        label = f"ep {episode_id}"

        ax_3d.plot(xs, ys, zs, linewidth=1.2, alpha=0.8, label=label)
        ax_dist.plot(ts, distances, linewidth=1.0, alpha=0.75)
        ax_speed.plot(ts, speeds, linewidth=1.0, alpha=0.75)
        ax_z.plot(ts, zs, linewidth=1.0, alpha=0.75)

    ax_3d.scatter([target[0]], [target[1]], [target[2]], color="red", s=60, label="target")
    ax_3d.set_xlabel("x (m)")
    ax_3d.set_ylabel("y (m)")
    ax_3d.set_zlabel("z (m)")
    ax_3d.set_title("3D Trajectories")

    ax_dist.axhline(args.success_radius, color="red", linestyle="--", linewidth=1.2)
    ax_dist.set_xlabel("time (s)")
    ax_dist.set_ylabel("distance (m)")
    ax_dist.set_title("Distance To Target")

    ax_speed.axhline(args.success_speed, color="red", linestyle="--", linewidth=1.2)
    ax_speed.set_xlabel("time (s)")
    ax_speed.set_ylabel("speed (m/s)")
    ax_speed.set_title("Speed")

    ax_z.axhline(args.target_z, color="red", linestyle="--", linewidth=1.2)
    ax_z.set_xlabel("time (s)")
    ax_z.set_ylabel("z (m)")
    ax_z.set_title("Altitude")

    success_count = sum(1 for row in episode_rows if row["is_success"])
    fig.suptitle(
        f"Hover Evaluation: {success_count}/{len(episode_rows)} successes, "
        f"action_scale={args.action_scale}"
    )
    fig.tight_layout()
    fig.savefig(output_path, dpi=160)
    plt.close(fig)


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    episode_rows, trajectory_rows = run_evaluation(args)
    summary = build_summary(args, episode_rows)

    write_csv(args.output_dir / "episodes.csv", episode_rows)
    write_csv(args.output_dir / "trajectory.csv", trajectory_rows)
    with (args.output_dir / "summary.json").open("w") as summary_file:
        json.dump(summary, summary_file, indent=2)
        summary_file.write("\n")
    plot_results(
        args.output_dir / "trajectory_overview.png",
        args,
        episode_rows,
        trajectory_rows,
    )

    print("\nEvaluation summary")
    print(json.dumps(summary, indent=2))
    print(f"\nSaved artifacts to {args.output_dir}")


if __name__ == "__main__":
    main()
