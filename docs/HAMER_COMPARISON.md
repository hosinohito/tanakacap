# HaMeRと実撮影の比較（2026-09-12）

SAMの承認待ちの間に実行。ライブのモデル・補正・設定・Unityコードは変更していない。

## 実行した範囲

- 撮影：results/comparison-takes/20260911T235327-031115Z、5187 frame / 約185秒。口・目の専用動作は撮っていないため、その精度評価には使わない。動作ラベルは案内時刻であり正解アノテーションではない。映像には案内と異なるタイミングの動作もある。
- results/comparisons/first-take：現行、DWPose-l、RTMW-Xの2D対照。5187 frameすべてで最終packet一致。今回交換した2D参照による制御改善は観測されなかった。3Dを共有しているため、モデル全般の優劣を意味しない。
- ORTの記録上限に達した警告あり。保存済みイベントではCUDA実行あり・主要CPU計算なし。全フレームのイベントが記録されたとは扱わない。
- tools/audit_comparison_input.py：元のpalm_basisとの判定一致をassertし、棄却理由を細分化。連続有効frameだけで肘/距離の変化を集計。results/comparisons/first-take/input-audit.json。

## 観測

距離stable対legacyの隣接変化p95：distance_stillは0.03054→0.00712（約77%減）、end_stillは0.01771→0.00461（約74%減）。基準距離比の差でありメートルではない。ゆっくりした変動は残り、完全静止の正解データでもない。

left_fingers_face区間417 frameで、解剖学的左肘の生の肩相対Zの隣接変化p95は約0.602m、制御後約0.077m。右は約0.012m→0.016m。モデル座標内の値で、実測人体距離ではない。生入力が大きく飛ぶ経路を確認したが、ユーザーの画面上の左右との対応や全原因の確定ではない。

左指は常時停止ではない。同区間の元モデル有効数（親指から）は373/367/360/359/367。姿勢・区間で棄却理由が変わる。補正を緩めて無条件採用する変更はしていない。

## HaMeR環境

- 公式コード： https://github.com/geopavlakos/hamer 、commit 3a01849f4148352e9260b69bf28b65d1671a4905。
- 公式重み： https://www.cs.utexas.edu/~pavlakos/hamer/data/hamer_demo_data.tar.gz 。必要なhamer.ckpt、model_config.yaml、mano_mean_params.npzのみ展開。重みSHA256 e5cc06f294d88a92dee24e603480aab04de532b49f0e08200804ee7d90e16f53。
- Python 3.11.16 / torch 2.11.0+cu128 / torchvision 0.26.0+cu128 / Lightning 2.6.6。公式CUDA wheelでWindows/4090実行を検証。PyTorch案内 https://pytorch.org/get-started/locally/ 。導入時のパッケージ全体はrequirements-hamer.lock.txt。
- 環境assets-source/hamer/venv。本体.venvは維持。公式setupの古いmmcv/Detectron2/ViTPoseは既存ROIを使う推論経路で不要と確認し導入していない。上流ソースは改変していない。
- Windowsで上流の既定EGL importが失敗。ワーカー内でPYOPENGL_PLATFORM=win32、モデルのinit_renderer=Falseで解決。最初のネットワーク接続リセットはpipが再試行し成功。
- MANO原本を保ち、tools/prepare_hamer_mano.pyで旧Chumpy配列をNumPyへ同値変換。主要配列の値一致と有限値を検査。出力assets-source/hamer/mano/MANO_RIGHT.pkl、receipt隣接。Chumpy公式 https://github.com/mattloper/chumpy commit 580566eafc9ac68b2614b64d6f7aaa84eebb70da。Python/NumPy旧名互換は変換プロセスだけ。ライブへ追加しない。
- モデル・MANO・上流コード・環境はGit管理外。ローカル比較可能という結果であり、これらの同梱配布を承認したものではない。

## 全映像の実推論と指比較

results/comparisons/first-take-hamer/report.json：5187 frame、10370 hand predictions（検出の正解数ではない）。CUDA出力・有限値・21関節を実検査。両手あり5185 frameの時間中央値38.02ms / p95 44.34ms。切り出し・GPU転送・推論・結果転送を含み、動画復号、人物/手領域検出、顔/身体推論、Unity、OBSを含まない。PyTorch最大allocated約2.80GB（全GPU使用量ではない）。初回warmupを含む。全体リアルタイム性能保証は未実施。

tools/compare_hamer_fingers.pyは指だけの3D座標交換。HaMeR公式OpenPose21関節・メートル・左手反射を使い、カメラ軸から既存軸へ3軸符号反転する。元RTMW3Dの信頼度/画面端ゲートを共通利用し、HaMeRの信頼度を捏造しない。この共通ゲートの欠測は改善しない条件。既存FingerTrackerと3/1観測処理は不変。元モデルの再計算との一致は5187 frame、左右の不一致0（角度許容0.002度）。指以外のpacket完全一致をassert。

right_fingers_face区間の有効な指判定数（417 frame×5指）：左1947→2085、右2025→2085。HaMeRでは同区間の骨長/平面による棄却が消えた。手を開いた投影画像4frameを目視確認、左右人差指MCPの値にも0〜約70度の変化あり。有効率は正解率ではなく、閉じた姿勢の全体精度、遅延/震え、アバターの実人物品質は未合格。

fingers/replay.jsonlは指だけ差し替えた比較再生。1900〜2499 frameの600packetを実Unityで処理し、results/hamer-setup/unity-fingers.png.audit.jsonlに600行生成、受信/描画成功。既存Unity監査は主に腕/掌であり、指骨精度の自動合格試験ではない。

## 再実行と次

- デスクトップtanakacap-compare-hamer.bat：run-hamer-comparison.ps1から保存済みfirst-takeを再推論し、指比較を生成。カメラ撮影は開始しない。Common引数で別の完了比較を指定可能。
- tools/update-desktop-launcher.ps1で従来の3つのbatも維持・更新。
- 環境再作成は同Pythonのvenv、requirements-hamer.lock.txtとCUDA128公式indexを使う。公式repoを上記commitへ固定し、取得済み原本から変換ツールを実行。モデルは上記配置とハッシュを確認する。既存本体環境を置換しない。
- 次はこの指比較の開閉・遮蔽・復帰を実アバターで評価。ライブへの可逆切替と非同期GPU実行は未実装。HaMeRは手モデルなので肩・肘の生深度不良は解決しない。SAM承認後に身体3D比較を継続する。
- 171pytest成功。各新ツールは上記実データで実行。PowerShell構文検査成功。顔/腕/掌のライブ既定は維持。
