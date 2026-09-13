# PhysBoneとConstraintの書き出し

2026-09-13：公開版の書出しエラーPhysBone/Constraint overlap（FakeBonePositionsForOrnamentsPB/Fake_Furry_Hair_R.001、ユーザー確認Parent Constraint）を修正。競合するボーンはUnity Constraintに任せ、PhysBoneの回転対象だけから外す。子の走査は継続、競合しない子は揺れ対象として維持。末端でtail=0の偽重複は報告しない。原本とConstraintを削除・無効化しない。失う揺れはパス/型とともにreport警告へ明記。ソルバー/本体は変更なし。修正プラグイン：builds/fixes/parent-constraint/TanakaCapExporter.unitypackage。公開v0.1.0 ZIPは未更新。Unityコンパイル、親/位置/回転Constraintの除外・末端判定・子の適格性・複製内参照と原本維持の検査、梱包ソース確認成功。results/unity-exporter-constraint-fix.log。実アバターの書出し/見た目は未確認。

## 判断の根拠

Unity Parent Constraintは位置/回転を追従する。Unity 2022.3のPlayerLoopではConstraintManagerUpdateはScriptRunBehaviourLateUpdateの後。現在のSecondaryMotionはLateUpdateで回転を出力するため、一律許可だけでは上書きが発生する。今回は更新順・solverの調整を行わず、Constraintのあるボーンをシミュレーション対象から除外し警告する。無効状態のConstraintも将来の有効化との競合を避けて同じ扱い。スクリプトを除去するためAnimatorによる元の切替は再現しない。

- https://docs.unity3d.com/2022.3/Documentation/Manual/class-ParentConstraint.html
- https://docs.unity3d.com/2022.3/Documentation/Manual/class-PositionConstraint.html
- https://github.com/Unity-Technologies/UnityCsReference/blob/2022.3/Runtime/Export/PlayerLoop/PlayerLoop.bindings.cs

SDKのPhysBoneソルバーは導入していない。警告付きの互換フォールバックで、完全なParent ConstraintとPhysBoneの合成を実装したものではない。実モデルの成功はユーザー確認待ち。


2026-09-13：続くOverlapping PhysBone chains（イヤリングBone）に対応。全有効PhysBoneルートを事前収集し、親からの走査は別の子ルートで停止。子の専用設定を優先し、親のtailは子ルート位置を参照する。親→子の順でデータを作成、同一rootの既存first-wins警告は維持。二重登録の最終検査は残す。元のPhysBone/ignore設定は変更せず、境界変更をreport警告へ記録。Unityで実際のCollectSegmentsの親/子領域、子PBなし、ignoreを回帰検査し成功。results/unity-exporter-nested-physbone-fix.log。builds/fixes/parent-constraint/TanakaCapExporter.unitypackageを両修正入りに更新。PlayerとGitHub公開ZIPは未変更、実アバター再書出しは未確認。
