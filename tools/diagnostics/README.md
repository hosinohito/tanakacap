# 継続利用する診断ツール

再利用する診断のスクリプトと起動用batはこのディレクトリに置く。
一時的な検証用のファイルはデスクトップの `tanakacap-tools` に置き、プロジェクト直下には増やさない。
診断結果はGit管理外の `results/` に保存する。

`diagnose-camera.bat` はCMS-V43BKの取得速度を次の順に比較する。開発環境の `.venv` が必要。
デスクトップの `tanakacap-tools/tanakacap-diagnose-camera.bat` からも起動できる。
利用者自身で起動すること。映像の表示・保存は行わない。

1. ちらつき防止：元設定の基準測定、無効・50Hz・60Hzの比較。
2. 露出：元設定の基準測定、自動・短い固定露出（対応範囲内の約1/64秒・1/128秒）の比較。
3. 対応モード：Windows Media Foundationのネイティブモード一覧から720p・MJPEG・約30fpsを一括選択し、適用結果と速度を記録。
4. 取得経路：同じ機種をそれぞれの列挙結果から選び、OpenCV DirectShow・OpenCV MSMF・ネイティブMedia Foundationを比較。

1・2も同じネイティブモードで測る。未対応の制御やモードは理由をログに記録し、代わりの値を黙って使わない。
ネイティブ測定は30サンプルを捨てた後の120圧縮サンプルの到着時刻とメディア時刻を記録する。
OpenCV測定は150フレームの画像変換後の到着速度。測定範囲とウォームアップが違うため、微小差をAPIの優劣と解釈しない。
ネイティブ経路は表示も画像バッファの読み出しも行わない。実写保存・推論は全試験で行わない。

制御変更前に`results/camera-diagnostic-pending-restore.json`へ元設定を保存する。
試験ごとの復元を読み戻して検証し、失敗したら停止する。タイムアウトやCtrl+Cでは子プロセス終了後にも復元する。
強制終了・電源断で復元できなかった場合、次の診断起動時に保存値の復元を先に試す。
この復元用JSONは復元完了まで削除しない。自動露出では値が自動変化するため自動モードへの復帰を検証する。

初回やC++修正後は `build-native.cmd` を実行する。Visual Studio 2022 CommunityのC++ツールとWindows SDKを使用し、
`builds/diagnostics/camera_native.exe`を生成する。通常Playerや配布ZIPのビルドは不要。
別の開発PCへは`tools/diagnostics/`と`builds/diagnostics/camera_native.exe`を同じ相対配置でコピーする（本体ソースと`.venv`は既存環境を使用）。

参照：
- [Windowsのちらつき防止制御](https://learn.microsoft.com/en-us/windows-hardware/drivers/stream/ksproperty-videoprocamp-powerline-frequency)
- [Media Foundationの形式選択と圧縮データ取得](https://learn.microsoft.com/en-us/windows/win32/medfound/processing-media-data-with-the-source-reader)

`check_partial_tracking.py` は、デモアバターと人工入力で顔なしの腕・腕なしの掌/指を確認し、既存録画で3モードの部位更新間隔を検査します。カメラ不使用・実写表示なし。`--synthetic-only` で人工入力だけを検査できます。結果は `results/partial-tracking/`。

`audit_eyelids.py` はUIで選択した保存動画を全部ONで再推論し、瞼のフィルター前後の値を集計します。カメラ不使用・実写表示なし・Playerへ送信なし。`--video`、`--frames`（既定900）で範囲を指定できます。結果は `results/eyelid-audit/`。

`check_arm_scale.py` は保存済みランドマークを変更前Git版と現在版へ同時入力して④の腕更新を比較します。`--source`でframes.jsonl、`--baseline`で比較コミットを指定できます。画像表示/カメラ起動なし、結果はresults/arm-scale。

`../smoke_unity.py --arm-rest-check` は実Playerのアバターで、欠測待機・机上姿勢・左右独立・復帰・全通信停止を検査します。人工入力のみ、実カメラ不使用。アバター画像と検査ログを保存します。


左右の手の混線・指の停止は`audit_hand_sides.py`で人工入力と保存済み数値を検査する。カメラは使用せず、指定したアバターと既存Playerを読み込む。[手順・検証範囲](../../docs/HAND_SIDE_AUDIT.md)。


手の実時間診断：`realtime_hands.py --source video` またはユーザー操作の `--source camera`。保存UI設定を読み、実写なしで点群・UDP・実骨を記録。`summarize_realtime_hands.py <結果フォルダー>` で有効な掌/指の送受信値を照合。[手順と限界](../../docs/HAND_SIDE_AUDIT.md#6秒15秒の照合と実時間診断)。

`audit_hand_causality.py <手のカメラ診断フォルダー> --output <新規フォルダー>` は共通尺度の感度、指の符号付き曲げ、片側のみ変化する人工入力を実Playerで検査する。実写は表示しない。結果は握りの正解率ではない。

- `compare_hand_mirror.py --take <録画フォルダー> --records <同じ録画のframes.jsonl> --output <新規フォルダー>`：`--mode graph`で元FP32、既定はgraph-fp16。元入力と水平反転入力を同じROI/尺度でモデルへ渡し、手の左右とXを復元して比較。元記録の顔/腕を保持、Z/XYのみ移植の診断も保存。`summarize_hand_mirror.py <結果フォルダー>`で集計。正解率ではない。

### 公式PyTorchとONNXの診断

`compare_rtmw_pytorch.py` は `prepare`（製品Pythonで録画から共通入力作成）、`torch`（隔離MMPose環境で公式重み実行・ONNX出力）、`compare`（製品PythonでORT照合）を分離する。全段階で同じ `--output <結果フォルダー>` を渡す。prepareのみ `--video <録画> --records <対応frames.jsonl>` が必要。torchは `--source <MMPoseソース>` と `--weights <公式pth>` を指定可能、既定パスと監査済み重みは[担当文書](../../docs/HAND_SIDE_AUDIT.md#元pytorchと自前onnxの比較)。prepare出力は新規フォルダーのみ。実写由来inputs.npyを表示・公開しない。

隔離環境の再作成はuv venvでPython3.11を選び、公式cu121 indexからtorch2.1.0/torchvision0.16.0を入れる。numpy1.26.4、setuptools69.5.1、pip/wheel/scipyを先に入れ、chumpy0.70は--no-build-isolationでインストール。その後mmengine0.10.7/mmcv2.1.0/mmpose1.3.2/mmdet3.3.0/onnx1.16.2（MMCVは公式cu121/torch2.1 wheel）。ソースはMMPoseコミット759b39c13fea6ba094afc1fa932f51dc1b11cbf9。TEMP/TMP/MPLCONFIGDIRはプロジェクト内の専用.cache以下へ向ける。sandboxで一時ファイル作成が止まる場合は通常権限の承認が必要。製品requirementsへこの診断依存を追加しない。

指の実装版比較：`compare_finger_revision.py --records <保存済み手観測frames.jsonl> --reference-report <compare_hand_mirrorのreport.json> --before-revision <Git版> --output <新規フォルダー>`。比較前のpacket完全再現と左指以外の一致を検査し、render_comparison_videos.py用の入力を生成する。実写を表示せず、推論も再実行しない。

- `audit_finger_signs.py`：旧Git版の指計算へ観測フックを追加し、保存packetとの一致を検査してから正値制限前の角度分布を指・関節別に集計。引数・結果の意味は[指の監査](../../docs/HAND_SIDE_AUDIT.md#左指ごと関節ごとの元の符号2026-09-23)。

- `audit_all_take_finger_signs.py --output <新規フォルダー>`：全保存元録画を共通FP16設定で再推論し、反転前の指計算を関節別に監査。入力は`--takes`で指定、既定results/comparison-takes。`audit_finger_signs.py`を呼び出して計測フックによる出力不変も確認。有効観測なしは判定不能として保存。実写表示や新規撮影なし。
