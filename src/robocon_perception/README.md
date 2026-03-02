# robocon_perception README (Task 2)

このドキュメントは、Task 2 の「画像認識結果を受けてからの処理」連携用です。
画像処理担当メンバーが `/yolo_detections` を正しくpublishできれば、R2側で `/book_map` と可視化が動作します。

## 1. 何をpublishすればよいか

### 必須入力topic
- Topic名: `/yolo_detections`
- Message型: `vision_msgs/msg/Detection2DArray`

`bookmap_node` はこのtopicを受けて `/book_map` を生成します。

## 2. Detection2DArrayの必須フィールド

各 detection で最低限必要な項目:
- `bbox.center.position.x`
- `bbox.center.position.y`
- `results[*].hypothesis.class_id`
- `results[*].hypothesis.score`

ノード側の仕様:
- `results` 内で `score` 最大要素を採用
- `class_id` は `R2` / `R1` / `FAKE` を想定（内部で大文字化）
- `score < confidence_threshold`（初期値 0.6）は `UNKNOWN` 扱い
- bbox中心がLUT範囲外の場合は無視

## 3. R2側の出力

### BookMap出力
- Topic名: `/book_map`
- 型: `robocon_interfaces/msg/BookMap`

内容:
- `book_type[12]`: EMPTY/R2/R1/FAKE/UNKNOWN
- `confidence[12]`: 各セルの信頼度

### 可視化出力
- Topic名: `/book_map_markers`
- 型: `visualization_msgs/msg/MarkerArray`
- 表示は手前列が `10,11,12`

## 4. 起動方法

### RVizで確認（推奨）
```bash
cd /home/rui3510/R2_ctrl
source /opt/ros/humble/setup.bash
colcon build --symlink-install
source install/setup.bash
ros2 launch robocon_bringup perception_rviz.launch.py
```

### Foxgloveで確認
```bash
cd /home/rui3510/R2_ctrl
source /opt/ros/humble/setup.bash
source install/setup.bash
ros2 launch robocon_bringup perception_foxglove.launch.py
```

補足:
- `foxglove_bridge` 未導入なら `sudo apt install ros-humble-foxglove-bridge`

## 5. 画像処理担当チェックリスト

1. `/yolo_detections` が `vision_msgs/msg/Detection2DArray` でpublishされる
2. `class_id` が `R2` / `R1` / `FAKE` で出る
3. `score` が [0.0, 1.0] 範囲に入る
4. `bbox.center.position` が画像座標（x右正, y下正）で正しい
5. `ros2 topic echo /book_map` で更新を確認できる
6. RVizで `/book_map_markers` が更新される

## 6. カメラなしでの可視化テスト

```bash
ros2 topic pub -r 1 /book_map robocon_interfaces/msg/BookMap "{
  header: {frame_id: 'map'},
  book_type: [0,0,0,0,0,0,0,0,0,1,3,4],
  confidence: [1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,0.95,0.88,0.55]
}"
```
