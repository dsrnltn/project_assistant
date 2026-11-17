import pandas as pd

def build_equipment_name(equipment_name: str, char_rows, value_map: dict, extra_text: str = "") -> str:
    """
    char_rows: строки characteristics.csv для данной номенклатуры (отсортированы по sort_order)
    value_map: {characteristic_id: (значение, is_custom)}
    """
    parts = []
    for _, ch in char_rows.iterrows():
        cid = str(ch["id"])
        if cid not in value_map:
            continue
        val, is_custom = value_map[cid]
        if not val:
            continue
        ctype = ch["тип"]
        if ctype == "flag":
            parts.append(ch["вывод_для_flag"] or ch["название"])
        else:
            parts.append(f"{ch['название']} {val}" if ctype == "number" else f"{ch['название']} – {val}")
    if extra_text:
        parts.append(extra_text)
    if not parts:
        return equipment_name
    return f"{equipment_name} ({', '.join(parts)})"

def export_to_excel(rows, path="specification.xlsx"):
    """
    rows: list[dict] с ключами № п/п, Наименование оборудования, Кол-во, Ед. измер
    """
    df = pd.DataFrame(rows, columns=["№ п/п", "Наименование оборудования", "Кол-во", "Ед. измер"])
    df.to_excel(path, index=False)
    return path