# 現在の引き継ぎ

更新：2026-11-11。会話履歴なしで再開するための現在状態。過去の完了報告はここへ積み重ねない。

## 再開の順序

1. [AGENTS](AGENTS.md)とこの文書を読む。
2. 作業対象の[仕様](docs/SPEC.md)・下記の機能仕様と、[PROGRESS末尾](docs/PROGRESS.md)を確認する。古い仕様書内の日付付き記述には後続の訂正がある。
3. `git status`と現在の設定・実装を確認し、ユーザーの最新指示に従う。採用・撤回・保留を混同しない。

セットアップ・ビルド・起動・検証は[DEVELOPMENT](docs/DEVELOPMENT.md)。旧HANDOFFの詳細は[PROGRESSの移管履歴](docs/PROGRESS.md#2026-09-21旧handoffからの履歴移管)に残した。古い「次の作業」を現在の実行指示として扱わない。

## 現在の作業・公開状態

- **揺れ物の暴れを修正・比較済み、見た目の確認待ち**。最新ユーザー提供tcapを変更せず、位置拘束からの速度増幅を角応答の方式へ変更し、動画物理刻みを固定。40秒/101骨の急回転最大179.99→34.00度、骨別p95最大179.29→9.88度。人工の収束/骨位置/手接触検査、Python350テスト成功。`results/secondary-audit/comparison.mp4` は左旧・右修正、`verified.mp4` は修正のみ。衣装状態はユーザー提供版。Exporterは無効コライダーを除外するよう修正。元tcapの再生成はしていない。builds/playerとbuilds/release-playerを最終ビルドへ更新し、実Playerの動作検査成功。デスクトップtanakacap-test.batは9/11録画＋最新版ユーザーアバターで検証できる。詳細・失敗試案はPROGRESS末尾、方式はSECONDARY_MOTION。腕・位置オプションと合わせて公開前の見た目確認とリリースノート編集待ち。`builds/releases/0.1.6-reviewed-candidate` は途中生成物で公開不可、梱包を再開しない。

- **今回の0.1.6候補の公開はユーザー指定で中止**。GitHubには未公開・未プッシュ。既存の色修正・標準手接触は保持し、(1)腕を真横に広げると斜め前へ出る問題、(2)肘がねじ切れて見える問題、(3)画像内の左右・上下位置へアバターを移動する既定OFFオプション（顔サイズ由来の前後移動と競合させない）を修正・実装・検証してから同じリリースへ含める。旧候補 `builds/releases/0.1.6/` を公開しない。リリースノート `release/RELEASE_NOTES_0.1.6.md` は修正完了後に更新して再確認を受ける。実装とビルドは承認済み、解決まで自走する。症状の基準録画は `results/comparison-takes/20260911T235327-031115Z/camera.avi` の10秒付近から（ユーザー指定）。

- **手接触**：SDK 3.7.0の実アバターコピーで標準10形状、許可6通り、Custom/Disabledと明示参照の保持を確認。左右接触・1800ステップ安定性・900フレーム録画経路・実Playerの動作/RGBA/Spout登録検査成功。新secondaryPhysics.version=2、旧version=1は従来のまま読む。利用者は新プラグインで再書き出しが必要。実人物の接触の見た目・本家物理との完全一致は未確認。仕様/数値/制限はSECONDARY_MOTION。エージェント生成tcapは衣装・表示状態がユーザーのアバターと異なったため削除済み。以後はデスクトップのユーザー提供 `avatar.tcap` を使用する。デスクトップtanakacap-test.batは録画+auto-customへ戻した。検証手順はDEVELOPMENT。
- **色修正**：描画をGammaからLinearへ統一し、指定tcapの花が白・茎が茶色になる症状を修正。builds/release-playerとbuilds/playerは手接触も含む修正版、配布済み0.1.5は旧版のまま。素材は`builds/releases/0.1.5/TanakaCap/avatars/hanalan.tcap`（綴り注意）、原本は`D:/work/vrc_projects/haoranRurukuPazyamaGorone - コピー`。原本は変更しない。比較画像/ログは`results/material-color/`、手検証用コピーは`results/hand-collision/project`。RGB/アルファ転送検査成功、実際のOBSシーン・ユーザーの見た目評価は未確認。

- v0.1.5を公開済み。ビルド・全343テスト・Git全履歴と配布ZIPの混入検査は成功。ユーザー編集済みの`release/RELEASE_NOTES_0.1.5.md`を使用。公開した2ZIPのサイズ・SHA256と本文を照合済み。詳細はPROGRESS末尾。

- 現在の課題は反対手ロール時の掌ピッチ変動と左指の握り追従不良。ユーザーのカメラ試験ログまで総合調査済み。送受信値の混線なし、片側目標固定の実骨試験でも直接連動なし。左指は有効なのに3Dの逆曲げ判定→0制限で握りが消える具体例あり。共通顔尺度だけの影響は最大約1.4度で主因ではない。推定の相対Z/掌基準と符号付き屈曲の解釈が優先調査対象。前腕±160度の到達可能角への復帰は修正・901観測/実骨/動作検査済み。[根拠と限界](docs/HAND_SIDE_AUDIT.md#カメラ試験の総合原因調査)。通常hingeの上限復帰に加え、両手5指の曲げ角度の絶対値化をユーザー指定で実装（左符号反転試行を置換し、右にも採用）。見た目確認待ち。関節別の元符号を調査し、一律の逆判定ではないことを確認（親指MCP・中指DIPは正側が多い）。保存元録画4本7,842フレームも共通条件で検証済み。1本は指の有効観測不足、残り3本でも動画・関節で傾向が異なり全反転の一般的妥当性は未成立。[全録画結果](docs/HAND_SIDE_AUDIT.md#全保存録画での関節別検証2026-09-23)。[関節別結果](docs/HAND_SIDE_AUDIT.md#左指ごと関節ごとの元の符号2026-09-23)。ユーザーが動画7秒台の異常を指摘し、7.7秒台の反対端への大回りを修正の副作用として確認。回転品質は合格ではなく再設計待ち。今回の右指停止の指摘はユーザーが勘違いとして撤回（以前からの左指屈曲課題とは別）。[最新調査](docs/HAND_SIDE_AUDIT.md#現在動画の指と7秒台の回り直し)。v0.1.5として公開指示あり。
- 顔ヨーは通常PnP経路で円周上の両目の投影弦長からacosで復元する方式を実装。正面10観測で基準取得、PnPの眼中心面距離で接近を補正。鼻は左右判定のみ。頭のピッチ・ヨー・ロール共通で可変速度追従を有効化（UI既定・ローカル保存値・通常PSランチャー）。[仕様と限界](docs/HEAD_YAW_AUDIT.md)。円周モデルの解釈はユーザー承認済み。最新901観測で数値確認、新旧比較動画で見た目の確認待ち。既存Playerで動作、再ビルド不要。
- ユーザー指定：別PCでのコピー・操作方法は、再度指示があるまで案内しない。
- READMEは公開入口、DEVELOPMENTは開発手順、HANDOFFは現在状態、PROGRESSは履歴に分離。別のCodexが再開できる情報を残すことが必須。
- 配布済み最新版は[v0.1.5](https://github.com/hosinohito/tanakacap/releases/tag/v0.1.5)。ローカル成果物は`builds/releases/0.1.5/TanakaCap/`。通常設定で作成し、個人設定・実写・アバターは同梱していない。公開済みExporterはv0.1.3から変更なし。0.1.6候補では標準手コライダー対応を追加。
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

- 上流のRTMW3Dバグ・更新も調査済み。元ONNXは現在の公開版とハッシュ一致、今回の左右Z問題の修正版は確認できない。同一条件FP32比較901観測を実行し、左右Z/屈曲非対称が元FP32 ONNXでも残ることを確認。FP16化だけが原因ではない。公式PyTorch対既存ONNX・自前再変換も80共通入力で比較済み。Zのargmax10640点全一致、再変換で改善なし。[結果と再開素材](docs/HAND_SIDE_AUDIT.md#元pytorchと自前onnxの比較)。**全身交換候補を調査済み。新しさ・配布条件・速度の全条件を満たす新候補は未発見。SAM系は独自契約と速度の課題がある条件付き候補、他の主要新候補は非商用または別人体モデル契約で除外。**[候補と一次資料](docs/WHOLEBODY_MODEL_CANDIDATES.md)。他製品の採用技術も同文書に整理済み。MediaPipe部位別構成の採用例を確認したが、新モデルや品質改善の証明ではなく、追加実装は未指示。交換・追加導入は未実行、次は採用候補と許容条件の判断。手専用別モデル探索は行わない。[FP32結果](docs/HAND_SIDE_AUDIT.md#fp32での左右反転再検証)。通常FP16を維持。両手の指を絶対値化済み。右への追加適用時も保存4本7,842フレームで左の値が変わらないことを確認。[仕様と掌XY案の保留課題](docs/FINGER_FOLLOW.md)。[調査範囲と根拠](docs/HAND_SIDE_AUDIT.md#公開バグ報告と更新状況の調査)。

- **左右の手の連動・左指**：ユーザーがカメラ試験済み。同じロール連動は出ず、反対手のピッチと左握りの問題あり。ログ `results/hand-realtime/20260923T070155-023807Z/`、詳細診断 `results/hand-causality-final-20260923/`。マーカーなし/実写保存なしのため実動作と各区間の正解照合は未完了。左右共有は未検出。上限復帰の修正結果は `results/twist-recovery-20260923/`。左右反転検証901観測が完了し、同じ左右の処理へ戻しても指の曲げ左右差が逆転、Zだけ移植で再現。主にモデルのZ出力の左右非対称性を示す。指は符号反転から両手の絶対値化へ変更済み。既存動画は左のみ絶対値化した時点。右の絶対値化の見た目は未確認。7秒台の掌反転はXY三角形の表裏反転もありZだけに限定しない。[結果](docs/HAND_SIDE_AUDIT.md#入力左右反転によるモデルの対称性検査)。正解の握りの確認と対処設計が次の課題。公式座標復号との一致だけでは独自の指解釈を保証しない。[詳細](docs/HAND_SIDE_AUDIT.md#上限復帰と指の解釈の再確認)。前の実写録画は `results/comparison-takes/20260923T064052-167149Z`、右手だけの動作は6秒・15秒。人工入力の成功を症状の解決と扱わない。
- **肘のねじれの見た目**：新方式の人工入力・録画比較は完了したが、改善の最終評価はユーザー待ち。通常±160度を維持し、制限を狭める／無制限にする変更を独断で採用しない。
- **肩の過抑制**：前傾・接近時の抑制とともに胴体ひねりも小さくなった区間があり、見た目の確認が残る。
- **指の振動、欠測・復帰**：人工入力と動作検証は済んでいるが、実人物の品質評価は未完了。最新の指試験に使った録画短区間には有効な指観測がなかった。
- **瞼**：入力の閉眼値が小さく平滑化で減衰することを確認。検出失敗と断定していない。ユーザー指定で目の課題は保留。[監査](docs/EYELID_INPUT_AUDIT.md)。瞬きに伴う頭ピッチの話は対象外指定。
- **汎用性・長時間品質**：他アバター、別PC、他カメラ、通常OBSシーン、最新構成の長時間安定性・端から端の遅延は、個別の検証範囲を越えて合格扱いしない。[検証](docs/PHASE4_VALIDATION.md)。
- **追加開発**：標準手・指コライダーの継承は実装・人工/録画検証済み（上記）。従来の揺れ物追加調整終了は今回の新規依頼以外に維持。音声口パクは将来課題。舌・デモ専用アバター経路は撤去済みで復活させない。手続き的なデモモーション入力は維持する。
- 次の機能実装はユーザーの指示・見た目評価を受けてから選ぶ。フェーズ全体を完了扱いしない。[フェーズ文書](docs/IMPLEMENTATION_PHASES.md)内の古い未実装一覧は、現在の上記状態・機能仕様と照合する。

## このPCの検証素材・実行方法

プロジェクトは`D:\work\tanakacap`。以下はローカル専用でGit管理外。別インスタンスは存在を確認して使い、別PCにない場合に自動生成済みと仮定しない。

| 用途 | 場所 |
| --- | --- |
| 通常の検証アバター | `builds/player/avatars/haolan.tcap`。ユーザー提供の `C:/Users/LLMTEST/Desktop/avatar.tcap` と同一（SHA256 `0ADC289B5B2B1C871573FEF108C6AAC0EB8310F82ED7F95D34D52872C67D2C44`）。auto-customを適用。エージェントが独自に再書き出したアバターへ戻さない。廃止済みデモ専用キーは使わない |
| 今回の症状のアバター | `builds/releases/0.1.3/TanakaCap/avatars/avatar.tcap`（改変済みHAOLAN）。人工入力の調査結果は`results/hand-sides-modified-20260923/`、配布版は`results/hand-sides-release-20260923/` |
| 円周ヨー・ひとつ前の撮影の動画 | `results/avatar-videos/head-yaw-previous-full-20260924/after.mp4`。9/21撮影の全901フレーム約30秒。同階層`side-by-side.mp4`は左=旧ヨー＋固定、右=円周ヨー＋可変。入力は`results/head-yaw-previous-full-20260924/`。`previous-take`名の旧出力は40フレームの試行なので使わない |
| 円周ヨー＋可変追従の9/23撮影動画 | `results/avatar-videos/head-yaw-circle-20260923/after.mp4`。比較は同階層`side-by-side.mp4`、左=旧比率ヨー＋固定追従、右=円周ヨー＋可変追従。両手はどちらも絶対値化、改変済みHAOLAN/auto-custom、901フレーム約30秒。入力は`results/head-yaw-video-20260923/` |
| 左のみ絶対値化時点の動画 | `results/avatar-videos/finger-absolute-20260923/after.mp4`。比較は同階層`side-by-side.mp4`、左=旧符号反転、右=絶対値化。最新録画901フレーム約30秒、改変済みHAOLAN/auto-custom。入力と数値検証は`results/finger-absolute-video-20260923/` |
| 旧・左指符号反転の比較動画 | `results/avatar-videos/finger-sign-20260923/side-by-side.mp4`。左画面=変更前、右画面=旧左指符号反転。現在の絶対値化の動画ではない。数値と再生入力は`results/finger-sign-20260923/`。最新録画・改変済みHAOLAN/auto-custom。掌XY案は将来課題として未実装 |
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
