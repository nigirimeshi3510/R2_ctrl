# AGENT.md — リポジトリエージェントガイド（R2制御）

## 0. ミッション
このリポジトリは、ロボコン2026 R2向け自律制御スタックを実装する
（Jetson Orin NX上のROS 2 Humble + STM32F446RE micro-ROS）。

主要目標:
- ミッションBehavior Tree（BT）
- 厳格な安全制約を満たす梅花林離散プランナ
- FLAT/CLIMBモード切替を伴う位置推定
- 運動プリミティブ（MoveCell / ClimbStep / PickAdjacentBook）

## 1. 厳守ルール（MUST NOT VIOLATE）
- 試合中にR1とR2が通信してはならない（Wi-Fi、ROSトピック共有、有線接続等は不可）。
- 梅花林では以下を厳守する:
  - 本が置かれているブロックへ進入する動作を生成しない（ただし回収済みでクリア済みなら可）。
  - FAKE本を動かさない。非隣接ブロックの本を動かさない。
  - 本の回収は隣接ブロックからのみ許可。

曖昧さがある場合は常に安全側で実装する（禁止扱いにする）。

## 2. 参照優先度（Source of Truth）
変更前に必ず以下を読むこと:
- `SPEC_R2_CONTROL.md`（システム要件・インタフェース）
- `TASKS.md`（実装計画・受け入れ条件）
- `README.md`（段差越えシーケンス等の機械手順）

## 3. ワークフロー
- 1タスク = 1PRサイズの変更。
- 必ず実行:
  - `colcon build`
  - `colcon test`
- 最終サマリには実行コマンドの結果を記載する。
- コミットは小さく、レビューしやすく保つ。

## 4. リポジトリ構成
- `src/robocon_interfaces/` : カスタムmsg/srv/action定義
- `src/robocon_plum_planner/` : プランナパッケージ
- `src/robocon_localization/` : 位置推定 + mux/gating
- `src/robocon_motion_primitives/` : プリミティブ用actionサーバ
- `src/robocon_bt_mission/` : BTノード / bt_navigator連携
- `src/robocon_bringup/` : launch・パラメータ

## 5. 完了条件（Definition of Done）
以下を満たしたら完了:
- `colcon build && colcon test` が通る
- フォーマット済みで、妥当な範囲で警告に対応済み
- プランナに以下のユニットテストがある:
  - 「未クリアの本ブロックに進入しない」
  - 「隣接ブロックからのみ回収する」
  - 「退出条件（10/11/12かつcarry>=1）」
  - 「1〜3にR2本がある場合の初手回収特別ルール」
- 公開API（msg/action）が`SPEC_R2_CONTROL.md`に記載されている

## 6. コミュニケーションスタイル
計画提案時は以下を示す:
- 変更対象ファイル
- 実行コマンド
- リスク/前提
出力は簡潔かつ実行可能に保つ。

PRは日本語で記述すること
