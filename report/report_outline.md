# Report Outline

## 1. Task Definition and Motivation

- Define Task B: random target navigation.
- Explain why generalization across targets matters more than memorizing one goal.

## 2. Pain Points of Existing Methods

- Discuss why a fixed P-controller may struggle with varying targets, actuator limits,
  and noisy dynamics.
- Include concrete examples from Part 1.

## 3. Literature Review

- Summarize at least three recent papers.
- For each paper, add one paragraph on what design choice it inspired in your work.

## 4. Proposed Solution

- Algorithm: PPO.
- State: position, velocity, relative target position.
- Action: bounded linear velocity command.
- Reward: progress, distance penalty, control penalty, velocity penalty, success bonus.
- Termination: success radius, timeout, crash, out-of-bounds.

## 5. Results and Discussion

- Add training curve.
- Report success rate over fixed evaluation targets.
- Compare against the baseline controller.
- Include failure cases honestly.

## Appendix A. Part 1 Observations

- Target-point experiments.
- Effects of `Kp`.
- Effects of `max_speed`.

## Acknowledgement

- Disclose any AI assistance used for brainstorming, debugging, or syntax help.

