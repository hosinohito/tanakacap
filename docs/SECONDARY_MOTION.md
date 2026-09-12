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

- VRChat標準/グローバル/他人との衝突、掴み/ポーズ、Stretch/Squish、Animatorパラメーター出力は未対応として書き出し警告に残す。原本の全ギミック互換ではない。
- 実HAOLANが使うのはAdvanced、Angle/Hinge、Inside Capsule。Simplified/Polar/Plane/新版1.1やSDKありの読み込み経路は実素材で未評価。非一様scaleには最大軸scaleの保守的近似を使う。
- 本家VRChatと同じ入力軌跡を使った比較は未実施。次は通常利用での見た目評価と、VRChat内の合法的な実行結果との比較により復元時間/振幅を校正する。現段階を動作一致の合格とは扱わない。

## 検証

- `tools/audit_secondary_package.py`：原本と530個のスカラー、カーブ値/個数、コライダー参照を照合。results/secondary-motion/source-audit.json。
- `SecondaryMotionProbe`：実パッケージの960ステップ。最大変位角129度（元制限）、静止速度約0.0000142m/sまで収束。本体回転/全Transformローカル位置の変化0、OFF復元成功。静止時最大12.63度は衝突等による初期形状との差で、本家との差の解消を意味しない。results/secondary-motion/check.json、.bones.txt、.on/.off.png。ステップ処理最大約0.80msはこの短い単独試験のCPU値で、カメラ+OBS併用の性能保証ではない。
- `tools/smoke_unity.py --motion-check`：顔/腕/掌/指/欠測保持/透過を含む既存実Playerチェック成功。results/secondary-motion/transport.*。
- 自作モーションの実アバター画像：results/secondary-motion/motion-final.png。画像だけで実人物追跡精度を評価しない。
- Unityビルドで原本依存hash前後一致 `25babac2d68f0ee4c5323cd154f54b98`。
