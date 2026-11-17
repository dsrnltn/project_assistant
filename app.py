import streamlit as st
import pandas as pd
from models import load_equipment, load_characteristics
from search import search_equipment
from export import build_equipment_name, export_to_excel

st.set_page_config(page_title="Спецификация", layout="wide")
st.title("Спецификация оборудования")

equipment = load_equipment()
characteristics = load_characteristics()

# --- состояние ---
if "spec" not in st.session_state:
    st.session_state.spec = []
if "edit_idx" not in st.session_state:
    st.session_state.edit_idx = None
if "draft" not in st.session_state:
    st.session_state.draft = {"equipment_id": None, "qty": 1, "unit": "шт.", "extra": "", "values": {}}
if "reset_search" not in st.session_state:
    st.session_state.reset_search = False

def fresh_draft():
    return {"equipment_id": None, "qty": 1, "unit": "шт.", "extra": "", "values": {}}

def default_values(eq_id):
    chars = characteristics[characteristics["equipment_id"] == str(eq_id)].copy()
    if chars.empty:
        return {}
    chars["sort_order"] = chars["sort_order"].astype(int)
    chars = chars.sort_values("sort_order")
    vals = {}
    for _, ch in chars.iterrows():
        d = str(ch.get("по_умолчанию", "")).strip()
        if not d:
            continue
        cid = str(ch["id"])
        if ch["тип"] == "flag" and d in ("1", "0"):
            if d == "1":
                vals[cid] = ("1", False)
        else:
            vals[cid] = (d, False)
    return vals

# --- сброс поиска ДО отрисовки виджета ---
if st.session_state.reset_search:
    st.session_state.search_input = ""
    st.session_state.reset_search = False

# --- форма добавления/редактирования ---
is_edit = st.session_state.edit_idx is not None
st.subheader("Редактировать позицию" if is_edit else "Добавить позицию")

if is_edit:
    cur = st.session_state.spec[st.session_state.edit_idx]
    if st.session_state.draft["equipment_id"] != cur["equipment_id"]:
        st.session_state.draft = {
            "equipment_id": cur["equipment_id"],
            "qty": cur["qty"],
            "unit": cur["unit"],
            "extra": cur["extra"],
            "values": dict(cur["values"]),
        }

q = st.text_input("Начните вводить наименование", key="search_input")

if q:
    matches = search_equipment(q, equipment)
    if matches:
        labels = [m["название"] for m in matches]
        chosen = st.selectbox("Подсказка", options=labels)
        eq_id = next(m["id"] for m in matches if m["название"] == chosen)
        if st.session_state.draft["equipment_id"] != eq_id:
            st.session_state.draft["equipment_id"] = eq_id
            st.session_state.draft["values"] = default_values(eq_id)

eq_id = st.session_state.draft["equipment_id"]
if eq_id:
    eq_row = equipment[equipment["id"] == str(eq_id)].iloc[0]
    st.markdown(f"**Выбрано:** {eq_row['название']}")

    chars = characteristics[characteristics["equipment_id"] == str(eq_id)].copy()
    values = dict(st.session_state.draft["values"])
    if not chars.empty:
        chars["sort_order"] = chars["sort_order"].astype(int)
        chars = chars.sort_values("sort_order")
        for _, ch in chars.iterrows():
            cid = str(ch["id"])
            ctype = ch["тип"]
            key = f"ch_{cid}"
            cur_val = values.get(cid, (None, False))[0]

            if ctype == "flag":
                checked = st.checkbox(ch["вывод_для_flag"] or ch["название"],
                                      value=(cur_val == "1"), key=key)
                if checked:
                    values[cid] = ("1", False)
                else:
                    values.pop(cid, None)
            elif ctype == "list":
                opts = [o.strip() for o in ch["варианты"].split("|") if o.strip()]
                options = ["—"] + opts + ["другое"]
                idx = options.index(cur_val) if cur_val in options else 0
                sel = st.selectbox(ch["название"], options, index=idx, key=key)
                if sel == "другое":
                    custom = st.text_input(f"{ch['название']} (своё)", key=key + "_custom")
                    if custom:
                        values[cid] = (custom, True)
                    else:
                        values.pop(cid, None)
                elif sel != "—":
                    values[cid] = (sel, False)
                else:
                    values.pop(cid, None)
            elif ctype == "number":
                n = st.text_input(f"{ch['название']} (число)", value=cur_val or "", key=key)
                if n.strip():
                    values[cid] = (n.strip(), False)
                else:
                    values.pop(cid, None)
            elif ctype == "text":
                t = st.text_input(ch["название"], value=cur_val or "", key=key)
                if t.strip():
                    values[cid] = (t.strip(), False)
                else:
                    values.pop(cid, None)

    st.session_state.draft["values"] = values
    st.session_state.draft["qty"] = st.number_input("Кол-во", min_value=1,
                                                    value=int(st.session_state.draft["qty"]))
    st.session_state.draft["unit"] = st.text_input("Ед. изм.", value=st.session_state.draft["unit"])
    st.session_state.draft["extra"] = st.text_input("Дополнительные параметры", value=st.session_state.draft["extra"])

    col1, col2 = st.columns(2)
    if col1.button("Сохранить" if is_edit else "Добавить в спецификацию"):
        d = st.session_state.draft
        item = {
            "equipment_id": d["equipment_id"],
            "qty": int(d["qty"]),
            "unit": d["unit"],
            "extra": d["extra"],
            "values": dict(d["values"]),
        }
        if is_edit:
            st.session_state.spec[st.session_state.edit_idx] = item
            st.session_state.edit_idx = None
        else:
            st.session_state.spec.append(item)
        st.session_state.draft = fresh_draft()
        st.session_state.reset_search = True
        st.rerun()
    if is_edit and col2.button("Отмена"):
        st.session_state.edit_idx = None
        st.session_state.draft = fresh_draft()
        st.session_state.reset_search = True
        st.rerun()

# --- таблица спецификации ---
st.subheader("Текущая спецификация")

if not st.session_state.spec:
    st.info("Пока пусто.")
else:
    rows = []
    for i, item in enumerate(st.session_state.spec, start=1):
        eq = equipment[equipment["id"] == item["equipment_id"]]
        eq_name = eq.iloc[0]["название"] if not eq.empty else "???"
        chars = characteristics[characteristics["equipment_id"] == item["equipment_id"]].copy()
        if not chars.empty:
            chars["sort_order"] = chars["sort_order"].astype(int)
            chars = chars.sort_values("sort_order")
        full_name = build_equipment_name(eq_name, chars, item["values"], item["extra"])
        rows.append({
            "idx": i - 1,
            "№ п/п": i,
            "Наименование оборудования": full_name,
            "Кол-во": item["qty"],
            "Ед. измер": item["unit"],
        })

    df_view = pd.DataFrame(rows)
    st.dataframe(
        df_view[["№ п/п", "Наименование оборудования", "Кол-во", "Ед. измер"]],
        use_container_width=True,
        column_config={
            "Наименование оборудования": st.column_config.TextColumn(width="large"),
        },
        hide_index=True,
    )

    col1, col2, col3 = st.columns(3)
    with col1:
        edit_no = st.selectbox("Редактировать №", [r["№ п/п"] for r in rows], key="edit_sel")
        if st.button("Редактировать"):
            st.session_state.edit_idx = edit_no - 1
            st.session_state.draft = fresh_draft()
            st.rerun()
    with col2:
        del_no = st.selectbox("Удалить №", [r["№ п/п"] for r in rows], key="del_sel")
        if st.button("Удалить"):
            st.session_state.spec.pop(del_no - 1)
            st.rerun()
    with col3:
        fname = st.text_input("Имя файла", value="specification", key="fname")
        if st.button("Подготовить Excel"):
            path = export_to_excel(rows, path=f"{fname}.xlsx")
            with open(path, "rb") as f:
                st.download_button("Скачать", f, file_name=f"{fname}.xlsx")