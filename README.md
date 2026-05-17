# HW2 NSYSU Drone RL

This repository is a starter scaffold for Homework 2. The suggested task is
**Task B - Random Target Navigation**, where the drone receives a new target at
the beginning of each episode and learns a policy that generalizes across target
positions.

## Folder Layout

```text
.
|-- README.md
|-- part1/
|   |-- README.md
|   +-- terminal_log.txt
|-- part2/
|   |-- __init__.py
|   |-- drone_env.py
|   |-- train.py
|   |-- test.py
|   |-- models/
|   +-- logs/
|-- report/
|   +-- report_outline.md
|-- HW2_Assignment_Intro.pdf
+-- HW2_NSYSU_Drone_RL_EN.pdf
```

## Chosen Task

Task B extends the provided single-target example in a meaningful way:

- A different goal is sampled every episode.
- The observation includes both drone state and relative target position.
- The reward encourages progress, smooth control, and successful arrival.
- The test script evaluates multiple target points instead of one memorized goal.

## Expected Runtime Environment

- Ubuntu 22.04
- ROS 2 Iron
- Gazebo Classic
- Python 3.10+
- `gymnasium`
- `stable-baselines3`
- `numpy`

## Typical Workflow

1. Start the simulator container and launch the drone world.
2. Confirm ROS 2 topics are available:

```bash
ros2 topic list
```

3. Train:

```bash
python3 -m part2.train
```

4. Test:

```bash
python3 -m part2.test --model part2/models/ppo_random_target.zip
```

## What You Still Need To Fill In

- Connect the ROS 2 adapter methods in `part2/drone_env.py` to the actual drone
  topics in your simulator.
- Tune reward weights, target ranges, and termination thresholds after observing
  real flights.
- Add Part 1 screenshots and the real terminal log.
- Train and save a real model before submission.
- Write the final PDF report from your own experiments and analysis.

