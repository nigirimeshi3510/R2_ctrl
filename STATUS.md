# STATUS.md — 作業進捗ログ

最終更新: 2026-03-03

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

## 完了タスク
- [x] Task 1: `robocon_interfaces`（msg/action定義、生成設定、型コンパイルテスト）
- [x] Task 2: `robocon_perception`（`/yolo_detections` -> `/book_map`、LUT、ユニットテスト）
- [x] Task 2.5: `bookmap_viz_node`（`/book_map_markers` 可視化、色分け、ラベル表示）
- [x] Task 2.7: `perception_rviz.launch.py` + `perception_bookmap.rviz`（RViz起動集約）
- [x] Task 3: `robocon_localization`（`/scan_left` + `/scan_right` -> `/scan_fused`、角度ビニング、TF変換、ユニットテスト）
- [x] Task 5: `robocon_plum_planner`（プランナコア、ROSノード、赤青番号変換、README、テスト）
- [x] README追加: 画像処理担当向け連携仕様ドキュメント（`src/robocon_perception/README.md`）

## 進行中タスク
- [ ] Task 4: `robocon_localization`（Localization Mode Switching）

## 次にやること（Next Action）
1. Task 4: `odom_mux` 実装（`ekf_flat/odometry` と `ekf_climb/odometry` の切替）
2. Task 4: `scan_gate` 実装（CLIMB時のscan遮断）
3. Task 4: bringup launchへ統合、テスト整備

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

## 関連PR
- #8 Task5: `robocon_plum_planner` 実装と競技ルール整合更新
  - https://github.com/nigirimeshi3510/R2_ctrl/pull/8
- #2 既存PR（履歴）
  - https://github.com/nigirimeshi3510/R2_ctrl/pull/2
