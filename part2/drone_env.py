from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import gymnasium as gym
import numpy as np
from gymnasium import spaces


@dataclass(frozen=True)
class DroneHoverConfig:
    """Configuration for Task A: precision hovering."""

    target_position: tuple[float, float, float] = (0.0, 0.0, 2.0)
    episode_horizon: int = 400
    control_dt: float = 0.1
    takeoff_settle_time: float = 1.0
    reset_start_height: float = 1.0
    reset_climb_speed: float = 0.5
    reset_climb_timeout: float = 8.0
    reset_settle_time: float = 0.5

    workspace_low: tuple[float, float, float] = (-4.0, -4.0, 0.2)
    workspace_high: tuple[float, float, float] = (4.0, 4.0, 4.0)
    max_distance_from_target: float = 5.0
    max_linear_speed: float = 1.0
    max_observed_speed: float = 3.0

    success_radius: float = 0.25
    success_speed: float = 0.2
    success_hold_steps: int = 50
    crash_height: float = 0.2

    progress_weight: float = 1.0
    distance_weight: float = 2.0
    velocity_weight: float = 0.4
    control_weight: float = 0.05
    smoothness_weight: float = 0.1
    hover_bonus: float = 0.1
    success_bonus: float = 200.0
    failure_penalty: float = 500.0


class RosDroneAdapter:
    """Thin interface between the Gym environment and ROS 2.

    The concrete implementation will live in the training/test scripts so this
    environment stays focused on the MDP, reward, and termination logic.
    """

    def reset_pose(self) -> None:
        raise NotImplementedError

    def takeoff(self) -> None:
        raise NotImplementedError

    def send_velocity_command(self, action: np.ndarray) -> None:
        raise NotImplementedError

    def read_pose(self) -> np.ndarray:
        """Return the current position as `[x, y, z]`."""
        raise NotImplementedError

    def read_velocity(self) -> np.ndarray:
        """Return the current linear velocity as `[vx, vy, vz]`."""
        raise NotImplementedError

    def wait(self, seconds: float) -> None:
        raise NotImplementedError


class DroneHoverEnv(gym.Env[np.ndarray, np.ndarray]):
    """Gymnasium environment for precision hovering under disturbance."""

    metadata = {"render_modes": []}

    def __init__(
        self,
        adapter: RosDroneAdapter,
        config: DroneHoverConfig | None = None,
        seed: int | None = None,
    ) -> None:
        super().__init__()
        self.adapter = adapter
        self.config = config or DroneHoverConfig()
        self.np_random = np.random.default_rng(seed)

        max_action = self.config.max_linear_speed
        self.action_space = spaces.Box(
            low=np.full(3, -max_action, dtype=np.float32),
            high=np.full(3, max_action, dtype=np.float32),
            dtype=np.float32,
        )

        workspace_low = np.asarray(self.config.workspace_low, dtype=np.float32)
        workspace_high = np.asarray(self.config.workspace_high, dtype=np.float32)
        max_speed = self.config.max_observed_speed

        error_low = workspace_low - workspace_high
        error_high = workspace_high - workspace_low
        obs_low = np.concatenate(
            [
                error_low,
                np.full(3, -max_speed, dtype=np.float32),
                workspace_low,
                self.action_space.low,
            ]
        ).astype(np.float32)
        obs_high = np.concatenate(
            [
                error_high,
                np.full(3, max_speed, dtype=np.float32),
                workspace_high,
                self.action_space.high,
            ]
        ).astype(np.float32)
        self.observation_space = spaces.Box(obs_low, obs_high, dtype=np.float32)

        self.target_position = np.asarray(self.config.target_position, dtype=np.float32)
        self.steps = 0
        self.stable_steps = 0
        self.previous_distance = 0.0
        self.previous_action = np.zeros(3, dtype=np.float32)

    def reset(
        self,
        *,
        seed: int | None = None,
        options: dict[str, Any] | None = None,
    ) -> tuple[np.ndarray, dict[str, Any]]:
        super().reset(seed=seed)
        if seed is not None:
            self.np_random = np.random.default_rng(seed)

        self.target_position = self._target_from_options(options)
        self.steps = 0
        self.stable_steps = 0
        self.previous_action = np.zeros(3, dtype=np.float32)

        self.adapter.reset_pose()
        self.adapter.takeoff()
        self.adapter.wait(self.config.takeoff_settle_time)
        self._move_to_start_height()

        position = self._read_position()
        velocity = self._read_velocity()
        self.previous_distance = self._distance(position)
        observation = self._build_observation(position, velocity)
        reset_failed = self._failure_reason(position, self.previous_distance) is not None
        return observation, self._build_info(position, velocity, False, reset_failed)

    def step(
        self,
        action: np.ndarray,
    ) -> tuple[np.ndarray, float, bool, bool, dict[str, Any]]:
        action = np.asarray(action, dtype=np.float32)
        action = np.clip(action, self.action_space.low, self.action_space.high)

        self.adapter.send_velocity_command(action)
        self.adapter.wait(self.config.control_dt)

        position = self._read_position()
        velocity = self._read_velocity()
        distance = self._distance(position)
        speed = float(np.linalg.norm(velocity))
        action_delta = float(np.linalg.norm(action - self.previous_action))

        stable_now = self._is_stable(distance, speed)
        self.stable_steps = self.stable_steps + 1 if stable_now else 0

        failure_reason = self._failure_reason(position, distance)
        failure = failure_reason is not None
        success = self.stable_steps >= self.config.success_hold_steps
        terminated = success or failure

        self.steps += 1
        truncated = self.steps >= self.config.episode_horizon

        reward = self._compute_reward(
            distance=distance,
            speed=speed,
            action=action,
            action_delta=action_delta,
            stable_now=stable_now,
            success=success,
            failure=failure,
        )
        observation = self._build_observation(position, velocity)
        info = self._build_info(position, velocity, success, failure)

        self.previous_distance = distance
        self.previous_action = action.copy()
        return observation, reward, terminated, truncated, info

    def close(self) -> None:
        close_adapter = getattr(self.adapter, "close", None)
        if callable(close_adapter):
            close_adapter()
        super().close()

    def _target_from_options(self, options: dict[str, Any] | None) -> np.ndarray:
        if options and "target_position" in options:
            return np.asarray(options["target_position"], dtype=np.float32)
        if options and "target" in options:
            return np.asarray(options["target"], dtype=np.float32)
        return np.asarray(self.config.target_position, dtype=np.float32)

    def _read_position(self) -> np.ndarray:
        return np.asarray(self.adapter.read_pose(), dtype=np.float32)

    def _read_velocity(self) -> np.ndarray:
        return np.asarray(self.adapter.read_velocity(), dtype=np.float32)

    def _move_to_start_height(self) -> None:
        if self.config.reset_start_height <= 0.0:
            return

        climb_action = np.array(
            [0.0, 0.0, self.config.reset_climb_speed],
            dtype=np.float32,
        )
        stop_action = np.zeros(3, dtype=np.float32)
        max_steps = max(
            1,
            int(np.ceil(self.config.reset_climb_timeout / self.config.control_dt)),
        )

        for _ in range(max_steps):
            position = self._read_position()
            if position[2] >= self.config.reset_start_height:
                break
            self.adapter.send_velocity_command(climb_action)
            self.adapter.wait(self.config.control_dt)

        self.adapter.send_velocity_command(stop_action)
        self.adapter.wait(self.config.reset_settle_time)

    def _build_observation(self, position: np.ndarray, velocity: np.ndarray) -> np.ndarray:
        position_error = self.target_position - position
        return np.concatenate(
            [position_error, velocity, position, self.previous_action]
        ).astype(np.float32)

    def _build_info(
        self,
        position: np.ndarray,
        velocity: np.ndarray,
        success: bool,
        failure: bool,
    ) -> dict[str, Any]:
        distance = self._distance(position)
        speed = float(np.linalg.norm(velocity))
        return {
            "target_position": self.target_position.copy(),
            "position": position.copy(),
            "velocity": velocity.copy(),
            "distance_to_target": distance,
            "speed": speed,
            "stable_steps": self.stable_steps,
            "is_success": success,
            "is_failure": failure,
            "failure_reason": self._failure_reason(position, distance),
        }

    def _distance(self, position: np.ndarray) -> float:
        return float(np.linalg.norm(self.target_position - position))

    def _compute_reward(
        self,
        *,
        distance: float,
        speed: float,
        action: np.ndarray,
        action_delta: float,
        stable_now: bool,
        success: bool,
        failure: bool,
    ) -> float:
        progress = self.previous_distance - distance
        reward = 0.0
        reward += self.config.progress_weight * progress
        reward -= self.config.distance_weight * distance
        reward -= self.config.velocity_weight * speed
        reward -= self.config.control_weight * float(np.linalg.norm(action))
        reward -= self.config.smoothness_weight * action_delta

        if stable_now:
            reward += self.config.hover_bonus
        if success:
            reward += self.config.success_bonus
        if failure:
            reward -= self.config.failure_penalty
        return float(reward)

    def _is_stable(self, distance: float, speed: float) -> bool:
        return (
            distance <= self.config.success_radius
            and speed <= self.config.success_speed
        )

    def _is_failure(self, position: np.ndarray, distance: float) -> bool:
        return self._failure_reason(position, distance) is not None

    def _failure_reason(self, position: np.ndarray, distance: float) -> str | None:
        workspace_low = np.asarray(self.config.workspace_low, dtype=np.float32)
        workspace_high = np.asarray(self.config.workspace_high, dtype=np.float32)
        if position[2] <= self.config.crash_height:
            return "below_floor"
        if np.any(position < workspace_low):
            return "below_workspace"
        if np.any(position > workspace_high):
            return "above_workspace"
        if distance > self.config.max_distance_from_target:
            return "too_far_from_target"
        return None
