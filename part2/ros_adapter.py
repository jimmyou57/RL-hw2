from __future__ import annotations

import time

import numpy as np
import rclpy
from geometry_msgs.msg import Pose, Twist
from rclpy.node import Node
from std_msgs.msg import Empty as EmptyMsg
from std_srvs.srv import Empty as EmptySrv

from part2.drone_env import RosDroneAdapter


class RealRosDroneAdapter(RosDroneAdapter, Node):
    """ROS 2 implementation of the adapter used by `DroneHoverEnv`."""

    def __init__(
        self,
        *,
        namespace: str = "/simple_drone",
        node_name: str = "rl_hover_adapter",
        queue_size: int = 10,
        init_rclpy: bool = True,
        world_reset_service: str = "/reset_world",
        simulation_reset_service: str = "/reset_simulation",
    ) -> None:
        self._owns_rclpy = init_rclpy and not rclpy.ok()
        if self._owns_rclpy:
            rclpy.init(args=None)

        Node.__init__(self, node_name)

        namespace = namespace.rstrip("/")
        self.current_pose: np.ndarray | None = None
        self.current_velocity: np.ndarray | None = None
        self._last_pose: np.ndarray | None = None
        self._last_pose_time: float | None = None
        self._velocity_from_pose = np.zeros(3, dtype=np.float32)

        self.cmd_vel_pub = self.create_publisher(
            Twist,
            f"{namespace}/cmd_vel",
            queue_size,
        )
        self.takeoff_pub = self.create_publisher(
            EmptyMsg,
            f"{namespace}/takeoff",
            queue_size,
        )
        self.reset_pub = self.create_publisher(
            EmptyMsg,
            f"{namespace}/reset",
            queue_size,
        )
        self.world_reset_client = self.create_client(EmptySrv, world_reset_service)
        self.simulation_reset_client = self.create_client(
            EmptySrv,
            simulation_reset_service,
        )
        self.pose_sub = self.create_subscription(
            Pose,
            f"{namespace}/gt_pose",
            self._pose_callback,
            queue_size,
        )
        self.velocity_sub = self.create_subscription(
            Twist,
            f"{namespace}/gt_vel",
            self._velocity_callback,
            queue_size,
        )

    def reset_pose(self) -> None:
        self.send_velocity_command(np.zeros(3, dtype=np.float32))
        self.reset_pub.publish(EmptyMsg())
        if not self._call_reset_service(self.simulation_reset_client):
            self._call_reset_service(self.world_reset_client)
        self.reset_pub.publish(EmptyMsg())
        self.current_pose = None
        self.current_velocity = None
        self._last_pose = None
        self._last_pose_time = None
        self._velocity_from_pose = np.zeros(3, dtype=np.float32)
        self.wait(0.7)

    def takeoff(self) -> None:
        self.takeoff_pub.publish(EmptyMsg())
        self.wait(0.2)

    def send_velocity_command(self, action: np.ndarray) -> None:
        action = np.asarray(action, dtype=np.float32)
        msg = Twist()
        msg.linear.x = float(action[0])
        msg.linear.y = float(action[1])
        msg.linear.z = float(action[2])
        self.cmd_vel_pub.publish(msg)

    def read_pose(self) -> np.ndarray:
        if self.current_pose is None:
            self._wait_for_state()
        if self.current_pose is None:
            raise RuntimeError("No pose received from /simple_drone/gt_pose.")
        return self.current_pose.copy()

    def read_velocity(self) -> np.ndarray:
        if self.current_velocity is None:
            self._wait_for_state()
        if self.current_velocity is not None:
            return self.current_velocity.copy()
        return self._velocity_from_pose.copy()

    def wait(self, seconds: float) -> None:
        end_time = time.monotonic() + seconds
        while rclpy.ok() and time.monotonic() < end_time:
            remaining = end_time - time.monotonic()
            rclpy.spin_once(self, timeout_sec=max(0.0, min(0.05, remaining)))

    def close(self) -> None:
        if rclpy.ok():
            self.send_velocity_command(np.zeros(3, dtype=np.float32))
            self.wait(0.1)
        self.destroy_node()
        if self._owns_rclpy and rclpy.ok():
            rclpy.shutdown()

    def _wait_for_state(self, timeout_sec: float = 2.0) -> None:
        end_time = time.monotonic() + timeout_sec
        while rclpy.ok() and time.monotonic() < end_time:
            if self.current_pose is not None:
                return
            rclpy.spin_once(self, timeout_sec=0.05)

    def _call_reset_service(
        self,
        client: rclpy.client.Client,
        timeout_sec: float = 2.0,
    ) -> bool:
        if not client.wait_for_service(timeout_sec=0.5):
            return False

        future = client.call_async(EmptySrv.Request())
        end_time = time.monotonic() + timeout_sec
        while rclpy.ok() and time.monotonic() < end_time:
            rclpy.spin_once(self, timeout_sec=0.05)
            if future.done():
                return True
        return False

    def _pose_callback(self, msg: Pose) -> None:
        now = time.monotonic()
        new_pose = np.array(
            [msg.position.x, msg.position.y, msg.position.z],
            dtype=np.float32,
        )

        if self._last_pose is not None and self._last_pose_time is not None:
            dt = max(now - self._last_pose_time, 1e-6)
            self._velocity_from_pose = ((new_pose - self._last_pose) / dt).astype(
                np.float32
            )

        self.current_pose = new_pose
        self._last_pose = new_pose
        self._last_pose_time = now

    def _velocity_callback(self, msg: Twist) -> None:
        self.current_velocity = np.array(
            [msg.linear.x, msg.linear.y, msg.linear.z],
            dtype=np.float32,
        )
