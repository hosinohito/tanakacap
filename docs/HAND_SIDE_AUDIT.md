# 左右の手の独立性の調査

2026-09-23。本人・アバターとも解剖学的な右手をロールすると、左手（画面向かって右）もロールする。両手を顔の前の横へ持ってきた姿勢で発生し、左指が動かない症状もある。対象はローカル0.1.3のavatars/avatar.tcapに置かれた改変済みHAOLAN。

## 結論と限界

左右の計算関数は共用するが、手の履歴・角度・送信フィールド・反映先の共有や取り違えは今回の調査では見つからなかった。人工入力では指定アバターの左右が独立して動く。実使用の症状そのものは未再現で、解決済みとはしない。製品コード・信頼度閾値・平滑化・アバター原本は変更していない。

## 処理経路の確認

| 段階 | 共通部分 | 左右を分ける部分 |
| --- | --- | --- |
| モデル | RTMW3D-Xが同じ画像から体・顔・両手を推論 | 手の21点は左91〜111、右112〜132 |
| 座標・腕 | 顔尺度、胴体の基準、幾何計算 | 腕は左5/7/9、右6/8/10。各腕の投影・時間フィルター・保持は別状態 |
| 掌 | palm_basis、PalmFilter.update | states/motionをsideで分離。受理フレーム・平均の履歴をコピー |
| 指 | FingerTracker.update | gateのキーは(side,finger)。角度・有効マスクはループごとに新規作成 |
| 送受信 | LocalSender、TrackingParts | left/rightのpalm/fingers各スロットに限定したフィールドのみ更新 |
| Unity | DriveHand、DriveFingers、DriveArmsWithLoss | Arm、Finger、PoseTransition、ArmRotationFrameを左右別に生成。HumanoidのLeft/Rightを明示 |

点番号は[公式COCO WholeBody定義](https://raw.githubusercontent.com/open-mmlab/mmpose/main/configs/_base_/datasets/coco_wholebody.py)とも照合した。共通モデルの推定誤差や共通の胴体・尺度変化による間接影響まで否定した検査ではない。

## 人工入力と実Player

Pythonは片手だけ回転・屈曲させて反対側の掌・指が不変であることを左右対称に検査。関連18 tests成功。

Unityは、両腕を固定して顔の両側へ手を上げ、基準／右ロール／左ロール／左指屈曲／右指屈曲の5条件。現在の開発Playerと配布v0.1.4 Playerの両方に実UDPで送信し、指定された改変アバターをauto-customでロード。原本は変更せず、実カメラは使用していない。

| 入力 | 結果（両Player） |
| --- | --- |
| 片手だけ60度ロール | 対象は約60度、反対側は0.001度未満 |
| 左指だけ屈曲 | 左指の最大変化約65度、右指の変化0度 |
| 右指だけ屈曲 | 右指の最大変化約65度、左指の変化0度 |

改変アバターの左指屈曲・右手ロールのスナップショットも目視し、骨の数値だけでなく表示メッシュの動きを確認した。全姿勢・全経路の保証ではない。

結果はローカル`results/hand-sides-modified-20260923/`と`results/hand-sides-release-20260923/`。各report.jsonと*.bones.json、*.tracking.json、画像、Playerログを保存。配布版検査のreportにはアバターとAssembly-CSharpのSHA256も記録。

## 既存録画の再処理

`results/comparisons/arm-corrections/recorded/frames.jsonl`の901観測を、現在のBodyRetarget(3,1,front_projection,face_ratio)で再処理。元映像は1280×720、モデルは再実行せず、画像も表示していない。保存データにZピーク振幅がないため有限値1で補完した。現実装はその振幅を信頼度閾値に使わないが、元の非有限判定は再現できない。XY信頼度は保存値のまま。

| 指の有効観測数（親指→小指） | 左 | 右 |
| --- | --- | --- |
| 901観測中 | 541 / 490 / 438 / 388 / 420 | 468 / 419 / 427 / 442 / 444 |

左指は常時停止してはいない。左246観測、右263観測で掌基準を作れず、全指を欠測にした。そのほか、関節長・点の信頼度・曲げ面・時間平均の待機でも保留する。これらの閾値は今回変更していない。有効数は正解数ではなく、今回の症状が録画に含まれると確認したものでもない。

手の根元が反対の体側手首へ10px以上近いケースは、双方とも比較可能899観測中0件。点群全体の左右交換を示す材料は得られなかった。掌の向きだけの誤推定はこの距離比較では検出できない。内訳は`results/hand-sides-modified-20260923/recorded.json`。

## 次の切り分け

症状が出る録画で、右手をロールした時刻の左手21点・生の掌法線・平滑化後の送信値・Unityの骨を順に照合する。左の推定値から動いているなら推定／幾何側、送信が不変なのに骨が動くなら姿勢補正／受信側へ絞れる。掌の形やZが崩れた場合は、左指の欠測とロールの誤推定が同時に起こる可能性があるが、現段階では仮説。

撮影が必要な場合はユーザー操作の既存30秒`tanakacap-face-capture.bat`を使い、実写非表示を維持する。長い動作案内や新しいカメラ設定変更は不要。エージェントが勝手に実カメラを開かない。

## 再実行

リポジトリ直下から、未使用の出力先を指定する。一般のアバターは既存snapshot診断の口幅シェイプ検査等に未対応の場合があり、その失敗を手の不具合と混同しない。

```powershell
.\.venv\Scripts\python.exe -X utf8 tools/diagnostics/audit_hand_sides.py --avatar builds/releases/0.1.3/TanakaCap/avatars/avatar.tcap --output results/hand-sides-next
.\.venv\Scripts\python.exe -X utf8 tools/diagnostics/audit_hand_sides.py --recorded results/comparisons/arm-corrections/recorded/frames.jsonl --output results/hand-sides-next-recorded.json
.\.venv\Scripts\python.exe -m pytest tests/test_hand_side_isolation.py tests/test_hand_orientation.py tests/test_fingers.py tests/test_partial_tracking.py -q
```

--playerで他の対応Playerを指定できる。これは部位別通信対応Playerの診断で、旧通信版へ自動変換しない。結果・アバター・実写・個人設定はGit管理外。


撮影後の数値生成は`tools/compare_precision.py --take <新しい録画フォルダー> --output <未使用の比較フォルダー> --name recorded --mode graph-fp16`を使用する。今回、記録に実際のbody_xy/body_scores/body_depth_scores、画像サイズ、body_diagnosticsを追加したため、次の録画では欠測理由とZの有限判定を同じ入力で追跡できる。推論・補正の動作は変えていない。撮影開始はユーザー操作で行う。

撮影準備の検査：関連31 tests成功。既存録画40観測で追加した点群・Z振幅・欠測理由・画像サイズの保存とcompleteレポートを確認（results/hand-sides-recording-check）。デスクトップの撮影batを再生成し、face-headプロファイル・実写表示許可なしを確認。カメラは起動していない。
