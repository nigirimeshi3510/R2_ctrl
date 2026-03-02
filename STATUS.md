# STATUS.md — 作業進捗ログ

最終更新: 2026-03-02

## 現在ブランチ
- `feat/task1-interfaces`

## 進捗サマリ
- Task 1（`robocon_interfaces`）実装完了
- `SPEC_R2_CONTROL.md` / `AGENT.md` / `TASKS.md` を日本語化
- PR #2 作成済み・更新中  
  - https://github.com/nigirimeshi3510/R2_ctrl/pull/2

## 完了タスク
- [x] Task 1: `robocon_interfaces`（msg/action定義、生成設定、型コンパイルテスト）

## 進行中タスク
- [ ] Task 2: `robocon_perception`（BookMap変換）

## 次にやること（Next Action）
1. `src/robocon_perception` パッケージ作成
2. `bookmap_node` の入出力定義（`/yolo_detections` -> `/book_map`）
3. 固定入力によるセルマッピングのユニットテスト追加

## 検証コマンド
- `colcon build --symlink-install`
- `colcon test --return-code-on-test-failure`
- `colcon test-result --verbose`

## メモ / ブロッカー
- URDF未確定でも Task 2/3/5/6(モック)/7(モック) は先行可能
- `ros2 interface` サブコマンド未導入環境のため、型確認はビルド生成物とテストで代替
