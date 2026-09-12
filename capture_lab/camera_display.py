"""Single display gate for real-person camera images, including recorded inputs.

Never enable through settings, diagnostic modes, hotkeys, environment variables,
or a remembered UI choice. Only the complete, explicit process startup token.
"""
import sys

DISPLAY_FLAG = '--explicitly-allow-displaying-raw-camera-images-on-screen-for-this-session-only'


def allowed():
    return DISPLAY_FLAG in sys.argv[1:]


def add_argument(parser):
    parser.add_argument(DISPLAY_FLAG, action='store_true', dest='preview',
                        help='Explicitly display real-person camera images for this process only; hidden by default')


def show(name, frame):
    if not allowed():
        return
    import cv2
    cv2.imshow(name, frame)


def select_roi(name, frame, from_center=False):
    if not allowed():
        raise RuntimeError('Image-based ROI selection requires the full startup option ' + DISPLAY_FLAG)
    import cv2
    return cv2.selectROI(name, frame, from_center)


def update_tk_preview(label, frame):
    if not allowed():
        return
    import cv2
    import tkinter as tk
    thumb = cv2.resize(frame, (800, 450))[:, :, ::-1][:, ::-1].copy()
    photo = tk.PhotoImage(data=b'P6\n800 450\n255\n' + thumb.tobytes(), format='PPM')
    label.configure(image=photo)
    label.image = photo
