import streamlit as st
import pandas as pd
from models import (
    load_equipment, load_characteristics, load_spec_items, load_spec_values,
    save_spec_items, save_spec_values, next_id,
)
from search import search_equipment
from export import build_equipment_name, export_to_excel

st.set_page_config(page_title="Спецификация", layout="wide")
st.title("Спецификация оборудования")

equipment = load_equipment()
characteristics = load_characteristics()
spec_items = load_spec_items()
spec_values = load_spec_values()

# --- состояние: добавляем строку ---
if "draft" not in st.session_state:
    st.session_state.draft = {"equipment_id": None, "qty": 1, "unit": "шт.", "extra": "", "values": {}}

st.subheader("Добавить позицию")

# 1. Подсказка по номенклатуре
q = st.text_input("Начните вводить наименование", key="search_query")
if q:
    matches = search_equipment(q, equipment)
    if matches:
        labels = [m["название"] for m in matches]
        chosen = st.selectbox("Подсказка", options=labels)
        eq_id = next(m["id"] for m in matches if m["название"] == chosen)
        st.session_state.draft["equipment_id"] = eq_id

# 2. Если выбрано — показываем характеристики
eq_id = st.session_state.draft["equipment_id"]
if eq_id:
    eq_row = equipment[equipment["id"] == str(eq_id)].iloc[0]
    st.markdown(f"**Выбрано:** {eq_row['название']}")

    chars = characteristics[characteristics["equipment_id"] == str(eq_id)].copy()
    if not chars.empty:
        chars["sort_order"] = chars["sort_order"].astype(int)
        chars = chars.sort_values("sort_order")
        values = {}
        for _, ch in chars.iterrows():
            cid = str(ch["id"])
            ctype = ch["тип"]
            key = f"ch_{cid}"
            if ctype == "flag":
                if st.checkbox(ch["вывод_для_flag"] or ch["название"], key=key):
                    values[cid] = ("1", False)
            elif ctype == "list":
                opts = [o.strip() for o in ch["варианты"].split(";") if o.strip()]
                opts = ["—"] + opts + ["другое"]
                sel = st.selectbox(ch["название"], opts, key=key)
                if sel == "другое":
                    custom = st.text_input(f"{ch['название']} (своё)", key=key + "_custom")
                    if custom:
                        values[cid] = (custom, True)
                elif sel != "—":
                    values[cid] = (sel, False)
            elif ctype == "number":
                n = st.text_input(f"{ch['название']} (число)", key=key)
                if n.strip():
                    values[cid] = (n.strip(), False)
            elif ctype == "text":
                t = st.text_input(ch["название"], key=key)
                if t.strip():
                    values[cid] = (t.strip(), False)
        st.session_state.draft["values"] = values

    st.session_state.draft["qty"] = st.number_input("Кол-во", min_value=1, value=int(st.session_state.draft["qty"]))
    st.session_state.draft["unit"] = st.text_input("Ед. изм.", value=st.session_state.draft["unit"])
    st.session_state.draft["extra"] = st.text_input("Дополнительные параметры (свободный текст)", value=st.session_state.draft["extra"])

    if st.button("Добавить в спецификацию"):
        d = st.session_state.draft
        new_id = next_id(spec_items)
        new_row = pd.DataFrame([{
            "id": new_id,
            "equipment_id": d["equipment_id"],
            "кол-во": str(d["qty"]),
            "ед.изм.": d["unit"],
            "доп_текст": d["extra"],
        }])
        spec_items = pd.concat([spec_items, new_row], ignore_index=True)
        save_spec_items(spec_items)

        if d["values"]:
            vrows = []
            for cid, (val, is_custom) in d["values"].items():
                vrows.append({
                    "spec_item_id": new_id,
                    "characteristic_id": cid,
                    "значение": val,
                    "is_custom": "1" if is_custom else "0",
                })
            spec_values = pd.concat([spec_values, pd.DataFrame(vrows)], ignore_index=True)
            save_spec_values(spec_values)

        st.session_state.draft = {"equipment_id": None, "qty": 1, "unit": "шт.", "extra": "", "values": {}}
        st.rerun()

# --- таблица спецификации ---
st.subheader("Текущая спецификация")

if spec_items.empty:
    st.info("Пока пусто.")
else:
    rows = []
    for i, (_, item) in enumerate(spec_items.iterrows(), start=1):
        eq = equipment[equipment["id"] == item["equipment_id"]]
        eq_name = eq.iloc[0]["название"] if not eq.empty else "???"
        chars = characteristics[characteristics["equipment_id"] == item["equipment_id"]].copy()
        if not chars.empty:
            chars["sort_order"] = chars["sort_order"].astype(int)
            chars = chars.sort_values("sort_order")
        vals = spec_values[spec_values["spec_item_id"] == item["id"]]
        vmap = {r["characteristic_id"]: (r["значение"], r["is_custom"] == "1") for _, r in vals.iterrows()}
        full_name = build_equipment_name(eq_name, chars, vmap, item["доп_текст"])
        rows.append({
            "№ п/п": i,
            "Наименование оборудования": full_name,
            "Кол-во": item["кол-во"],
            "Ед. измер": item["ед.изм."],
            "_id": item["id"],
        })

    df_view = pd.DataFrame(rows)
    st.dataframe(df_view.drop(columns=["_id"]), use_container_width=True)

    # удаление
    del_id = st.selectbox("Удалить позицию №", options=[r["№ п/п"] for r in rows])
    if st.button("Удалить"):
        target = next(r["_id"] for r in rows if r["№ п/п"] == del_id)
        spec_items = spec_items[spec_items["id"] != target]
        save_spec_items(spec_items)
        spec_values = spec_values[spec_values["spec_item_id"] != target]
        save_spec_values(spec_values)
        st.rerun()

    if st.button("Экспорт в Excel"):
        path = export_to_excel(rows)
        with open(path, "rb") as f:
            st.download_button("Скачать спецификацию", f, file_name="specification.xlsx")