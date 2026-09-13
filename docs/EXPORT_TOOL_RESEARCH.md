# 着せ替えツールの書き出し準備調査（2026-09-13）

利用者向け操作はUSER_GUIDE.mdへ記載。全操作を複製プロジェクトで行い、原本のシーン/Prefab/共有素材を変更しない。ベイク自体がコピーを作る場合も、事前のプロジェクト複製を省略しない。

| 対象 | 確認した根拠 | TanakaCapへの適用 |
| --- | --- | --- |
| MA | [公式手動処理](https://modular-avatar.nadena.dev/ja/docs/manual-processing)は右クリックModular Avatar/Manual bake avatar、変換済みコピー生成を明記 | コピーをExport。生成素材はAssetBundle完成まで保持 |
| NDMF / AAO | [公式基本手順](https://vpm.anatawa12.com/avatar-optimizer/ja/docs/tutorial/basic-usage/)はNDM Framework/Manual bake avatarと複製への適用を明記 | ベイク前のAAO設定を変更してから処理。MAのボーン結合と同じ処理系 |
| VRCFury | 作者repo commit 2863a3fea5f2a4f36808a4b7dc8f7e8f106dbc0d、Editor-Common/Menu/MenuItems.csとEditor-Avatars/Menu/VRCFuryTestCopyMenuItem.csを確認 | Tools/VRCFury/Build an Editor Test Copy。複製にVRCBuildPipelineCallbacks.OnPreprocessAvatarを実行。単独VRCFury処理だけではないため、MA/AAO併用時の準備入口にもする |
| キセテネ | [作者説明](https://tomo-shi-vi.hateblo.jp/entry/kisetene)の1-6で着せる操作後に服の格納・ボーン関連付けが完了 | 着せた結果をExport。配置/サイズ調整だけの状態を完成としない |
| AvatarTools | [原作者](https://booth.pm/ja/items/1564788)、[takecccc版](https://github.com/takecccc/AvatarTools)のAvatarAssemblerUI.cs/Core.cs | 結合済み結果を選択。takecccc版UIのCheck/Assemble!を確認。原版や派生のボタン表記が全て同一とは断言しない |

VRCFuryは複製前にVRCFPrefabFixer.Fix(originalObject)を呼ぶ。また同名の古いTest Copyを削除する。『絶対に原本へ触れないツール』とは説明せず、複製プロジェクトを操作することで原本を保護する。

AAOの[Trace And Optimize](https://vpm.anatawa12.com/avatar-optimizer/ja/docs/reference/trace-and-optimize/)はAnimation等から未使用BlendShape・Objectを除去する。TanakaCapの外部駆動はその解析に含まれないため、表情/ボーン保持の初期案として該当自動最適化OFFを案内。MMD互換だけでARKit等全表情を保護できるとは扱わない。衣装の見た目を作るRemove Mesh等を一括撤去しない。

現行AvatarExporter.ExportはVRCSDK前処理を呼ばない。未知のコンポーネントで停止し、Animator Controllerを除去する。そのため『ベイクしたらVRChat全機能互換』ではなく、完成したメッシュ・骨・素材・表情・PhysBone設定を書き出すための準備。IConstraint以外の未対応部品が残る改変や、動的な衣装メニューは保証しない。

今回は公式説明/作者実装と現行Exporterの静的照合。これらのツールを実際に導入した改変アバターでの書き出し試験は未実施。未検証を互換性合格にしない。DressingToolsなど、今回具体的な処理手順を確定できなかったツールへ同じ操作を無条件に流用しない。
