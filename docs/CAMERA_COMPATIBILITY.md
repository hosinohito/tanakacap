# Windowsカメラ互換性（2026-09-13）

通常UIに「カメラ」タブを追加。ちらつき防止（変更しない／無効／50／60Hz）、
暗所補正（変更しない／速度優先／明るさ優先）、入力解像度、入力fps、転送形式、取得方式を設定できる。
入力解像度とfpsは描画設定とは独立。3推論モードすべてで共通Camera経路を使い、録画・デモには渡さない。
新しい依存ライブラリやネイティブ配布バイナリーは不要。Windows標準Media Foundation/KSをctypesから利用する。

## 機種・ドライバー固有の根拠と実装

| 対象・根拠 | 落とし穴 | 実装した対策 |
|---|---|---|
| CMS-V43BK、本環境の診断 | MJPEGを先に指定すると解像度/fps設定後にYUY2へ戻り約11.5fps。50Hzで約25fps、無効/60Hzで約30fps | 形式を最後に指定、読み戻し、任意のちらつき防止制御・復元 |
| [Logitech C922](https://support.logi.com/hc/en-sg/articles/360023345533-Maintain-a-constant-720p-60fps-stream-with-the-C922-webcam) | 720p60の維持には露出/Low Light Compensationが影響。ChromaCam利用時は720p30の制約 | 入力fps/解像度を独立指定、標準の暗所補正を速度優先へ切替可能。C922検出時に条件付きの案内 |
| [初代Elgato Facecam](https://help.elgato.com/hc/en-us/articles/4406119479693-Elgato-Facecam-Frame-Rate-Modes) | 30fps要求は15〜30fpsの可変動作、60fps要求でCFRになる機種仕様 | 30fpsを全カメラへ固定しない。初代の名前に限定して案内、60fpsを任意選択。MK.2/Pro/Neoへ同じ規則を拡張しない |
| [初代Facecamの接続条件](https://help.elgato.com/hc/en-us/articles/4416197650573-Elgato-Facecam-Requires-USB-3-0) | USB 3.0が必要。全FacecamがMJPEG対応とは限らない | 対応モードからMJPEG/NV12/YUY2を選択。MJPEGがなければ非圧縮形式を使用。停止/低fps時に接続条件を案内 |
| [Facecam MK.2](https://help.elgato.com/hc/en-us/articles/24162241010317-Elgato-Facecam-MK-2-System-Requirements) | USB 2.0接続ではMJPEGのみ対応 | 現在の接続で列挙された形式を優先し、形式を手動変更する入口も用意。初代の「USB 3.0必須」と混同しない |
| [Facecamの露出](https://help.elgato.com/hc/en-us/articles/4405055113357-Elgato-Facecam-Camera-Hub-Settings-Overview) | シャッター速度がfpsへ影響、ちらつき防止は自動露出時に作用する機種がある | フレーム取得後に実速度を測る。設定成功だけで30/60fps達成と判断しない。低fps時にCamera Hub側の露出確認を案内 |
| [BRIO 4K Stream Edition](https://support.logi.com/hc/en-ch/articles/360023356833-BRIO-4K-Stream-Edition-webcam-4K-support-information)、[BRIOの帯域問題](https://support.logi.com/hc/en-sg/articles/360023197314-How-come-I-m-not-seeing-1080p-resolution-with-BRIO-BRIO-4K) | USB接続・帯域で使えるモードが変わる。4Kの条件をすべてのBRIO製品へ適用できない | 対応する幅・高さ・fps・形式の組み合わせを検査。モード不一致/低fps時に対象を限定した案内。USB速度は実測していないので断定しない |
| [OBS仮想カメラ](https://obsproject.com/kb/virtual-camera-guide) | DirectShowにはあるがMFにはない場合がある。物理カメラの露出制御がない | APIを変更した時は識別子で照合、見つからなければ停止。未対応設定は無変更で継続。OBS側の起動・出力設定を案内 |

上の他機種は公式資料に基づく実装で、実機検証済みではない。
機種名照合は案内用。自動的な値の決め打ちには使わない。形式選択は機器の列挙結果で行う。
ファームウェア更新やレジストリ変更、メーカー固有の非公開制御は行わない。

## 共通の落とし穴と処理

- [DevicePath](https://learn.microsoft.com/en-us/windows/win32/directshow/selecting-a-capture-device)をUI設定に保存し、起動直前に番号を解決する。同型カメラが複数あっても名前だけでは選ばない。未接続の保存IDを別の番号へ置換しない。
- MFとDirectShowの番号は別物。PnPインスタンスとピン名を保ち、既知の映像インターフェースGUIDだけを正規化して照合する。実PCでCMSとDroidCamの列挙照合を確認（撮影はしていない）。仮想カメラが片方のAPIにしかない時は自動で別カメラへ切り替えない。
- `set()`が成功しても実設定が違う場合がある。[OpenCV公式](https://docs.opencv.org/4.x/d8/dfe/classcv_1_1VideoCapture.html)もAPI/OS/ドライバー/ハードウェアの層を区別している。対応組合せ・読み戻し・実画像サイズ・取得間隔を別に記録する。
- 非対応プロパティのNaN/例外を処理し、JSONへNaNを出さない。MSMFのFourCC欄がAPI固有の数値を返す時は形式不明とし、YUY2等と断定しない。
- 空画像/切断/不正な配列は理由付きで停止。グレースケール・BGRAはBGRへ変換する。無断で別デバイスを開いたり解像度を下げたりしない。
- 初期30フレームを除いた3秒間隔の到着速度を測り、要求の90%未満を一度警告する。API到着速度でありセンサーの真の更新頻度や重複なしの保証ではない。静止映像を重複として捨てる処理は入れない。
- 暗所補正は[標準のAuto Exposure Priority](https://learn.microsoft.com/en-us/windows-hardware/drivers/stream/ksproperty-cameracontrol-auto-exposure-priority)を使用する。自動露出を読み戻せた場合だけ変更し、露出そのものは勝手に自動へ切り替えない。機種により未対応なら警告する。
- [ちらつき防止](https://learn.microsoft.com/en-us/windows-hardware/drivers/stream/ksproperty-videoprocamp-powerline-frequency)と暗所補正は既定「変更しない」。変更前の値/flagsを保存、書込みと読み戻し、撮影開始後の再確認、停止後の復元を実施する。失敗時に適用済みと表示しない。
- 変更前に`logs/camera-settings/`へ復元用JSONを排他的に保存する。強制終了後は同じカメラの次回起動で復元。復元失敗時は記録を残す。別の生存プロセスの復元記録は上書きしない。停電中の即時復元や、USBを抜いたままでの復元はできない。
- Windowsのカメラ許可、他アプリによる占有、USB帯域不足は取得失敗メッセージへ含める。設定画面を自動で開かない（カメラプレビューが現れる可能性があるため）。

## 検証と配布

模擬デバイスで番号変化・同名機種・非対応制御・部分的書込失敗・設定リセット・異常終了復元・非対応形式を検査。
全テストと、カメラなしの実Tk操作検査を実施。今回追加したctypes設定経路は実撮影では未検証。
CMSの25→30fpsは前のネイティブ診断で確認した結果で、新経路での達成保証ではない。

別PCの更新は`tanakacap/`全体を同じ場所へ上書き。Unity Player・モデル・runtime・私用ui-settings.jsonのコピーは不要。
利用説明書も更新する場合は`docs/USER_GUIDE.md`を配布先の`使い方.md`へコピーする。
次回リリースビルドは既存のソース同梱処理で新モジュールも入る。今回はZIPを作成しない。


## Windows制御ABIの検証（2026-09-13）

KSPROPERTYはLONGLONGを含むunionで8byte境界。KSPROPERTY_VIDEOPROCAMP_Sは40byteであり、36byteの要求は実機で0x8007007Aとなった。ctypesへ同じunionを実装し、診断helperの `--abi`（カメラを起動しない）とsizeof/offsetを照合する回帰検査を追加。60Hz適用成功と実速度の確認はユーザー再試験待ち。照明ONで17→25Hzという報告は暗所露出の影響を示唆する。
