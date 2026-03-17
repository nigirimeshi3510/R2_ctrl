# STATUS.md — 作業進捗ログ

最終更新: 2026-03-18

## 現在ブランチ
- `feat/task5-plum-planner`

## 進捗サマリ
- Task 1（`robocon_interfaces`）実装完了
- Task 2（`robocon_perception`）実装完了（BookMap変換ノード + LUT + ユニットテスト）
- Task 2.5（`bookmap_viz_node`）実装完了（RViz可視化、手前列=10/11/12）
- Task 2.7（RViz向けlaunch+設定）実装完了（project内rviz設定を使用）
- Task 3（`robocon_localization`）実装完了（`scan_fuser` + ユニットテスト + launch）
- Task 5（`robocon_plum_planner`）実装完了（Dijkstraプランナ + 赤青番号正規化 + ユニットテスト）
- 競技ルール反映: 4.4.17/4.4.18 相当を仕様書へ追記
- Foxglove関連を削除（`perception_foxglove.launch.py` 廃止、READMEから記載削除）
- 画像処理担当向けREADMEを追加（`src/robocon_perception/README.md`）
- `SPEC_R2_CONTROL.md` / `AGENT.md` / `TASKS.md` を日本語化
- Task 7 着手: `robocon_bt_mission` の ament_python パッケージ骨格を追加
- Task 7 試作: 簡易 Plum BT（Observe/Plan/Execute/Exit + 1回再計画）を実装
- Task 7 可視化: Groot 用の静的 BT XML を追加
- `src/robocon_bt_mission/btplan.md` を現行 `robocon_*` 実装前提の計画書へ更新

## 完了タスク
- [x] Task 1: `robocon_interfaces`（msg/action定義、生成設定、型コンパイルテスト）
- [x] Task 2: `robocon_perception`（`/yolo_detections` -> `/book_map`、LUT、ユニットテスト）
- [x] Task 2.5: `bookmap_viz_node`（`/book_map_markers` 可視化、色分け、ラベル表示）
- [x] Task 2.7: `perception_rviz.launch.py` + `perception_bookmap.rviz`（RViz起動集約）
- [x] Task 3: `robocon_localization`（`/scan_left` + `/scan_right` -> `/scan_fused`、角度ビニング、TF変換、ユニットテスト）
- [x] Task 5: `robocon_plum_planner`（プランナコア、ROSノード、赤青番号変換、README、テスト）
- [x] README追加: 画像処理担当向け連携仕様ドキュメント（`src/robocon_perception/README.md`）

## 進行中タスク
- [ ] Task 3.5: rosbag取得（`scan + imu + tf + cmd_vel`）
- [ ] Task 3.6: Nav2最小テスト（`slam + nav2` で経路追従）
- [ ] Task 4: `robocon_localization`（Localization Mode Switching）
- [ ] Task 7: `robocon_bt_mission` 本番BTへの拡張（試作BTは実装済み）

## 次にやること（Next Action）
1. Task 7: 試作BTを本番仕様へ拡張（`ClimbStep` / `DockToAruco` / 詳細リカバリ）
2. Task 6: `robocon_motion_primitives` を独立パッケージとして実装し、試作BTのモック世界を置換
3. Task 3.5: `scan + imu + tf + cmd_vel` のrosbag取得（60秒以上）
4. Task 3.6: `slam + nav2` の最小構成で経路追従テスト
5. Task 4: `odom_mux` 実装（`ekf_flat/odometry` と `ekf_climb/odometry` の切替）
6. Task 4: `scan_gate` 実装（CLIMB時のscan遮断）

## 検証コマンド
- `colcon build --symlink-install`
- `colcon test --return-code-on-test-failure`
- `colcon test-result --verbose`

## メモ / ブロッカー
- URDF未確定でも Task 2/3/5/6(モック)/7(モック) は先行可能
- `ros2 interface` サブコマンド未導入環境のため、型確認はビルド生成物とテストで代替
- sandbox制約により `rclpy` 実行ノードのE2E確認は不可（DDSソケット/SHM生成失敗）。CI/ローカル実機環境で実行確認する。
- Task 3の実装は完了。`colcon build --packages-select robocon_localization robocon_bringup`、`colcon test --packages-select robocon_localization` は通過済み。
- Task 5の実装は完了。`colcon test --packages-select robocon_plum_planner` は通過済み。
- ワークスペース全体の `colcon test` は既存 `urg_node2` が環境権限（`~/.ros/log` 書き込み）で失敗する。
- RVizは `ros2 launch robocon_bringup perception_rviz.launch.py` でプロジェクト設定を直接読み込める。
- このセッションでは `sudo` パスワード入力不可のため、`ros-humble-foxglove-bridge` アンインストールは手動実施が必要。
- `robocon_bt_mission` は追加済み。`colcon build --packages-select robocon_bt_mission --symlink-install` は通過。
- `robocon_bt_mission` に簡易BT試作を追加:
  - pure Python のBTコア（Observe / Plan / Execute / Exit）
  - action失敗時の1回だけ再計画
  - `/move_cell` と `/pick_adjacent_book` のモック世界ノード
  - `simple_plum_bt_demo.launch.py`
- `robocon_bt_mission/behavior_trees/simple_plum_bt.xml` を追加し、Groot で開ける静的BTを作成。
- `colcon test --packages-select robocon_bt_mission --event-handlers console_direct+` で 6件成功を確認。

## 関連PR
- #8 Task5: `robocon_plum_planner` 実装と競技ルール整合更新
  - https://github.com/nigirimeshi3510/R2_ctrl/pull/8
- #2 既存PR（履歴）
  - https://github.com/nigirimeshi3510/R2_ctrl/pull/2

## 追加実装（機体モデル / 2026-03-05）
- `src/r2_sldasm_description` を `R2_ctrl` ワークスペースへ移管し、`colcon` 認識・単体ビルド確認済み。
- URDFの機体寸法を更新（先端基準x/y指定、main/sub wheel配置、lift/subwheel/lidar位置調整）。
- main wheel / subwheel / lidar の簡易形状を寸法指定で反映。
  - main wheel: 直径100mm, 幅50mm
  - subwheel: 直径60mm, 幅30mm
  - lidar: 直径50mm, 高さ60mm
- `base_link` 形状を 600x400mm（厚み10mm）の中空フレームとして定義。
- TF構成を拡張:
  - `world -> base_footprint -> base_link` を追加
  - `imu_link` を追加（現状は `base_link` 中心固定）
  - `laser_left/right` エイリアスを追加（`lidar1/2_link` 互換維持）
- Gazebo用worldを追加（`worlds/lift_box_world.sdf`）し、1200x1200x200mm の箱を配置。

## 検証メモ（機体モデル）
- `cd /home/rui3510/R2_ctrl && colcon list` で `r2_sldasm_description` を認識。
- `cd /home/rui3510/R2_ctrl && colcon build --packages-select r2_sldasm_description` 通過。
- ルート直下の `colcon` 実行時に `CMakeLists.txt` 識別エラー表示あり（既知・パッケージ自体のビルドは成功）。
