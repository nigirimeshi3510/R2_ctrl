# SPEC_R2_CONTROL.md — R2制御スタック仕様（ロボコン2026）

## 0. 目的
このリポジトリは、NHK学生ロボコン2026「ロボットが挑む“同心協力”」向けロボットR2の自律制御スタックを実装する。

主要成果物:
- R2向けミッションBehavior Tree（BT）
- 梅花林の認識→離散計画→実行パイプライン
- FLAT/CLIMBモード切替を伴う自己位置推定
- ROS 2 Actionベースの運動プリミティブ（MoveCell / ClimbStep / PickAdjacentBook / DockToAruco）

対象プラットフォーム:
- Jetson Orin NX + ROS 2 Humble
- STM32F446RE + micro-ROS（低レベルI/O・アクチュエータ）

---

## 1. ハードウェア前提
### 1.1 機体
- ベース: 4輪メカナム
- フットプリント: 600mm x 400mm

### 1.2 センサ
- IMU: BNO055
  - 経路: UART -> STM32F446RE -> `/imu`（`sensor_msgs/Imu`）
- 接地オドメトリ: 小型オムニホイールエンコーダ（x, y）
  - 重要: リフト機構が上がっている間は常に接地エンコーダが浮くため無効
- LiDAR: Hokuyo URG-30LX-EW x2
  - 270度、左右外向き
  - 段差ブロック検知可能
- カメラ: YOLOv8
  - 本の印字分類: R1 / R2 / FAKE
  - 梅花林進入直前（通路短辺）から全ブロックの本を識別可能（本仕様では成立を仮定）

### 1.3 アクチュエーション/機構
- 本吸着用サクション機構
- 段差越えはリフト + 補助車輪で実施（手順は`README.md`準拠）
- 上段配置時にR1がR2を持ち上げる（詳細未確定）

---

## 2. 厳守ルール（Must Not Violate）
### 2.1 ロボット間通信
- 試合中、R1-R2間で通信してはならない（Wi-Fi共有、ROSグラフ共有、有線接続等すべて禁止）。
- 協調は視覚（Aruco）、物理ドッキング、時系列制御のみで実現する。

### 2.2 梅花林制約
- 進入はR2側通路からのみ。
- R2が回収できるのはR2本のみ。
- 回収可能なのは、R2が現在いるブロックに隣接したブロック上の本のみ。
- 1〜3番ブロックにR2本が存在する場合、最初の1冊目は通路状態から回収しなければならない。
- 1冊以上保持していなければ梅花林を退出できない。
- 退出可能ブロックは10〜12番のみ。

### 2.3 強制リトライ/違反（クリティカル）
- FAKE本を動かしてはならない。
- 本が置かれているブロックには乗ってはならない（ただしそのブロックの本を回収済みなら可）。
- 非隣接ブロックから本を動かしてはならない。
- 曖昧な場合は必ず安全側に倒し、禁止として扱うこと。

---

## 3. システム構成（ROS 2パッケージ）
推奨パッケージ構成:
- `robocon_interfaces`
  - msg / srv / action定義
- `robocon_perception`
  - YOLOv8推論
  - BookMap生成（12セル分類）
- `robocon_plum_planner`
  - 梅花林向け離散プランナ（厳格な安全制約を実装）
- `robocon_localization`
  - LaserScan融合（left+right -> fused）
  - `robot_localization` EKF（flat/climb）
  - AMCL（map->odom）
  - モード切替（odom mux / scan gate）
- `robocon_motion_primitives`
  - Actionサーバ: MoveCell, ClimbStep, PickAdjacentBook, DockToAruco
- `robocon_bt_mission`
  - ミッションBT
  - Nav2 BT Navigator連携（任意。梅花林は独自BTでも可）
- `robocon_bringup`
  - 全体launch / params

---

## 4. 座標系とTF
- `map`: フィールド固定座標
- `odom`: EKF由来の連続ローカル座標
- `base_link`: 機体基準
- `imu_link`: IMU搭載座標
- `laser_left`, `laser_right`: LiDAR座標
- `camera_link`: カメラ座標

必須TF:
- `base_link -> imu_link`
- `base_link -> laser_left / laser_right`
- `base_link -> camera_link`

---

## 5. ROSインタフェース
### 5.1 Topics
- `/imu` : `sensor_msgs/Imu`
- `/ground_odom` : `nav_msgs/Odometry`
- `/scan_left` : `sensor_msgs/LaserScan`
- `/scan_right` : `sensor_msgs/LaserScan`
- `/scan_fused` : `sensor_msgs/LaserScan`（`scan_fuser`生成）
- `/loc_mode` : `std_msgs/String`（`"FLAT"` | `"CLIMB"`）
- `/cell_state` : `robocon_interfaces/msg/CellState`
- `/book_map` : `robocon_interfaces/msg/BookMap`
- `/plum_plan` : `robocon_interfaces/msg/PlumPlan`（またはAction result）

### 5.2 Actions
- `/move_cell` : `robocon_interfaces/action/MoveCell`
  - goal: `from_cell_id`, `to_cell_id`
  - result: `success`, `error_code`, `debug`
- `/climb_step` : `robocon_interfaces/action/ClimbStep`
  - goal: `direction`（UP/DOWN）, `expected_to_cell_id`
  - result: `success`, `error_code`, `debug`
- `/pick_adjacent_book` : `robocon_interfaces/action/PickAdjacentBook`
  - goal: `target_cell_id`
  - result: `success`, `error_code`, `debug`
- `/dock_to_aruco` : `robocon_interfaces/action/DockToAruco`
  - goal: `marker_id`, `pos_tol`, `yaw_tol`
  - result: `success`, `error_code`, `debug`

---

## 6. 位置推定仕様
### 6.1 背景
- リフト上昇中は接地オドメトリが無効。
- 段差越え中は2D LiDARスキャンが歪む可能性がある。

### 6.2 モード定義
- FLAT:
  - 入力: IMU + ground_odom（+任意でwheel odom）
  - 出力: `/odometry/filtered`（`odom->base_link`）
  - AMCLは`/scan_fused`で有効
- CLIMB:
  - 入力: IMUのみ（またはIMU + 極めて弱い他ソース）
  - ground_odomは無視
  - AMCLへのscan更新をゲート/無効化（または弱化）
  - BT/Plannerは離散セル追跡を利用（`cell_id`は意図アクションに追従）

### 6.3 実装要件
- `robot_localization` EKF #1: `ekf_flat.yaml`
- `robot_localization` EKF #2: `ekf_climb.yaml`
- `odom_mux`:
  - `/loc_mode`に応じて`ekf_flat`または`ekf_climb`の`/odometry/filtered`を選択
- `scan_gate`:
  - CLIMB中は`/scan_fused`からAMCLへの入力を遮断

### 6.4 段差越え後の再ローカライズ
`ClimbStep`完了後:
1) 0.3〜0.5秒安定化（停止）
2) 必要に応じて短時間旋回（±90度）しscan情報を増やす
3) AMCL収束待ち（共分散閾値または姿勢安定判定）
4) セル中心スナップ（任意）:
   - 離散計画と連続位置推定の整合維持のため、期待セル中心へ補正

---

## 7. 梅花林認識（BookMap）
### 7.1 BookMap定義
- 12セル（ブロック）: `cell_id = 1..12`
- 各セルの`book_type`: `EMPTY | R2 | R1 | FAKE | UNKNOWN`
- 各セルの`confidence`: `float [0..1]`
- `timestamp`

### 7.2 検出結果のセルマッピング
通路観測視点は固定であるため:
- 事前キャリブレーション済みホモグラフィ、または静的pixel->cell LUTを利用
- 各検出に対して:
  - 中心点を算出
  - `cell_id`へ変換
  - 信頼度に基づき投票/上書き（高信頼を優先）

安全ルール:
- `confidence < threshold` は `UNKNOWN` とする。
- Plannerは`UNKNOWN`を進入禁止として扱う。

---

## 8. 梅花林離散プランナ
### 8.1 状態
- `pos`: 現在セルID（または特別状態`CORRIDOR`）
- `cleared_mask`: 回収済みセルbitmask（回収済みセルは走行可）
- `carry_r2`: 0..2
- `book_map`: 開始時固定（本仕様では全観測済みを仮定）

### 8.2 走行可能判定
- `walkable(cell) = (book_type == EMPTY) OR (cleared_maskにcellビットあり)`
- `forbidden(cell) = (book_type in {R2,R1,FAKE,UNKNOWN}) AND 未cleared`

FAKEはclearedにしない。

### 8.3 行動
- `MOVE(to_cell)`:
  - 前提: `to_cell`が現在セルに隣接
  - 前提: `walkable(to_cell) == true`
  - コスト: `step_move_cost_sec`（パラメータ、目標5秒）
- `PICK(target_cell)`:
  - 前提: `target_cell`が現在セルに隣接
  - 前提: `book_type[target_cell] == R2`
  - 効果: `cleared_mask[target_cell]=true`, `carry_r2 += 1`
  - コスト: `pick_cost_sec`（パラメータ）
- `EXIT`:
  - 前提: 現在セルが`{10,11,12}`
  - 前提: `carry_r2 >= 1`

特別ルール:
- `{1,2,3}`にR2本がある場合、最初のPICKは必ず`CORRIDOR`状態から実行（通路ピック）する。

### 8.4 目的
- 第一目的: R2本を2冊取得し、退出（10/11/12 + `carry>=1`）
- フォールバック: 1冊取得して退出
- 最適化: 総時間コスト最小。タイの場合は安全余裕（リスクステップが少ない）を優先。

### 8.5 アルゴリズム
状態空間が小さいため:
- `(pos, cleared_mask, carry)` 上で DP / 均一コスト探索（UCS）を推奨
- 出力: 行動列 `[MOVE, PICK, MOVE, ..., EXIT]`
- 2冊が不可能な場合は1冊フォールバック計画も出力

---

## 9. 運動プリミティブ
### 9.1 MoveCell
隣接セルへの信頼性の高い遷移を実装:
- エッジ/段差開始位置への整列
- 段差越え手順の実行
- 停止して成功/失敗を返す

### 9.2 ClimbStep
- `README.md` の機械手順に沿って段差越えを実装
- 開始時に`/loc_mode="CLIMB"`、完了後に`"FLAT"`へ復帰
- デバッグ用に内部状態ログを出力

### 9.3 PickAdjacentBook
- `target_cell`が隣接かつR2本の場合のみ実行
- 成功検証を必須化:
  - 推奨: 負圧センサ閾値 + 保持時間
  - 代替: ポンプ電流上昇 + 画像確認（対象セルから本が消失）
- 検証失敗時はabortし、BT側で再試行/再計画へ移行

### 9.4 DockToAruco
- マーカーへの相対姿勢許容内へ到達する視覚サーボ
- ロボット間通信なしでも頑健に動作すること

---

## 10. ミッションBehavior Tree（BT）
### 10.1 上位フェーズ
1) Init（bringup確認、TF、センサ）
2) Dojo:
   - 安全条件待ち
   - 槍先取得
3) Assembly:
   - Arucoへドッキング/待機姿勢
   - ドッキング成功確認
4) Plum:
   - ObserveAllBooksFromCorridor -> BuildSafetyGrid -> ComputePlan(2, fallback=1) -> ExecutePlan -> Exit
5) Arena:
   - R2本1冊目を中段へ配置
   - R1で持ち上げられた場合は2冊目を上段へ配置
6) End

### 10.2 主要ガード
- 禁止セルへのMOVEを出さない
- 隣接条件を満たさないPICKを出さない
- `carry>=1`かつ10/11/12以外でEXITを出さない
- Action失敗時は（可能なら）再ローカライズ -> 再計画 -> 再試行

---

## 11. テスト要件（必須）
### 11.1 Plannerユニットテスト
- 回収前の本配置セルへ進入しない
- PICKは隣接セルのみ
- EXITは10/11/12かつ`carry>=1`のみ
- 1〜3にR2がある場合の初手通路ピック制約を満たす
- `UNKNOWN`を禁止セルとして扱う

### 11.2 統合テスト（最低限）
- ダミー`/book_map`投入で`/plum_plan`が出力される
- モックActionサーバが計画を消費して成功完了できる（成功系）

---

## 12. Build & CI
- ROS 2 Humbleでビルド可能であること
- 必須コマンド:
  - `colcon build`
  - `colcon test`
  - `colcon test-result --verbose`
