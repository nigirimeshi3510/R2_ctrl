# STATUS.md — 作業進捗ログ

最終更新: 2026-03-02

## 現在ブランチ
- `feat/task1-interfaces`

## 進捗サマリ
- Task 1（`robocon_interfaces`）実装完了
- Task 2（`robocon_perception`）実装完了（BookMap変換ノード + LUT + ユニットテスト）
- Task 2.5（`bookmap_viz_node`）実装完了（RViz可視化、手前列=10/11/12）
- Task 2.6（Foxglove向けlaunch）実装完了（bookmap + viz + bridge一括起動）
- Task 2.7（RViz向けlaunch+設定）実装完了（project内rviz設定を使用）
- 画像処理担当向けREADMEを追加（`src/robocon_perception/README.md`）
- `SPEC_R2_CONTROL.md` / `AGENT.md` / `TASKS.md` を日本語化
- PR #2 作成済み・更新中  
  - https://github.com/nigirimeshi3510/R2_ctrl/pull/2

## 完了タスク
- [x] Task 1: `robocon_interfaces`（msg/action定義、生成設定、型コンパイルテスト）
- [x] Task 2: `robocon_perception`（`/yolo_detections` -> `/book_map`、LUT、ユニットテスト）
- [x] Task 2.5: `bookmap_viz_node`（`/book_map_markers` 可視化、色分け、ラベル表示）
- [x] Task 2.6: `perception_foxglove.launch.py`（起動コマンド集約）
- [x] Task 2.7: `perception_rviz.launch.py` + `perception_bookmap.rviz`（RViz起動集約）
- [x] README追加: 画像処理担当向け連携仕様ドキュメント（`src/robocon_perception/README.md`）

## 進行中タスク
- [ ] Task 3: `robocon_localization`（scan_fuser）

## 次にやること（Next Action）
1. `src/robocon_localization` パッケージ作成
2. `/scan_left` + `/scan_right` を融合する `scan_fuser` 実装
3. `/scan_fused` の角度範囲と基本健全性テスト追加

## 検証コマンド
- `colcon build --symlink-install`
- `colcon test --return-code-on-test-failure`
- `colcon test-result --verbose`

## メモ / ブロッカー
- URDF未確定でも Task 2/3/5/6(モック)/7(モック) は先行可能
- `ros2 interface` サブコマンド未導入環境のため、型確認はビルド生成物とテストで代替
- sandbox制約により `rclpy` 実行ノードのE2E確認は不可（DDSソケット/SHM生成失敗）。CI/ローカル実機環境で実行確認する。
- この環境には `foxglove_bridge` パッケージが存在しないため、ローカル環境で `sudo apt install ros-humble-foxglove-bridge` が必要。
- RVizは `ros2 launch robocon_bringup perception_rviz.launch.py` でプロジェクト設定を直接読み込める。
