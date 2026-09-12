# RTMW3D-X / SAM DINOv3 / SAM ViT-H の身体比較

2026-09-12。ユーザーが上位3候補の実装完了とアバター動画化を指定。現在は接続・短い結合検証まで成功し、DINOv3全編推論中。ViT-Hは設定ファイル受領、重み待ち。全編3方式動画の完成ではない。

## 一次比較で固定するもの

入力は `results/comparison-takes/20260911T235327-031115Z`（全5187フレーム、実時刻約185秒）。顔・頭・目線・口・顔距離は first-take/common.jsonl の既存出力。画像、人物ROI、フレームと実時刻、補正コードと設定、Unityモデルとカメラを共通とする。各候補の補正内部状態は冒頭から独立に学習する。同一校正済み値の流用ではない。

交換範囲は身体・掌・指の3D形状と対応する投影点。顔の詳細68点と頭の推定は交換しない。SAMの full モード（身体と左右の手デコーダ）を使う。間引きなし。FOV推定器は導入せず、SAM公式の既定内部パラメーターを使う。動画は保存済み時刻で再生するオフライン比較であり、SAMの実時間更新頻度を30fpsと主張しない。

## 座標・関節・信頼度

- tools/sam_body_adapter.py：公式 MHR70 の並びを COCO WholeBody へ対応。左手首62、右手首41。指のtip→根元の列をOpenPose21の根元→tip順へ直す。画像の左右と解剖学的左右を区別する。
- SAMは mhr_head.py でcmをmへ変換済み。出力はカメラX右/Y下/Z奥。pred_cam_tを足してfocal_lengthで再投影した値と公式2D出力の差を全入力で確認（0.02px超なら失敗）。Unity用には既存と同様にXYZの符号を反転。
- BodyRetarget.update に比較専用の省略可能な camera_xyz を追加。ネイティブXYZは平行移動で肩中心へ合わせるだけで、XYを投影から作り直したり任意の倍率で伸縮しない。ピクセル座標は可視性・顔尺度・肩幅・交差等の既存判断へ使う。既存の時間フィルター、前後prior、腕長、関節制限を追加変更しない。
- SAMは関節ごとの信頼度を返さない。既存RTMW3Dの信頼度・元の画面外判定を共通の観測可否として使い、SAM投影がさらに画面外なら既存処理で棄却する。全点を1.0として隠れた関節を観測済みにしない。したがってRTMW側が見失った点をSAMが救う能力の評価ではなく、共通可視性条件で3D形状を交換する試験。depth_scoresもSAMの確信度ではない。
- 肩幅によるヨー量、肘深度による符号等もそのまま。補正後の差だけでモデル自体の優劣を断定せず、raw.jsonlを併せて残す。

## 検証済み

- results/comparisons/body-baseline-verification-3：既存基準全5187フレームのパケット再計算、最大差0。新しいオプション未指定時の既存動作を維持。
- tests/test_sam_body_adapter.py：左右手首/股関節/指順、全3D座標、共通信頼度、画面外保持、投影不一致の拒否、前方肘の符号。全既存テストを含め176成功（results/sam-setup/pytest-body-1）。
- results/sam-setup/body-smoke-600：冒頭600フレームのSAM接続成功、投影最大差0.000211px未満、顔関連フィールド一致。snapshotは部分検証と明記。
- results/avatar-videos/body-smoke-600：実Unityによる2方式の短い結合検証、647描画フレーム/21.567秒、全編復号成功。16秒の静止画で腕・掌のモデル間差を確認。全撮影の品質判定には使わない。
- 検査実装の初回は共通faceパケット中の身体初期フィールドまで顔固定として検査し失敗。顔・頭・目線・口・顔距離だけを明示対象に修正。元の出力や補正は変更せず、最終の全パケット一致で基準を検証した。

## 実行設定と速度の限界

モデル重み・解像度・fullモード・bfloat16設定を保ち、ワーカーのオプション --keep-cuda-cache で毎フレームの empty_cache を局所的に抑制、--torch-threads 1 でCPU制御のスレッド数を明示した。GPU推論をCPUへ移していない。上流ソースは無改変。

同じ2100〜2119の20フレーム、単独測定：旧既定中央値715.60ms、メモリ再利用661.51ms、さらにCPU制御1スレッド529.52ms。新設定と旧設定の関節位置差は最大0.374mm相当、p95 0.121mm未満（SAM座標上の差で、人体の推定誤差ではない）。ビット一致とは主張しない。20標本だけで精度不変や一般的な性能を保証しない。

本番全編は --keep-cuda-cache --torch-threads 1 で実行中。途中の動画結合検証などとGPU利用が重なるため、全編時間分布を単独モデルの速度として使わない。ライブ統合・4090での実用性は別途判断する。

## 実装と再開

- tools/compare_external_model.py：独立CUDA環境でSAM生推論。assets-source/sam-3d-body-venvを使用。
- tools/compare_body_models.py：全編の生推論結果を共通補正へ接続。--candidate name=folder を複数指定。顔固定と基準再現を検査し、replay.jsonlを生成。--limit は明示的な部分結合検証。
- tools/render_comparison_videos.py：--comparison に完成した比較フォルダーを指定すると各方式と横並び動画を生成。全時刻一致と動画復号を検証する。既存の現行対HaMeR用呼び出しも維持。

ViT-H受領先：assets-source/sam-3d-body-vith。DINOv3と同じファイル名を別フォルダーへ保存する。ブラウザーログインをPython認証済みと扱わず、秘密トークンはチャットに出さない。

## 一次資料

- https://github.com/facebookresearch/sam-3d-body （ローカル b5c765a0d89d789985e186d396315e7590887b94）
- https://huggingface.co/facebook/sam-3d-body-dinov3
- https://huggingface.co/facebook/sam-3d-body-vith
- 公式関節定義：assets-source/sam-3d-body-code/sam_3d_body/metadata/mhr70.py
- 公式単位/軸：models/heads/mhr_head.py、models/heads/camera_head.py
