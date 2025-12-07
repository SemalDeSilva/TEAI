import cv2
import serial
import time
import numpy as np
import os
import csv

# ================== CONFIG ==================

SERIAL_PORT = 'COM7'        # your Arduino port
BAUD_RATE = 115200

CAMERA_INDEX = 0            # UGREEN webcam index

TARGET_WIDTH = 3840
TARGET_HEIGHT = 2160

FOCUS_WAIT_SECONDS = 1.0
WARMUP_FRAMES = 5

JPEG_QUALITY = 98
SAVE_RAW = True
SAVE_ENHANCED = True

RAW_DIR = "raw_images"
ENH_DIR = "enhanced_images"

ENABLE_CROP = False
CROP_X = 640
CROP_Y = 360
CROP_W = 2048
CROP_H = 1344

CSV_LOG = "measurements_log.csv"

# ============================================


def ensure_dirs():
    if SAVE_RAW and not os.path.exists(RAW_DIR):
        os.makedirs(RAW_DIR)
    if SAVE_ENHANCED and not os.path.exists(ENH_DIR):
        os.makedirs(ENH_DIR)


def ensure_csv_log():
    """Create CSV file with header if it does not exist."""
    if not os.path.exists(CSV_LOG):
        with open(CSV_LOG, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "sample_idx",
                "timestamp",
                "raw_path",
                "enh_path",
                "weight_g",
                "temp_c",
                "humidity_pct",
            ])


def init_serial():
    print(f"Opening serial port {SERIAL_PORT}...")
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=2)
    time.sleep(2)

    print("Flushing initial Arduino messages...")
    while ser.in_waiting:
        line = ser.readline().decode(errors='ignore').strip()
        if line:
            print("Arduino:", line)
    return ser


def wait_for_arduino(ser, expected_msg, timeout=10):
    print(f"Waiting for '{expected_msg}' from Arduino (timeout {timeout}s)...")
    start = time.time()
    while True:
        if time.time() - start > timeout:
            print(f"Timeout waiting for '{expected_msg}'")
            return False
        line = ser.readline().decode(errors='ignore').strip()
        if line:
            print("Arduino:", line)
        if line == expected_msg:
            return True


def _extract_number(token: str):
    """Strip unit letters and keep only [-0-9.] so float() won't crash."""
    token = token.strip()
    # remove possible 'W=' / 'T=' / 'H=' already before calling if needed
    num_chars = []
    for ch in token:
        if ch.isdigit() or ch in ".-":
            num_chars.append(ch)
    if not num_chars:
        return None
    try:
        return float("".join(num_chars))
    except ValueError:
        return None


def read_measurement(ser, timeout=20):
    """
    Wait for:
        MEASURED W=1.23g T=27.4C H=61.2%
    then 'WEIGH_DONE'.

    Returns (weight_g, temp_c, humidity_pct) or (None, None, None) on timeout.
    """
    weight = None
    temp_c = None
    hum_pct = None

    start = time.time()
    while True:
        if time.time() - start > timeout:
            print("Timeout waiting for measurement data")
            return None, None, None

        line = ser.readline().decode(errors='ignore').strip()
        if not line:
            continue

        print("Arduino:", line)

        if line.startswith("MEASURED"):
            # Expected format:
            #   MEASURED W=1.23g T=27.4C H=61.2%
            try:
                parts = line.split()[1:]  # skip "MEASURED"
                for p in parts:
                    p = p.strip()
                    if p.startswith("W="):
                        val = p.split("=", 1)[1]
                        w = _extract_number(val)
                        if w is not None:
                            weight = w
                    elif p.startswith("T="):
                        val = p.split("=", 1)[1]
                        t = _extract_number(val)
                        if t is not None:
                            temp_c = t
                    elif p.startswith("H="):
                        val = p.split("=", 1)[1]
                        h = _extract_number(val)
                        if h is not None:
                            hum_pct = h
            except Exception as e:
                print("Error parsing MEASURED line:", e)

        if line == "WEIGH_DONE":
            break

    return weight, temp_c, hum_pct


def init_camera():
    print("Opening camera...")
    cap = cv2.VideoCapture(CAMERA_INDEX, cv2.CAP_DSHOW)

    if not cap.isOpened():
        print("ERROR: Could not open camera.")
        return None

    fourcc = cv2.VideoWriter_fourcc(*'MJPG')
    cap.set(cv2.CAP_PROP_FOURCC, fourcc)

    print(f"Requesting resolution {TARGET_WIDTH} x {TARGET_HEIGHT}...")
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, TARGET_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, TARGET_HEIGHT)

    cap.set(cv2.CAP_PROP_AUTOFOCUS, 1)

    ret, frame = cap.read()
    if ret:
        h, w, c = frame.shape
        print(f"Camera resolution in use: {w} x {h}")
    else:
        print("WARNING: Could not read test frame.")
    print("Camera opened.\n")
    return cap


def enhance_image_soft(img_bgr):
    lab = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)

    clahe = cv2.createCLAHE(clipLimit=1.5, tileGridSize=(8, 8))
    l2 = clahe.apply(l)

    lab2 = cv2.merge((l2, a, b))
    enhanced = cv2.cvtColor(lab2, cv2.COLOR_LAB2BGR)

    kernel = np.array([[0, -0.2, 0],
                       [-0.2, 1.8, -0.2],
                       [0, -0.2, 0]], dtype=np.float32)
    sharpened = cv2.filter2D(enhanced, -1, kernel)

    return sharpened


def apply_crop(img):
    if not ENABLE_CROP:
        return img

    h, w = img.shape[:2]
    x = max(0, CROP_X)
    y = max(0, CROP_Y)
    x2 = min(w, x + CROP_W)
    y2 = min(h, y + CROP_H)

    if x2 <= x or y2 <= y:
        return img

    return img[y:y2, x:x2]


def main():
    ensure_dirs()
    ensure_csv_log()

    # Arduino
    print("Connecting to Arduino on", SERIAL_PORT)
    ser = init_serial()
    print("Connected to Arduino.\n")

    # ---- Initial tare with empty tray ----
    print("Make sure tray is EMPTY, then taring...")
    ser.write(b'Z')
    time.sleep(0.5)  # small pause so Arduino definitely sees 'Z'

    ok = wait_for_arduino(ser, "ZERO_DONE", timeout=20)
    if not ok:
        print("Warning: did not receive ZERO_DONE.")
        print("→ Tray is still tared once in Arduino setup(),")
        print("  so reset the board with EMPTY tray before running.\n")
    else:
        print("Tray tared successfully.\n")

    # Camera
    cap = init_camera()
    if cap is None:
        ser.close()
        return

    sample_idx = 1

    while True:
        user_in = input(
            f"\nPlace sample #{sample_idx} on the conveyor.\n"
            "Press ENTER to run cycle, or type q and ENTER to quit: "
        ).strip().lower()

        if user_in == 'q':
            print("Exiting capture loop...")
            break

        # ---------- 1) MOVE TO CAPTURE ----------
        print(f"\n[Sample {sample_idx}] Sending C to Arduino (move to capture)...")
        ser.write(b'C')

        if not wait_for_arduino(ser, "AT_CAPTURE", timeout=15):
            print("Did not receive AT_CAPTURE. Skipping sample.")
            continue

        # ---------- 2) CAPTURE IMAGE ----------
        print("Waiting for autofocus to settle...")
        time.sleep(FOCUS_WAIT_SECONDS)

        print(f"Discarding {WARMUP_FRAMES} warmup frames...")
        for _ in range(WARMUP_FRAMES):
            cap.read()

        print("Capturing final image...")
        ret, frame = cap.read()
        raw_path = ""
        enh_path = ""
        if not ret:
            print("ERROR: could not read frame from camera.")
        else:
            ts = time.strftime("%Y%m%d_%H%M%S")
            frame_proc = apply_crop(frame)

            if SAVE_RAW:
                raw_name = f"sample_{sample_idx:03d}_{ts}_raw.jpg"
                raw_path = os.path.join(RAW_DIR, raw_name)
                cv2.imwrite(
                    raw_path,
                    frame_proc,
                    [int(cv2.IMWRITE_JPEG_QUALITY), JPEG_QUALITY]
                )
                print(f"[Sample {sample_idx}] RAW image saved as {raw_path}")

            if SAVE_ENHANCED:
                enh_frame = enhance_image_soft(frame_proc)
                enh_name = f"sample_{sample_idx:03d}_{ts}_enh.jpg"
                enh_path = os.path.join(ENH_DIR, enh_name)
                cv2.imwrite(
                    enh_path,
                    enh_frame,
                    [int(cv2.IMWRITE_JPEG_QUALITY), JPEG_QUALITY]
                )
                print(f"[Sample {sample_idx}] ENHANCED image saved as {enh_path}")

                display_frame = enh_frame
            else:
                display_frame = frame_proc

            cv2.imshow(f"Sample {sample_idx}", display_frame)
            cv2.waitKey(300)
            cv2.destroyAllWindows()

        # ---------- 3) MOVE TO WEIGH + READ WEIGHT/T/H ----------
        print("Sending W to Arduino (move to tray + measure)...")
        ser.write(b'W')

        weight, temp_c, hum_pct = read_measurement(ser, timeout=20)
        print(f"[Sample {sample_idx}] Measured: "
              f"weight={weight} g, T={temp_c} C, H={hum_pct} %")

        # ---------- 4) MOVE BACK HOME ----------
        print("Sending H to Arduino (move back home)...")
        ser.write(b'H')

        if not wait_for_arduino(ser, "AT_HOME", timeout=15):
            print("Did not receive AT_HOME.")
        else:
            print(f"[Sample {sample_idx}] Back at home position.")

        # ---------- 5) LOG TO CSV ----------
        ts_now = time.strftime("%Y-%m-%d %H:%M:%S")
        with open(CSV_LOG, mode="a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                sample_idx,
                ts_now,
                raw_path,
                enh_path,
                weight,
                temp_c,
                hum_pct,
            ])

        sample_idx += 1

    cap.release()
    ser.close()
    cv2.destroyAllWindows()
    print("Done.")


if __name__ == "__main__":
    main()
