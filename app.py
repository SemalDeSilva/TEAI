import streamlit as st
from ultralytics import YOLO
from PIL import Image
import numpy as np
import tempfile
import os

st.set_page_config(page_title="Foreign Particle Detector", layout="wide")

st.title("🫖 Foreign Particle Detector (YOLOv8)")
st.caption("Upload an image → run detection → view annotated output + detection count.")

# --- Sidebar controls ---
st.sidebar.header("Settings")
conf = st.sidebar.slider("Confidence threshold", 0.05, 0.95, 0.25, 0.05)
imgsz = st.sidebar.selectbox("Image size (inference)", [640, 768, 896, 1024], index=3)
device = st.sidebar.selectbox("Device", ["cpu", "0"], index=0)  # "0" = first GPU if available

# --- Model path ---
# Put your model in the same folder as app.py OR change this path
MODEL_PATH = st.sidebar.text_input(
    "Model path",
    value="foreign_particle_detector_best.pt",
    help="Example: foreign_particle_detector_best.pt (same folder) or a full path",
)

@st.cache_resource
def load_model(path: str):
    return YOLO(path)

# --- File upload ---
uploaded = st.file_uploader("📤 Upload an image (jpg/png/jpeg)", type=["jpg", "jpeg", "png"])

if uploaded is None:
    st.info("Upload an image to start.")
    st.stop()

# Display input image
image = Image.open(uploaded).convert("RGB")
col1, col2 = st.columns(2)

with col1:
    st.subheader("Input")
    st.image(image, use_container_width=True)

# Run inference button
run = st.button("▶️ Run Detection", type="primary")

if run:
    # Load model
    try:
        model = load_model(MODEL_PATH)
    except Exception as e:
        st.error(f"Could not load model from: {MODEL_PATH}\n\nError: {e}")
        st.stop()

    # Save uploaded image temporarily (Ultralytics likes file paths)
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = os.path.join(tmpdir, "input.jpg")
        image.save(input_path)

        # Predict
        results = model.predict(
            source=input_path,
            conf=conf,
            imgsz=imgsz,
            device=device,
            verbose=False
        )

        r = results[0]
        annotated_bgr = r.plot()  # numpy array (BGR)
        annotated_rgb = annotated_bgr[..., ::-1]  # BGR->RGB

        # Count detections
        det_count = 0
        if r.boxes is not None:
            det_count = len(r.boxes)

        with col2:
            st.subheader("Output (Annotated)")
            st.image(annotated_rgb, use_container_width=True)

        st.success(f"✅ Detections found: {det_count}")

        # Optional: show a small table of detections
        if det_count > 0:
            st.write("### Detection details")
            rows = []
            for b in r.boxes:
                cls_id = int(b.cls.item()) if b.cls is not None else 0
                conf_i = float(b.conf.item()) if b.conf is not None else 0.0
                x1, y1, x2, y2 = map(float, b.xyxy[0].tolist())
                rows.append({
                    "class_id": cls_id,
                    "confidence": round(conf_i, 4),
                    "x1": round(x1, 1),
                    "y1": round(y1, 1),
                    "x2": round(x2, 1),
                    "y2": round(y2, 1),
                })
            st.dataframe(rows, use_container_width=True)

        # Download annotated image
        st.download_button(
            "⬇️ Download annotated image",
            data=Image.fromarray(annotated_rgb).tobytes(),
            file_name="annotated_output.rgb",
            mime="application/octet-stream",
            help="Raw RGB bytes. If you want a PNG download, tell me and I’ll add it."
        )
