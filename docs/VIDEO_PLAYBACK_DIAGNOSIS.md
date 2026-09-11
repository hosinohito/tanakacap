# 動画再生の重さ：2026-09-12

ユーザー報告：Windows Media Playerはコマ送り、MPCは映像再生できるがウインドウ移動が非常に遅い。

読み取りで確認した事実：

- NVIDIA RTX4090、595.71（Windows32.0.15.9571）、デバイス状態OK/エラーコード0。
- Dell S2721DGF DP、2560×1440 165Hz。Meta Virtual Monitorドライバーも存在するが、原因や有効な画面であることは未確認。
- Videosの2026-09-12 07-30-29.mp4は1920×1080、60fps、H264、2373frame。最初の240frameをメモリ内でCPU復号し約380fps。全ファイル正常やWMP互換性を保証する検査ではない。
- OBSはNVENC H264 High、6000kbps、NV12、Hybrid MP4。プレーヤーによる挙動差の根本原因は未確定。
- MPC-HC2.8.0、LAVVideoとMPC Video Rendererをロード、UseD3D11=1。再生中MPC VideoDecode16〜17%、3D9〜11%、DWM3D8〜10%、GPU全体21%、VRAM1465MiB。ハードウェア復号は実際に動作。
- P8/低クロックは観測されたが、それだけで電源制御異常とは断定しない。
- EVR custom presenter変更後も遅さ不変とユーザー確認。DSVidRen=11を読み取り確認。変更後サンプルGPU35%、Decode19%。MPCVR固有原因説は弱まった。
- 直近6時間のSystemログでDisplay/nvlddmkm/WHEAに一致するイベント出力なし。すべてのドライバー不具合を否定するものではない。

次の切り分けは、録画・配信していない時にOBSを終了しMPC単独で比較すること（質問中）。ドライバー未導入やGPU飽和とは合わない観測だが、描画/合成/同期の原因は未確定。OS、ドライバー、仮想モニター、電源設定は変更していない。プレーヤー設定比較はユーザーが実施。

参考：[MPC Video Renderer公式](https://github.com/Aleksoid1978/VideoRenderer) はDXVA2/Direct3D11のデコード/表示処理対応を記載。今回の環境の不具合原因を説明する資料ではない。
