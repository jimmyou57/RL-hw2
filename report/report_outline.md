# Report Outline

## 1. Task Definition And Motivation

- Chosen task: Task A - Precision Hovering and Disturbance Rejection.
- Goal: train the drone to hover at the fixed pose `(0.0, 0.0, 2.0)`.
- Stability requirement: maintain low position error and low velocity even when
  `motionDriftNoise` is non-zero.
- Explain why precision hovering matters:
  - inspection
  - sensing
  - station keeping
  - stable takeoff/landing preparation
- Clarify scope:
  - this is fixed-pose precision hovering
  - arbitrary target generalization belongs to Task B / future work

## 2. Pain Points Of Existing Methods

- Baseline: the P-controller behavior observed in Part 1 `fly_straight.py`.
- Discuss limitations of hand-tuned control:
  - `Kp` trades response speed against overshoot
  - `max_speed` trades convergence time against smoothness
  - fixed gains do not adapt to drift noise or changing dynamics
  - tuning is manual and task-specific
- Use concrete Part 1 observations:
  - lower `Kp` was smoother but slower
  - higher `Kp` was faster but caused more overshoot
  - lower `max_speed` was smoother but increased arrival time
  - higher `max_speed` reduced travel time but can make aggressive motion more likely
- Explain why RL is plausible:
  - the reward can combine distance, speed, control smoothness, and success
  - the policy can learn a closed-loop correction behavior from interaction data

## 3. Literature Review

- Include at least three recent papers from the past five years.
- Recommended themes:
  - PPO or policy-gradient methods for continuous control
  - UAV reinforcement learning for position control or trajectory tracking
  - disturbance rejection / robust RL / sim-to-real UAV control
- For each paper:
  - summarize the method
  - summarize the experiment
  - explain what design idea influenced this project
- Possible connection points:
  - why PPO was selected
  - why continuous velocity action is reasonable
  - why reward shaping is important
  - why disturbance testing is necessary

## 4. Proposed Solution

- Algorithm:
  - PPO with Stable-Baselines3
  - `MlpPolicy`
  - justify PPO over SAC / TD3 / DDPG:
    - stable clipped policy updates
    - easy to tune
    - suitable for low-dimensional continuous control
- MDP formulation:
  - State / observation:
    - position error: `target_position - current_position`
    - linear velocity
    - current position
    - previous action
    - total dimension: 12
  - Action:
    - bounded velocity command `[vx, vy, vz]`
    - published to `/simple_drone/cmd_vel`
  - Reward:
    - progress reward
    - distance penalty
    - velocity penalty
    - control magnitude penalty
    - action smoothness penalty
    - hover bonus
    - success bonus
    - failure penalty
  - Discount factor:
    - report PPO `gamma`
  - Termination:
    - success after stable hover for 50 consecutive steps
    - timeout
    - crash / below floor
    - out of workspace
    - too far from target
- ROS/Gazebo integration:
  - `ros_adapter.py` publishes takeoff/reset/cmd_vel
  - subscribes to `gt_pose` and `gt_vel`
  - uses `/reset_simulation` or `/reset_world` during reset
- Deployment detail:
  - deterministic policy
  - `action_scale = 0.5` to reduce drift and produce smoother hover

## 5. Results And Discussion

- Include `part2/logs/training_curve.png`.
- Explain training curve:
  - raw episode reward is noisy because PPO explores during training
  - failed episodes produce large negative rewards
  - moving average recovers later, showing fewer severe failures
  - final evaluation is more representative than raw training reward
- Nominal evaluation:
  - episodes: `10`
  - success rate: `10/10 = 100%`
  - mean final distance: about `0.09496 m`
  - max final distance: about `0.09610 m`
  - mean final speed: about `0.02897 m/s`
- Disturbance evaluation:
  - `motionDriftNoise = 0.02`
  - `motionDriftNoiseTime = 0.5`
  - episodes: `10`
  - success rate: `10/10 = 100%`
  - mean final distance: about `0.08892 m`
  - max final distance: about `0.17057 m`
  - mean final speed: about `0.02451 m/s`
- Compare with baseline P-controller:
  - P-controller can reach targets but requires manual gain/speed tuning
  - RL policy is trained specifically to balance hover accuracy, velocity, and smoothness
  - RL policy was evaluated under explicit drift noise
- Failure analysis:
  - early policies terminated too quickly because reset did not fully restore simulator state
  - raw policy actions were too large for stable hover
  - `action_scale = 0.5` improved deployment stability
  - the final policy is not claimed to generalize to arbitrary targets

## Appendix A. Part 1 Observations

- Include screenshots and terminal logs from `part1/`.
- Summarize at least three alternative target experiments.
- Discuss `Kp`:
  - lower `Kp` is smoother but slower
  - higher `Kp` is faster but can overshoot
- Discuss `max_speed`:
  - lower `max_speed` increases convergence time
  - higher `max_speed` reduces travel time but can increase aggressive motion

## Acknowledgement

- Disclose AI assistance if included in the submitted report.
- State that code, experiments, and final report content were reviewed and
  submitted individually.
