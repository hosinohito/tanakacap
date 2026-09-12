# SAM 3D Body導入・初回GPU検証（2026-09-12）

ユーザーのアクセス承認・ダウンロード後、プロジェクト直下の3ファイルをassets-source/sam-3d-body-dinov3へ移動（mhr_model.ptのみassets/）。原本の値は変更していない。

- model.ckpt SHA256 b5a2f9d305dd02626b967aa2e86021fba07065df66ce7a7e00ffb9664f150abf
- model_config.yaml SHA256 1012fc3f39cb5e90e3f8fbadf7bded31604bfafdce0321d17a7c1a2d3f08b88d
- assets/mhr_model.pt SHA256 352e271a6c42729c68554ceaea0c955e866970160c31e35506d782dc0f7377bc

公式コード https://github.com/facebookresearch/sam-3d-body commit b5c765a0d89d789985e186d396315e7590887b94、DINOv3 https://github.com/facebookresearch/dinov3 commit 6876159a11b4df116f30f667f8c9888617df0751。どちらもassets-sourceへclone、改変なし。SAMはpretrained=FalseでDINOv3を作り、取得済みSAM重みを読む。ワーカーのモデル初期化中だけtorch.hub.loadを明示的なローカルDINOv3へ振り分け、finallyで復元する。未指定の重みやコードを暗黙に取得しない。

## 環境・検証

assets-source/sam-3d-body-venv、Python3.11.16、torch2.11.0+cu128、torchvision0.26.0+cu128。HaMeR/本体と別環境。requirements-sam.lock.txtに依存を保存。pip check成功。公式INSTALL.mdの全学習依存を無条件に導入せず、既存ROIでの実推論に必要な経路を検証。Detectron2/MoGe/SAM3/Momentumは未導入。MHRは公式のTorchScript経路でGPU実行。既定FOVを使用し、カメラ内部パラメーター校正は未実施。

DINOv3のtermcolor不足による初回失敗は追加導入で解決。チェックポイントのmissing警告を監査し、別ファイルから既に読み込むhead_pose/head_pose_handのMHR部分、マスクなし入力で参照されないmask_token、上流の初期化用hand_pose_comps_oriを区別した。未知の欠落/余分なキーはワーカーで失敗扱い。MHRキーを全て未学習と誤解したり、警告を無記録で無視したりしない。

- results/sam-setup/smoke-2：2100〜2102の3frame成功。初回2232ms、続く2frameは658/660ms。
- results/sam-setup/sampled-2：全撮影から150frameおきの35標本、34人物出力、CUDA backbone hook102回。全区間の生出力検査であり、連続時間の補正比較ではない。この試験は動画作成と同時実行なので単独速度として使わない。
- results/sam-setup/isolated-20：動画作成完了後、2100〜2119の20連続frameで成功、CUDA backbone hook60回。時間中央値715.60ms/p95 840.48ms、最初の3frameを除くと716.93/760.28ms。PyTorch最大allocated3,639,804,928bytes。切り出し/推論/転送を含むが動画復号・別検出モデル・Unity・OBSは含まない。現在の公式full設定はそのままリアルタイム用途に採用できる速度ではない。最適化後の性能限界とは断定しない。
- CUDA backboneの実出力と3D出力の有限値を検査。人物70点、MHRは上流でcmからmへ/100変換。RTMWと関節順が異なる（例えば手首は41/62）ため、そのまま既存133点へ代入しない。個別関節の信頼度は得られない。

## 次の作業

SAMは生3D推論まで。モデル精度の比較、左右/単位/関節対応の実画像監査、既存補正への身体アダプターは未完了。腕・肩のモデル交換済みとは扱わない。まず体と手を分けた推論負荷の内訳を測定し、TorchScriptや毎frameのempty_cache等の負荷を調べる。補正・モデル精度を変えずに減らせる処理から検討する。今回のユーザー指定の2方式動画は現行対HaMeR指であり、SAM動画ではない。

実行例はtools/compare_external_model.py sam3dに --repo assets-source/sam-3d-body-code --checkpoint assets-source/sam-3d-body-dinov3/model.ckpt --mhr assets-source/sam-3d-body-dinov3/assets/mhr_model.pt --dinov3-repo assets-source/dinov3 と既存--take/--common/新しい--outputを指定する。--start-frame/--limit/--strideで試験区間を指定。承認トークンは不要、資産はGit管理外。
