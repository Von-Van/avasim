from typing import Dict, Any
import json
import streamlit as st
from character import Character, Item, default_slots
from equipment_data import sample_equipment
from phase2.ui import phase2_ui

st.set_page_config(page_title="AvaSim — Character Builder", layout="wide")

# --- Initialize session state ---
if "char" not in st.session_state:
    st.session_state.char = Character.default()

if "presets" not in st.session_state:
    # simple in-memory presets store (name -> character dict)
    st.session_state.presets = {}

char: Character = st.session_state.char

st.title("AvaSim — Character Builder")
st.markdown(
    "Build and save characters for the simulator. Use the sidebar to edit info, stats, equipment, "
    "or to import/export character files. Phase 2 combat area is below when ready."
)

menu = st.sidebar.radio("Menu", ("Info", "Stats", "Equipment", "Phase 2 (placeholder)"))

# Save / Load controls
with st.sidebar.expander("Save / Load Character", expanded=True):
    st.write("Download your current character to a JSON file, or upload one to restore it.")
    json_payload = char.to_json()
    download_filename = f"{(char.name or 'character').replace(' ', '_')}.json"
    st.download_button(
        label="Download character (.json)",
        data=json_payload,
        file_name=download_filename,
        mime="application/json",
    )

    uploaded = st.file_uploader("Upload character JSON to load", type=["json"])
    if uploaded:
        try:
            payload = json.load(uploaded)
            st.session_state.char = Character.from_dict(payload)
            char = st.session_state.char
            st.success(f"Loaded character '{char.name or 'Unnamed'}'\n")
            st.experimental_rerun()
        except Exception as e:
            st.error(f"Failed to load character: {e}")

    st.markdown("---")
    st.write("Presets (in this browser session)")
    preset_name = st.text_input("Preset name", value="MyPreset")
    colp1, colp2 = st.columns([1, 1])
    with colp1:
        if st.button("Save preset"):
            if not preset_name:
                st.error("Enter a name for the preset.")
            else:
                st.session_state.presets[preset_name] = char.to_dict()
                st.success(f"Saved preset '{preset_name}'")
    with colp2:
        if st.button("Save & Download preset"):
            if not preset_name:
                st.error("Enter a name for the preset.")
            else:
                st.session_state.presets[preset_name] = char.to_dict()
                st.download_button(
                    label=f"Download preset '{preset_name}'",
                    data=json.dumps(char.to_dict(), indent=2),
                    file_name=f"{preset_name.replace(' ', '_')}.json",
                    mime="application/json",
                )

    if st.session_state.presets:
        load_choice = st.selectbox("Load preset", options=["(select)"] + list(st.session_state.presets.keys()))
        if load_choice and load_choice != "(select)":
            if st.button("Load selected preset"):
                st.session_state.char = Character.from_dict(st.session_state.presets[load_choice])
                st.success(f"Loaded preset '{load_choice}'")
                st.experimental_rerun()

    st.markdown("---")
    if st.button("Reset to richer default character"):
        st.session_state.char = Character.default()
        st.success("Reset to default character")
        st.experimental_rerun()

# --- Info panel ---
if menu == "Info":
    st.header("Character Info")
    col1, col2 = st.columns([2, 1])
    with col1:
        name = st.text_input("Name", value=char.name)
        char.name = name
        notes = st.text_area("Notes", value=char.notes, height=140)
        char.notes = notes
    with col2:
        level = st.number_input("Level", min_value=1, max_value=99, value=char.level)
        char.level = int(level)
        char_class = st.text_input("Class", value=char.char_class)
        char.char_class = char_class
        race = st.text_input("Race", value=char.race)
        char.race = race

    st.markdown("---")
    st.subheader("Summary")
    st.json(char.to_summary())

# --- Stats panel ---
elif menu == "Stats":
    st.header("Base Stats")
    st.write("Adjust base attributes. Green bars show effective stat (base + equipment bonuses).")
    stats = char.stats.copy()
    cols = st.columns(4)
    stat_names = list(stats.keys())
    for i, name in enumerate(stat_names):
        with cols[i % 4]:
            val = st.number_input(name.capitalize(), min_value=0, max_value=999, value=stats[name])
            stats[name] = int(val)
    char.stats = stats

    st.markdown("Effective stats (base + equipment):")
    eff = char.effective_stats()
    bs = st.columns(len(eff))
    # visual bar and numeric
    for i, (k, v) in enumerate(eff.items()):
        with bs[i]:
            st.metric(label=k.capitalize(), value=v)
            # display a lightweight progress bar normalized to 100 for quick visual comparison
            pct = min(1.0, v / 100.0)
            st.progress(pct)

# --- Equipment panel ---
elif menu == "Equipment":
    st.header("Equipment")
    st.write("Equip sample items or create custom items. Only compatible sample items are shown per slot.")
    col1, col2 = st.columns([1, 2])
    with col1:
        slot = st.selectbox("Slot", options=default_slots, index=0)
        # only show sample items that fit the chosen slot
        slot_samples = {k: v for k, v in sample_equipment.items() if v.slot == slot}
        equip_choices = ["(unequip)"] + ["[sample] " + k for k in slot_samples.keys()] + ["(custom)"]
        choice = st.selectbox("Choose item", options=equip_choices)

        if choice.startswith("[sample]"):
            key = choice.replace("[sample] ", "")
            item = sample_equipment[key]
            st.write("Selected sample item:")
            st.write(f"Name: {item.name}")
            st.write(f"Bonuses: {item.bonuses}")
            st.write(f"{item.description}")
            if st.button("Equip sample item"):
                char.equip(slot, item)
                st.success(f"Equipped {item.name} in {slot}")
        elif choice == "(unequip)":
            if st.button("Unequip"):
                char.unequip(slot)
                st.success(f"Unequipped {slot}")
        elif choice == "(custom)":
            with st.form(key="custom_item"):
                name = st.text_input("Item name", value="Custom Item")
                str_bonus = st.number_input("Strength bonus", value=0)
                dex_bonus = st.number_input("Dexterity bonus", value=0)
                int_bonus = st.number_input("Intelligence bonus", value=0)
                vit_bonus = st.number_input("Vitality bonus", value=0)
                submit = st.form_submit_button("Create & Equip")
                if submit:
                    custom = Item(
                        name=name,
                        slot=slot,
                        bonuses={"strength": int(str_bonus), "dexterity": int(dex_bonus),
                                 "intelligence": int(int_bonus), "vitality": int(vit_bonus)},
                        description="Custom item created in app",
                    )
                    char.equip(slot, custom)
                    st.success(f"Equipped custom item '{name}' in {slot}")

    with col2:
        st.subheader("Equipped")
        eq_rows = char.equipment_table()
        st.table(eq_rows)

        st.subheader("Equipment Bonuses (aggregated)")
        st.json(char.aggregated_equipment_bonuses())

        st.subheader("Effective Stats (base + equipment)")
        st.table(char.effective_stats())

# --- Phase 2 integration ---
elif menu == "Phase 2 (placeholder):"
    # Delegate to the phase2 UI integration
    phase2_ui()

st.sidebar.markdown("---")
st.sidebar.write("AvaSim · Streamlit UI")