# RTMW3D-X / SAM DINOv3 / SAM ViT-H の身体比較

2026-09-12。ユーザーが上位3候補の実装完了とアバター動画化を指定。全編3方式の共通補正と動画4本が完成。以下の実行途中の記述より末尾の完成結果を優先する。通常ライブの採用モデルは変更しない。

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

## ViT-H受領と全編ジョブ

C:/Users/LLMTEST/Downloads/model (1).ckpt（1,691,205,237 bytes）を専用フォルダーへコピー。SHA256 `3b1cb897f4bbd977bf81cbb0b30780a9582681ac642ee112865790ceb4d66056`。設定1486 bytes、SHA256 `d2e772e108b8727e9367681845fecb32806144acd0debc20868d100689470570`。原本は削除していない。

両候補に同じ受領済みMHR TorchScript資産を指定し、身体表現を共通化した。ViT-HリポジトリのMHRファイルとハッシュ一致を確認したという意味ではない。ViT-Hチェックポイントの不明な欠落/余剰キーなし、20実フレームで60回のCUDAバックボーン実行と有限3D出力を確認。投影最大差0.000133px未満（results/sam-setup/vith-smoke-20）。DINO全編と同時の中央値約797msは単独性能に使わない。

両モデルの全編は同時に処理中。tools/finish_body_comparison.py が両方の完了と5187frameを確認後、共通補正→3方式動画生成を行う。失敗・不足フレームは完成扱いにしない。tools/body_comparison_status.py は読み取り専用の進捗表示。再実行用はrun-body-comparison.ps1、デスクトップtanakacap-compare-body.bat。新たなカメラ録画は行わない。

## 集計とリアルタイムに関する回答

tools/summarize_body_comparison.py は全候補共通で可視だった連続フレームの組だけを使い、案内区間の境界や欠測をまたがず、生肘深度と補正後の変動を集計する。指/腕の観測と保持も区別。tests/test_body_temporal_audit.py と全177pytest成功（results/sam-setup/pytest-body-final）。基準5187frameで集計実行成功。最終3方式の集計は全編待ち。変換スクリプト自体のSHA256も比較レポートに追加した。

ユーザーの「リアルタイム処理は不可能ということ？」への回答：現在のSAM fullをそのまま使うと、DINO単独約530ms（約1.9回/秒）で滑らかな実時間駆動には遅すぎる。30fps動画は計算済みのオフライン再生。将来のリアルタイム化が不可能と確定したわけではない。エンジン最適化、手デコーダを別モデルへ分離、既存高速推定＋低頻度SAMの併用は提案段階であり、採用・品質・30fps達成を保証していない。ユーザーから動画比較の中止指示はなく、全編作成を継続する。


## 全編完成（2026-09-12）

results/comparisons/body-three-models、results/avatar-videos/body-three-modelsのreport.jsonはcomplete。入力5187フレームすべてを処理。SAM各5185予測、欠測2は既存の保持方式へ接続した。候補ごと15555 CUDAバックボーン実行。基準全パケット最大差0、顔/目/口/距離を固定。再投影最大差DINO0.0002101px、ViT-H0.0002197px。

動画はcurrent.mp4、sam-dinov3.mp4、sam-vith.mp4、side-by-side.mp4。各5551描画フレーム、30fps、185.033秒。個別1280×720、横並び3840×768。全4本の全編復号成功。85秒と148秒の比較画像で腕・手が描画へ反映されることを確認（check-85.jpg、check-148.jpg）。全動作の人体品質が合格という意味ではない。横並びは左から現行、DINOv3、ViT-H。

共通可視性の連続ペア集計はtemporal-audit.json/md。静止距離案内区間410ペアで生肘前後変化p95は現行左279/右29.4mm、DINO3.31/3.33mm、ViT-H2.95/3.76mm。これは推定値の変化量であり、正解との誤差ではない。実動作案内は正解ラベルでもない。腕深度区間567ペアでも現行左288/右233mm、DINO17.8/19.5mm、ViT-H22.7/21.6mm。左の極端な深度変動はSAMで減っている。

指の採用観測数（5指×5187の最大25935観測に対して）は、現行左8849/右9610、DINO13346/14372、ViT-H13340/14374。RTMWの可視性ゲートを共通にした試験なので、SAM独自の欠測復帰率とは呼ばない。指の精度や可動域は動画で別途評価する。ヨー案内区間の出力p5/p95は現行-8.8/+1.7度、DINO-24.1/+13.7度、ViT-H-25.9/+14.0度。動く範囲が増えても、正解角度との一致は未検証。

性能計測も動画完成後に実施。GPU実行は確認したが、細かいカーネル起動・同期が多く、現在の実行時間を4090の演算性能の限界とは扱わない。docs/SAM_PERFORMANCE.md。次は完成動画の人物評価と、出力を維持する実行経路の最適化検証。SAMの通常ライブ採用、30fps達成は未完了。
