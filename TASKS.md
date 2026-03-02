# TASKS.md — 実装計画（Codex向け）

## 共通ルール
- 1 task = 1 PRサイズの変更
- 毎回必ず実行:
  - `colcon build`
  - `colcon test`
  - `colcon test-result --verbose`
- コミットは小さく、レビューしやすく保つ

## 現在の優先順（2026-03-03時点）
1. Task 4: Localization Mode Switching
2. Task 6: Motion Primitives（モック優先）
3. Task 7: Mission BT（モック連携）
4. Task 8: CI

---

## Task 0: リポジトリ初期構成
### 目的
最小パッケージ構成のROS 2ワークスペースを作成し、ビルド成功状態にする。

### 成果物
- `src/robocon_interfaces/`（msg/actionの空スキャフォールド）
- `src/robocon_bringup/`（基本launch）
- ROS2ビルド成果物向け`.gitignore`
- リポジトリルートに`AGENT.md`、`SPEC_R2_CONTROL.md`、`TASKS.md`

### 受け入れ条件
- `colcon build` が通る
- `ros2 pkg list | grep robocon_` でパッケージが確認できる

---

## Task 1: robocon_interfaces（msg/action）
### 目的
スタックで必要な全メッセージ/アクションを定義する。

### 成果物
- `msg/BookMap.msg`
- `msg/CellState.msg`
- `msg/PlumPlan.msg`（またはAction resultで代替）
- `action/MoveCell.action`
- `action/ClimbStep.action`
- `action/PickAdjacentBook.action`
- `action/DockToAruco.action`

### 受け入れ条件
- ビルドが通る
- メッセージ/アクション生成が機能する
- 最小Publisher/Subscriberサンプルがコンパイルできる

---

## Task 2: Perception BookMap（robocon_perception）
### 目的
YOLO検出結果を12セルBookMapへ変換する。

### 成果物
- Node: `bookmap_node`
  - Sub: `/yolo_detections`（独自msg定義または`vision_msgs`利用）
  - Pub: `/book_map`（`robocon_interfaces/BookMap`）
- キャリブレーション設定:
  - ホモグラフィ行列、またはYAMLのpixel->cell LUT

### 受け入れ条件
- ユニットテスト: 固定検出入力 -> 期待`cell_id`へマッピング
- `conf<threshold` は `UNKNOWN`
- `ros2 run ...` で `/book_map` が正しくpublishされる

---

## Task 3: Scan Fusion（robocon_localization）
### 目的
左右LaserScanを融合し、AMCL向け`/scan_fused`を生成する。

### 成果物
- Node: `scan_fuser`
  - Sub: `/scan_left`, `/scan_right`
  - Pub: `/scan_fused`
- パラメータ:
  - フレームマッピング方針
  - 角度ビニング戦略

### 受け入れ条件
- ノードが起動し、有効なLaserScanを出力できる
- 基本健全性: `/scan_fused` の角度範囲が妥当

---

## Task 4: Localization Mode Switching（robocon_localization）
### 目的
オドメトリ切替とscanゲーティングによるFLAT/CLIMB切替を実装する。

### 成果物
- `robot_localization` 向け `ekf_flat.yaml`, `ekf_climb.yaml`
- Node: `odom_mux`
  - Sub: `ekf_flat/odometry`, `ekf_climb/odometry`, `/loc_mode`
  - Pub: `/odometry/filtered`
- Node: `scan_gate`
  - Sub: `/scan_fused`, `/loc_mode`
  - Pub: `/scan_for_amcl`（またはAMCL入力へ透過）

### 受け入れ条件
- `/loc_mode` 切替でodomソースが切り替わる
- CLIMB時にAMCLへのscan入力が遮断される

---

## Task 5: Plum Planner（robocon_plum_planner）
### 目的
BookMapから安全な離散計画を生成する。

### ステータス
- 実装完了（PR #8）
- 次タスクは Task 4 へ移行

### 成果物
- Node: `plum_planner_node`
  - Sub: `/book_map`, `/cell_state`
  - Pub: `/plum_plan`
- プランナコアライブラリ:
  - `(pos, cleared_mask, carry)` 上のDP/均一コスト探索
  - 仕様通りの制約を厳密実装

### 受け入れ条件（ユニットテスト必須）
- 禁止セル（未クリア本セル）へMOVEしない
- PICKは隣接のみ
- EXITは10/11/12かつ`carry>=1`のみ
- 1〜3にR2がある場合の初手回収特別ルールを満たす
- `UNKNOWN`を禁止扱いにする
- 2冊が不可能な場合に1冊フォールバック計画を返す
- 赤青番号系の変換後も同等の計画を返す（内部は赤側番号で正規化）
- 4.4.17/4.4.18（落下本ルール）はTask 5では仕様注記に留め、Task 6以降の実行層で担保する

---

## Task 6: Motion Primitives（robocon_motion_primitives）
### 目的
MoveCell/Climb/PickのActionサーバを実装する。

### 成果物
- Actionサーバ:
  - `/move_cell`
  - `/climb_step`
  - `/pick_adjacent_book`
- 段差越え手順（`README.md`）向け内部状態機械
- `/loc_mode` 遷移publish:
  - 段差越え中はCLIMB、完了後はFLAT

### 受け入れ条件
- モックモード: actionが成功を返し、遷移ログが出る
- 実機モードのフック準備（STM32向けtopic/service）
- 失敗時に意味のあるエラーコードを返す

---

## Task 7: Mission BT（robocon_bt_mission）
### 目的
PlumフェーズBTをエンドツーエンドで実装する。

### 成果物
- BTノード:
  - `ObserveAllBooksFromCorridor`
  - `ComputePlumPlan`
  - `ExecutePlumPlan`（actionを逐次dispatch）
  - `ExitPlumForest`
- Blackboard変数:
  - `book_map`, `cell_state`, `plan`, `carry`, `loc_mode`

### 受け入れ条件
- モックactionでBTが完了する:
  - Observe -> Plan -> Execute -> Exit
- 任意action失敗時:
  - 再計画・再試行（回数上限あり）を発火

---

## Task 8（任意だが推奨）: CI
### 目的
mainブランチで常時build/testが通る状態を保証する。

### 成果物
- GitHub Actionsワークフロー:
  - Ubuntu 22.04 + ROS 2 Humbleでbuild + test
- 反復高速化のためのキャッシュ設定

### 受け入れ条件
- マージ前にPRでCI通過が必須
