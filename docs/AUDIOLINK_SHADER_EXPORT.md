# AudioLink旧include互換

2026-09-13：ユーザー提供の外部プロジェクトを読み取り、MSL/Ring Particles Shaderの旧include Assets/AudioLink/Shaders/AudioLink.cgincが欠落、AudioLink 1.4.0はPackages/com.llealloo.audiolink/Runtime/Shaders/AudioLink.cgincにあると確認。隔離コピーでincludeだけ補正しDirect3D11 shader.isSupported/Material.SetPass(0)/コンパイルエラー0を確認。AvatarShaderCompatibilityをExporterへ追加：旧include欠落かつ新include実在時のみ書出しscratch内へshader/materialを複製し参照補正。原本変更なし、警告へ記録、音声AudioLink入力の実装ではない。builds/fixes/parent-constraint/TanakaCapExporter.unitypackageを更新、第三者shader/includeは同梱していない。外部shaderのバイト不変を確認。results/unity-shader-compat.log（初回import順の一時CS0103は再importで解消、最終executeMethod/検査/export成功）。実アバターの再書出し/見た目は未確認。Playerの再ビルド不要、公開ZIPは未更新。

読取元：D:/work/vrc_projects/haoranRurukuPazyamaGorone - コピー。シェーダー中の5箇所が旧includeを参照。DLL/GPU変更なし。検証用の原本/補正コピー/includeはunity/TanakaCap/Assets/TanakaCapExport-shadercheck（Git除外）に保存、プラグインのExportPackage対象外。
