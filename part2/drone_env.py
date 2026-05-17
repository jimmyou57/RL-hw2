from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import gymnasium as gym
import numpy as np
from gymnasium import spaces


@dataclass(frozen=True)
class DroneEnvConfig:
    """Configuration for the random-target navigation task."""

    episode_horizon: int = 400
    control_dt: float = 0.1
    workspace_low: tuple[float, float, float] = (-6.0, -6.0, 0.5)
    workspace_high: tuple[float, float, float] = (6.0, 6.0, 4.0)
    target_low: tuple[float, float, float] = (-4.0, -4.0, 1.0)
    target_high: tuple[float, float, float] = (4.0, 4.0, 3.0)
    max_linear_speed: float = 1.5
    success_radius: float = 0.35
    crash_height: float = 0.2
    success_bonus: float = 20.0
    progress_weight: float = 3.0
    distance_weight: float = 0.5
    control_weight: float = 0.05
    velocity_weight: float = 0.02


class RosDroneAdapter:
    """Thin ROS-facing layer.

    Replace each `NotImplementedError` with the actual ROS 2 publishers,
    subscribers, and synchronization logic used by your simulator.
    """

    def reset_pose(self) -> None:
        raise NotImplementedError

    def takeoff(self) -> None:
        raise NotImplementedError

    def send_velocity_command(self, action: np.ndarray) -> None:
        raise NotImplementedError

    def read_pose(self) -> np.ndarray:
        """Return `[x, y, z]` from `/simple_drone/gt_pose`."""
        raise NotImplementedError

    def read_velocity(self) -> np.ndarray:
        """Return `[vx, vy, vz]` from `/simple_drone/gt_vel`."""
        raise NotImplementedError

    def wait(self, seconds: float) -> None:
        raise NotImplementedError


class DroneRandomTargetEnv(gym.Env[np.ndarray, np.ndarray]):
    """Gymnasium environment for random target navigation."""

    metadata = {"render_modes": []}

    def __init__(
        self,
        adapter: RosDroneAdapter,
        config: DroneEnvConfig | None = None,
        seed: int | None = None,
    ) -> None:
        super().__init__()
        self.adapter = adapter
        self.config = config or DroneEnvConfig()
        self.np_random = np.random.default_rng(seed)

        max_speed = self.config.max_linear_speed
        self.action_space = spaces.Box(
            low=np.array([-max_speed, -max_speed, -max_speed], dtype=np.float32),
            high=np.array([max_speed, max_speed, max_speed], dtype=np.float32),
            dtype=np.float32,
        )

        obs_low = np.array(
            [
                *self.config.workspace_low,
                -max_speed,
                -max_speed,
                -max_speed,
                -12.0,
                -12.0,
                -4.0,
            ],
            dtype=np.float32,
        )
        obs_high = np.array(
            [
                *self.config.workspace_high,
                max_speed,
                max_speed,
                max_speed,
                12.0,
                12.0,
                4.0,
            ],
            dtype=np.float32,
        )
        self.observation_space = spaces.Box(obs_low, obs_high, dtype=np.float32)

        self.target = np.zeros(3, dtype=np.float32)
        self.steps = 0
        self.previous_distance = 0.0

    def reset(
        self,
        *,
        seed: int | None = None,
        options: dict[str, Any] | None = None,
    ) -> tuple[np.ndarray, dict[str, Any]]:
        super().reset(seed=seed)
        if seed is not None:
            self.np_random = np.random.default_rng(seed)

        self.adapter.reset_pose()
        self.adapter.takeoff()
        self.adapter.wait(1.0)

        self.target = self._sample_target(options)
        self.steps = 0

        position = self.adapter.read_pose()
        velocity = self.adapter.read_velocity()
        self.previous_distance = self._distance(position)
        observation = self._build_observation(position, velocity)
        return observation, {"target": self.target.copy()}

    def step(
        self,
        action: np.ndarray,
    ) -> tuple[np.ndarray, float, bool, bool, dict[str, Any]]:
        action = np.asarray(action, dtype=np.float32)
        action = np.clip(action, self.action_space.low, self.action_space.high)
        self.adapter.send_velocity_command(action)
        self.adapter.wait(self.config.control_dt)

        position = self.adapter.read_pose()
        velocity = self.adapter.read_velocity()
        distance = self._distance(position)
        reward = self._compute_reward(distance, action, velocity)

        self.steps += 1
        terminated = self._is_success(distance) or self._is_failure(position)
        truncated = self.steps >= self.config.episode_horizon
        observation = self._build_observation(position, velocity)

        info = {
            "target": self.target.copy(),
            "distance_to_target": distance,
            "is_success": self._is_success(distance),
            "is_failure": self._is_failure(position),
        }
        self.previous_distance = distance
        return observation, reward, terminated, truncated, info

    def _sample_target(self, options: dict[str, Any] | None) -> np.ndarray:
        if options and "target" in options:
            return np.asarray(options["target"], dtype=np.float32)
        return self.np_random.uniform(
            low=np.asarray(self.config.target_low, dtype=np.float32),
            high=np.asarray(self.config.target_high, dtype=np.float32),
        ).astype(np.float32)

    def _build_observation(self, position: np.ndarray, velocity: np.ndarray) -> np.ndarray:
        relative_target = self.target - position
        return np.concatenate([position, velocity, relative_target]).astype(np.float32)

    def _distance(self, position: np.ndarray) -> float:
        return float(np.linalg.norm(self.target - position))

    def _compute_reward(
        self,
        distance: float,
        action: np.ndarray,
        velocity: np.ndarray,
    ) -> float:
        progress = self.previous_distance - distance
        reward = 0.0
        reward += self.config.progress_weight * progress
        reward -= self.config.distance_weight * distance
        reward -= self.config.control_weight * float(np.linalg.norm(action))
        reward -= self.config.velocity_weight * float(np.linalg.norm(velocity))
        if self._is_success(distance):
            reward += self.config.success_bonus
        return reward

    def _is_success(self, distance: float) -> bool:
        return distance <= self.config.success_radius

    def _is_failure(self, position: np.ndarray) -> bool:
        below_floor = position[2] <= self.config.crash_height
        below_bounds = np.any(position < np.asarray(self.config.workspace_low))
        above_bounds = np.any(position > np.asarray(self.config.workspace_high))
        return bool(below_floor or below_bounds or above_bounds)

