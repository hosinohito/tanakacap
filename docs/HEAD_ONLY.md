# 頭専用モード

2026-09-13。頭の向きをMobileNet V3 smallで推定し、YuNetで入力領域の位置・大きさと存在を確認する。両方ONNX Runtime CUDA。表情/口/まばたき/虹彩/体/腕/指のモデルや従来の人物検出は生成しない。音声口パクはユーザー指定で後日の課題。頭以外の姿勢は保持する。目線だけは既存仕様どおりカメラ方向へ戻る。

## 起動

- デスクトップtanakacap-head-only.bat：非記録・無期限、Player終了で停止。
- デスクトップtanakacap-test.bat：今回の検証対象は頭専用、1800観測、診断記録あり。
- 直接：`.\run-avatar.ps1 -Camera 1 -HeadOnly -NoLog`。通常のfull設定を変更しない。
- 実写表示は既定禁止。完全一致の長い専用起動オプションを明示した場合のみ、P：一時停止/再開、R：対象リセット、S：頭の矩形選択、Q/Esc：終了が使える。通常はアバターを閉じるか端末Ctrl+Cで終了する。表示ルールとオプションは[開発手順](DEVELOPMENT.md#開発ui設定ログ)参照。
- `-HeadRoi X,Y,W,H` はautoでは最初の対象指定。頭の動きとともに更新する。
- `-HeadRoiMode fixed` は従来の手動固定方式。頭領域モデルも起動せず、空の範囲の自動ロストはできない。通常は範囲の数値指定が必須。CLIは `--head-roi-mode fixed --roi X Y W H`。映像を使う選択は長い専用起動オプションがない場合拒否する。autoではプレビューなし・範囲指定なしでも動く。

## 領域取得と保持

YuNetの固定640入力を使用。全画面をアスペクト比維持で縮小・右下余白、BGR/float32/0..255。clsとobjの積の平方根が0.8以上の候補を取り、NMS0.3。顔の5点出力は制御へ使わない。最小24px、画面内面積85%以上を要求する。顔矩形へ20%余白の正方形を作り姿勢モデルへ渡す。箱の更新だけ旧25%/新75%を混ぜる。

初回・復帰は連続2検出を確認してから従来の3平均/重複2観測ゲートへ渡す。未検出フレームから直ちにheadTracked=falseとし、姿勢モデルへ空画像を渡さず最後のアバター姿勢を保持。復帰時は古い方向履歴をリセット。通常の頭角度の時間補正は追加していない。

同じ場所付近の顔を優先する。離れた他者へ即切り替えない。0.8秒見失い、画面内の候補が一人なら離れた場所からも2検出確認して再取得。初回複数人では自動選択せず、SまたはHeadRoiで指定する。本人識別ではないので長時間離席後に別人が一人で入るとその人を対象にする。写真・画面上の顔の識別や完全な横/後ろ向きは保証しない。

## モデル取得

追加のPython依存はない。既存ONNX Runtime/CUDA/OpenCVを使用しOpenCVのCPU DNNは本体の推論に使わない。

PowerShellでプロジェクト直下から：

```powershell
Invoke-WebRequest -Uri 'https://github.com/yakhyo/head-pose-estimation/releases/download/weights/mobilenetv3_small.onnx' -OutFile 'models/head-mobilenetv3-small.onnx'
Invoke-WebRequest -Uri 'https://media.githubusercontent.com/media/opencv/opencv_zoo/main/models/face_detection_yunet/face_detection_yunet_2023mar.onnx' -OutFile 'models/head-region-yunet.onnx'
```

両モデルは起動時SHA256照合。不一致は停止し、別モデルへ黙って切り替えない。

- 頭姿勢：e8ae4d932b3d13221638fc72e171603e020c6da28b770753f76146867f40e190
- 頭領域：8f2383e4dd3cfbb4553ea8718107fc0423210dc964f9f4280604804ed2552fa4

頭姿勢の作者 https://github.com/yakhyo/head-pose-estimation 。コードMIT（HEAD_MODEL_LICENSE.txt）、学習300W-LP。2026-09-13再監査で作者の重み別MIT表記と現行ファイルSHA一致を確認し、モデルの商用利用・再配布可へ更新。[根拠と条件](MODEL_LICENSE_DECISIONS.md)。製品ZIPへの同梱は可能、Gitへモデル原本を入れない方針は維持。学習データ自体を配布する許諾ではない。

YuNet公式 https://github.com/opencv/opencv_zoo/tree/main/models/face_detection_yunet 。モデルを含む同ディレクトリはMIT、原文YUNET_LICENSE.txtを保持。2026may版も確認したが、これは入力形状を動的にする再export。今回は既存ORTで固定640の明確な入出力を検証できる2023mar版を選んだ。古い依存を新規導入したわけではない。デコード仕様の参考は https://github.com/opencv/opencv/blob/4.x/modules/objdetect/src/face_detect.cpp 。GPU必須、CPU-onlyへの代替なし。ネットワークの重みは全てGit除外。

## 検証結果と限界

- tools/audit_head_only_auto.py：既存実写1frameから黒画像・顔領域遮蔽・左右220px移動・±20度回転を作る。未検出で姿勢推論停止/再取得、移動量-219.85/+216.85px、ロール20.80/1.32/-18.58度を確認。人工的な入力変化であり、実人物による遮蔽精度の保証ではない。
- results/head-auto-audit-1789228337328949100/report.json：頭姿勢CUDA2223 node、頭領域CUDA2650 node、どちらもCPU node0。
- 既存1280x720録画先頭930frame（30warmup+900測定）、Player/OBS/プレビューなし、ORT traceOFF：900/900追跡有効、ループ中央値8.601ms、p95は当該report参照。頭姿勢2.339ms、領域3.828ms、decode1.892ms。結果results/20260912T155231-635213Z-head-only/report.json。更新Hzや実際の表示遅延とは別。
- 実Player：同じ推論のpacket.jsonをtools/smoke_unity.pyへ渡し、頭ピッチ反映とロスト保持を確認。results/head-auto-player/transport.pngと付属JSON。
- カメラ1で非記録65観測（5warmup/60測定）が正常終了。これは起動確認で、実人物の追従品質の合格ではない。
- 210プロジェクトtests成功。最初のpytestは誤ってassets-source/resultsも収集して失敗、tests指定へ訂正。サンドボックス内のpytest一時フォルダーACLで失敗したため通常権限の別tempで成功。資産や環境の依存は変更しない。

自動取得・追従・停止・復帰・旧方式復帰の実装は完了。実人物での大きいyaw/pitch、手の遮蔽、照明、通常OBS併用の最終品質確認と頭姿勢モデルの配布監査は残る。今回の変更ではUnity/揺れ物/通常追跡のコードは変更しない。
