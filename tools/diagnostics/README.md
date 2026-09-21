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
