import os
import glob
import json
import streamlit as st
import pandas as pd
import numpy as np
try:
    import joblib
except Exception:
    joblib = None
    # If joblib is missing, show a clear message in the Streamlit UI at import time
    try:
        st.error("El paquete 'joblib' no está instalado en el entorno del servidor.\n\nAsegúrate de que `requirements.txt` contiene 'joblib' y redeploya la app en Streamlit Cloud.")
        st.stop()
    except Exception:
        # If Streamlit isn't ready to display, just continue so the error is visible in logs
        pass
import pickle


def load_metadata(path="modelo_heartdisease_meta.json"):
    if not os.path.exists(path):
        st.warning(f"No se encontró {path}. Algunas funcionalidades pueden faltar.")
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_columns(path="columnas_heartdisease.pkl"):
    if not os.path.exists(path):
        return None
    try:
        with open(path, "rb") as f:
            cols = pickle.load(f)
        # Ensure it's a list of strings
        if isinstance(cols, (list, tuple)):
            return [str(c) for c in cols]
        return None
    except Exception:
        return None


def load_model(path):
    # Try joblib then pickle
    try:
        return joblib.load(path)
    except Exception:
        try:
            with open(path, "rb") as f:
                return pickle.load(f)
        except Exception as e:
            st.error(f"Error cargando modelo {path}: {e}")
            return None


def find_models():
    files = glob.glob("*.pkl") + glob.glob("*.joblib")
    return files


def build_input_ui(meta):
    st.header("Entrar datos del paciente")

    cat = meta.get("features", {}).get("categorical", []) if meta else []
    num = meta.get("features", {}).get("numerical", []) if meta else []

    values = {}

    # Handle gender specially if those dummy columns exist
    if "Gender_Female" in cat and "Gender_Male" in cat:
        gender = st.selectbox("Género", ["Masculino", "Femenino", "Otro/Prefiero no decir"], index=0)
        values["Gender_Female"] = 1 if gender == "Femenino" else 0
        values["Gender_Male"] = 1 if gender == "Masculino" else 0
        # Remove from categorical list so we don't ask separately
        cat = [c for c in cat if c not in ("Gender_Female", "Gender_Male")]

    # Binary categorical features as checkboxes
    for c in cat:
        # Show nicer labels: replace underscores
        label = c.replace("_", " ")
        values[c] = 1 if st.checkbox(label, value=False) else 0

    # Numerical inputs
    for n in num:
        # default values chosen generically
        if "Age" in n:
            values[n] = st.number_input(n, min_value=0, max_value=120, value=50)
        else:
            values[n] = st.number_input(n, value=0.0)

    return values


def make_dataframe(values, meta, cols_override=None):
    # Determine column order: override from columnas file, else metadata, else keys
    if cols_override:
        cols = cols_override
    else:
        cols = []
        if meta:
            cols += meta.get("features", {}).get("categorical", [])
            cols += meta.get("features", {}).get("numerical", [])
        else:
            cols = list(values.keys())

    # Build row using provided columns; missing values default to 0
    row = {c: float(values.get(c, 0)) for c in cols}
    return pd.DataFrame([row], columns=cols)


def predict_and_display(model, X, meta):
    threshold = meta.get("threshold", 0.5) if meta else 0.5
    label_map = meta.get("label_map") if meta else None
    pos_index = meta.get("positive_label_index", 1) if meta else 1

    if hasattr(model, "predict_proba"):
        probs = model.predict_proba(X)
        # handle binary vs multi
        prob_pos = float(probs[:, pos_index])
        pred_label = (prob_pos >= threshold)
        pred_text = None
        if label_map:
            pred_text = label_map[str(int(pred_label))]
        st.metric("Probabilidad (positivo)", f"{prob_pos:.3f}")
        if pred_text:
            st.success(f"Predicción: {pred_text} (umbral {threshold})")
        else:
            st.success(f"Predicción binaria: {int(pred_label)} (umbral {threshold})")
    else:
        pred = model.predict(X)
        pred0 = int(pred[0])
        if label_map:
            st.success(f"Predicción: {label_map.get(str(pred0), pred0)}")
        else:
            st.success(f"Predicción: {pred0}")


def main():
    st.title("Demo: Clasificador Heart Disease (Streamlit)")

    meta = load_metadata()
    cols_override = load_columns()

    st.sidebar.header("Modelos disponibles")
    models = find_models()
    if not models:
        st.sidebar.warning("No se encontraron archivos .pkl ni .joblib en este directorio. Copie sus modelos aquí.")
    selected = st.sidebar.selectbox("Seleccionar modelo (.pkl / .joblib)", options=["-- Ninguno --"] + models)

    st.sidebar.markdown("---")
    st.sidebar.markdown("Coloque los archivos de modelo en la misma carpeta que `app.py`.")

    values = build_input_ui(meta)

    if st.button("Predecir"):
        if selected and selected != "-- Ninguno --":
            model = load_model(selected)
            if model is None:
                st.error("No se pudo cargar el modelo seleccionado.")
                return
            X = make_dataframe(values, meta, cols_override=cols_override)
            st.write("Entrada procesada:")
            st.dataframe(X)
            predict_and_display(model, X, meta)
        else:
            st.error("Seleccione un modelo válido desde la barra lateral.")


if __name__ == "__main__":
    main()
