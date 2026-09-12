# フェーズ4：品質・継続動作の検証

2026-09-12。追加AAに続いて、OBS併用の継続安定性、描画/受信速度、遅延の切り分け、採用済み追跡の残件を評価する。計測実装をしただけでフェーズ4合格とは扱わない。

## 今回の変更

- 軽量AAをプレビューとRGBA出力へ追加。ANTIALIASING.md参照。
- 既定720pを保持し、--output-height 1080（PowerShellは-OutputHeight 1080）でフルHD出力を選べる。
- PerformanceProbeは--performance-log保存先を指定した場合だけ追加。1秒分の固定長配列から描画間隔・描画投入CPU時間・揺れCPU時間・受信頻度・メモリを集計する。--performance-secondsで検証だけ自動終了。通常の無期限/非記録モードは変更しない。-Diagnoseの既存検証batではresults/player-performanceへPlayer統計も残す。
- --performance-gpuを明示した比較時だけUnityのGPU Frame Time recorderを開始する。統計を取得できなければ-1と有効サンプル0を記録し、CPU時間で代用しない。GPUカウンターには測定負荷と結果遅延がある。
- 推論パケットに最新入力の読み取り完了時刻と送信時刻を追加した。Windowsの共通QPC時計でPlayerの描画投入後と比較する。古い時刻なしパケットは追跡でき、遅延だけ未計測となる。
- --source video --loop-video --no-logで既存動画を繰り返しGPU推論する。EOFだけ巻き戻し、通常カメラの挙動を変えない。録画や外部送信はしない。採用した頭/口/掌/肩face_ratio/腕front_projectionを変更しない。

## 計測値の意味

| 値 | 測るもの | 含まないもの |
|---|---|---|
| fps / frameP95Ms | Playerの1秒窓のフレーム頻度と間隔 | 実ディスプレイの走査、OBSで見える独立姿勢数 |
| receivedPackets / windowSeconds | Playerが検査を通して受けたパケット数/秒 | 正確な推定数、センサーフレーム数 |
| renderSubmitMeanMs | 透過Camera.Render呼び出しのCPU経過時間 | GPU完了までの時間、AAだけの時間 |
| gpuFrameMeanMs | UnityカウンターのGPU描画時間 | 推論モデルだけの実行時間。共有GPUの競合は影響し得る |
| latestInputReadToRenderSubmit* | 最新画像read完了からPlayerの描画投入まで | 露光/カメラ内部待ち/動画decode前、時間フィルターの実効位相遅れ、GPU完了/Spout/OBS/画面走査 |
| sendToRenderSubmit* | Python送信直前から描画投入まで | センサーと推論時間 |
| packetAgeMeanMs | 最後の受信からの時間 | 全体遅延 |
| メモリ | プロセスのWorking Set/Private Bytes、Unity各メモリ値 | RAMとVRAMを同じ数値として扱わない |

1秒窓ごとのp95の中央値は、全フレームをまとめたp95ではない。撮影済み動画のストレス反復は実カメラの取得経路を使わず、ファイル再生時刻にも同期しない。既存録画だけでは実人物の動作→表示の遅延や認識正解率を測れない。

## 再実行

セットアップ・Playerビルド済みで、results/phase3-obs/appの隔離OBSとSpoutがある開発環境が対象。ユーザーの通常OBS設定を変えず、配信/録画は開始しない。4456の隔離サーバーが既に使用中なら中断する。outputにはまだ存在しないフォルダーを指定する。

    .\.venv\Scripts\python.exe tools/phase4_soak.py --seconds 1800 --video results/comparison-takes/20260911T235327-031115Z/camera.avi --output results/phase4/soak-new

720p既定、隔離OBSは60fps。フルHDは--output-height 1080。AA比較は同じ条件で--no-edge-aaを付け、別のoutputで実行する。--gpu-timingを使うなら両比較に付ける。カメラなし自作モーションによる描画だけの比較は--demo（--video不要）。

resultsにはplayer.jsonl、system.jsonl、report.json、OBSで受信したsource/composite画像、診断コンソールを残す。既存の実写動画は入力として参照するだけ。OBS画像はアバターであり実写ではない。Python venvの小さい起動プロセスだけを測らず、子の実Pythonもメモリ集計する。

    .\.venv\Scripts\python.exe tools/audit_phase4_tracking.py results/comparisons/shoulder-projection-final/shoulder-face/frames.jsonl results/phase4/tracking-audit.json

## 追跡品質の監査

既存採用済み入力の5,187フレームのステージ別監査はresults/phase4/tracking-audit.json（正確な総数は同ファイルのframes合計）。開始neutralの肩ヨーは0だが、end_stillの絶対yaw中央値15.99度/p95 19.41度が残る。指の有効フラグは左右ともあり、単純な「左系統が未実装」では説明できない。一方、顔付近の手のステージで左手首の大きい差分が多く、追跡点/奥行き/補正/実ボーンを時刻対応させた継続調査が必要。フラグや角度の変化を正解率とは呼ばない。

ユーザーが補正を採用して次へ進むと指定したため、今回の描画作業に無根拠な肩/腕の新補正を混ぜない。既知残件を消した扱いにせず、Phase2/4に残す。

## 検証結果

- 非記録反復、画面外保持、腕投影、肩投影、腕長校正、掌/指、顔距離/頭、観測平均の回帰76件成功。pytest cache書込を行わない条件で実行。
- AA同一姿勢の実Player比較成功。詳細はANTIALIASING.md。
- 初回OBS画像の目視で、過去のキャンバス変更によるソース倍率2/3の残留を発見。透過自体は届いているが余白が生じた。再検証ツールにソース寸法からキャンバスへ合わせる変換と背景四隅の検査を追加。ユーザーの通常OBSは変更しない。
- 30分試験：results/phase4/soak-aa、集計soak-summary.json。720p/追加AA/全モデル/録画反復、隔離OBS30fps。Player中央値59.990fps、受信20.168Hz、1秒窓p95の中央値17.617ms。OBSのrenderSkipped増分0。途中のソース倍率は2/3だったため、全面表示の最終合成検証とは分ける。
- メモリ（先頭/末尾の6観測中央値）：Player Private 656.725→657.527MiB、OBS 861.947→861.859MiB。実推論プロセスと子の合計Private 4390.658→4387.379MiB、Working Set 1389.910→1386.010MiB。推論側は補足1671秒の計測。初版system.jsonlのcapture値は小さいvenvランチャーだけなので使わず、capture-memory.jsonlで補っている。大きな継続増加は見られないが、全条件のリーク不存在の証明ではない。
- 36秒付近に434.953ms、61秒付近に209.295msのフレーム間隔が2件ある。後者は管理メモリ約68MB→約1MBの回収と同時。前者と診断画像取得の因果は未確定。中央値だけで長時間の一時停止を隠さない。
- 読み込み時のMemoryStream成長＋ToArrayの一時配列重複を、ZIP内の検査済み長さの単一バッファに整理。読み取り不足/超過とSHA256照合を維持。明示GC強制や追跡中のGC無効化はしていない。この最終変更後の長時間再試験は未実施。
- AA負荷比較：aa-gpu-on / aa-gpu-off。各90秒、720p、自作モーション、OBS60fps、同じGPUカウンター計測。AA ON/OFFのPlayerは59.998/59.999fps。GPU描画の1秒平均値の中央値は3.182/3.382msと順序が逆になった。描画内容とクロック等のばらつきがあり、AAが速くしたとは解釈せず、追加GPU時間の厳密な分離は未達。両方で60fps維持、OBS取りこぼし増分0、RGBAの透明/不透明/中間画素、画像の変化、背景四隅の一致を確認。
- 最終1080p：fullhd-final / fullhd-summary.json、120秒の既存録画推論＋OBS60fps。Player59.992fps、受信20.101Hz、1秒窓p95の中央値17.637ms、測定対象の最大間隔19.157ms。最新入力read→描画投入の1秒窓中央値の中央値56.284ms、同p95の中央値65.438ms、送信→描画投入中央値8.635ms。露光/フィルター位相/表示遅延は含まず、100ms/150msのエンドツーエンド目標達成とは書かない。
- フルHDの実Spout受信：透明1,361,455、不透明700,345、中間11,800画素、始終の変化966,528画素、背景四隅誤差0。OBS描画取りこぼし増分0。最終の表示全体で合成成功。初回縮小設定の残留は解消した。
- 最終実Player回帰：transport.*で顔/腕/掌/指/ロスト保持とalpha成功。secondary.jsonで73区間960ステップ、静止速度0.0000142m/s、本体回転/位置変化0、OFF復元。単独CPUステップ最大約0.95ms。元PhysBoneとの同一動作の証明ではない。
- package-check/report.jsonで形式/ハッシュ/Unity版/不正Bundleの4ケースをcode2で拒否。原本依存hashは25babac2d68f0ee4c5323cd154f54b98のまま。no-log-final.jsonで最終AA既定の自作モーション4秒、Player.log不変/新規results項目なし。テスト/ライブ/モーションのデスクトップbat更新済み。
- 30分試験後の読み込みバッファ整理・GPU統計/1080p等を含む最終ビルドで、30分を再実行したわけではない。実カメラの30分、実人物の品質、本家PhysBoneとの差、認識30Hz、実動作→画面表示の遅延は未達/未確認。通常OBSへ停止/設定変更操作を行わず、検証用Player/隔離OBSのみ終了。配信/録画は開始していない。

## 一次資料

- Unity FrameTimingManagerと計測負荷、ProfilerRecorderによる必要時だけの取得：
  https://docs.unity3d.com/ja/2022.3/Manual/frame-timing-manager.html
- Python 3.11のperf_counter（Windowsでsystem-wideになったのは3.10以降）：
  https://docs.python.org/3.11/library/time.html#time.perf_counter
- Windows QueryPerformanceCounter：
  https://learn.microsoft.com/en-us/windows/win32/api/profileapi/nf-profileapi-queryperformancecounter
