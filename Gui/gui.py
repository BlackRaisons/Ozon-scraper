import json
from io import BytesIO

import pandas as pd
import requests
import streamlit as st

API_URL_DEFAULT = "http://127.0.0.1:8000/scrape"

st.set_page_config(page_title="Ozon Parser Pro", layout="wide", page_icon="🛒")

if "last_result" not in st.session_state:
    st.session_state.last_result = []
if "last_count" not in st.session_state:
    st.session_state.last_count = 0

st.title("🛒 Ozon Parser")
st.caption("Парарельный сбор информации со страниц")

with st.sidebar:
    st.header("Параметры")
    request_timeout = st.number_input("Timeout (сек)", min_value=30, max_value=3600, value=600, step=30)
    default_limit = st.number_input("Лимит по умолчанию", min_value=1, max_value=1000, value=100, step=10)
    max_mode_global = st.checkbox("MAX для всех ссылок (без лимита)", value=False)

    st.divider()
    st.subheader("Форматы выгрузки")
    save_json_flag = st.checkbox("JSON", value=True)
    save_csv_flag = st.checkbox("CSV", value=True)
    save_xlsx_flag = st.checkbox("XLSX", value=True)

links_input = st.text_area(
    "Ссылки Ozon (по одной в строке или через запятую)",
    height=140,
    placeholder="https://www.ozon.ru/category/...\nhttps://www.ozon.ru/category/...",
)

raw_links = [
    link.strip()
    for link in links_input.replace("\n", ",").split(",")
    if link.strip()
]

metric_col1, metric_col2, metric_col3 = st.columns(3)
metric_col1.metric("Ссылок в запросе", len(raw_links))
metric_col2.metric("Последний результат", st.session_state.last_count)


links_settings = []
if raw_links:
    st.subheader("Настройки по ссылкам")
    for idx, link in enumerate(raw_links):
        with st.expander(f"Ссылка #{idx + 1}", expanded=(idx == 0)):
            st.code(link)
            limit = st.number_input(
                "Лимит",
                min_value=1,
                max_value=1000,
                value=int(default_limit),
                key=f"limit_{idx}",
            )
            is_max = st.checkbox("MAX (без лимита)", value=max_mode_global, key=f"max_{idx}")
            links_settings.append({"url": link, "limit": None if is_max else int(limit)})

run_btn = st.button("🚀 Запустить парсинг", use_container_width=True, type="primary")

if run_btn:
    if not links_settings:
        st.warning("Добавь хотя бы одну ссылку.")
        st.stop()

    payload = {"links_settings": links_settings}

    with st.status("Выполняю парсинг...", expanded=True) as status:
        try:
            response = requests.post(API_URL_DEFAULT , json=payload, timeout=int(request_timeout))
        except Exception as e:
            st.error(f"Ошибка подключения к API: {e}")
            st.stop()

        if response.status_code != 200:
            try:
                error_json = response.json()
                detail = error_json.get("detail", response.text)
            except Exception:
                detail = response.text
            st.error(f"API error ({response.status_code}): {detail}")
            st.stop()

        try:
            result = response.json()
        except Exception:
            st.error("API вернул ответ не в JSON формате.")
            st.stop()

        if result.get("error"):
            st.error(f"Ошибка воркера: {result['error']}")
            st.stop()

        status.update(label="Парсинг завершен", state="complete")

    data = result.get("data", [])
    st.session_state.last_result = data
    st.session_state.last_count = len(data)
    st.success(f"Готово. Найдено товаров: {len(data)}")

if st.session_state.last_result:
    result_df = pd.DataFrame(st.session_state.last_result)
    tab_data, tab_json = st.tabs(["Таблица", "JSON preview"])

    with tab_data:
        st.dataframe(result_df, use_container_width=True, height=500)

    with tab_json:
        st.code(json.dumps(st.session_state.last_result[:20], ensure_ascii=False, indent=2), language="json")
        st.caption("Показаны первые 20 записей.")

    st.subheader("Скачать результат")
    dcol1, dcol2, dcol3 = st.columns(3)

    if save_json_flag:
        dcol1.download_button(
            "Download JSON",
            data=json.dumps(st.session_state.last_result, ensure_ascii=False, indent=4),
            file_name="result.json",
            mime="application/json",
            use_container_width=True,
        )

    if save_csv_flag:
        dcol2.download_button(
            "Download CSV",
            data=result_df.to_csv(index=False).encode("utf-8-sig"),
            file_name="result.csv",
            mime="text/csv",
            use_container_width=True,
        )

    if save_xlsx_flag:
        buffer = BytesIO()
        result_df.to_excel(buffer, index=False)
        buffer.seek(0)
        dcol3.download_button(
            "Download XLSX",
            data=buffer,
            file_name="result.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )