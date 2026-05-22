# HW2 NSYSU Drone RL

This repository contains my Homework 2 implementation for the NSYSU drone
control assignment. The selected Part 2 task is:

**Task A - Precision Hovering and Disturbance Rejection**

The goal is to train a reinforcement learning agent to hover at a fixed target
pose `(0.0, 0.0, 2.0)` and remain stable when `motionDriftNoise` is enabled in
the Gazebo drone plugin.

## Folder Layout

```text
.
|-- README.md
|-- Assignment2_env/
|   |-- Dockerfile
|   |-- run_docker.sh
|   |-- nsysu_drone_bringup/
|   |-- nsysu_drone_control/
|   +-- nsysu_drone_description/
|-- part1/
|   |-- README.md
|   |-- screenshot_01.png
|   |-- screenshot_02.png
|   +-- terminal_log.txt
|-- part2/
|   |-- drone_env.py
|   |-- ros_adapter.py
|   |-- train.py
|   |-- evaluate.py
|   |-- test.py
|   |-- models/
|   |   +-- ppo_drone.zip
|   |-- logs/
|   |   +-- training_curve.png
|   +-- evaluation/
|       |-- final_hover/
|       +-- disturbance_hover/
|-- report/
|   +-- report_outline.md
|-- HW2_Assignment_Intro.pdf
+-- HW2_NSYSU_Drone_RL_EN.pdf
```

## Runtime Environment

- Ubuntu 22.04
- Docker 24.x
- ROS 2 Iron
- Gazebo Classic
- Python 3.10
- PyTorch
- Gymnasium
- Stable-Baselines3
- NumPy, pandas, matplotlib, tensorboard

The Dockerfile in `Assignment2_env/` installs the ROS/Gazebo environment and
the Python RL packages needed for Part 2.

## Build And Start The Container

From the host machine:

```bash
cd Assignment2_env
docker build -t nsysu_drone_vnc:iron .
./run_docker.sh
```

`run_docker.sh` mounts the whole repository into the container at:

```text
/workspace/RL_Assignment2
```

If the default GPU is not available, choose another GPU:

```bash
GPU_ID=0 ./run_docker.sh
```

## Launch Gazebo

Inside the container:

```bash
source /opt/ros/iron/setup.bash
source /ros2_ws/install/setup.bash
launch_drone
```

Wait until the drone model appears in Gazebo. Keep this terminal running.

## Run The Final Test Script

Open a second container terminal from the host:

```bash
docker exec -it nsysu_drone_vnc bash
```

Then run:

```bash
cd /workspace/RL_Assignment2

source /opt/ros/iron/setup.bash
source /ros2_ws/install/setup.bash

python3 -m part2.test \
  --episodes 3 \
  --output-dir part2/evaluation/ta_demo
```

The test script loads:

```text
part2/models/ppo_drone.zip
```

The drone should reset, take off, move close to `(0.0, 0.0, 2.0)`, and hover
stably. The terminal prints each episode's success flag, final distance, and
final speed.

The output files are saved under the selected output directory:

```text
episodes.csv
trajectory.csv
summary.json
trajectory_overview.png
```

## Reproduce Evaluation Results

Nominal hover evaluation:

```bash
python3 -m part2.evaluate \
  --episodes 10 \
  --output-dir part2/evaluation/final_hover \
  --action-scale 0.5 \
  --device cpu
```

Final nominal result:

```text
success rate: 10/10
mean final distance: 0.09496 m
mean final speed: 0.02897 m/s
```

Disturbance evaluation was performed with the Gazebo plugin setting:

```text
motionDriftNoise = 0.02
motionDriftNoiseTime = 0.5
```

Final disturbance result:

```text
success rate: 10/10
mean final distance: 0.08892 m
mean final speed: 0.02451 m/s
```

The saved evaluation artifacts are in:

```text
part2/evaluation/final_hover/
part2/evaluation/disturbance_hover/
```

## Reproduce Training

The submitted model is already provided at `part2/models/ppo_drone.zip`. To run
a new PPO training experiment, launch Gazebo first and then run:

```bash
cd /workspace/RL_Assignment2

source /opt/ros/iron/setup.bash
source /ros2_ws/install/setup.bash

python3 -m part2.train \
  --timesteps 6000 \
  --run-name reproduce_hover_task_a \
  --device cpu \
  --n-steps 128 \
  --batch-size 64 \
  --target-x 0.0 \
  --target-y 0.0 \
  --target-z 2.0 \
  --reset-start-height 1.8 \
  --max-linear-speed 0.1 \
  --success-radius 0.25 \
  --success-speed 0.2 \
  --success-hold-steps 50 \
  --distance-weight 3.0 \
  --velocity-weight 2.0 \
  --control-weight 0.7 \
  --smoothness-weight 0.4 \
  --hover-bonus 2.0 \
  --success-bonus 300.0 \
  --failure-penalty 500.0
```

Because Gazebo physics and PPO exploration are stochastic, a new training run
may not reproduce the exact same model. The submitted model should be used for
grading.

## Part 1 Evidence

Part 1 evidence is stored under `part1/`:

- `screenshot_01.png`
- `screenshot_02.png`
- `terminal_log.txt`
- `README.md`

The Part 1 notes include three alternative target-point experiments and an
Appendix A draft discussing how `Kp` and `max_speed` affect the P-controller.

## Part 2 Design Summary

- Algorithm: PPO from Stable-Baselines3
- Observation: 12D vector containing relative target error, velocity, position,
  and previous action
- Action: bounded velocity command `[vx, vy, vz]`
- Target: `(0.0, 0.0, 2.0)`
- Success: remain within `0.25 m` and below `0.2 m/s` for 50 consecutive steps
- Termination: success, crash/below floor, out of workspace, too far from target,
  or timeout
- Test-time action scaling: `0.5`

Task A uses a fixed target pose. Generalization to arbitrary target positions is
outside the scope of Task A and corresponds more closely to Task B.
