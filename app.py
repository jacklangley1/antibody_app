# ================================
# Antibody Panel Manager (Streamlit)
# ================================

import streamlit as st
import pandas as pd
from datetime import datetime
import json

st.set_page_config(
    page_title="Antibody Panel Manager",
    layout="wide"
)

# -------------------------------------------------
# Session State Initialization
# -------------------------------------------------
def init_state():
    if "user" not in st.session_state:
        st.session_state.user = None

    if "inventory" not in st.session_state:
        st.session_state.inventory = [
            {
                "id": 1,
                "antigen": "CD3",
                "clone": "UCHT1",
                "metal": "170Er",
                "concentration": 0.5,
                "volumePerTest": 2.0,
                "stockVolume": 500.0,
                "alertThreshold": 50.0,
                "stainType": "Extracellular",
            },
            {
                "id": 2,
                "antigen": "CD4",
                "clone": "RPA-T4",
                "metal": "145Nd",
                "concentration": 0.5,
                "volumePerTest": 2.0,
                "stockVolume": 450.0,
                "alertThreshold": 50.0,
                "stainType": "Extracellular",
            },
            {
                "id": 3,
                "antigen": "CD8",
                "clone": "SK1",
                "metal": "146Nd",
                "concentration": 0.5,
                "volumePerTest": 2.0,
                "stockVolume": 35.0,
                "alertThreshold": 50.0,
                "stainType": "Intracellular",
            },
        ]

    if "selected_panel" not in st.session_state:
        st.session_state.selected_panel = []

    if "saved_panels" not in st.session_state:
        st.session_state.saved_panels = []

    if "history" not in st.session_state:
        st.session_state.history = []

    if "templates" not in st.session_state:
        st.session_state.templates = []

init_state()

# -------------------------------------------------
# Helper Functions
# -------------------------------------------------
def calculate_volume(ab, cell_count):
    base = ab["volumePerTest"]
    if ab.get("stainType") == "Intracellular":
        base *= 0.2
    return base * (cell_count / 4.0)

def get_inventory_df():
    return pd.DataFrame(st.session_state.inventory)

# -------------------------------------------------
# Login Screen
# -------------------------------------------------
if not st.session_state.user:
    st.title("Antibody Panel Manager")
    name = st.text_input("Enter your name to continue")
    if st.button("Continue") and name.strip():
        st.session_state.user = name.strip()
        st.rerun()
    st.stop()

# -------------------------------------------------
# Sidebar Navigation
# -------------------------------------------------
st.sidebar.success(f"Logged in as {st.session_state.user}")

page = st.sidebar.radio(
    "Navigation",
    [
        "Build Panel",
        "Inventory",
        "Saved Panels",
        "History",
        "Templates",
    ],
)

# -------------------------------------------------
# BUILD PANEL
# -------------------------------------------------
if page == "Build Panel":
    st.header("Build Panel")

    left, right = st.columns([3, 1])

    # -------- Left: Antibody Selection --------
    with left:
        search = st.text_input("Search antibodies (antigen / metal)")
        for ab in st.session_state.inventory:
            if (
                search.lower() in ab["antigen"].lower()
                or search.lower() in ab["metal"].lower()
            ):
                is_selected = ab in st.session_state.selected_panel
                checked = st.checkbox(
                    f"{ab['antigen']} ({ab['metal']})",
                    value=is_selected,
                    key=f"chk_{ab['id']}",
                )
                if checked and ab not in st.session_state.selected_panel:
                    st.session_state.selected_panel.append(ab)
                if not checked and ab in st.session_state.selected_panel:
                    st.session_state.selected_panel.remove(ab)

    # -------- Right: Summary --------
    with right:
        panel_name = st.text_input("Panel name")
        cell_count = st.number_input(
            "Cell count (millions)", value=4.0, min_value=0.1
        )

        st.subheader("Panel Summary")

        if not st.session_state.selected_panel:
            st.info("No antibodies selected")
        else:
            for ab in st.session_state.selected_panel:
                vol = calculate_volume(ab, cell_count)
                st.write(
                    f"**{ab['antigen']} ({ab['metal']})** → {vol:.2f} µL"
                )

        if st.button("💾 Save Panel"):
            if not panel_name:
                st.warning("Panel name required")
            else:
                st.session_state.saved_panels.append(
                    {
                        "name": panel_name,
                        "antibody_ids": [ab["id"] for ab in st.session_state.selected_panel],
                        "createdBy": st.session_state.user,
                        "createdAt": datetime.now().isoformat(),
                    }
                )
                st.success("Panel saved")

        if st.button("✓ Execute Panel"):
            if not panel_name:
                st.warning("Panel name required")
            else:
                for ab in st.session_state.selected_panel:
                    ab["stockVolume"] -= calculate_volume(ab, cell_count)

                st.session_state.history.insert(
                    0,
                    {
                        "panelName": panel_name,
                        "user": st.session_state.user,
                        "cellCount": cell_count,
                        "timestamp": datetime.now().isoformat(),
                        "antibodies": [
                            {
                                "antigen": ab["antigen"],
                                "metal": ab["metal"],
                                "volumeUsed": calculate_volume(ab, cell_count),
                            }
                            for ab in st.session_state.selected_panel
                        ],
                    },
                )

                st.session_state.selected_panel = []
                st.success("Panel executed and stock updated")
                st.rerun()

# -------------------------------------------------
# INVENTORY
# -------------------------------------------------
elif page == "Inventory":
    st.header("Inventory")

    df = get_inventory_df()
    edited_df = st.data_editor(
        df,
        num_rows="dynamic",
        use_container_width=True,
    )
    st.session_state.inventory = edited_df.to_dict("records")

    st.download_button(
        "Export Inventory (CSV)",
        edited_df.to_csv(index=False),
        "inventory.csv",
        "text/csv",
    )

# -------------------------------------------------
# SAVED PANELS
# -------------------------------------------------
elif page == "Saved Panels":
    st.header("Saved Panels")

    if not st.session_state.saved_panels:
        st.info("No saved panels")
    else:
        for p in st.session_state.saved_panels:
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(
                    f"**{p['name']}** — created by {p['createdBy']}"
                )
            with col2:
                if st.button("Load", key=f"load_{p['name']}"):
                    st.session_state.selected_panel = [
                        ab
                        for ab in st.session_state.inventory
                        if ab["id"] in p["antibody_ids"]
                    ]
                    st.rerun()

# -------------------------------------------------
# HISTORY
# -------------------------------------------------
elif page == "History":
    st.header("Execution History")

    if not st.session_state.history:
        st.info("No panels executed yet")
    else:
        st.dataframe(
            pd.DataFrame(st.session_state.history),
            use_container_width=True,
        )

# -------------------------------------------------
# TEMPLATES
# -------------------------------------------------
elif page == "Templates":
    st.header("Panel Templates")

    if st.button("Save current selection as template"):
        st.session_state.templates.append(
            {
                "name": f"Template {len(st.session_state.templates) + 1}",
                "antibody_ids": [ab["id"] for ab in st.session_state.selected_panel],
            }
        )
        st.success("Template saved")

    for t in st.session_state.templates:
        if st.button(f"Load {t['name']}"):
            st.session_state.selected_panel = [
                ab
                for ab in st.session_state.inventory
                if ab["id"] in t["antibody_ids"]
            ]
            st.rerun()
