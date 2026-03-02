# robocon_plum_planner

Task 5 用の離散プランナパッケージです。  
`/book_map` と `/cell_state` から、`/plum_plan`（行動列）を生成します。

## 1. このノードが何をするか
- ノード名: `plum_planner`
- 入力:
  - `/book_map` (`robocon_interfaces/msg/BookMap`)
  - `/cell_state` (`robocon_interfaces/msg/CellState`)
- 出力:
  - `/plum_plan` (`robocon_interfaces/msg/PlumPlan`)

探索は Dijkstra です。  
2冊回収+退出を優先し、無理なら1冊回収+退出（fallback）を返します。

## 2. `/plum_plan` の Action 意味
`robocon_interfaces/msg/PlanStep.msg` の定義:
- `ACTION_MOVE = 0`
- `ACTION_PICK = 1`
- `ACTION_EXIT = 2`

### 2.1 ACTION_MOVE (`action_type=0`)
- 意味: 隣接セルへ移動する
- `target_cell_id`: 移動先セルID

### 2.2 ACTION_PICK (`action_type=1`)
- 意味: 隣接セル上の R2ブックを回収する
- `target_cell_id`: 回収対象セルID

### 2.3 ACTION_EXIT (`action_type=2`)
- 意味: 梅花林から退出する
- `target_cell_id`: `-1`（退出はセル指定なしとして扱う）

## 3. 守っているルール（実装済み）
- R2は R2本のみ回収
- PICK は隣接セルのみ
- EXIT は `10/11/12` かつ `carry_r2 >= 1`
- `1,2,3` にR2本がある場合、最初のPICKはCORRIDORからのみ
- `UNKNOWN` / `FAKE` / 未クリア本セルへはMOVEしない

## 4. 赤青番号系の扱い
- 内部計算は赤側番号を正規系で固定
- `team_color:=blue` の場合は入出力で左右反転変換

青→赤の変換例:
- `1->3`, `4->6`, `10->12`

## 5. 高さ情報（メモ）
Task5では未使用ですが、Task6向けに以下を保持しています:
- `1,3,5,7,9,11 = 200mm`
- `6,8 = 400mm`

## 6. 明日見たときの確認手順（最短）
### 6.1 ビルド
```bash
cd /home/rui3510/R2_ctrl
colcon build --symlink-install --packages-select robocon_plum_planner
source install/setup.bash
```

### 6.2 ノード起動
```bash
ros2 launch robocon_plum_planner plum_planner.launch.py team_color:=red
```

### 6.3 出力確認
```bash
ros2 topic echo /plum_plan
```

### 6.4 ダミー入力投入（例）
```bash
ros2 topic pub --once /book_map robocon_interfaces/msg/BookMap "{book_type: [1,1,0,0,0,0,0,0,0,0,0,0], confidence: [1.0,1.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0]}"
ros2 topic pub --once /cell_state robocon_interfaces/msg/CellState "{current_cell_id: 0, carry_r2: 0, cleared_mask: 0, loc_mode: 'FLAT'}"
```

`/plum_plan` に `ACTION_PICK` と `ACTION_EXIT` を含む step 列が出れば動作確認OKです。

## 7. テスト
```bash
cd /home/rui3510/R2_ctrl
colcon test --return-code-on-test-failure --packages-select robocon_plum_planner
colcon test-result --verbose --test-result-base build/robocon_plum_planner
```

