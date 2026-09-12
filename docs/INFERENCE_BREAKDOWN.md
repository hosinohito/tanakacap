# 推論時間内訳と統合構成オプション

最新（2026-09-13）：通常はRTMW3D顔/体共有＋PnPピッチ/Z口角、Gのcrop後RGB化、Iの左右眼batch2を採用。Fの人物Graph分割は任意OFF、H並行は遅くrevert。[新しい測定条件・結果](FURTHER_OPTIMIZATION.md)。

2026-09-12。RTX4090、既存HuffYUV録画1280x720の先頭930フレーム（30 warmup＋900観測）、各構成を順番に計測。専用Player/隔離OBS/プレビューをこの試験では起動しない。録画読み込みは実時間の速度制限なし。ORT詳細トレースをOFFにして結果JSONを記録した。

再現：tools/profile_inference_stages.py。入力は既存のresults/comparison-takes/20260911T235327-031115Z/camera.avi。統合結果はresults/inference-stages-1789224490331791700/summary.json、各reportへの参照を含む。頭専用の固定ROIはこの録画に合わせた618,246,170,165で、他の映像へはそのまま使えない。

## 全構成の内訳（900観測の中央値）

| 区間 | ms |
|---|---:|
| 人物検出の前処理 | 1.193 |
| 人物検出の推論呼び出し | 14.968 |
| 人物検出の後処理 | 0.053 |
| 顔/頭用RTMW-Lの前処理＋推論＋後処理 | 5.683 |
| 体RTMW3Dの前処理＋推論＋後処理 | 10.228 |
| 目線（虹彩、切り出し/後処理含む） | 4.106 |
| 頭のPnP幾何処理 | 0.585 |
| ランドマークからの制御作成 | 0.179 |
| 顔の時間フィルター | 0.067 |
| 顔距離 | 0.116 |
| 体/腕/掌/指の共通補正 | 0.843 |
| UDP送信 | 0.097 |
| 上記以外の送信前処理 | 0.598 |
| 録画read/decode | 1.875 |
| 結果送信まで（read後） | 39.217 |
| readからループ末尾まで | 41.145 |

中央値を合計して全体中央値とはしない。推論呼び出しはGPUカーネル時間そのものではなく、アップロード/出力取得/同期を含む。人物検出の内訳も今回分離した。独立した手専用モデルは通常構成にはなく、RTMW-L/RTMW3Dの共通出力を使う。

顔モデルは頭だけの点を計算するネットワークではなく、133点をまとめて出す。表情の反映だけOFFにしても、そのモデルの計算量を大幅には削れない。モデル別の有無を比較した数値と、その内部で頭/指だけが何msかという未測定値を混同しない。

## 構成比較

| 構成 | ループ中央値 |
|---|---:|
| 全てON | 41.145ms |
| 体モデルと体/手制御OFF、目線ON | 29.352ms |
| 顔・頭のみ、体/目線OFF | 24.579ms |
| 顔・頭のみ＋人物検出OFF（画像全体を使用） | 9.719ms |
| 頭専用MobileNet、手動固定範囲 | 3.177ms |

下2行は入力範囲やモデルも変わるので精度同等の比較ではない。頭専用モデル処理は1.589ms。実カメラ30fpsならこの数値の逆数で更新されるわけではない。撮影/時間フィルター位相/Unity描画/Spout/OBS/表示までの遅延でもない。

以前の全モデル＋Player/OBS約20Hzと、この試験の約41msは条件が異なる。60fps描画は直前の追跡姿勢を補間しており、各推論を直列に行う認識周期が自動で60Hzになるものではない。単一のCPUコアや4090の能力不足が原因と断定しない。

## 起動・既定

同じrun-avatar-lab.ps1 / 同じPlayerを使い、-TrackingMode full / face_head / head_onlyで切り替える。tracking-settings.jsonのtracking_modeにも対応。既定full。個別-NoBody/-NoGaze/-NoPersonDetectorも利用可能。body_enabled/person_detector_enabled/gaze_enabledの既定はtrue。切替は起動時、実行中の再ロードUIは未実装。

-NoBodyはモデル生成と体/腕/掌/指/顔距離による胴体制御を停止し、残った2D点で腕が動く代替経路も止める。目線OFFは虹彩推論の停止で、顔モデル由来のまばたきは残る。-NoPersonDetectorは人物の在不在判定を失う診断用。head_onlyは別の専用モデルへ内部切替する。詳しくはHEAD_ONLY.md。

--no-ort-profileは計測JSONを残してORT node traceだけOFFにする開発引数。--no-logは従来通り全記録/詳細profileを停止。新たな性能ログに実写画像は保存しない。head-onlyの最終CUDA証拠はresults/20260912T145144-131515Z-head-only/report.json、CUDA node 5643、CPU node 0。配置された重みのSHA256も照合した。

## 2026-09-13 頭専用auto

自動頭領域YuNetを追加した頭専用autoは同じ先頭930入力/900測定、単独/previewなし/ORT traceOFFでループ中央値8.601ms、領域3.828ms、姿勢2.339ms、decode1.892ms。900/900が追跡有効（精度の正解率ではない）。results/20260912T155231-635213Z-head-only/report.json。旧fixed3.177msとは機能が異なり、同時再測定ではない。上の既存full内訳は未変更。再現スクリプトはhead-only-fixedとhead-only-autoを分けるよう更新。通常構成の高速化はまだ実装せず、PERFORMANCE_OPTIONS.mdの案に対する優先順位指定待ち。
