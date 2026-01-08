import streamlit as st
import pandas as pd
import pickle
from pathlib import Path
from datetime import date

# ---------------------------------
# PAGE CONFIG
# ---------------------------------
st.set_page_config(
    page_title="Tea Price Prediction Demo",
    page_icon="🍃",
    layout="centered"
)

# ---------------------------------
# MODEL PATH
# ---------------------------------
LOCAL_MODEL_PATH = Path(__file__).parent / "Best_Tea_Price_Model_Model_4_Categorical.pkl"
MNT_MODEL_PATH = Path("/mnt/data/Best_Tea_Price_Model_Model_4_Categorical.pkl"

)

# OPTIONAL: dataset to populate dropdowns
DATASET_PATH = Path(__file__).parent / "Tea_Prices_Combined.csv"  # must have Region, Estate, Grade

# ---------------------------------
# LOAD BUNDLE
# ---------------------------------
@st.cache_resource
def load_bundle():
    model_path = LOCAL_MODEL_PATH if LOCAL_MODEL_PATH.exists() else MNT_MODEL_PATH
    if not model_path.exists():
        raise FileNotFoundError(
            f"Model file not found.\nTried:\n- {LOCAL_MODEL_PATH}\n- {MNT_MODEL_PATH}"
        )

    with open(model_path, "rb") as f:
        bundle = pickle.load(f)

    if not isinstance(bundle, dict):
        raise ValueError("This .pkl is not a dict bundle. Expected keys like: model, features, cat_cols, target.")

    required = ["model", "features"]
    missing = [k for k in required if k not in bundle]
    if missing:
        raise KeyError(f"Bundle is missing keys: {missing}")

    return bundle


def load_dropdowns():
    """Prefer real values from training_data.csv; otherwise placeholders."""
    if DATASET_PATH.exists():
        df = pd.read_csv(DATASET_PATH)
        regions = sorted(df["Region"].astype(str).dropna().unique().tolist())
        estates = sorted(df["Estate"].astype(str).dropna().unique().tolist())
        grades = sorted(df["Grade"].astype(str).dropna().unique().tolist())
        return regions, estates, grades, True

    # placeholders (works only if these categories existed during training)
    return ["Region_A", "Region_B"], ["Estate_1", "Estate_2"], ["OP", "BOP"], False


bundle = load_bundle()
model = bundle["model"]
expected_cols = list(bundle["features"])
cat_cols = list(bundle.get("cat_cols", []))
target_name = bundle.get("target", "Price")
model_name = bundle.get("model_name", "Tea Price Model")

regions, estates, grades, from_data = load_dropdowns()

# ---------------------------------
# UI HEADER
# ---------------------------------
st.title("🍃 Tea Auction Price Prediction")
st.caption(f"Model: {model_name}  •  Target: {target_name}")

# ---------------------------------
# DEBUG (small + useful)
# ---------------------------------
with st.expander("🔍 Debug info (click to view)"):
    st.write("Bundle keys:", list(bundle.keys()))
    st.write("Expected feature columns:", expected_cols)
    st.write("Categorical columns:", cat_cols)
    st.write("Model type:", type(model))

if not from_data:
    st.warning(
        "⚠️ Dropdown values are placeholders.\n"
        "To load real Region/Estate/Grade values, add `training_data.csv` next to app.py."
    )

st.divider()

# ---------------------------------
# INPUTS (match required features exactly)
# features: year, month, day_of_month, Region, Estate, Grade
# ---------------------------------
with st.form("predict_form"):
    selected_date = st.date_input("Select Date", value=date.today())

    region = st.selectbox("Region", regions)
    estate = st.selectbox("Estate", estates)
    grade = st.selectbox("Grade", grades)

    submitted = st.form_submit_button("Predict Price")

# ---------------------------------
# PREDICTION
# ---------------------------------
if submitted:
    dt = pd.to_datetime(selected_date)

    row = {
        "year": int(dt.year),
        "month": int(dt.month),
        "day_of_month": int(dt.day),
        "Region": str(region),
        "Estate": str(estate),
        "Grade": str(grade),
    }

    # Build X EXACTLY in training column order
    X = pd.DataFrame([[row[c] for c in expected_cols]], columns=expected_cols)

    try:
        pred = model.predict(X)
        price = float(pred[0]) if hasattr(pred, "__len__") else float(pred)

        st.success("✅ Prediction successful")
        st.metric("Predicted Price", f"{price:,.2f}")

        with st.expander("📌 Features used"):
            st.dataframe(X)

    except Exception as e:
        st.error("❌ Prediction failed")
        st.code(str(e))
        st.info(
            "If you used placeholder Region/Estate/Grade values that were NOT in training, CatBoost may fail.\n"
            "Fix: add `training_data.csv` so dropdowns use real categories."
        )
