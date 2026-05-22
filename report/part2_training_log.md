# Part 2 訓練紀錄

這份文件用來記錄 HW2 Part 2 從環境設定、任務設計、reward function、
演算法選擇，到訓練與測試結果的完整過程。之後寫正式報告時，可以直接
回頭整理這裡的設計理由、參數設定、實驗結果與失敗案例。

## 紀錄規則

- 每次有實質進度後，都要更新這份紀錄。
- 需要記錄的內容包含：環境修改、MDP 設計、reward 調整、訓練指令、
  model 檔名、測試結果、失敗案例與觀察。
- 保留足夠細節，讓之後報告可以說明「為什麼這樣設計」，但不需要貼上
  大量無意義的 terminal output。

## 2026-05-19 - 環境設定與任務方向

### 選定任務

- 選擇 Task A：Precision Hovering and Disturbance Rejection。
- 目標是訓練無人機維持在固定 hover pose，並在模擬器加入 motion drift
  disturbance 時仍能保持穩定。
- 目前 starter scaffold 原本偏向 Task B random target navigation，因此
  後續需要把 `part2` 程式改成定點懸停任務。

### Docker / ROS / RL 環境

- Part 1 的 `fly_straight.py` 可以執行，是因為它只依賴 ROS 2 Python
  套件，例如 `rclpy`、`geometry_msgs`、`std_msgs`。這些套件已經存在於
  Docker/ROS 環境中。
- Part 2 需要在同一個 Python runtime 同時 import ROS 和 RL 套件，因此
  Docker/ROS 環境也必須安裝 Stable-Baselines3、Gymnasium、PyTorch 等
  套件。
- 已修改 `Assignment2_env/Dockerfile`，讓 Docker image 內建 Part 2
  需要的套件：
  - `python3-pip`
  - GPU 版 PyTorch wheel，來源為 `https://download.pytorch.org/whl/cu128`
  - `stable-baselines3`
  - `gymnasium`
  - `numpy<2`
  - `pandas`
  - `matplotlib`
  - `tensorboard`
- 第一次 Docker build 時裝到 `numpy 2.2.6`，導致某些以 NumPy 1.x 編譯的
  module 出現相容性警告。後續將 Dockerfile 改為固定 `numpy<2`。
- 在 container 中檢查 GPU 版 PyTorch 成功：
  - 觀察到的 Torch 版本：`2.11.0+cu128`
  - PyTorch 偵測到的 CUDA 版本：`12.8`
  - `torch.cuda.is_available()` 回傳 `True`

### Task A 初版 MDP 草案

- 預計環境名稱：`DroneHoverEnv`。
- 第一版 target hover pose：`(0.0, 0.0, 2.0)`。
- Action：送到 `/simple_drone/cmd_vel` 的 bounded velocity command
  `[vx, vy, vz]`。
- 初版 action range：每個軸向皆為 `[-1.0, 1.0] m/s`。
- 初版 observation components：
  - 位置誤差：`target_position - current_position`
  - 當前線速度
  - 當前位置
  - 前一個 action
- 初版 episode length：`400` steps。
- 初版 control interval：`0.1 s`。
- 初版 success condition：
  - 無人機距離 target 小於 `0.25 m`
  - 速度 norm 小於 `0.2 m/s`
  - 以上條件連續維持 `50` steps
- 初版 failure conditions：
  - 墜落或高度過低
  - 飛出 workspace 邊界
  - 距離 target 過遠
- 初版 reward terms：
  - 懲罰 position error
  - 懲罰 velocity magnitude
  - 懲罰 action magnitude
  - 懲罰 action change magnitude，鼓勵控制平順
  - 在 target 附近穩定懸停時給 bonus

### 下一步

- 將 `part2/drone_env.py` 從 Task B random-target scaffold 改成 Task A hovering
  environment。
- 接著更新 `part2/train.py` 與 `part2/test.py`，使用 hover 任務專用的 model
  名稱、log、metric 與 evaluation output。

## 2026-05-20 - Git 差異檢查

### 檢查結果

- 目前 Git 只有一個 commit：`c7d61ef Initialize RL homework scaffold`。
- 本地 `main`、`origin/main`、`origin/HEAD` 都指向同一個 commit，因此目前
  沒有偵測到「遠端比本地更新」的狀況。
- 本地工作區和最後一次 commit 相比有以下差異：
  - `part1/README.md`：已加入 Part 1 target experiments、Kp/max_speed 比較
    實驗與 Appendix A 草稿。
  - `part1/terminal_log.txt`：已從 placeholder 改成實際 `fly_straight.py`
    terminal log。
  - `part2/train.py`、`part2/test.py`：import path 從 `part2.drone_env` 改成
    `code.RL_Assignment2.part2.drone_env`，這個改法後續需要重新檢查，因為在
    `python3 -m part2.train` 的執行方式下可能不是正確 import path。
  - `Assignment2_env/`：整個資料夾目前是 untracked，Git 尚未追蹤，因此
    Dockerfile 修改也不會出現在普通 `git diff` 中。
  - `part1/screenshot_01.png`、`part1/screenshot_02.png`：目前是 untracked。
  - `report/part2_training_log.md`：目前是 untracked，作為 Part 2 過程紀錄。

### 判斷

- 目前沒有需要 `git pull` 的跡象。
- 接下來進入 Part 2 前，應該先決定哪些 untracked 檔案要納入作業提交與
  版本控制，尤其是 `Assignment2_env/Dockerfile`、Part 1 screenshots、以及
  本訓練紀錄。

### Part 2 檔案整理

- 刪除 Task B scaffold 檔案：
  - `part2/drone_env.py`
  - `part2/train.py`
  - `part2/test.py`
- 保留以下檔案：
  - `part2/__init__.py`
  - `part2/plot_training_curve.py`
  - `part2/logs/.gitkeep`
  - `part2/models/.gitkeep`
- 理由：Task A 會重新建立 hover-specific environment、training script、test
  script；`plot_training_curve.py` 仍然可用於之後產生 reward curve。

### `Assignment2_env` 修改檢查

- `Assignment2_env` 是從老師的 GitHub repo
  `https://github.com/NSYSU-ARL/Assignment2.git` clone 下來的 nested Git repo。
- 該 repo 目前相對老師原始版本有三個本地修改：
  - `Dockerfile`：加入 Part 2 所需的 RL 套件與 GPU 版 PyTorch。
  - `nsysu_drone_control/fly_straight.py`：加入 `signal` 處理與 `rclpy.ok()`
    防呆，避免 Ctrl+C 或 shutdown 時重複操作造成錯誤。
  - `run_docker.sh`：只有 file mode 從 `100644` 變成 `100755`，也就是變成
    可執行檔，內容沒有變更。
- 因為 `Assignment2_env` 本身包含 `.git`，如果直接在外層 repo 執行
  `git add Assignment2_env`，Git 可能會把它當成 submodule，而不是把內部檔案
  作為普通作業檔案完整追蹤。後續若要一起上傳到自己的 GitHub，建議先決定：
  1. 將 `Assignment2_env` 當成普通資料夾納入外層 repo。
  2. 或正式使用 submodule/fork 流程。

### 追蹤策略決定

- 決定將 `Assignment2_env` 作為外層 repo 的普通資料夾追蹤，方便老師之後直接
  取得完整執行環境。
- 已將 `Assignment2_env/.git` 移到 `/tmp/Assignment2_env.git.backup.RL_Assignment2`
  備份，避免外層 Git 將它當成 submodule。
- 已將 `Assignment2_env` 內 54 個檔案加入外層 repo staging。
- 已將 Part 1 作業證明加入 staging：
  - `part1/screenshot_01.png`
  - `part1/screenshot_02.png`
  - `part1/README.md`
  - `part1/terminal_log.txt`
- 決定不追蹤 `report/part2_training_log.md`，因為它是本地工作紀錄，不是最後要
  上傳給老師的作業內容；已加入 `.gitignore`。

### GitHub Push

- 已建立 commit：`72a1aee Add Part 1 evidence and Docker environment`。
- 已推送到 GitHub remote：`git@github.com:jimmyou57/RL-hw2.git` 的 `main`
  branch。
- 本次 commit 包含：
  - Part 1 實驗紀錄、terminal log、兩張 screenshot。
  - `Assignment2_env` 作為普通資料夾納入外層 repo。
  - Dockerfile 中 Part 2 所需 RL/GPU PyTorch 套件設定。
  - `.gitignore` 忽略本地訓練紀錄。
- 本次 commit 沒有包含 Part 2 scaffold 刪除；`part2/drone_env.py`、
  `part2/train.py`、`part2/test.py` 的刪除仍保留在本地工作區，之後會用
  Task A 版本重新建立。

## 2026-05-20 - 建立 Task A `DroneHoverEnv`

### 已完成內容

- 重新建立 `part2/drone_env.py`，將原本 Task B random target navigation
  scaffold 改成 Task A hovering environment。
- 新增 `DroneHoverConfig`，集中管理 Task A 初版參數：
  - `target_position = (0.0, 0.0, 2.0)`
  - `episode_horizon = 400`
  - `control_dt = 0.1`
  - `workspace_low = (-4.0, -4.0, 0.2)`
  - `workspace_high = (4.0, 4.0, 4.0)`
  - `max_linear_speed = 1.0`
  - `success_radius = 0.25`
  - `success_speed = 0.2`
  - `success_hold_steps = 50`
- 保留 `RosDroneAdapter` 介面，之後由 `train.py` / `test.py` 實作 ROS 2
  publisher/subscriber。
- 新增 `DroneHoverEnv`：
  - action space：3 維速度命令 `[vx, vy, vz]`，每軸範圍 `[-1.0, 1.0]`。
  - observation space：12 維，包含 position error、velocity、position、
    previous action。
  - `reset()`：重置 drone、takeoff、等待穩定、讀取 pose/velocity、回傳初始
    observation 與 info。
  - `step()`：送出速度命令、等待 `control_dt`、讀取狀態、計算 reward、
    更新 stable steps，並判斷 success/failure/timeout。
- Reward 初版設計包含：
  - progress bonus：距離 target 有變近則加分。
  - distance penalty：距離 target 越遠扣越多。
  - velocity penalty：速度越大扣越多。
  - control penalty：action magnitude 越大扣越多。
  - smoothness penalty：action 變化越大扣越多。
  - hover bonus：每一步符合 hover 條件時加小 bonus。
  - success bonus：連續穩定懸停達成後加大 bonus。
  - failure penalty：墜落、飛出邊界或距離 target 過遠時扣分。

### 驗證

- 已用 `python3 -m py_compile part2/drone_env.py` 做語法檢查，通過。
- 目前 Docker/ROS container 沒有在跑，所以尚未用 mock adapter 做完整 import
  與 reset/step 行為測試。

## 2026-05-20 - 實作 ROS Adapter

### 已完成內容

- 新增 `part2/ros_adapter.py`，實作 `RealRosDroneAdapter`。
- 參考老師提供的 `fly_straight.py` 與 `rl_fly_to_target.py`，使用相同的核心
  ROS topics：
  - publish `/simple_drone/cmd_vel`
  - publish `/simple_drone/takeoff`
  - publish `/simple_drone/reset`
  - subscribe `/simple_drone/gt_pose`
  - subscribe `/simple_drone/gt_vel`
- `RealRosDroneAdapter` 同時繼承 `RosDroneAdapter` 與 `rclpy.node.Node`，讓
  `DroneHoverEnv` 可以透過一般 Python function 呼叫 ROS 2 publisher /
  subscriber。
- 實作方法：
  - `reset_pose()`：送出 zero velocity，publish reset，清空舊 pose/velocity，
    並 spin 等待 reset 生效。
  - `takeoff()`：publish takeoff，並 spin 短暫等待。
  - `send_velocity_command(action)`：將 `[vx, vy, vz]` 轉成 `geometry_msgs/Twist`
    後 publish 到 `/simple_drone/cmd_vel`。
  - `read_pose()`：回傳目前 `/simple_drone/gt_pose` 的 `[x, y, z]`。
  - `read_velocity()`：優先使用 `/simple_drone/gt_vel`；若尚未收到 velocity
    topic，則使用 pose 差分估計速度。
  - `wait(seconds)`：透過 `rclpy.spin_once()` 在等待期間持續處理 ROS callback。
  - `close()`：結束前送出 zero velocity、destroy node，必要時 shutdown rclpy。

### 驗證

- 已用 `python3 -m py_compile part2/drone_env.py part2/ros_adapter.py` 做語法檢查，
  通過。
- 目前尚未在正在運行的 Gazebo/ROS container 內做實際 topic 測試。

## 2026-05-20 - 測試 Docker/RL 環境與 Task A scaffold

### 測試結果

- 發現目前正在跑的 `nsysu_drone_vnc` container 是舊 image：
  - image 建立時間約 3 天前。
  - container 裡沒有 `pip`，也找不到 `torch`。
  - 因此不能直接用這個舊 container 測 Part 2 Python/RL 程式。
- 重新 build 目前的 `Assignment2_env/Dockerfile`，新的 `nsysu_drone_vnc:iron`
  image 已包含 Part 2 套件。
- 用新版 image 開短命測試 container，確認套件：
  - `rclpy` import 正常。
  - `stable_baselines3` import 正常。
  - `gymnasium` import 正常。
  - `numpy = 1.26.4`，已避開 NumPy 2 與 OpenCV/ROS 套件相容性問題。
  - `torch = 2.11.0+cu128`，`torch.version.cuda = 12.8`，
    `torch.cuda.is_available() = True`。
- 在新版 image 內掛載本 repo，測試 `DroneHoverEnv` 與 `RealRosDroneAdapter`：
  - `part2.drone_env` import 正常。
  - `part2.ros_adapter` import 正常。
  - 使用 fake adapter 執行 `env.reset()` 與 `env.step()` 成功。
  - observation shape 為 `(12,)`。
  - action shape 為 `(3,)`。
- 檢查目前舊 container 內的 ROS topics，Gazebo/ROS 已經有資料：
  - `/simple_drone/gt_pose`
  - `/simple_drone/gt_vel`
  - `/simple_drone/cmd_vel`
  - `/simple_drone/takeoff`
  - `/simple_drone/reset`
- 抽樣 ROS topic：
  - `/simple_drone/gt_pose` 顯示目前 drone 約在地面附近，`z ~= 0.05`。
  - `/simple_drone/gt_vel` 顯示線速度幾乎為 0。

### 結論

- Part 2 的 Python/RL 套件在新版 image 裡已可用。
- `DroneHoverEnv` 初版邏輯可以正常 reset/step。
- `RealRosDroneAdapter` 可以在 ROS 環境中 import，且老師環境提供的必要 topic
  名稱與 adapter 設計相符。
- 下一個阻塞點不是程式邏輯，而是執行流程：正式訓練時需要用新版 image 重開
  container，並把 repo 掛載進 container，否則 container 裡看不到最新的 `part2`
  程式，也沒有 RL 套件。

## 2026-05-20 - 釐清下一步工作順序

### 已確認內容

- 再次用目前的 `nsysu_drone_vnc:iron` image 開短命 container 測試，確認新版
  image 已經包含 Part 2 需要的 RL/GPU 套件：
  - `torch = 2.11.0+cu128`
  - `torch.version.cuda = 12.8`
  - `torch.cuda.is_available() = True`
  - `numpy = 1.26.4`
  - `stable_baselines3`、`gymnasium`、`rclpy` import 正常。
- 因此目前問題不是 image 裡缺套件，而是正式啟動 container 時要確保使用新版
  image，並且讓 container 看得到外面的 repo。

### 下一步

- 優先修改 `Assignment2_env/run_docker.sh`，讓它啟動 container 時掛載 repo：
  - host repo：`/data2/pg/code/RL_Assignment2`
  - container path：`/workspace/RL_Assignment2`
- 重開新版 container 後，在 container 裡跑 `part2` 程式。
- 接著做 `RealRosDroneAdapter` 端到端測試：
  - reset drone。
  - takeoff。
  - 讀取 `/simple_drone/gt_pose` 與 `/simple_drone/gt_vel`。
  - 發送一個很小的 zero/velocity command。
  - 確認 drone 狀態能被 Python 正確讀回。
- Adapter 測通後，再建立正式 `part2/train.py`，開始 PPO 訓練流程。

## 2026-05-20 - 修改 Docker 啟動腳本掛載 repo

### 已完成內容

- 修改 `Assignment2_env/run_docker.sh`，讓 script 自動推算 repo 根目錄：
  - `SCRIPT_DIR`：`run_docker.sh` 所在資料夾。
  - `REPO_ROOT`：`Assignment2_env` 的上一層，也就是整份作業 repo。
  - `CONTAINER_REPO`：container 內固定路徑 `/workspace/RL_Assignment2`。
- 在 `docker run` 加上：
  - `-v "${REPO_ROOT}:${CONTAINER_REPO}"`
  - `-w "${CONTAINER_REPO}"`
- 啟動畫面現在會顯示 workspace 掛載關係，方便確認外部 repo 有沒有正確掛進
  container。

### 驗證

- 已執行 `bash -n Assignment2_env/run_docker.sh`，shell 語法檢查通過。
- 下一次用新版 image 啟動 container 後，應可直接在 container 內進入
  `/workspace/RL_Assignment2` 執行 Part 2 程式。

## 2026-05-20 - 規劃 `RealRosDroneAdapter` 手動測試流程

### 測試目標

- 在新版 Docker/ROS container 裡確認 `RealRosDroneAdapter` 可以完成 Task A
  訓練前需要的基本控制能力：
  - reset drone。
  - takeoff。
  - 讀取 `/simple_drone/gt_pose`。
  - 讀取 `/simple_drone/gt_vel`。
  - 發送 `/simple_drone/cmd_vel`。

### 測試流程

- 先用新版 image 啟動 container，並確認 repo 被掛載到
  `/workspace/RL_Assignment2`。
- 在 container 中啟動老師提供的模擬環境 `launch_drone`。
- 開第二個 container terminal，source ROS 環境後檢查 topics：
  - `ros2 topic list`
  - `ros2 topic echo --once /simple_drone/gt_pose`
  - `ros2 topic echo --once /simple_drone/gt_vel`
- 接著用一段短 Python 腳本建立 `RealRosDroneAdapter`，依序測試 reset、
  takeoff、讀 pose/velocity、送小速度命令、停止。

### 尚未完成

- 尚未由使用者實際執行端到端測試。
- 測試通過後，下一步才建立正式 `part2/train.py`。

## 2026-05-20 - `RealRosDroneAdapter` 端到端測試通過

### 實測結果

- 使用者在新版 container 內確認 `/simple_drone` 相關 ROS topics 都存在，包括：
  - `/simple_drone/gt_pose`
  - `/simple_drone/gt_vel`
  - `/simple_drone/cmd_vel`
  - `/simple_drone/reset`
  - `/simple_drone/takeoff`
- `ros2 topic echo --once /simple_drone/gt_pose` 成功讀到 pose，初始高度約
  `z = 0.0500`。
- `ros2 topic echo --once /simple_drone/gt_vel` 成功讀到 velocity，初始速度接近 0。
- 使用 `RealRosDroneAdapter` 執行 Python 端到端測試，結果如下：
  - reset 後 pose 約 `[0.000876, 0.000710, 0.049999]`，符合回到地面附近。
  - takeoff 並等待 3 秒後 pose 約 `z = 0.864`，表示 takeoff topic 有作用。
  - 發送 `cmd_vel = [0.0, 0.0, 0.2]` 並等待 1 秒後 pose 約 `z = 0.995`，
    velocity 約 `vz = 0.193`，表示 `/simple_drone/cmd_vel` 有作用。
  - 發送 zero velocity 並等待 0.5 秒後 pose 約 `z = 1.050`，velocity 約
    `vz = 0.062`，表示 drone 仍有一些慣性或控制器收斂時間，後續訓練時需要讓
    stop/settle 等待時間足夠。

### 結論

- `RealRosDroneAdapter` 已確認可以完成 reset、takeoff、讀 pose、讀 velocity、
  發送 velocity command。
- Task A 的 ROS 連接層已經可以進入下一步：建立正式訓練腳本。

### 下一步

- 建立 `part2/train.py`，用 Stable-Baselines3 的 PPO 接上：
  - `RealRosDroneAdapter`
  - `DroneHoverEnv`
  - TensorBoard logging
  - model checkpoint 儲存
- 初版訓練先使用短 timesteps 做 pipeline 測試，確認 episode 可以正常跑完或中止。

## 2026-05-20 - 建立 Task A PPO 訓練腳本

### 已完成內容

- 建立 `part2/train.py`，作為 Task A hovering 的正式訓練入口。
- 訓練腳本使用 Stable-Baselines3 的 PPO：
  - policy：`MlpPolicy`
  - 預設 timesteps：`5_000`
  - learning rate：`3e-4`
  - `n_steps = 256`
  - `batch_size = 64`
  - `gamma = 0.99`
  - `gae_lambda = 0.95`
  - `clip_range = 0.2`
- 訓練腳本會建立：
  - `RealRosDroneAdapter`
  - `DroneHoverEnv`
  - `Monitor` wrapper
  - `CheckpointCallback`
- 新增 CLI 參數，方便之後調整：
  - target position：`--target-x`、`--target-y`、`--target-z`
  - environment：`--episode-horizon`、`--control-dt`、
    `--takeoff-settle-time`、`--max-linear-speed`
  - success criteria：`--success-radius`、`--success-speed`、
    `--success-hold-steps`
  - PPO 參數：`--learning-rate`、`--n-steps`、`--batch-size`、
    `--gamma`、`--gae-lambda`、`--clip-range`、`--ent-coef`、`--vf-coef`
  - log/model：`--log-dir`、`--model-dir`、`--run-name`、`--checkpoint-freq`
  - resume：`--resume`
- 訓練前會先跑 `--preflight-steps` 個 zero-action step，確認 reset、observation、
  reward、distance、speed 都能正常印出。
- 訓練完成後會儲存 final model 到：
  - `part2/models/<run-name>_final.zip`
- 中途會依 `--checkpoint-freq` 存 checkpoint 到：
  - `part2/models/`
- 補上 `DroneHoverEnv.close()`，讓訓練結束時可以呼叫 adapter 的 `close()`，
  停止 drone 並關閉 ROS node。

### 驗證

- 已執行 `python3 -m py_compile part2/drone_env.py part2/ros_adapter.py part2/train.py`，
  語法檢查通過。
- 已用新版 Docker image 測試 `import part2.train`，通過。

### 下一步

- 在 Gazebo/ROS 已啟動的 container 中跑短訓練：
  - 建議先從 `--timesteps 1000` 開始。
  - 確認 model、checkpoint、monitor log、TensorBoard log 是否成功產生。
- 若短訓練能跑完，再開始觀察 reward 是否合理，必要時調整 reward weights、
  target height、takeoff settle time 或 success criteria。

## 2026-05-20 - 第一次 smoke training 觀察

### 使用者執行結果

- 使用者在 container 中執行：
  - `python3 -m part2.train --timesteps 1000 --checkpoint-freq 500 --run-name smoke_hover_001`
- 前面誤貼了一段 `import part2.train` 到 bash，因此出現：
  - `bash: import: command not found`
  - 此錯誤不影響後續訓練，因為真正的 `python3 -m part2.train ...` 有執行。
- Preflight 結果：
  - observation shape：`(12,)`
  - position 約 `[-0.0029, 0.0007, 3.6197]`
  - distance 約 `1.6197`
  - velocity 約 `[0, 0, 0.0098]`
  - zero-action step 連續 3 步皆未 terminated/truncated。
- PPO 開始訓練後，第一次 rollout 統計：
  - `total_timesteps = 256`
  - `time_elapsed = 407`
  - `ep_len_mean = 1`
  - `ep_rew_mean = -35`
  - `success_rate = 0`

### 判讀

- 程式沒有卡死；PPO 會每收集完 `n_steps = 256` 個 step 才印一次統計。
- 目前每 256 steps 花約 407 秒，主因是 `ep_len_mean = 1`，表示 episode 幾乎每
  一步就結束，導致大量 reset/takeoff overhead。
- 無人機一直動是訓練過程持續送 velocity command，以及失敗後反覆 reset/takeoff
  的結果。
- 這次 smoke training 不建議繼續等完整跑完，應先停止並診斷為什麼 episode
  長度幾乎都是 1。

### 下一步

- 建議先 Ctrl+C 停止目前訓練。
- 接著跑短診斷腳本，逐步印出 `position`、`distance`、`speed`、`is_failure`、
  `terminated`，找出訓練 episode 立即結束的原因。
- 可能需要調整 reset/takeoff 流程、workspace 高度上限、或 preflight/訓練前
  的無人機初始狀態。

## 2026-05-20 - 修正 `ep_len_mean = 1` 問題

### 問題原因

- 新增 `part2/diagnose_hover.py` 診斷腳本，直接用 `DroneHoverEnv` 跑固定或隨機
  action，不經過 PPO。
- 第一次診斷發現 reset 後 drone 高度約 `z = 11.3`，遠高於
  `workspace_high.z = 4.0`。
  - 第一個 action 後 `terminated=True`。
  - `failure_reason = above_workspace`。
- 因此第一次 smoke training 的 `ep_len_mean = 1` 不是 PPO 本身壞掉，而是
  episode reset 後起始狀態已經不合法。

### 嘗試修正

- `RealRosDroneAdapter.reset_pose()` 加入 Gazebo `/reset_world` service call。
- 加入後再診斷，drone 可以從 `z = 11.3` 回到地面附近，但起飛後仍只有
  `z ~= 0.06`，低於 `crash_height = 0.2`。
  - 第一個 action 後 `failure_reason = below_floor`。
- 手動測試 `/reset_world`、`/reset_simulation`、`/simple_drone/reset`、
  `/simple_drone/takeoff` 後，發現老師環境的 reset/takeoff 狀態不是每次都能把
  drone 放到安全訓練高度。

### 最終修正

- 在 `DroneHoverEnv.reset()` 裡新增 reset warm-up：
  - reset/takeoff 後，若高度低於 `reset_start_height`，就用
    `/simple_drone/cmd_vel` 發送向上速度。
  - 預設 `reset_start_height = 1.0`。
  - 預設 `reset_climb_speed = 0.5`。
  - 預設 `reset_climb_timeout = 8.0`。
  - 預設 `reset_settle_time = 0.5`。
- 這段 warm-up 不算 RL step，只是讓每個 episode 從安全且一致的高度開始。
- `info` 新增 `failure_reason`，方便後續 debug。
- `part2/train.py` 新增 reset warm-up 相關 CLI 參數。

### 驗證結果

- 重新跑 `part2.diagnose_hover --episodes 3 --steps 5 --action-mode random`：
  - reset 後高度約 `z = 1.15`。
  - `failure=False`。
  - `failure_reason=None`。
  - random action 連續多步都沒有立即 terminated。
- 重新跑短訓練：
  - 指令：
    `python3 -m part2.train --timesteps 128 --n-steps 64 --batch-size 32 --checkpoint-freq 64 --preflight-steps 1 --device cpu --run-name smoke_after_reset_fix`
  - 結果：
    - preflight reset 後 `distance ~= 0.8355`。
    - preflight `failure=False`。
    - PPO 跑完 `128` timesteps。
    - 沒有再出現 `ep_len_mean = 1`。
    - 成功儲存模型到 `part2/models/smoke_after_reset_fix_final.zip`。

### 結論

- `ep_len_mean = 1` 的主因已定位並修正：episode reset 起始高度不合法。
- 下一步可以重新跑較長的 smoke training，例如 `1000` timesteps，觀察 reward
  是否合理。

## 2026-05-20 - 分析 `1000` timesteps smoke training

### 使用者執行結果

- 執行指令：
  - `python3 -m part2.train --timesteps 1000 --n-steps 128 --batch-size 64 --checkpoint-freq 500 --preflight-steps 1 --device cpu --run-name smoke_hover_1000_reset_fix`
- Preflight：
  - reset 後 position 約 `[-0.0184, -0.0150, 1.1648]`。
  - distance 約 `0.8356`。
  - `failure=False`，`failure_reason=None`。
  - zero-action step 未 terminated/truncated。
- 訓練結果：
  - 實際跑到 `1024` timesteps，這是因為 PPO 會以 `n_steps=128` 為單位收集
    rollout。
  - FPS 約 `7~8`，符合真實 ROS/Gazebo 模擬環境每步等待 `control_dt=0.1` 的
    預期。
  - `ep_len_mean` 從先前的 `1` 改善到 `400`，後來約 `314`。
  - `success_rate = 0`。
  - `ep_rew_mean` 約 `-1.05e3` 到 `-1.19e3`。
  - 成功儲存：
    - `part2/models/smoke_hover_1000_reset_fix_checkpoint_500_steps.zip`
    - `part2/models/smoke_hover_1000_reset_fix_checkpoint_1000_steps.zip`
    - `part2/models/smoke_hover_1000_reset_fix_final.zip`
- Monitor log 顯示兩個已結束 episode：
  - episode 1：reward `-1050.738836`，length `400`。
  - episode 2：reward `-1331.667526`，length `227`。

### 判讀

- `ep_len_mean = 1` 問題已解決；episode 不再一開始就因非法高度結束。
- `success_rate = 0` 在 `1000` timesteps 的 smoke training 裡是合理的，因為 PPO
  幾乎還在隨機探索。
- `entropy_loss ~= -4.25`、`std ~= 1` 表示 policy 仍很隨機，尚未學到穩定策略。
- `explained_variance` 接近 0 或負值，代表 critic 還沒學好，早期訓練常見。
- 目前 monitor log 只記 reward/episode length，還不足以判斷 episode 2 為什麼在
  227 steps 結束，因此需要把 `failure_reason`、`distance_to_target`、`speed`
  等 info 寫進 monitor log。

### 已做修正

- 修改 `part2/train.py` 的 `Monitor` wrapper，新增 `info_keywords`：
  - `is_success`
  - `is_failure`
  - `failure_reason`
  - `distance_to_target`
  - `speed`
  - `stable_steps`
- 修改 `part2/diagnose_hover.py`，新增 `target` action mode，用簡單 PD controller
  驗證環境是否可解。

### PD baseline 驗證

- 執行：
  - `python3 -m part2.diagnose_hover --episodes 1 --steps 120 --action-mode target --target-kp 0.8 --target-kd 0.3`
- 結果：
  - 從 `z ~= 1.1659` 起始。
  - 約第 18 step 進入 success radius 附近。
  - 第 68 step 達成 `stable_steps = 50`。
  - 終止時 `success=True`，`failure=False`，`distance ~= 0.0026`，
    `speed ~= 0.0023`。
- 這表示 Task A 環境、reward、success criteria 本身是可解的。

### 下一步

- 下一輪訓練應先使用更完整的 monitor log 重跑，方便分析每個 episode 結束原因。
- 建議使用較小 action range 或更容易的 curriculum 起點：
  - `--max-linear-speed 0.5`
  - 或 `--reset-start-height 1.5`
- 建議下一輪先跑 `5000` timesteps，不需要期待完全成功，但要觀察：
  - `ep_rew_mean` 是否變得比較不負。
  - `distance_to_target` 是否下降。
  - episode 結束原因是否主要是 timeout 而不是 failure。
  - `stable_steps` 是否開始增加。

## 2026-05-20 - 分析 `hover_curriculum_5000_v1`

### 使用者執行結果

- 執行 curriculum smoke training：
  - `--timesteps 5000`
  - `--max-linear-speed 0.5`
  - `--reset-start-height 1.5`
  - `--run-name hover_curriculum_5000_v1`
- 成功產出：
  - `part2/logs/hover_curriculum_5000_v1.monitor.csv`
  - `part2/models/hover_curriculum_5000_v1_checkpoint_1000_steps.zip`
  - `part2/models/hover_curriculum_5000_v1_checkpoint_2000_steps.zip`
  - `part2/models/hover_curriculum_5000_v1_checkpoint_3000_steps.zip`
  - `part2/models/hover_curriculum_5000_v1_checkpoint_4000_steps.zip`
  - `part2/models/hover_curriculum_5000_v1_checkpoint_5000_steps.zip`
  - `part2/models/hover_curriculum_5000_v1_final.zip`

### Monitor 統計

- 共記錄 `21` 個 episode。
- 成功 episode：`0`。
- Timeout episode：`4`。
  - 平均 reward 約 `-1040.82`。
  - episode length 全部為 `400`。
  - 結束時平均 distance 約 `2.28`。
- Failure episode：`17`。
  - 全部都是 `failure_reason = above_workspace`。
  - 平均 reward 約 `-476.17`。
  - 平均 episode length 約 `187.06`。
  - 結束時平均 distance 約 `2.53`。

### 判讀

- 訓練 pipeline 正常，checkpoint/model/log 都有產出。
- reset 起始狀態問題已解決，因為 episode 不再一開始就死。
- 目前主要問題變成 reward 設計：
  - failure episode 的 reward 平均 `-476`。
  - timeout episode 的 reward 平均 `-1041`。
  - 這代表「早點飛出上界」反而比「努力撐完整個 episode」看起來更不差。
- 這會誤導 PPO，讓 policy 不會強烈避免 `above_workspace`。
- `success_rate = 0` 在 5000 timesteps 仍可接受，但 failure reward 比 timeout reward
  好這件事需要先修正。

### 已做修正

- 將 `DroneHoverConfig` 預設 reward terminal 參數調整：
  - `success_bonus: 25.0 -> 200.0`
  - `failure_penalty: 25.0 -> 500.0`
- `part2/train.py` 新增 CLI 參數，之後不用改 code 即可調 reward：
  - `--progress-weight`
  - `--distance-weight`
  - `--velocity-weight`
  - `--control-weight`
  - `--smoothness-weight`
  - `--hover-bonus`
  - `--success-bonus`
  - `--failure-penalty`
- `part2/diagnose_hover.py` 同步支援：
  - `--success-bonus`
  - `--failure-penalty`

### 下一步

- 用新的 terminal reward 重新跑一輪 curriculum。
- 建議維持容易起點與較小 action range，但增加訓練長度：
  - `--timesteps 10000`
  - `--max-linear-speed 0.3`
  - `--reset-start-height 1.8`
  - `--success-hold-steps 30`
  - `--failure-penalty 500`
  - `--success-bonus 200`
- 觀察重點：
  - `above_workspace` failure 是否下降。
  - failure episode 的 reward 是否明顯比 timeout 更糟。
  - `stable_steps` 是否開始上升。
  - 是否出現第一個 success episode。

## 2026-05-21 - 分析 `hover_curriculum_10000_v2`

### 使用者執行結果

- 使用者完成 `hover_curriculum_10000_v2`。
- 成功產出：
  - `part2/logs/hover_curriculum_10000_v2.monitor.csv`
  - `part2/models/hover_curriculum_10000_v2_checkpoint_2000_steps.zip`
  - `part2/models/hover_curriculum_10000_v2_checkpoint_4000_steps.zip`
  - `part2/models/hover_curriculum_10000_v2_checkpoint_6000_steps.zip`
  - `part2/models/hover_curriculum_10000_v2_checkpoint_8000_steps.zip`
  - `part2/models/hover_curriculum_10000_v2_checkpoint_10000_steps.zip`
  - `part2/models/hover_curriculum_10000_v2_final.zip`

### Monitor 統計

- 共記錄 `29` 個 episode。
- Success episode：`3`。
  - 平均 reward 約 `188.64`。
  - 平均 length 約 `40.33`。
  - 結束時平均 distance 約 `0.165`。
  - 結束時平均 speed 約 `0.126`。
  - `stable_steps = 30`。
- Failure episode：`7`。
  - 全部仍是 `failure_reason = above_workspace`。
  - 平均 reward 約 `-1324.79`。
  - 平均 length 約 `295`。
- Timeout episode：`19`。
  - 平均 reward 約 `-948.30`。
  - 平均 length `400`。
- 相比 `5000_v1`：
  - success 從 `0` 增加到 `3`。
  - `above_workspace` failure 從 `17/21` 降到 `7/29`。
  - failure reward 已比 timeout reward 更差，terminal reward 修正有效。

### Deterministic evaluation

- 使用 `hover_curriculum_10000_v2_final.zip` 做 deterministic policy evaluation。
- 起始狀態已非常接近 target：
  - reset distance 約 `0.0355`
  - position 約 `z = 1.9736`
  - speed 約 `0.1435`
- 但 deterministic policy 沒有停住，而是逐漸離開 target：
  - step 21 distance 約 `0.4204`
  - step 61 distance 約 `1.7052`
  - step 121 distance 約 `3.7504`
  - step 141 觸發 `failure_reason = above_workspace`
- 結論：這輪出現 success，但 final policy 還沒有真正學到「接近 target 時輸出小速度
  並穩定懸停」。success 很可能多半來自 stochastic exploration 的偶然成功。

### 下一步

- 進入更簡單的 hold curriculum：
  - 讓 reset 起點幾乎就在 target 附近。
  - 明顯降低 action range。
  - 加大 hover bonus。
  - 縮短 success hold steps。
- 目標不是先學從遠處飛到 target，而是先學會「靠近 target 時不要亂動，穩定停住」。
- 等 deterministic policy 能穩定 hover 後，再逐步增加難度：
  - 拉低 reset 起點高度。
  - 增加 success hold steps。
  - 增加 max action range。

## 2026-05-22 - 分析 `hover_hold_15000_v3`

### 使用者執行結果

- 使用者完成 hold curriculum 訓練。
- 成功產出：
  - `part2/logs/hover_hold_15000_v3.monitor.csv`
  - `part2/models/hover_hold_15000_v3_checkpoint_3000_steps.zip`
  - `part2/models/hover_hold_15000_v3_checkpoint_6000_steps.zip`
  - `part2/models/hover_hold_15000_v3_checkpoint_9000_steps.zip`
  - `part2/models/hover_hold_15000_v3_checkpoint_12000_steps.zip`
  - `part2/models/hover_hold_15000_v3_checkpoint_15000_steps.zip`
  - `part2/models/hover_hold_15000_v3_final.zip`

### Monitor 統計

- 共記錄 `329` 個 episode。
- Success episode：`234`。
  - 平均 reward 約 `314.27`。
  - 平均 length 約 `11.19`。
  - 結束時平均 distance 約 `0.181`。
  - 結束時平均 speed 約 `0.059`。
  - `stable_steps = 10`。
- Failure episode：`71`。
  - failure reasons：
    - `above_workspace = 63`
    - `too_far_from_target = 6`
    - `below_floor = 2`
  - 平均 reward 約 `-681.97`。
  - 平均 length 約 `37.0`。
- Timeout episode：`24`。
  - 平均 reward 約 `-976.43`。
  - 平均 length `400`。
- 相比 `hover_curriculum_10000_v2`：
  - success 從 `3/29` 大幅提升到 `234/329`。
  - 代表 hold curriculum 確實讓 agent 更容易得到成功訊號。

### Deterministic evaluation

- 使用 `hover_hold_15000_v3_final.zip` 做 deterministic evaluation。
- reset 後已接近 target：
  - distance 約 `0.1271`
  - position 約 `z = 2.1248`
  - speed 約 `0.1435`
- 但 deterministic policy 輸出幾乎固定在 action 邊界：
  - action 約 `[-0.1, 0.1, 0.1]`
- 結果逐步離開 target：
  - step 1 distance 約 `0.1416`
  - step 21 distance 約 `0.4208`
  - step 81 distance 約 `1.4592`
  - step 141 distance 約 `2.5201`
  - step 176 觸發 `failure_reason = above_workspace`
- 結論：
  - training 中的 stochastic policy 很常成功。
  - 但 deterministic mean policy 仍未學會輸出接近 zero 的穩定 hover action。
  - 目前 action distribution/探索尺度仍是主要問題。

### 已做修正

- `part2/train.py` 新增 `--log-std-init`。
- 預設 `log_std_init = -2.0`，讓 PPO Gaussian policy 初始 std 從 SB3 預設的
  `1.0` 降低到約 `0.135`。
- 原因：
  - 目前 action range 很小，例如 `[-0.1, 0.1]`。
  - 若 Gaussian std 太大，sampled action 幾乎都會被 clip 到邊界。
  - 這會讓 policy mean 學到奇怪的邊界動作，而不是 hover 需要的小動作。

### 下一步

- 重跑 hold curriculum，但使用較小的初始 std。
- 建議下一輪：
  - `--log-std-init -3.0`
  - `--max-linear-speed 0.1`
  - `--reset-start-height 1.95`
  - `--success-hold-steps 10`
  - 保持較大的 action/velocity/smoothness penalty。
- 觀察重點：
  - deterministic action 是否不再長期卡在 `[-0.1, 0.1, 0.1]`。
  - deterministic evaluation 是否能成功 hover。
  - success episode 是否維持高比例。

## 2026-05-22 - 分析 `hover_hold_20000_v4`

### 使用者執行結果

- 使用者完成 `hover_hold_20000_v4`。
- 成功產出：
  - `part2/logs/hover_hold_20000_v4.monitor.csv`
  - `part2/models/hover_hold_20000_v4_checkpoint_4000_steps.zip`
  - `part2/models/hover_hold_20000_v4_checkpoint_8000_steps.zip`
  - `part2/models/hover_hold_20000_v4_checkpoint_12000_steps.zip`
  - `part2/models/hover_hold_20000_v4_checkpoint_16000_steps.zip`
  - `part2/models/hover_hold_20000_v4_checkpoint_20000_steps.zip`
  - `part2/models/hover_hold_20000_v4_final.zip`

### Monitor 統計

- 共記錄 `840` 個 episode。
- Success episode：`807`，約 `96.1%`。
  - 平均 reward 約 `314.91`。
  - 平均 length 約 `10.11`。
  - 結束時平均 distance 約 `0.184`。
  - 結束時平均 speed 約 `0.041`。
  - `stable_steps = 10`。
- Failure episode：`12`，約 `1.4%`。
  - 全部為 `failure_reason = above_workspace`。
  - 平均 reward 約 `-1348.50`。
- Timeout episode：`21`，約 `2.5%`。
  - 平均 reward 約 `-767.58`。
- 最後 10 個 episode 全部 success。

### 和 `hover_hold_15000_v3` 比較

- Success rate：
  - `v3`: `234/329 = 71.1%`
  - `v4`: `807/840 = 96.1%`
- Failure rate：
  - `v3`: `71/329 = 21.6%`
  - `v4`: `12/840 = 1.4%`
- 結束速度：
  - `v3` success 平均 speed 約 `0.059`
  - `v4` success 平均 speed 約 `0.041`
- 結論：
  - 降低 `log_std_init` 加上更強的 velocity/control/smoothness penalty 有明顯效果。
  - hold curriculum 幾乎已經學起來。

### 尚未完成

- 嘗試做 deterministic evaluation，但 `nsysu_drone_vnc` container 已關閉，無法直接
  評估 final model。
- 下一步必須重開 container/Gazebo，使用 `hover_hold_20000_v4_final.zip` 做
  deterministic evaluation。

### 下一步

- 先做 deterministic evaluation，確認 final mean policy 是否真的能穩定 hover。
- 若 deterministic evaluation 成功：
  - 將課程難度往 Task A 正式條件推進。
  - 建議下一階段：
    - `success_hold_steps: 10 -> 20`
    - `reset_start_height: 1.95 -> 1.8`
    - `max_linear_speed: 0.1 -> 0.15`
- 若 deterministic evaluation 仍失敗：
  - 先不要加難度。
  - 繼續降低 action std 或增加 action penalty。

## 2026-05-22 - `hover_hold_20000_v4` deterministic evaluation 通過

### Evaluation 設定

- 使用模型：
  - `part2/models/hover_hold_20000_v4_final.zip`
- 使用與 `v4` 訓練相同的環境設定：
  - `max_linear_speed = 0.1`
  - `reset_start_height = 1.95`
  - `success_hold_steps = 10`
  - `hover_bonus = 2.0`
  - `success_bonus = 300.0`
  - `failure_penalty = 500.0`
  - `velocity_weight = 1.5`
  - `control_weight = 0.5`
  - `smoothness_weight = 0.3`

### Evaluation 結果

- reset 後狀態：
  - distance 約 `0.1102`
  - position 約 `[0.0013, 0.0024, 2.1102]`
  - speed 約 `0.1532`
  - `failure=False`
- deterministic policy action 不再卡在邊界：
  - step 1 action 約 `[0.0435, -0.0022, -0.0021]`
  - step 6 action 約 `[0.0451, -0.0024, -0.0033]`
  - step 10 action 約 `[0.0470, -0.0005, -0.0016]`
- step 10 達成：
  - `stable_steps = 10`
  - `success=True`
  - `failure=False`
  - distance 約 `0.1672`
  - speed 約 `0.045`

### 結論

- `hover_hold_20000_v4` 已經成功學到 deterministic hover policy。
- `--log-std-init -3.0` 修正了前一輪 deterministic policy 卡在 action 邊界的問題。
- 下一階段可以開始逐步提高 Task A 難度：
  - 增加穩定懸停持續時間。
  - 讓 reset 起點離 target 稍遠。
  - 之後再逐步加大 action range。

### 下一步

- 建議下一輪先保持 action range `0.1`，避免同時改太多條件。
- 將：
  - `success_hold_steps: 10 -> 20`
  - `reset_start_height: 1.95 -> 1.8`
- 從 `hover_hold_20000_v4_final.zip` resume 訓練，因為 action space 未改變。

## 2026-05-22 - 分析 `hover_hold_15000_v5`

### 使用者執行結果

- 使用者從 `hover_hold_20000_v4_final.zip` resume，完成
  `hover_hold_15000_v5`。
- 本輪 curriculum 調整：
  - `reset_start_height: 1.95 -> 1.8`
  - `success_hold_steps: 10 -> 20`
  - `max_linear_speed` 維持 `0.1`
  - reward weights 維持 v4 設定
- 因為 `train.py` 在 resume 時使用 `reset_num_timesteps=False`，所以 checkpoint
  檔名接續前一個模型的 timestep，例如 `23096`、`26096`，這是正常現象。

### Monitor 統計

- 共記錄 `728` 個 episode。
- Success episode：`726`，約 `99.7%`。
  - 平均 reward 約 `335.67`。
  - 平均 length 約 `20.02`。
  - 結束時平均 distance 約 `0.056`。
  - 結束時平均 speed 約 `0.048`。
  - `stable_steps = 20`。
- Failure episode：`2`，約 `0.3%`。
  - 全部為 `failure_reason = above_workspace`。
  - 平均 reward 約 `-1226.37`。
- Timeout episode：`0`。
- 最後 10 個 episode 全部 success，且 length 都是 `20`。

### 和 `hover_hold_20000_v4` 比較

- Success rate：
  - `v4`: `807/840 = 96.1%`
  - `v5`: `726/728 = 99.7%`
- Failure rate：
  - `v4`: `12/840 = 1.4%`
  - `v5`: `2/728 = 0.3%`
- Success 結束距離：
  - `v4` 平均 distance 約 `0.184`
  - `v5` 平均 distance 約 `0.056`
- 結論：
  - 把 success hold 從 10 steps 增加到 20 steps 後，模型不但沒有退步，反而更穩。
  - 從 `1.8` 起始高度的 hold curriculum 已經可以穩定達成。

### Deterministic evaluation

- 使用模型：
  - `part2/models/hover_hold_15000_v5_final.zip`
- 使用與 v5 訓練相同的環境設定。
- reset 後狀態：
  - distance 約 `0.0394`
  - position 約 `[-0.0184, -0.0150, 1.9686]`
  - speed 約 `0.1435`
  - `failure=False`
- deterministic policy 輸出已不是邊界亂衝，而是小幅控制：
  - step 1 action 約 `[0.0057, 0.0525, -0.0583]`
  - step 6 action 約 `[0.0049, 0.0581, -0.0608]`
  - step 16 action 約 `[0.0039, 0.0611, -0.0611]`
- step 20 達成：
  - `stable_steps = 20`
  - `success=True`
  - `failure=False`
  - distance 約 `0.0906`
  - speed 約 `0.0777`
  - total reward 約 `335.59`

### 結論

- `hover_hold_15000_v5` deterministic evaluation 通過。
- 目前 agent 已經能在接近 target 的起點穩定 hover 20 steps。
- 下一步不需要大改 reward；應該繼續做 curriculum，把正式 Task A 條件慢慢加回來。

### 下一步

- 建議下一輪 `hover_hold_15000_v6`：
  - `success_hold_steps: 20 -> 30`
  - `reset_start_height: 1.8 -> 1.6`
  - `max_linear_speed` 先維持 `0.1`
- 這樣一次只增加兩個難度：
  - 需要穩定懸停更久。
  - 起始高度離 target 稍微更遠。
- 若 v6 deterministic evaluation 通過，再往：
  - `success_hold_steps = 50`
  - `reset_start_height = 1.3~1.5`
  - 或加入 disturbance / 更隨機的起始狀態
  推進。

## 2026-05-22 - CPU/GPU 資源使用確認

### 檢查背景

- 因為每輪 PPO + Gazebo 訓練時間較長，確認是否改用 GPU 能加速，以及目前是否
  占用過多 CPU。

### 目前 container 狀態

- 目前 `nsysu_drone_vnc` container 正在執行，但沒有偵測到
  `python3 -m part2.train` 訓練程序。
- `docker stats` 顯示：
  - CPU 約 `180.78%`，約等於使用 `1.8` 個 CPU core。
  - Memory 約 `2.144 GiB / 62.48 GiB`，約 `3.43%`。
  - container 可見 CPU cores：`32`。
- 主要 CPU 使用者：
  - `gzclient` 約 `85.7%`
  - `gzserver` 約 `55.9%`
  - `rviz2` 約 `31.2%`
  - `Xvnc` 約 `27.5%`
- GPU 狀態：
  - GPU：`NVIDIA RTX A6000`
  - GPU utilization 約 `37%`
  - GPU memory 約 `859 MiB / 49140 MiB`
  - 沒有偵測到 PyTorch compute process；目前 GPU 使用多半來自 Gazebo/RViz
    視覺化或顯示相關負載。

### 判斷

- 目前沒有訓練程序時，CPU 使用量主要來自 Gazebo GUI、RViz、VNC，不是 PPO。
- 對 32-core server 來說，目前約 `1.8 cores` 的使用量不算過高。
- PPO 使用 `MlpPolicy`，神經網路很小；真實瓶頸是 ROS/Gazebo environment step
  與 `control_dt = 0.1` 的等待，因此改 `--device cuda` 通常不會明顯加速，甚至
  可能因 CPU/GPU 資料搬移 overhead 變慢。
- 若要真的加速，優先方向不是改 GPU，而是：
  - 減少 GUI 負載，例如不用時關閉 RViz/Gazebo client。
  - 使用 headless 模式。
  - 調小 `control_dt`，但這會改變控制頻率與任務設定，需要小心。
  - 多環境並行，但目前一個 Gazebo world 不容易直接用 SB3 vector env 平行化。

## 2026-05-22 - 分析 `hover_hold_15000_v6`

### 使用者執行結果

- 使用者從 `hover_hold_15000_v5_final.zip` resume，完成
  `hover_hold_15000_v6`。
- 本輪原本想同時增加兩個難度：
  - `reset_start_height: 1.8 -> 1.6`
  - `success_hold_steps: 20 -> 30`
- 成功產出：
  - `part2/logs/hover_hold_15000_v6.monitor.csv`
  - `part2/models/hover_hold_15000_v6_final.zip`

### Monitor 統計

- 共記錄 `40` 個 episode。
- Success episode：`0`。
- Failure episode：`9`，約 `22.5%`。
  - `below_floor = 8`
  - `above_workspace = 1`
  - 平均 reward 約 `-1302.94`
  - 平均 length 約 `263.11`
- Timeout episode：`31`，約 `77.5%`。
  - 平均 reward 約 `-1259.19`
  - 結束時平均 distance 約 `2.172`
  - 結束時平均 speed 約 `0.016`
- 最後 10 個 episodes 全部 timeout，沒有 success。

### Deterministic evaluation

- 用 v6 設定評估 `hover_hold_15000_v5_final.zip`：
  - reset 後 position 約 `z = 1.7676`，distance 約 `0.2336`。
  - policy 輸出 z 方向約 `-0.056 ~ -0.066`，也就是從 target 下方仍持續往下飛。
  - 第 21 step 後離開 success radius，`stable_steps` 歸零。
  - 第 120 step distance 約 `1.099`，沒有成功。
- 用 v6 設定評估 `hover_hold_15000_v6_final.zip`：
  - reset 後 position 約 `z = 1.7693`，distance 約 `0.2319`。
  - 同樣持續往下與側向漂移。
  - 第 120 step distance 約 `0.8694`，沒有成功。

### 額外驗證

- 使用 `hover_hold_15000_v5_final.zip`，但只改：
  - `reset_start_height = 1.8`
  - `success_hold_steps = 30`
- deterministic evaluation 成功：
  - reset distance 約 `0.037`
  - step 30 達成 `success=True`
  - step 30 distance 約 `0.1709`
- 使用同一個 v5 模型測 `success_hold_steps = 50`：
  - 前 30 steps 仍在 success radius 內。
  - 第 41 step distance 約 `0.2637`，超過 success radius，`stable_steps` 歸零。
  - 第 120 step distance 約 `0.9588`，沒有成功。

### 判斷

- v6 失敗主因不是 `success_hold_steps = 30` 太難，而是我們同時把
  `reset_start_height` 降到 `1.6`。
- v5 policy 是從接近 target 的狀態學到的，當起點在 target 下方時，它仍輸出負的
  z velocity，造成慢慢往下離開 target。
- v5 目前可以穩定 30 steps，但還不能穩到 50 steps；它會慢慢往 y 方向與下方漂移。
- 因此下一輪不應從 v6 resume，也不應繼續降低 reset height。

### 下一步

- 捨棄 v6 作為 resume 起點，回到 `hover_hold_15000_v5_final.zip`。
- 先只增加 hover duration，不降低起始高度：
  - `reset_start_height = 1.8`
  - `success_hold_steps = 40`
- 稍微加重 reward 對 drift 的懲罰：
  - `distance_weight: 2.0 -> 3.0`
  - `velocity_weight: 1.5 -> 2.0`
  - `control_weight: 0.5 -> 0.7`
  - `smoothness_weight: 0.3 -> 0.4`
- 使用較小 learning rate `1e-4` 做 fine-tuning，避免已學會的 hover policy 被破壞。

## 2026-05-22 - 分析 `hover_hold_12000_v7`

### 使用者執行結果

- 使用者從 `hover_hold_15000_v5_final.zip` resume，完成
  `hover_hold_12000_v7`。
- 本輪設定：
  - `reset_start_height = 1.8`
  - `success_hold_steps = 40`
  - `learning_rate = 1e-4`
  - `distance_weight = 3.0`
  - `velocity_weight = 2.0`
  - `control_weight = 0.7`
  - `smoothness_weight = 0.4`
- 成功產出：
  - `part2/logs/hover_hold_12000_v7.monitor.csv`
  - `part2/models/hover_hold_12000_v7_final.zip`

### Monitor 統計

- 共記錄 `50` 個 episode。
- Success episode：`23`，約 `46.0%`。
  - 平均 reward 約 `360.17`
  - episode length 全部為 `40`
  - 結束時平均 distance 約 `0.206`
  - 結束時平均 speed 約 `0.076`
  - `stable_steps = 40`
- Failure episode：`0`。
- Timeout episode：`27`，約 `54.0%`。
  - 平均 reward 約 `-1746.04`
  - 結束時平均 distance 約 `2.486`
  - 結束時平均 speed 約 `0.064`
- episode 時間序列顯示：
  - 前 24 個 episode 中，除了第 4 個以外幾乎全部 success。
  - 從第 25 個 episode 開始全部 timeout。
  - 最後 10 個 episode 全部 timeout。

### Deterministic / checkpoint evaluation

- 使用 v7 設定評估 `hover_hold_15000_v5_final.zip`：
  - reset 正常時 max stable steps 約 `39`。
  - 距離在第 40 step 左右超出 success radius。
  - 主要問題是持續往 y 方向與下方慢慢漂移。
- 使用 v7 checkpoints / final 評估：
  - v7 checkpoint 與 final 都沒有通過 deterministic evaluation。
  - v7 final 在 y 方向 action 幾乎卡在 `+0.1` 邊界。
  - final max stable steps 約 `32`，第 120 step distance 約 `1.128`。
- 判斷：
  - v7 訓練後段把原本 v5 已經會的 hover policy 破壞掉。
  - final model 不適合當下一輪 resume 起點。

### 發現 reset 污染問題

- checkpoint evaluation 時發現一個更根本的環境問題：
  - 前一個 evaluation 結束時 drone 漂到 `y ~= 0.72`。
  - 下一次 `env.reset()` 後，起始位置仍可能在 `y ~= 0.76`，沒有回到原點。
- 這代表目前的 `reset_pose()` 只用 `/simple_drone/reset` 和 `/reset_world` 不夠可靠。
- 這也能解釋 v7 訓練為什麼前 24 集成功、後面突然全部 timeout：
  - episode 之間的 x/y 位置可能累積漂移。
  - 後續 episode 起點離 target 越來越遠，但這並不是原本 curriculum 想訓練的分布。

### 已做修正

- 測試 `/reset_simulation`，確認它可以把 drone pose 清回原點附近：
  - reset 後約 `x = -0.0185`
  - reset 後約 `y = -0.0151`
  - reset 後約 `z = 0.0653`
- 修改 `part2/ros_adapter.py`：
  - 新增 `/reset_simulation` client。
  - `reset_pose()` 優先呼叫 `/reset_simulation`。
  - 若 `/reset_simulation` 不存在，才 fallback 到 `/reset_world`。
  - simulation reset 後再次 publish `/simple_drone/reset`，同步重置 drone plugin
    controller 狀態。
- 驗證：
  - 先用 velocity command 故意把 drone 推到 `y ~= 0.475`。
  - 連續三次呼叫 `reset_pose()` 後，都回到約
    `x ~= -0.017`、`y ~= -0.014`、`z ~= 0.058`。
  - `python3 -m py_compile part2/ros_adapter.py part2/drone_env.py part2/train.py`
    通過。

### 下一步

- 不要從 v7 final resume。
- 回到 `hover_hold_15000_v5_final.zip`，在 reset 修正後重新做 fine-tuning。
- 為避免 agent 用「慢慢漂但撐滿 40 steps」取得 success，下一輪建議：
  - 維持 `reset_start_height = 1.8`。
  - 維持 `success_hold_steps = 40`。
  - 將 `success_radius` 從 `0.25` 收緊到 `0.18`。
  - 加強 distance / velocity / control / smoothness penalty。
  - 使用更小 learning rate `5e-5`，避免破壞 v5 policy。

## 2026-05-23 - 分析 `hover_hold_8000_v8_resetfix_tight`

### 使用者執行結果

- 使用者從 `hover_hold_15000_v5_final.zip` resume，完成
  `hover_hold_8000_v8_resetfix_tight`。
- 本輪使用已修正的 reset 流程，也就是 `reset_pose()` 優先呼叫
  `/reset_simulation`。
- 本輪設定：
  - `reset_start_height = 1.8`
  - `success_radius = 0.18`
  - `success_hold_steps = 40`
  - `learning_rate = 5e-5`
  - `distance_weight = 4.0`
  - `velocity_weight = 2.0`
  - `control_weight = 1.0`
  - `smoothness_weight = 0.6`

### Monitor 統計

- 共記錄 `21` 個 episode。
- Success episode：`0`。
- Failure episode：`6`，約 `28.6%`。
  - `below_floor = 5`
  - `above_workspace = 1`
  - 平均 reward 約 `-2392.79`
  - 平均 length 約 `335.17`
- Timeout episode：`15`，約 `71.4%`。
  - 平均 reward 約 `-1989.92`
  - 結束時平均 distance 約 `2.161`
  - 結束時平均 speed 約 `0.089`
- 最後 10 個 episode 全部未成功。

### Deterministic / checkpoint evaluation

- 這次 evaluation 的 reset 起點都穩定回到原點附近：
  - reset distance 約 `0.03~0.04`
  - position 約 `x ~= -0.018`、`y ~= -0.015`、`z ~= 1.97`
- 因此前一輪發現的 reset 污染問題已改善。
- 但在 `success_radius = 0.18`、`success_hold_steps = 40` 的 tight 設定下：
  - `hover_hold_15000_v5_final.zip` deterministic max stable steps 約 `31`。
  - v8 checkpoints / final max stable steps 約 `21~26`。
  - 全部沒有成功。
- 在放寬回 `success_radius = 0.25`、`success_hold_steps = 40` 的設定下：
  - v5 final max stable steps 約 `39`，非常接近成功。
  - v8 final max stable steps 約 `32`。
  - v8 checkpoints 也都沒有超過 v5。

### 判斷

- reset 修正有效；現在 episode 起點不再被上一輪漂移污染。
- `v8` 失敗主因是 curriculum 一次加太硬：
  - `success_radius` 從 `0.25` 直接收緊到 `0.18`。
  - 同時要求 hold `40` steps。
  - 同時加大多個 penalty。
- 這讓 agent 幾乎拿不到 success bonus，訓練訊號變成長時間 timeout / failure 的負訊號。
- v8 final policy 比 v5 更差，不適合當下一輪 resume 起點。
- v5 在 radius `0.25`、hold `40` 下已經能撐到 `39` steps，因此下一步應該先用
  溫和課程把「39 steps」補到「穩定 40 steps」，不要直接收緊半徑。

### 下一步

- 不要從 v8 final resume。
- 回到 `hover_hold_15000_v5_final.zip`。
- 使用 reset 修正後的環境，先做一輪較保守的 fine-tuning：
  - `success_radius = 0.25`
  - `success_hold_steps = 40`
  - `learning_rate = 3e-5`
  - penalty 只小幅加強，不使用 v8 那麼硬的設定。
- 若下一輪 deterministic evaluation 通過，再逐步：
  - 先把 `success_hold_steps` 拉到 `50`。
  - 再把 `success_radius` 從 `0.25 -> 0.22`。
  - 最後才考慮 `0.18`。

## 2026-05-23 - 分析 `hover_hold_6000_v9_resetfix_hold40`

### 使用者執行結果

- 使用者從 `hover_hold_15000_v5_final.zip` resume，完成
  `hover_hold_6000_v9_resetfix_hold40`。
- 本輪使用 reset 修正後的環境，並回到較溫和的 curriculum：
  - `success_radius = 0.25`
  - `success_hold_steps = 40`
  - `learning_rate = 3e-5`
  - `distance_weight = 3.0`
  - `velocity_weight = 2.0`
  - `control_weight = 0.7`
  - `smoothness_weight = 0.4`
- 成功產出：
  - `part2/logs/hover_hold_6000_v9_resetfix_hold40.monitor.csv`
  - `part2/models/hover_hold_6000_v9_resetfix_hold40_checkpoint_37200_steps.zip`
  - `part2/models/hover_hold_6000_v9_resetfix_hold40_checkpoint_39200_steps.zip`
  - `part2/models/hover_hold_6000_v9_resetfix_hold40_checkpoint_41200_steps.zip`
  - `part2/models/hover_hold_6000_v9_resetfix_hold40_final.zip`

### Monitor 統計

- 共記錄 `45` 個 episode。
- Success episode：`34`，約 `75.6%`。
  - 平均 reward 約 `359.65`
  - episode length 全部為 `40`
  - 結束時平均 distance 約 `0.208`
  - 結束時平均 speed 約 `0.067`
  - `stable_steps = 40`
- Failure episode：`1`，約 `2.2%`。
  - failure reason：`below_floor`
  - length `385`
  - 結束時 distance 約 `2.876`
- Timeout episode：`10`，約 `22.2%`。
  - 平均 reward 約 `-1651.09`
  - 結束時平均 distance 約 `2.941`
- 最後 10 個 episode 中有 8 個 success，最後 6 個 episode 全部 success。

### Deterministic evaluation

- 使用 hold40 設定評估：
  - `hover_hold_15000_v5_final.zip`：max stable steps 約 `39`，未成功。
  - `hover_hold_6000_v9_resetfix_hold40_checkpoint_37200_steps.zip`：step 40 成功。
  - `hover_hold_6000_v9_resetfix_hold40_checkpoint_39200_steps.zip`：step 40 成功。
  - `hover_hold_6000_v9_resetfix_hold40_checkpoint_41200_steps.zip`：step 40 成功。
  - `hover_hold_6000_v9_resetfix_hold40_final.zip`：step 40 成功。
- 使用 hold50 設定評估：
  - `hover_hold_15000_v5_final.zip`：max stable steps 約 `39`，未成功。
  - `checkpoint_37200_steps`：step 50 成功。
  - `checkpoint_39200_steps`：max stable steps 約 `42`，未成功。
  - `checkpoint_41200_steps`：max stable steps 約 `41`，未成功。
  - `final`：max stable steps 約 `43`，未成功。

### 判斷

- v9 成功修復 v8 的失敗方向：
  - reset 修正有效。
  - hold40 deterministic policy 已經可成功。
- 但 v9 final 還不能穩定撐到 50 steps。
- 很有趣的是，最早的 `checkpoint_37200_steps` 在 deterministic hold50 測試中通過，
  後續 checkpoint/final 反而變得比較會漂。
- 因此下一輪不建議從 v9 final resume；應優先從
  `hover_hold_6000_v9_resetfix_hold40_checkpoint_37200_steps.zip` 這個較穩的
  checkpoint 繼續。

### 下一步

- 從 `checkpoint_37200_steps` resume，而不是 v9 final。
- 下一輪目標：穩定化 hold50。
- 建議設定：
  - `success_radius = 0.25`
  - `success_hold_steps = 50`
  - `learning_rate = 1e-5`
  - `timesteps = 4000`
  - 保持同一組 reward weights。
- 如果 v10 final 和最後 checkpoint 都能 deterministic hold50 成功，才開始考慮
  收緊 `success_radius` 到 `0.22`。

## 2026-05-23 - 分析 `hover_hold_4000_v10_hold50_from_best`

### 使用者執行結果

- 使用者從
  `part2/models/hover_hold_6000_v9_resetfix_hold40_checkpoint_37200_steps.zip`
  resume，完成 `hover_hold_4000_v10_hold50_from_best`。
- 本輪設定：
  - `success_radius = 0.25`
  - `success_hold_steps = 50`
  - `learning_rate = 1e-5`
  - `timesteps = 4000`
  - reward weights 延續 v9。
- 成功產出：
  - `part2/logs/hover_hold_4000_v10_hold50_from_best.monitor.csv`
  - `part2/models/hover_hold_4000_v10_hold50_from_best_checkpoint_38200_steps.zip`
  - `part2/models/hover_hold_4000_v10_hold50_from_best_checkpoint_39200_steps.zip`
  - `part2/models/hover_hold_4000_v10_hold50_from_best_checkpoint_40200_steps.zip`
  - `part2/models/hover_hold_4000_v10_hold50_from_best_checkpoint_41200_steps.zip`
  - `part2/models/hover_hold_4000_v10_hold50_from_best_final.zip`

### Monitor 統計

- 共記錄 `12` 個 episode。
- Success episode：`3`，約 `25.0%`。
  - 平均 reward 約 `373.82`
  - episode length 全部為 `50`
  - 結束時平均 distance 約 `0.223`
  - 結束時平均 speed 約 `0.054`
  - `stable_steps = 50`
- Failure episode：`1`，約 `8.3%`。
  - failure reason：`above_workspace`
  - episode length `381`
  - 結束時 distance 約 `2.598`
- Timeout episode：`8`，約 `66.7%`。
  - 平均 reward 約 `-968.78`
  - 結束時平均 distance 約 `1.683`
- 最後 10 個 episode 中只有 1 個 success，後段沒有穩定改善。

### Deterministic evaluation 狀態

- 嘗試做 deterministic evaluation，但 evaluation reset 時沒有收到
  `/simple_drone/gt_pose`。
- 檢查後發現 Gazebo/ROS 模擬節點已不在：
  - `gzserver`、`gzclient`、`rviz2` 都不在 process list。
  - `/simple_drone/gt_pose` 沒有 publisher。
- 因此本輪尚未完成 v10 final / checkpoints 的 deterministic evaluation。

### 判斷

- 即使尚未完成 deterministic evaluation，monitor 結果已顯示 v10 整體退步。
- v10 從一個先前 deterministic hold50 成功的 checkpoint 繼續訓練，但 success rate
  只有 `25%`，大多數 episode 變成 timeout。
- 因此 v10 final 不適合當下一階段模型。
- 目前最佳候選仍是：
  - `part2/models/hover_hold_6000_v9_resetfix_hold40_checkpoint_37200_steps.zip`
- 這個 checkpoint 在上一輪 deterministic evaluation 中已通過 hold50。

### 下一步

- 先不要再訓練 v10 final。
- 重開 Gazebo/ROS 後，優先對
  `hover_hold_6000_v9_resetfix_hold40_checkpoint_37200_steps.zip`
  做多次 deterministic hold50 evaluation。
- 若多次 deterministic evaluation 都能通過：
  - 將它視為目前 Task A 基礎 hover 模型。
  - 下一階段再考慮 disturbance 或把 `success_radius` 收到 `0.22`。
- 若多次 evaluation 不穩：
  - 不從 v10 final resume。
  - 回到 v9 checkpoint_37200，用更短、更小 learning rate 的 fine-tuning，例如
    `timesteps = 1000`、`learning_rate = 1e-6`，並密集檢查 checkpoint。

## 2026-05-23 - 重開 Gazebo 後補做 deterministic evaluation

### Gazebo 狀態

- 使用者重開 container 後，第一次檢查發現 Gazebo/ROS 模擬節點尚未執行：
  - `/simple_drone/gt_pose` 沒有 publisher。
  - `gzserver`、`gzclient`、`rviz2` 不在 process list。
- 後續重新啟動 `launch_drone`，確認：
  - `gzserver`、`gzclient`、`rviz2` 正常執行。
  - `/simple_drone/gt_pose` 可以 echo 到 pose。

### v9 checkpoint 原始 action 評估

- 模型：
  - `part2/models/hover_hold_6000_v9_resetfix_hold40_checkpoint_37200_steps.zip`
- 設定：
  - `success_radius = 0.25`
  - `success_hold_steps = 50`
  - `reset_start_height = 1.8`
- 3 次 deterministic evaluation：
  - trial 1：未成功，max stable steps 約 `48`，最後 distance 約 `0.8729`。
  - trial 2：成功，step 50 達成，最後 distance 約 `0.2343`。
  - trial 3：成功，step 50 達成，最後 distance 約 `0.2342`。
- 成功率：`2/3`。
- 觀察：
  - 失敗那次只差約 2 steps，但仍會慢慢往 `+y` 和下方漂移。
  - 成功時也接近 success radius 邊界，distance 約 `0.234`。

### v10 final 對照評估

- 模型：
  - `part2/models/hover_hold_4000_v10_hold50_from_best_final.zip`
- 單次 deterministic hold50 evaluation：
  - 未成功。
  - max stable steps 約 `29`。
  - 最後 distance 約 `1.1052`。
  - action 的 z 分量一開始卡在 `-0.1` 邊界。
- 判斷：
  - v10 final 明顯比 v9 checkpoint_37200 差。
  - v10 不適合作為後續模型。

### v9 checkpoint 加 action scaling 評估

- 使用同一個 v9 checkpoint，但在 deployment/evaluation 時將 deterministic action
  乘上 `0.5` 後再送入 environment。
- 3 次 deterministic hold50 evaluation：
  - trial 1：成功，最後 distance 約 `0.0941`，speed 約 `0.0252`。
  - trial 2：成功，最後 distance 約 `0.0947`，speed 約 `0.0315`。
  - trial 3：成功，最後 distance 約 `0.0946`，speed 約 `0.0251`。
- 成功率：`3/3`。
- 觀察：
  - action scaling 明顯降低 drift。
  - 原始 action 下成功時距離 target 約 `0.234m`，非常接近 radius 邊界。
  - scaling 後成功時距離 target 約 `0.095m`，更接近中心，速度也更慢。

### 判斷

- 目前最佳策略不是 v10 final，而是：
  - `hover_hold_6000_v9_resetfix_hold40_checkpoint_37200_steps.zip`
  - 搭配 deterministic inference 時的 `action_scale = 0.5`
- action scaling 可以視為部署時的控制輸出縮放：
  - PPO policy 已學到大致方向。
  - 但輸出速度偏大，造成長時間 hover 時慢慢漂移。
  - 把 action 縮小可降低速度與漂移，符合 Task A「速度要慢、穩定懸停」的目標。

### 下一步

- 不再繼續從 v10 或 v9 做長時間訓練。
- 下一步應建立正式 evaluation/test script，固定：
  - model path：`hover_hold_6000_v9_resetfix_hold40_checkpoint_37200_steps.zip`
  - `action_scale = 0.5`
  - `success_hold_steps = 50`
  - `success_radius = 0.25`
- 接著跑更多次 evaluation，例如 10 episodes，產生正式報告要用的成功率、
  平均 final distance、平均 speed、以及 trajectory plot。

## 2026-05-23 - 正式 evaluation 與報告資料收集

### 新增正式 evaluation script

- 新增 `part2/evaluate.py`，作為 Task A 最終模型驗收腳本。
- 預設使用目前最佳模型：
  - `part2/models/hover_hold_6000_v9_resetfix_hold40_checkpoint_37200_steps.zip`
- 預設 evaluation 設定：
  - deterministic policy
  - `action_scale = 0.5`
  - `target_position = (0.0, 0.0, 2.0)`
  - `success_radius = 0.25`
  - `success_speed = 0.2`
  - `success_hold_steps = 50`
  - `reset_start_height = 1.8`
  - `max_linear_speed = 0.1`
- script 會輸出：
  - `episodes.csv`：每個 episode 的成功/失敗、reward、final distance、final speed。
  - `trajectory.csv`：每個 step 的位置、速度、action、reward、stable steps。
  - `summary.json`：整體成功率與平均指標。
  - `trajectory_overview.png`：軌跡、distance、speed、高度圖。

### Smoke evaluation

- 先跑 `2` episodes 做 smoke test：
  - 成功率：`2/2 = 100%`
  - 平均 final distance：約 `0.0953 m`
  - 平均 final speed：約 `0.0283 m/s`
- 確認 CSV、JSON、PNG 都能正確產生。

### 正式 10 episodes evaluation

- 執行：
  - `python3 -m part2.evaluate --episodes 10 --output-dir part2/evaluation/final_hover --action-scale 0.5`
- 產出檔案：
  - `part2/evaluation/final_hover/episodes.csv`
  - `part2/evaluation/final_hover/trajectory.csv`
  - `part2/evaluation/final_hover/summary.json`
  - `part2/evaluation/final_hover/trajectory_overview.png`
  - `part2/evaluation/final_hover/training_curve_v9.png`
- Evaluation summary：
  - episodes：`10`
  - success count：`10`
  - failure count：`0`
  - timeout count：`0`
  - success rate：`100%`
  - average steps：`50.0`
  - average total reward：約 `389.51`
  - average final distance：約 `0.09496 m`
  - average final speed：約 `0.02897 m/s`
  - average minimum distance：約 `0.01534 m`
  - average max stable steps：`50.0`
  - maximum final distance：約 `0.09610 m`
  - maximum final speed：約 `0.03156 m/s`

### 判斷

- 目前最終策略在正式 evaluation 中達成 `10/10` 成功。
- final distance 約 `0.095 m`，明顯小於 success radius `0.25 m`。
- final speed 約 `0.029 m/s`，明顯小於 success speed `0.2 m/s`。
- 因此目前可以將 Task A 的訓練與正式測試視為完成。
- 後續重點轉為報告撰寫：
  - MDP 設計：observation、action、termination。
  - reward function 設計。
  - PPO 參數與 curriculum 設計。
  - reset 修正與 action scaling 的理由。
  - evaluation 結果與圖表。

## 2026-05-23 - 整理交作業版本與新增 test.py

### 新增正式測試入口

- 新增 `part2/test.py`，作為老師或助教執行 Task A 最終模型的入口。
- `test.py` 直接呼叫 `part2.evaluate` 的正式 evaluation 流程。
- 預設執行方式：
  - `python3 -m part2.test`
- 若需要調整測試次數或輸出資料夾，可沿用 evaluation 參數，例如：
  - `python3 -m part2.test --episodes 10 --output-dir part2/evaluation/final_hover`

### 調整交作業預設檔案

- 將最佳模型複製成作業規格較容易辨識的名稱：
  - `part2/models/ppo_drone.zip`
- `part2/evaluate.py` 的預設模型也改為：
  - `part2/models/ppo_drone.zip`
- 將正式訓練曲線複製到作業規格期待的位置：
  - `part2/logs/training_curve.png`
- 保留正式 evaluation 結果：
  - `part2/evaluation/final_hover/episodes.csv`
  - `part2/evaluation/final_hover/trajectory.csv`
  - `part2/evaluation/final_hover/summary.json`
  - `part2/evaluation/final_hover/trajectory_overview.png`
  - `part2/evaluation/final_hover/training_curve_v9.png`

### 專案資料夾清理

- 移除舊的實驗 checkpoint，只保留最後交作業使用的 `ppo_drone.zip`。
- 移除舊的 smoke test / TensorBoard 暫存輸出，只保留 `training_curve.png`。
- 移除 `part2/evaluation/smoke_hover_eval/`，正式結果只保留 `final_hover/`。
- 移除 `part2/diagnose_hover.py`，因為目前正式流程已由 `evaluate.py` 和 `test.py` 取代。
- 保留 Part 2 主要程式：
  - `drone_env.py`
  - `ros_adapter.py`
  - `train.py`
  - `evaluate.py`
  - `test.py`
  - `plot_training_curve.py`

### 驗證

- 在 Docker image 中執行語法檢查：
  - `python3 -m py_compile part2/test.py part2/evaluate.py part2/drone_env.py part2/ros_adapter.py part2/train.py`
- 執行 `python3 -m part2.test --help` 成功，確認正式測試入口可正常載入。

## 2026-05-23 - 剩餘測試確認

### 目前狀態

- Task A 的核心訓練已完成。
- 正常情境正式 evaluation 已完成，結果為 `10/10` 成功。
- 交作業用的 `test.py`、`ppo_drone.zip`、`training_curve.png` 已整理完成。

### 剩餘重點

- 最後主要還缺 disturbance / motionDriftNoise robustness test。
- 這個測試用來證明模型不只在乾淨環境可以 hover，也能在干擾或漂移噪聲下維持穩定。
- 完成 disturbance test 後，就可以把正常 evaluation、disturbance evaluation、reward 設計、PPO 參數與失敗/修正過程整理進正式報告。

## 2026-05-23 - Disturbance / motionDriftNoise 正式測試

### 測試設定

- 使用老師 drone plugin 內建的 `motionDriftNoise`，不是額外手動推 drone。
- 在 container 中暫時修改安裝後的 drone config：
  - `motionDriftNoise = 0.02`
  - `motionDriftNoiseTime = 0.5`
- 重新啟動 Gazebo 後確認 robot description 內含：
  - `<motionDriftNoise>0.02</motionDriftNoise>`
  - `<motionDriftNoiseTime>0.5</motionDriftNoiseTime>`
- Evaluation 指令使用：
  - `python3 -m part2.evaluate --episodes 10 --output-dir part2/evaluation/disturbance_hover --test-label disturbance_hover_motion_drift_noise --disturbance-type motionDriftNoise --motion-drift-noise 0.02 --motion-drift-noise-time 0.5 --action-scale 0.5 --device cpu`

### 產出檔案

- `part2/evaluation/disturbance_hover/episodes.csv`
- `part2/evaluation/disturbance_hover/trajectory.csv`
- `part2/evaluation/disturbance_hover/summary.json`
- `part2/evaluation/disturbance_hover/trajectory_overview.png`

### 測試結果

- episodes：`10`
- success count：`10`
- failure count：`0`
- timeout count：`0`
- success rate：`100%`
- average steps：`50.0`
- average total reward：約 `388.96`
- average final distance：約 `0.08892 m`
- average final speed：約 `0.02451 m/s`
- average minimum distance：約 `0.02072 m`
- maximum final distance：約 `0.17057 m`
- maximum final speed：約 `0.04222 m/s`

### 與正常 evaluation 比較

- 正常 evaluation：
  - success rate：`100%`
  - average final distance：約 `0.09496 m`
  - average final speed：約 `0.02897 m/s`
- disturbance evaluation：
  - success rate：`100%`
  - average final distance：約 `0.08892 m`
  - average final speed：約 `0.02451 m/s`
- 判斷：
  - 在 `motionDriftNoise=0.02`、每 `0.5s` 更新 drift 的設定下，模型仍能連續 10 次成功 hover。
  - 最大 final distance 約 `0.17057 m`，仍低於 success radius `0.25 m`。
  - 最大 final speed 約 `0.04222 m/s`，仍低於 success speed `0.2 m/s`。
  - 因此可以在報告中主張模型對中等強度的 motion drift noise 具有穩定性。

### 後處理

- Disturbance test 結束後，已將 container 中的 config 恢復：
  - `motionDriftNoise = 0.00`
  - `motionDriftNoiseTime = 50`
- 並重新以正常設定啟動 Gazebo，避免後續測試受到 disturbance 設定影響。

## 2026-05-23 - Train/Test 效果總結

### Training 效果

- 最終採用的模型是 `part2/models/ppo_drone.zip`。
- 來源是訓練過程中表現最穩定的 v9 checkpoint，並在測試與部署時使用 `action_scale = 0.5`。
- 模型已學會將 drone 拉到 `(0.0, 0.0, 2.0)` 附近，並用較小速度維持 hover。
- 原始 policy 動作偏大，長時間 hover 時容易漂移；加入 action scaling 後，hover 位置更靠近 target，速度也更低。

### Test 效果

- 正常環境正式測試：
  - 成功率：`10/10 = 100%`
  - 平均 final distance：約 `0.09496 m`
  - 最大 final distance：約 `0.09610 m`
  - 平均 final speed：約 `0.02897 m/s`
  - 最大 final speed：約 `0.03156 m/s`
- Disturbance / motionDriftNoise 測試：
  - 成功率：`10/10 = 100%`
  - 平均 final distance：約 `0.08892 m`
  - 最大 final distance：約 `0.17057 m`
  - 平均 final speed：約 `0.02451 m/s`
  - 最大 final speed：約 `0.04222 m/s`

### 判斷

- 成功條件是：
  - distance 小於 `0.25 m`
  - speed 小於 `0.2 m/s`
  - 連續穩定 `50` steps
- 兩組正式測試都達成 `100%` 成功率。
- 即使在 `motionDriftNoise = 0.02` 且每 `0.5s` 更新 drift 的情境下，最大 final distance 和最大 final speed 仍明顯低於門檻。
- 因此目前 Part 2 Task A 可以視為訓練與測試完成。

## 2026-05-23 - Task A 是否需要任意 target 的確認

### 作業要求判讀

- 作業原文中 Task A 是：
  - `Precision Hovering and Disturbance Rejection`
  - train the drone to hover at a given `(x, y, z)` pose and maintain stability when `motionDriftNoise` is non-zero.
- 這裡的重點是「給定的一個 hover pose」與 disturbance rejection。
- 任意 target / 每個 episode 不同 target 的泛化要求，對應的是 Task B：
  - `Random Target Navigation`
  - generate a different target point in each episode and train a policy that generalizes across targets.

### 對目前作法的判斷

- 我們選的是 Task A，因此固定 target `(0.0, 0.0, 2.0)` 是合理的。
- 報告中應避免宣稱模型能泛化到任意 target。
- 可以誠實描述為：
  - 本模型完成固定 pose precision hovering。
  - 已在正常環境與 `motionDriftNoise` 非零環境下驗證穩定性。
  - 任意 target 泛化屬於 Task B 或 future work。

## 2026-05-23 - Training curve 解釋

### 圖的意義

- 淺藍線是每個 episode 的 raw reward。
- 橘線是 20-episode moving average，用來觀察整體趨勢。
- 因為 reward function 包含：
  - 距離 target 的懲罰
  - 速度懲罰
  - 控制量與動作變化懲罰
  - stable hover bonus
  - success bonus
  - failure penalty
- 所以成功 episode 通常會得到較高 reward，而失敗、漂太遠或長時間不穩的 episode 會出現很大的負 reward。

### 曲線現象

- 淺藍線有很多尖銳下跌，代表訓練過程中 policy 仍在探索，偶爾會讓 drone 漂移、失穩或累積大量 distance penalty。
- 橘線一開始下降，表示早期雖然偶爾成功，但失敗 episode 的負 reward 很大，拉低平均。
- 後半段橘線逐漸往上回升，代表嚴重失敗的頻率或嚴重程度下降，policy 開始學到比較穩的 hover 行為。
- 曲線沒有單調上升是正常的，因為 PPO 訓練時仍有 stochastic exploration，而且 Gazebo 動態系統本身也會造成 episode 間差異。

### 與最終結果的關係

- Training curve 主要用來說明訓練過程，而不是唯一的模型選擇依據。
- 最終採用的模型不是只看最後一個 episode，而是根據 checkpoint evaluation 選出表現最穩定的模型。
- 最終 deterministic evaluation 搭配 `action_scale = 0.5` 後：
  - 正常環境成功率 `10/10`
  - disturbance 環境成功率 `10/10`
- 因此可以解釋為：
  - 訓練過程 noisy，但 agent 最後確實學到可穩定 hover 的 policy。
  - Final evaluation 比 raw training reward 更能代表部署時表現。

## 2026-05-23 - TA 執行 test.py 流程

### 目的

- 讓 TA 不需要重新訓練，只要開啟 Gazebo 後執行 `test.py`。
- `test.py` 會載入 `part2/models/ppo_drone.zip`，並讓 agent 在 Gazebo 中執行 precision hover。

### 建議流程

- Host terminal：
  - `cd Assignment2_env`
  - `./run_docker.sh`
- Container terminal 1：
  - `source /opt/ros/iron/setup.bash`
  - `source /ros2_ws/install/setup.bash`
  - `launch_drone`
- Container terminal 2：
  - `cd /workspace/RL_Assignment2`
  - `source /opt/ros/iron/setup.bash`
  - `source /ros2_ws/install/setup.bash`
  - `python3 -m part2.test --episodes 3 --output-dir part2/evaluation/ta_demo`

### 預期現象

- Gazebo 中 drone 會 reset、takeoff，然後移動/穩定在 target `(0.0, 0.0, 2.0)` 附近。
- Terminal 會印出每個 episode 的成功與 final distance / speed。
- 測試結果會輸出到指定資料夾，例如 `part2/evaluation/ta_demo/`。

## 2026-05-23 - 更新 README 與報告大綱

### README.md

- 將 root `README.md` 從舊的 Task B scaffold 改成目前實際完成的 Task A 版本。
- 內容包含：
  - 作業任務：Precision Hovering and Disturbance Rejection。
  - 專案資料夾結構。
  - Docker build / run 指令。
  - Gazebo 啟動方式。
  - TA 如何執行 `python3 -m part2.test`。
  - 如何重跑 nominal evaluation。
  - 最終 nominal 與 disturbance 測試結果摘要。
  - 如何重跑一個新的 PPO training experiment。
  - Part 1 證明資料位置。
  - Part 2 MDP / PPO / reward / success condition 摘要。

### report_outline.md

- 將 `report/report_outline.md` 從 Task B 大綱改成 Task A 報告大綱。
- 目前大綱已對齊作業要求的五個 section：
  - Task Definition and Motivation。
  - Pain Points of Existing Methods。
  - Literature Review。
  - Proposed Solution。
  - Results and Discussion。
- 也加入 Appendix A 的 Part 1 observation 方向，以及 acknowledgement。

### 清理

- 移除 container 產生的 `part2/__pycache__/`，避免最後打包混入暫存檔。
