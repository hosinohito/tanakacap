# 髪・服：PhysBone設定の互換変換（2026-09-12）

ユーザーは自然な揺れに加え、元のPhysBoneパラメーターを引き継いで似た動きに変換するよう指定した。当初の髪/服別の固定ばね設定は撤回した。独立実装の近似ソルバーであり、PhysBone本体やSDKのコード/DLLをPlayerへ含めない。

## 本体を持ち込まない理由と参照資料

現行SDK Licenseは、SDKの第三者への提供、オブジェクトコードの改変、VRChat外向け開発などを制限している。本体をこのアプリへ同梱できる許諾は確認できないため採用しない。特別な許諾が得られる可能性まで否定するものではない。読んでいるのは購入アバターに保存された作者の設定値で、SDKバイナリの解析/逆コンパイルはしていない。

- SDK公式ライセンス：https://hello.vrchat.com/legal/sdk
- 公式PhysBones仕様（バージョン、力、階層、制限、衝突）：https://creators.vrchat.com/common-components/physbones/
- Unity Playerの非記録引数：https://docs.unity3d.com/2022.3/Documentation/Manual/PlayerCommandLineArguments.html

仕様の意味は公式資料、下記の数式と係数はこのプロジェクトの近似設計。公式の内部計算式を再現した、という意味ではない。

## 変換と実行

`SecondaryMotionExporter`はSDKが存在する場合UnityのSerializedObjectで選択中の値・カーブ・Transform参照を読む。SDKが欠損している現在のHAOLAN環境ではテキストPrefabを読む。後者は原本の旧script識別子を確認し、入れ子/Variantや変更付きインスタンスを拒否する。SDKありの実改変プロジェクトでの端から端までの検証は残る。

`.tcap`のmanifestにsecondaryPhysics v1を追加。35系統、73区間、15個の明示コライダー。原本36コンポーネントのうち左zipperの同一root重複は先頭を使い警告する。今回の原本はversionフィールドなしのため旧版0（1.0）として扱い、その仮定を維持する。元値を保存するため係数の再調整に再インポートは不要。

| 入力 | 実装 |
|---|---|
| Root / Ignore / Endpoint / Multi-child | 元参照からチェーンを構築。Ignoreは子孫も除外。仮想末端、分岐Ignore/First/Average（平均方向近似）に対応 |
| Pull / Spring・Momentum / Integration / Stiffness | 保存値から復元力と減衰を算出。Simplified/Advancedで減衰を分け、版1.1のStiffnessは前の方向保持として近似 |
| Gravity / Falloff / Version | 符号で上下、初期姿勢からの変化でFalloff。旧版は加速度、新版はPullに従う目標方向への混合 |
| Immobile / Type | チェーン親の移動・回転の相殺と、アバター全体の並進のみの相殺を分ける |
| 曲線 | キーの時刻/値/接線/重み/Wrapを保存しUnity AnimationCurveで評価。深度を最長階層に正規化する方式は近似 |
| Angle / Hinge / Polar / Rotation | 元角度と回転軸、各カーブを使う。Hingeは面内、Polarはピッチ/ヨーに分解する近似 |
| Radius / Collider参照 | 元半径、Sphere/Capsule/Plane、位置/回転/高さ、Inside Bounds、Bones As Spheresを取り込む。Transformのscaleを反映 |
| Is Animated / Reset When Disabled | 基準姿勢の更新、非アクティブ時の状態リセット。元Animator Controllerの仕掛けは未対応 |

Pullから角周波数を `2π(0.5+8√pull)`（pull=0なら0）へ変換する。減衰はSpring/Momentumが大きいほど弱くする。これらは未校正の独自写像。本家と同じ数値が同じ減衰時間になることまでは保証しない。

外側の衝突は骨区間の4点近似、内包衝突は動かせる末端を対象とする。固定支点まで押すと裾が角度限界へ折れることを実試験で発見して修正した。内包形状に固定支点が入らない場合、区間全体の包含を満たせるとは限らない。2回の衝突/角度投影を行い、競合時は骨長と角度制限を優先する。髪同士・衣服の面同士の衝突、完全な貫通防止ではない。

更新順序は追跡と標準Constraintの後、Spout描画より前。最大1/120秒へ小分け、遅延時の追いつき処理は有界。移動0.4m超/長い停止はばね状態をリセット。Humanoid骨への書き込み、同一骨のConstraint競合、チェーン重複は拒否。原本Transformの位置/長さを変えない。

F6で表示中の揺れをON/OFF。`--no-secondary-motion`で起動時OFF。追跡ロスト時の本体姿勢保持は従来どおりで、揺れは最後の本体姿勢の周囲で収束する。

## 未対応と検証の限界

- 他ユーザー・ワールドとの衝突、掴み/ポーズ、Stretch/Squish、Animatorパラメーター出力は未対応として書き出し警告に残す。原本の全ギミック互換ではない。
- 実HAOLANが使うのはAdvanced、Angle/Hinge、Inside Capsule。Simplified/Polar/Plane/新版1.1やSDKありの読み込み経路は実素材で未評価。非一様scaleには最大軸scaleの保守的近似を使う。
- 本家VRChatと同じ入力軌跡を使った比較は未実施。次は通常利用での見た目評価と、VRChat内の合法的な実行結果との比較により復元時間/振幅を校正する。現段階を動作一致の合格とは扱わない。

## 検証

- `tools/audit_secondary_package.py`：原本と530個のスカラー、カーブ値/個数、コライダー参照を照合。results/secondary-motion/source-audit.json。
- `SecondaryMotionProbe`：実パッケージの960ステップ。最大変位角129度（元制限）、静止速度約0.0000142m/sまで収束。本体回転/全Transformローカル位置の変化0、OFF復元成功。静止時最大12.63度は衝突等による初期形状との差で、本家との差の解消を意味しない。results/secondary-motion/check.json、.bones.txt、.on/.off.png。ステップ処理最大約0.80msはこの短い単独試験のCPU値で、カメラ+OBS併用の性能保証ではない。
- `tools/smoke_unity.py --motion-check`：顔/腕/掌/指/欠測保持/透過を含む既存実Playerチェック成功。results/secondary-motion/transport.*。
- 自作モーションの実アバター画像：results/secondary-motion/motion-final.png。画像だけで実人物追跡精度を評価しない。
- Unityビルドで原本依存hash前後一致 `25babac2d68f0ee4c5323cd154f54b98`。

## 2026-09-12 本家Editor比較

本家SDKでの同一骨比較を実施し、独自減衰を1.5倍へ調整。復元周波数は比較で悪化したため維持。-LegacySecondaryResponseで旧減衰へ復帰。比較条件・数値・未達は[本家比較](PHYSBONE_REFERENCE.md)を参照。本文の本家比較未実施は今回以前の状態。


## 手による揺れ物への接触

ユーザー指定：VRChat標準の手・指コライダーとPhysBone側の衝突設定を引き継いで再現する。独自寸法のコライダーを一律追加する当初案は撤回。Exporterと独立ソルバーに実装。

[公式仕様](https://creators.vrchat.com/common-components/physbones/)のStandard CollidersではAvatar Descriptorに標準コライダーを定義し、未調整時は自動設定、手・指をグローバルPhysBoneコライダーとして使う。指の対象は人差し指・中指・薬指・小指であり、独断で親指を追加しない。

- 書き出し時にAvatar Descriptorの左右の手・指のAutomatic/Custom/Disabled、参照Transform、位置・回転・半径・高さ等を取得する。Customは元値、Disabledは無効を保持。AutomaticはSDKが生成する有効設定をコピー側で取得できるか確認し、取得不能を独自寸法で黙って補わず警告する。原本は変更しない。
- PhysBoneのAllow Collision（True/False/Other）と自分への衝突許可を保存し、手との衝突を許可したチェーンだけに適用する。Falseは明示Collidersのみ、Otherは自己フィルターに従う。明示コライダーとの関係は対象SDK版と公式仕様で確認し、一律に無効化／有効化しない。
- 0.1.5以前のExporterは明示Collidersだけを取り込み、Descriptorを省略し、Allow Collisionも保存していない。この情報を失った既存tcapから元設定を正確に復元することはできない。再書き出しが必要になる前提で設計し、旧パッケージに手衝突を推測追加しない。
- 表示に使う手・指の最終姿勢（平滑化・頭との接触補正後）へ追従し、左右独立で計算する。SDK本体をPlayerへ持ち込まず、保存した形状と許可設定を独立ソルバーで扱う。
- 検証：Automatic/Custom/Disabled、Allow Collisionの各選択と自己許可、左右独立、元の明示コライダー維持。欠測・復帰・瞬間移動、速い手のすり抜け、振動、骨長・角度制限との競合、追加負荷を人工入力と録画で評価する。設定の再現と本家の物理挙動の完全一致は区別する。

つかむ／固定する操作、他ユーザー・ワールドとの衝突、布の面衝突はこの課題に含めない。過去の「揺れ物追加調整終了」は、この新規依頼を除く既存調整に対して維持する。

### 保存形式と更新順序

新しいsecondaryPhysics.versionは2。旧version=1は従来どおり読み込む。新しい書き出しは新しいPlayerと組み合わせる。
StandardHandColliderExporterは書き出しコピーのDescriptorを読み、SDKの公開CalcPalmCollider/CalcFingerCollider APIでAutomaticと参照骨を解決する。Customの寸法を保持し、Disabledは省く。取得できない骨/API/状態はレポートへ理由を残す。SDKのDLLやソルバーは配布Playerに含めない。

標準形状はsourceId/sourceStateとともに保存。掌は位置・回転を手のTransformから計算し、指は親骨から対象骨への向きでカプセルを更新する。SDKのCOLLIDER_MAX_SIZEに従い半径と掌の高さを制限する。非一様スケールは従来どおり最大軸による近似。

Allow Collision False/True/Otherを保存し、TrueまたはOtherかつallowSelfのチェーンへ標準コライダーの参照を追加する。既存の明示コライダー参照は保持する。標準手形状は最終Humanoid姿勢を反映したStepの開始時に一度計算し、離れた点は境界球で除外。揺れ物に付いた明示コライダーは従来どおり衝突判定時に更新する。非表示の手・指は接触しない。

衝突はサンプル点による離散判定で、1フレーム間に薄い揺れ物を通過する速い手の連続衝突を保証しない。骨長・角度制限と衝突が両立しない場合は元の骨制限を優先する。本家VRChatのソルバーとの完全一致ではない。

### 手接触の検証結果（2026-11-11）

SDK 3.7.0の改変済みHAOLANコピーで標準10形状を取得。True/False/Other×自己許可の6通り、Custom寸法・Disabled、明示参照の維持を確認。新tcapは42チェーン・96セグメント・26コライダー（標準10を含む）。左右それぞれの人工接触でOFF=0度、ON=約6.56度の変位を確認。

900ステップ×ON/OFFで瞬間移動、非表示・復帰、0.5秒中断、リセット、ローカル骨長の維持を確認。Editorでの平均はOFF約0.314ms、ON約1.320ms（最大5.524ms）。30/60fps混在の人工入力、単一アバターであり一般性能の保証ではない。初回実装はON平均14.567msだったため、標準形状キャッシュと境界球除外で削減。詳細ログは `results/hand-collision/runtime-cached.log`。

最新録画900フレームを通常UIと同じプロセス制御で処理し正常終了・受信を確認（`recorded-session.json`）。新tcapの実Playerで動作経路検査とRGBA/Spout登録検査、旧0.1.5 tcapの読み込み・透過検査も成功。実人物による接触の見た目評価と本家VRChatとの挙動一致は未確認。
