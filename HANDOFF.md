# 現在の引き継ぎ

更新：2026-09-23。会話履歴なしで再開するための現在状態。過去の完了報告はここへ積み重ねない。

## 再開の順序

1. [AGENTS](AGENTS.md)とこの文書を読む。
2. 作業対象の[仕様](docs/SPEC.md)・下記の機能仕様と、[PROGRESS末尾](docs/PROGRESS.md)を確認する。古い仕様書内の日付付き記述には後続の訂正がある。
3. `git status`と現在の設定・実装を確認し、ユーザーの最新指示に従う。採用・撤回・保留を混同しない。

セットアップ・ビルド・起動・検証は[DEVELOPMENT](docs/DEVELOPMENT.md)。旧HANDOFFの詳細は[PROGRESSの移管履歴](docs/PROGRESS.md#2026-09-21旧handoffからの履歴移管)に残した。古い「次の作業」を現在の実行指示として扱わない。

## 現在の作業・公開状態

- 現在の課題は反対手ロール時の掌ピッチ変動と左指の握り追従不良。ユーザーのカメラ試験ログまで総合調査済み。送受信値の混線なし、片側目標固定の実骨試験でも直接連動なし。左指は有効なのに3Dの逆曲げ判定→0制限で握りが消える具体例あり。共通顔尺度だけの影響は最大約1.4度で主因ではない。推定の相対Z/掌基準と符号付き屈曲の解釈が優先調査対象。前腕±160度の到達可能角への復帰は修正・901観測/実骨/動作検査済み。[根拠と限界](docs/HAND_SIDE_AUDIT.md#カメラ試験の総合原因調査)。通常hingeの上限復帰だけ変更、指は未変更。ユーザーが動画7秒台の異常を指摘し、7.7秒台の反対端への大回りを修正の副作用として確認。回転品質は合格ではなく再設計待ち。今回の右指停止の指摘はユーザーが勘違いとして撤回（以前からの左指屈曲課題とは別）。[最新調査](docs/HAND_SIDE_AUDIT.md#現在動画の指と7秒台の回り直し)。公開指示なし。
- READMEは公開入口、DEVELOPMENTは開発手順、HANDOFFは現在状態、PROGRESSは履歴に分離。別のCodexが再開できる情報を残すことが必須。
- 配布済み最新版は[v0.1.4](https://github.com/hosinohito/tanakacap/releases/tag/v0.1.4)。ローカル成果物は`builds/releases/0.1.4/TanakaCap/`。通常設定で作成し、個人設定・実写・アバターは同梱していない。Exporterはv0.1.3から変更なし。
- リポジトリは`hosinohito/tanakacap`。この環境の作業ブランチ`master`から公開先`main`へプッシュする。履歴から旧アバターシーンを除去済み。再度の履歴書き換えは不要。[公開データ監査](docs/RELEASE_PRIVACY.md)を維持する。
- 配布モデルとランタイムの条件は監査済み。独自コードMIT。過去文書の「ライセンス未確定」を再開時の残件へ戻さない。根拠は[モデル](docs/MODEL_LICENSE_DECISIONS.md)・[ランタイム](docs/RUNTIME_LICENSE_DECISIONS.md)。

## 採用中の重要な方式

| 対象 | 現在の扱い・詳細 |
| --- | --- |
| 通信・UI | 部位別送受信を実装済み。旧通信との互換層を作らずGitで戻す方針。PythonとPlayerを対応する版で更新。更新速度表示はfpsへ統一。[設計](docs/PARTIAL_TRACKING_DESIGN.md) |
| 頭・顔 | 頭角度はPnPが通常。顔Zによるピッチは通常不採用。表情は既存キー優先、auto-customも選択可能。[表情](docs/EXPRESSION_PORTABILITY.md) |
| 腕の欠測 | 腕自体が有効なら保持した顔尺度で追従を続ける。全体欠測などでキャッシュを破棄。腕欠測は0.5秒待って1秒で机上姿勢、復帰0.5秒のイージング。[条件](docs/ARM_LOSS_POSE.md) |
| 肩 | 顔肩比の共通短縮補正・不確かな区間の保持・正面感度緩和。学習幅の短縮禁止は維持。[仕様](docs/SHOULDER_CONTINUOUS_CORRECTION.md) |
| 腕の補正 | 旧経路の「内側の手は前」は完全削除。他の前方補正は通常ON。頭回避は楕円体の近い表面へ手全体を移し、掌・指も対象。[整理](docs/ARM_CORRECTION_ISOLATION.md)・[接触](docs/HAND_HEAD_CONTACT.md) |
| 肘・手首 | 上腕に従属する曲げと連続スカラーねじりを分離。通常±160度。±90度・旧方式は実験UI、無制限は診断専用。[仕様](docs/ARM_ROTATION_COUPLED.md) |
| 指 | 可変速度追従を採用。信頼度の扱い・4フレーム法は維持。[仕様](docs/FINGER_FOLLOW.md) |
| 実験UI・性能 | 棚卸しと10項目追加済み。参考負荷は既存録画の同条件ベンチ由来。[項目・測定条件](docs/UI_EXPERIMENT_AUDIT.md) |
| 精度・高速化 | CUDA混合FP16を通常採用。FP32は実験UI。TensorRTはユーザーが不採用指定。遅くなった並行処理Hは撤回。[比較](docs/PRECISION_COMPARISON.md)・[採否](docs/FURTHER_OPTIMIZATION.md) |

## 未解決・保留と次の確認

- 上流のRTMW3Dバグ・更新も調査済み。元ONNXは現在の公開版とハッシュ一致、今回の左右Z問題の修正版は確認できない。次候補は同一条件FP32比較でFP16の影響を切り分けること（未実行・未採用）。左指符号反転案は保留。[調査範囲と根拠](docs/HAND_SIDE_AUDIT.md#公開バグ報告と更新状況の調査)。

- **左右の手の連動・左指**：ユーザーがカメラ試験済み。同じロール連動は出ず、反対手のピッチと左握りの問題あり。ログ `results/hand-realtime/20260923T070155-023807Z/`、詳細診断 `results/hand-causality-final-20260923/`。マーカーなし/実写保存なしのため実動作と各区間の正解照合は未完了。左右共有は未検出。上限復帰の修正結果は `results/twist-recovery-20260923/`。左右反転検証901観測が完了し、同じ左右の処理へ戻しても指の曲げ左右差が逆転、Zだけ移植で再現。主にモデルのZ出力の左右非対称性を示す。左指の符号反転案はユーザー指定で保留。7秒台の掌反転はXY三角形の表裏反転もありZだけに限定しない。[結果](docs/HAND_SIDE_AUDIT.md#入力左右反転によるモデルの対称性検査)。正解の握りの確認と対処設計が次の課題。公式座標復号との一致だけでは独自の指解釈を保証しない。[詳細](docs/HAND_SIDE_AUDIT.md#上限復帰と指の解釈の再確認)。前の実写録画は `results/comparison-takes/20260923T064052-167149Z`、右手だけの動作は6秒・15秒。人工入力の成功を症状の解決と扱わない。
- **肘のねじれの見た目**：新方式の人工入力・録画比較は完了したが、改善の最終評価はユーザー待ち。通常±160度を維持し、制限を狭める／無制限にする変更を独断で採用しない。
- **肩の過抑制**：前傾・接近時の抑制とともに胴体ひねりも小さくなった区間があり、見た目の確認が残る。
- **指の振動、欠測・復帰**：人工入力と動作検証は済んでいるが、実人物の品質評価は未完了。最新の指試験に使った録画短区間には有効な指観測がなかった。
- **瞼**：入力の閉眼値が小さく平滑化で減衰することを確認。検出失敗と断定していない。ユーザー指定で目の課題は保留。[監査](docs/EYELID_INPUT_AUDIT.md)。瞬きに伴う頭ピッチの話は対象外指定。
- **汎用性・長時間品質**：他アバター、別PC、他カメラ、通常OBSシーン、最新構成の長時間安定性・端から端の遅延は、個別の検証範囲を越えて合格扱いしない。[検証](docs/PHASE4_VALIDATION.md)。
- **追加開発**：揺れ物の追加調整は終了指定。音声口パクは将来課題。舌・デモ専用アバター経路は撤去済みで復活させない。手続き的なデモモーション入力は維持する。
- 次の機能実装はユーザーの指示・見た目評価を受けてから選ぶ。フェーズ全体を完了扱いしない。[フェーズ文書](docs/IMPLEMENTATION_PHASES.md)内の古い未実装一覧は、現在の上記状態・機能仕様と照合する。

## このPCの検証素材・実行方法

プロジェクトは`D:\work\tanakacap`。以下はローカル専用でGit管理外。別インスタンスは存在を確認して使い、別PCにない場合に自動生成済みと仮定しない。

| 用途 | 場所 |
| --- | --- |
| 通常の検証アバター | `builds/player/avatars/haolan.tcap`。通常アバターにauto-customを適用。廃止済みデモ専用キーは使わない |
| 今回の症状のアバター | `builds/releases/0.1.3/TanakaCap/avatars/avatar.tcap`（改変済みHAOLAN）。人工入力の調査結果は`results/hand-sides-modified-20260923/`、配布版は`results/hand-sides-release-20260923/` |
| 入力左右反転の比較動画 | `results/avatar-videos/hand-mirror-20260923/side-by-side.mp4`。左画面=元入力、右画面=反転推論・左右復元。数値は `results/hand-mirror-corrected-20260923/summary.json` |
| 最新の上限復帰修正アバター動画 | `results/twist-recovery-20260923/avatar-current.mp4`。最新録画由来、改変済みHAOLAN/auto-custom、約30秒。見た目確認待ち |
| 現在の録画 | `results/comparison-takes/20260923T064052-167149Z/camera.avi` |
| 肘の4条件・6本比較 | `results/avatar-videos/arm-rotation-coupled-final/` |
| 掌・指の頭接触比較 | `results/avatar-videos/hand-head-contact/` |
| 前方補正の単独比較 | `results/avatar-videos/arm-corrections-final/` |
| 個人設定 | `ui-settings.json`。以前の試験版の設定は`builds/releases/0.1.3-ui-audit-final/TanakaCap/ui-settings.json`に保持 |

- デスクトップの`tanakacap-test.bat`は`run-ui.ps1 -AutoCustom -RecordedTest`を起動する。UIで録画を確認し「保存して開始」。有効な保存動画選択は保持されるため、必要なら上の録画を指定する。
- ランチャー再生成は`tools/update-desktop-launcher.ps1`。比較batはデスクトップの`tanakacap-tools/`。再生方法を変えたらこの手順とランチャーを同時に更新する。
- 実写は表示しない。録画検証を基本とし、エージェントの実カメラ試験には明示指示または事前相談が必要。
- 最新の機能検証は315 Python tests、実Tk、Unity回転・接近・欠測復帰、録画と配布構成の起動。[詳細](docs/UI_EXPERIMENT_AUDIT.md)。文書整理ではこれらを再実行していない。
- 次のコード変更では関連テストを選び、必要に応じてPlayerを再ビルド。ZIP不要なら`build-release.bat -NoZip -Version <未使用版名>`。手順はDEVELOPMENT／RELEASE_BUILDを参照する。

## コピー・公開時の注意

文書のみの変更では別PCのアプリ更新は不要。v0.1.4を試す場合は配布の両ZIPを同じ新規フォルダーへ展開し、自分のアバターを選ぶ。ローカル試験版は生成された`TanakaCap/`全体をコピーし、Playerのexeだけを移さない。

旧履歴のバックアップや原本・録画・個人設定はローカル保持のまま公開しない。認証情報を文書へ貼らない。プッシュ成否は実際の応答で確認し、承認待ちの中断を成功扱いしない。
