# R2 BT 実装計画書

## 1. 目的
本計画書は、`R2_ctrl` ワークスペースの現行実装を前提として、`robocon_bt_mission` を段階的に本番仕様へ拡張するための実装手順をまとめる。

主対象は梅花林フェーズの Mission BT であり、Dojo / Arena は後段の拡張方針として扱う。

この文書の方針は以下の 4 点とする。

1. 既存 `robocon_*` パッケージ構成を維持する
2. 既存 ROS interface を基準にし、互換性を壊さない
3. Plum フェーズを先に完成させ、後から試合全体 BT へ拡張する
4. mock と real を切り替えながら常に部分統合可能な状態を保つ

## 2. スコープ

### 2.1 今回の主スコープ
- `robocon_bt_mission` の Plum フェーズ BT
- `robocon_plum_planner` との接続
- `robocon_motion_primitives` との接続準備
- `Groot2` での静的可視化

### 2.2 今回の主スコープ外
- Dojo / Arena の詳細な leaf 設計
- `BehaviorTree.CPP` への全面移行
- Groot のライブモニタ連携
- Nav2 統合の本実装

## 3. 現在の実装状況

### 3.1 既に実装済み
- `robocon_interfaces`
  - `BookMap.msg`
  - `CellState.msg`
  - `PlumPlan.msg`
  - `MoveCell.action`
  - `ClimbStep.action`
  - `PickAdjacentBook.action`
  - `DockToAruco.action`
- `robocon_perception`
  - `/book_map` 生成
- `robocon_plum_planner`
  - `/book_map` + `/cell_state` から `/plum_plan` を生成
  - 安全制約とフォールバック計画を実装済み
- `robocon_bt_mission`
  - 簡易 Plum BT を実装済み
  - `ObserveAllBooksFromCorridor -> ComputePlumPlan -> ExecutePlumPlan -> ExitPlumForest`
  - action 失敗時の 1 回だけ再計画
  - モック世界ノード
  - `Groot2` 用の静的 XML

### 3.2 未実装または未完了
- `robocon_localization`
  - Task 4: `odom_mux`, `scan_gate`
- `robocon_motion_primitives`
  - 独立パッケージとして未作成
- 実機を含む E2E
  - DDS 制約のためこの環境では未確認

## 4. 現行アーキテクチャ

### 4.1 パッケージ責務

`robocon_interfaces`
- スタック全体で使う msg / action 定義

`robocon_perception`
- YOLO 結果から `/book_map` を生成

`robocon_plum_planner`
- `BookMap` と `CellState` から安全な離散計画を作る
- 梅花林ルールの主要制約はここを正とする

`robocon_localization`
- scan fusion
- 将来的に FLAT / CLIMB 切替

`robocon_motion_primitives`
- `MoveCell`
- `ClimbStep`
- `PickAdjacentBook`
- `DockToAruco`

`robocon_bt_mission`
- Mission BT
- Blackboard 管理
- planner / action / state の接続
- static BT XML の管理

`robocon_bringup`
- launch と全体構成

### 4.2 レイヤ構成

1. Mission Layer
   - フェーズ進行
   - リカバリ判断
   - blackboard 更新

2. Planning Layer
   - 梅花林離散計画
   - 退出条件を満たす行動列の算出

3. Skill Execution Layer
   - move / climb / pick / dock の action 実行

4. Localization / Perception Layer
   - `book_map`
   - `cell_state`
   - `loc_mode`

## 5. 固定するインタフェース

### 5.1 Topics
- `/book_map` : `robocon_interfaces/msg/BookMap`
- `/cell_state` : `robocon_interfaces/msg/CellState`
- `/plum_plan` : `robocon_interfaces/msg/PlumPlan`
- `/loc_mode` : `std_msgs/String`

### 5.2 Actions
- `/move_cell` : `robocon_interfaces/action/MoveCell`
- `/climb_step` : `robocon_interfaces/action/ClimbStep`
- `/pick_adjacent_book` : `robocon_interfaces/action/PickAdjacentBook`
- `/dock_to_aruco` : `robocon_interfaces/action/DockToAruco`

### 5.3 action result の前提
現状の action result は以下を基準とする。

- `success`
- `error_code`
- `debug`

新しい共通 result フィールドは追加前提にしない。必要になった場合は `robocon_interfaces` の別タスクとして扱う。

## 6. Blackboard 方針

### 6.1 現在の必須キー
- `book_map`
- `cell_state`
- `plan`
- `carry`
- `loc_mode`
- `retry_count`
- `last_error`
- `mission_phase`

### 6.2 将来の拡張候補
- `selected_target`
- `selected_staging_pose`
- `selected_exit_pose`
- `arena_strategy`
- `dock_result`

将来キーは追加候補であり、現在の Plum BT 実装の前提にはしない。

## 7. 現在の Plum BT

### 7.1 現在の木構造

```text
ObserveAllBooksFromCorridor
  -> ComputePlumPlan
  -> ExecutePlumPlan
  -> ExitPlumForest
```

### 7.2 各 leaf の責務

`ObserveAllBooksFromCorridor`
- `/book_map` と `/cell_state` を待つ
- 取得済みなら blackboard を更新する

`ComputePlumPlan`
- `/plum_plan` を受け取り blackboard に格納する
- 空 plan は失敗扱い

`ExecutePlumPlan`
- `plan.steps` を先頭から順に dispatch する
- `ACTION_MOVE` は `/move_cell`
- `ACTION_PICK` は `/pick_adjacent_book`
- `ACTION_EXIT` は BT 内部で Exit 判定へ遷移する

`ExitPlumForest`
- `current_cell_id in {10, 11, 12}`
- `carry >= 1`
を満たしたら成功とする

### 7.3 現在のリカバリ方針
- action 失敗時は 1 回だけ再計画する
- 再計画後も失敗したら mission failure とする

## 8. これからの実装方針

### 8.1 Step A: 現在の簡易 BT を維持しながら整理する
目的:
- 既存の simple BT を壊さず、将来の本番化に備える

作業内容:
- `mission_bt_core.py` の責務を維持
- `simple_plum_bt.xml` を `Groot2` 用静的図として維持
- ログ出力と blackboard の意味を文書化

完了条件:
- mock world + planner + mission BT で現在の成功系が維持される

### 8.2 Step B: Localization Mode Switching を先に完成させる
目的:
- `ClimbStep` 実装時に必要な `FLAT / CLIMB` 切替を先に固める

対象:
- `robocon_localization`

作業内容:
- `odom_mux`
- `scan_gate`
- `/loc_mode` に基づく切替

完了条件:
- CLIMB 中に AMCL 入力を遮断できる
- FLAT / CLIMB の状態が BT から参照可能になる

### 8.3 Step C: `robocon_motion_primitives` を独立実装する
目的:
- いま `robocon_bt_mission` 内に置いているモック世界を、本来の action server へ置き換える

対象 action:
- `/move_cell`
- `/climb_step`
- `/pick_adjacent_book`

初期方針:
- まずは mock 実装で良い
- result は既存 interface に合わせる
- 実機 I/O フックは後から差し込める構造にする

完了条件:
- `robocon_bt_mission` から action client で呼べる
- fake I/O で成功 / 失敗 / 進行ログが確認できる

### 8.4 Step D: Plum BT を本番寄りに拡張する
目的:
- simple BT を `Task 7` の本番に近い形へ育てる

追加する内容:
- `ClimbStep` を含む plan 実行
- action 失敗分類
- 再計画前の再ローカライズ待ち
- `loc_mode` を踏まえた実行判定
- retry policy の段階化

この段階でも、主フローは Plum に限定する。

### 8.5 Step E: 梅花林完遂を安定化する
目的:
- 机上・mock ではなく、実機に近い条件で Observe -> Plan -> Execute -> Exit を完走させる

必要な確認:
- perception の信頼度しきい値
- planner との同期
- action 実行後の `cell_state` 更新
- 退出条件の安定判定

### 8.6 Step F: 将来の試合全体 BT へ拡張する
後段で追加するフェーズ:
- Init
- Dojo
- Assembly
- Plum
- Arena
- End

この段階で初めて、`RootMission` 相当の木を検討する。

## 9. Nav2 の扱い

### 9.1 現時点の位置づけ
- `SPEC_R2_CONTROL.md` 上では Nav2 BT Navigator 連携は任意
- 現在の Plum BT は Nav2 非依存の構成を採る
- 梅花林内は離散セル追跡を優先する

### 9.2 先にやるべきこと
- Task 3.6 の Nav2 最小成立確認
- staging pose までの移動成立確認

### 9.3 後で追加するもの
- `robocon_bt_mission` から Nav2 action を呼ぶ adapter
- Plum 外フェーズでの活用

## 10. Groot2 可視化

### 10.1 現在の運用
- `behavior_trees/simple_plum_bt.xml` を `Groot2` で開く
- これは静的可視化であり、現在の Python 実装のライブ状態は反映しない

### 10.2 目的
- 木構造の共有
- リカバリ枝の確認
- 命名と責務の固定

### 10.3 将来拡張
- `BehaviorTree.CPP` 採用時にライブモニタを検討する
- それまでは static XML を設計図として使う

## 11. 推奨実装順

### Stage 0: 現状維持確認
1. `robocon_bt_mission` の simple BT を維持
2. static XML を `Groot2` で確認
3. mock launch で Observe -> Plan -> Execute -> Exit を確認

### Stage 1: 足回りの前提整備
4. Task 4: `robocon_localization` の FLAT / CLIMB 切替
5. Task 3.6: Nav2 最小テスト

### Stage 2: 実行層の独立
6. Task 6: `robocon_motion_primitives` を新規実装
7. mock action server を `robocon_bt_mission` 外へ移す
8. `move / climb / pick` の失敗コードを揃える

### Stage 3: Plum BT 強化
9. `robocon_bt_mission` を real action server と接続
10. retry / replan / relocalize の分岐を追加
11. `cell_state` の更新責務を整理

### Stage 4: 実機寄り統合
12. perception + planner + motion primitives + BT を接続
13. 梅花林単独完遂を目標に調整

### Stage 5: 将来拡張
14. Dojo / Arena の設計を追加
15. 必要なら `RootMission` を導入

## 12. マイルストーン

### M1. simple Plum BT が mock で通る
- 目的: 骨格確認

### M2. localization mode switching 完了
- 目的: climb 系 action の前提成立

### M3. motion primitives mock 独立化
- 目的: `robocon_bt_mission` と action 実装を分離

### M4. Plum phase 単独完遂
- 目的: Observe -> Plan -> Execute -> Exit の成立

### M5. 試合全体 BT 拡張開始
- 目的: Dojo / Arena を後付けで統合

## 13. テスト戦略

### 13.1 単体テスト
- `robocon_plum_planner` の planner unit test
- `robocon_bt_mission` の BT core test
- static XML の parse test

### 13.2 コンポーネントテスト
- planner + BT
- action server + BT
- localization mode switching

### 13.3 最低限の統合確認
- ダミー `/book_map` に対して `/plum_plan` が出る
- mock action で plan を消費できる
- 失敗時に 1 回だけ再計画する

### 13.4 実行コマンド
- `colcon build --packages-select robocon_bt_mission --symlink-install`
- `colcon test --packages-select robocon_bt_mission --event-handlers console_direct+`
- `colcon test-result --verbose --test-result-base build/robocon_bt_mission`
- `ros2 launch robocon_bt_mission simple_plum_bt_demo.launch.py`

## 14. 補足

### 14.1 本計画でやらないこと
- 既存 public interface の破壊的変更
- `robocon_plum_planner` の責務を別 planner / rule engine へ再分割
- `r2_*` 名前空間への全面移行

### 14.2 将来の再検討項目
- `BehaviorTree.CPP` への移行可否
- Nav2 adapter の追加
- full mission BT の root 構成
- live monitor 用の BT 状態配信
