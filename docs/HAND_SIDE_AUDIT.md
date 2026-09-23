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


## 2026-09-23の再現用録画

`results/comparison-takes/20260923T064052-167149Z` はcomplete、1280×720、30fps、901観測、約30秒。ハッシュ検査後、全身ON/CUDA graph-fp16で再推論。実写は表示していない。数値・診断・動画は `results/hand-sides-new-recording-20260923/`。

- `recorded/frames.jsonl`：モデル出力、マスク後入力、Z振幅、欠測理由、送信値。今回Z振幅の代用は0件。
- `fingers.json`：左の有効指観測は親指から684/676/620/613/627、右674/642/641/652/645（各901中）。左の主な拒否理由は関節点の信頼度不足。左指が常時無効という現象ではない。有効率は精度を表さない。
- 左の生の掌法線が1観測で100度以上変わる時刻は0.224、8.656、9.024、16.719、19.920秒。推論点から求める幾何の段階で起きており、Unityだけで発生した回転ではない。ただし実際の左右独立動作の時刻は未指定、これだけでモデル誤推定と断定しない。
- 指定の改変済みHAOLANの実骨監査 `avatar.png.audit.jsonl` は901観測成功。約10〜18秒の左前腕は+160度、要求約+277〜285度。同じ向きの約-83〜-75度が可動範囲内なのに、現在の表示角に近い360度別表現を選んでからclampするため上限から戻れない。約9〜20秒で掌方向誤差が大きくなる。`DriveHand` の `UnwrapTwist` / `ResolveArmTwist` の組み合わせを次の修正候補とする。可動限界±160度自体の撤廃はしない。
- 初期姿勢の影響を切り分けるため、通常のオフライン描画でも再生し同じ張り付きを確認。`avatar-replay.mp4` は実写なし、指定アバター/auto-custom、901フレーム・30fps。対応JSONに実骨のねじりを保存。これは推論レイテンシ比較ではない。

左右の共有状態が原因という証拠は依然ない。指については無効観測と有効だが小さい屈曲を分けて調べる。信頼度の閾値や製品コードは今回変更していない。ユーザーから右手だけを回した時間帯を聞き、点群・法線との対応を確認する。

再実行例：

```powershell
.\.venv\Scripts\python.exe -X utf8 tools/smoke_unity.py --avatar builds/releases/0.1.3/TanakaCap/avatars/avatar.tcap --replay-file results/hand-sides-new-recording-20260923/recorded/replay.jsonl --output results/hand-sides-new-recording-20260923/next.png
```

ローカルUIの録画とアバターをこの組み合わせに設定。以前の個人設定は結果フォルダーの `ui-settings-before.json` に保存。別PCで同じ検証をする場合は上記takeフォルダー全体、指定 `avatar.tcap`、数値再生なら `recorded/replay.jsonl`、更新した `tools/smoke_unity.py` をコピーする。アプリ本体は未変更。


## 6秒・15秒の照合と実時間診断

ユーザー指定の右手だけを回す区間は6秒と15秒。各±0.5秒における生の掌法線の最大角距離は、左21.0/27.9度、右137.9/111.9度。平滑化後は左16.3/23.9度、右132.4/76.5度。左の推定揺れは存在するが、右回転の同量コピーではない。

`tools/diagnostics/realtime_hands.py` は保存UI設定から通常の推論コマンドとPlayerを起動し、全身ON・auto-customで記録。`--source video` は動画FPSを上限に再推論し、通常の部位別UDP経路を通す。`--source camera` は保存カメラ設定を使いユーザーが開始する。901観測で終了、黒いコンソールでSPACEを押すと症状の時刻を記録、Qで終了。実写は保存・表示しない。数値ランドマーク記録の追加処理と中継ログの負荷を含むため、通常動作と同一負荷とは扱わない。

Playerの明示引数 `--hand-trace <新規JSONLパス>` のみで、各描画フレームの受信済み目標、部位別元フレーム/状態/経過時間、実際の掌基準・前腕ねじり・指角度を記録する。通常起動では無効。起動時刻の異なるPython/Unity間は部位別frameIdで照合する。カメラの欠落フレームを単純なframe/30で動画時刻へ変換しない。

実時間検証は `results/hand-realtime/20260923T065613-282164Z/`。901推論、2703UDP、2037描画記録。12,138個の有効な掌/指フィールドを部位の元フレーム番号で照合し、不一致0（許容1e-4、最大3.79e-6）。6秒付近の実際の左掌変動約16.1度、右131.8度。15秒付近は左約21.7度、右68.4度、左前腕は+160度に固定。通常経路でも境界張り付きを再現した。左指の実角度も非ゼロであり、完全停止ではない。録画での成功を実カメラの症状解決とは扱わない。

フォルダーには `wire.jsonl`（中継前に受けた部位別データ）、`player-hands.jsonl`（実骨/受信）、`status.jsonl`、`markers.jsonl`、`session.json` を保存。`session.json`の `inference_results` が元点群・欠測理由の `frames.jsonl` のフォルダー。詳細な推論ログはそちらにあり、実写は含まれない。

```powershell
.\.venv\Scripts\python.exe -X utf8 tools/diagnostics/realtime_hands.py --source video --headless
.\.venv\Scripts\python.exe -X utf8 tools/diagnostics/summarize_realtime_hands.py results/hand-realtime/20260923T065613-282164Z
```

カメラ試験はまだ実行していない。デスクトップ `tanakacap-tools/tanakacap-hands-camera.bat` をユーザーが起動する。録画版は同じ場所の `tanakacap-hands-video.bat`。Playerのビルド成功、関連Python14 tests成功。診断無効の左右人工入力5条件も成功（results/hand-sides-trace-build-20260923）。反対手への最大角変化0.003度未満、左右の指屈曲はそれぞれ約65度。


## カメラ試験の総合原因調査

ユーザーによるカメラ試験 `results/hand-realtime/20260923T070155-023807Z` はcomplete、901観測。前回と同じロール連動は出ず、反対手のピッチへの影響と左指の追従不良を報告。SPACEの時刻マーカーは0件、実写は保存しない診断のため、実際の握り姿勢の正解と各時刻を完全には照合できない。

確認済み：

- 14,316個の掌/指送信フィールドを部位別frameIdでUnity受信と照合。不一致0、float変換差最大3.79e-6。取り違え・通信による値混線の証拠なし。
- 左指の有効観測数は896/891/864/863/863（901中）。Unityの実指角度も大きく変わっている。常時欠測・常時不動という意味ではなく、意図した握りに対応しない現象として調べるべき。
- 2Dで指先がMCPへ近づく短縮比0.45未満の有効観測を抽出。左中指60観測の送信中央値は3関節すべて0度。その平滑化前の符号付き角度中央値は約-22/-150/-19度。左薬指62観測も約-28/-116/-23度から送信0度。一方、右中指/薬指の同じ抽出条件では送信PIP中央値約101/105度。推定された3D形状・掌基準で逆曲げ判定になり、負角を0へ制限する経路が左の握りを消す具体例。短縮比は握りの正解ラベルではなく、Z/掌基準のどちらが実像と違うかの断定には実写との照合が必要。
- 顔由来の共通model_scaleだけを全期間中央値に固定し、同じXY/Zの掌ピッチを再計算。通常との差は左p95 0.50度/最大1.31度、右0.76/1.42度。今回の数十度の変動を尺度共有だけでは説明できない。掌の相対Zは左p5〜p95 -1.51〜10.57cm、右-7.55〜1.51cm。推定点、特に相対奥行きの変動を優先調査する。
- 全身の姿勢を一つの有効なカメラ観測で固定し、右に属する目標だけを録画値で動かす実Player試験と、その逆を実施。整定後、固定側の掌角変動は最大0.00017度、指角変動0.00003度未満。直接の左右状態共有は再現しない。胴体/頭/片側目標を固定した人工的な切り分けであり、通常の全身連動やモデル精度を保証しない。

再現ツール：`tools/diagnostics/audit_hand_causality.py <カメラ診断フォルダー> --output <未使用の出力先>`。今回の結果は `results/hand-causality-final-20260923/report.json`。初回 `results/hand-causality-20260923` は手と無関係なgazeのsnapshot検査で失敗したため、固定基準のgazeTrackedのみfalseとして再試験し成功。信頼度ゲート・製品の動きは変更していない。関連17 tests成功。

次の候補は、掌の相対Z/幾何の安定性と、左右それぞれの手の基準面に基づく屈曲解釈を一緒に検討すること。左だけ符号反転、負角を絶対値化、信頼度の一律緩和は未採用。前回確認したUnityの±160度境界張り付きは別の確定した問題として残す。今回のピッチ連動すべてをこの境界問題だけで説明しない。

公式の[SimCC3Dデコーダー](https://raw.githubusercontent.com/open-mmlab/mmpose/main/projects/rtmpose3d/rtmpose3d/simcc_3d_label.py)と[H3WB点順](https://raw.githubusercontent.com/open-mmlab/mmpose/main/configs/_base_/datasets/h3wb.py)も照合。XYZデコードを左右で別順序にする実装や、Zだけ左右を入れ替える処理は確認していない。
