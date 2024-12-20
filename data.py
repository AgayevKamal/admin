import streamlit as st
import pandas as pd
from google.oauth2.service_account import Credentials
import gspread

# Düzgün scope-ları təyin edin
SCOPES = ['https://www.googleapis.com/auth/spreadsheets',  # Google Sheets üçün
          'https://www.googleapis.com/auth/drive']         # Google Drive üçün

# JSON faylını oxuyun və scope-ları əlavə edin
credentials = Credentials.from_service_account_file(
    "winter-return-445318-f6-0db16e54b8c9.json", 
    scopes=SCOPES
)

# Google Sheets API ilə autentikasiya
client = gspread.authorize(credentials)

# Faylın ID-sini istifadə edin
spreadsheet_id = "1uIIf9cvgkJwacX0moWjVPLDCDI1jXHYgM8f3UHFkjb8"  # Faylın ID-sini bura daxil edin

# Sheetin adını düzgün yazın
sheet = client.open_by_key(spreadsheet_id).worksheet("sheet1")  # Faylınızdakı səhifənin adı

# **Session State** istifadə edirik ki, yalnız bir dəfə DataFrame-i saxlayaq
if 'df' not in st.session_state:
    # İlk dəfə işlədikdə DataFrame yaradılır
    data = sheet.get_all_values()
    df = pd.DataFrame(data[1:], columns=data[0])  # İlk sətir başlıq kimi qəbul edilir
    st.session_state.df = df
else:
    # Hər dəfə yenilədikdə məlumatları yenidən əldə et
    data = sheet.get_all_values()
    df = pd.DataFrame(data[1:], columns=data[0])  # İlk sətir başlıq kimi qəbul edilir
    st.session_state.df = df

# İlk sütunu çıxarırıq
df_display = st.session_state.df.iloc[:, 1:]

# Streamlit-də məlumatları vizuallaşdırın
if df_display.empty:
    st.write("Sheet boşdur!")
else:
    st.write("Databaza:")
    # Tam genişlikdə cədvəli göstərmək üçün use_container_width=True istifadə edirik
    st.dataframe(df_display, use_container_width=True)  # Tam genişlikdə göstərmək

    # Sidebar daxilində seçimlər
    action = st.sidebar.radio("Əməliyyat seçin:", ("Yeni sətir əlavə et", "Redaktə et"))

    # Yeni sətir əlavə etmə
    if action == "Yeni sətir əlavə et":
        # Yeni sətir üçün inputlar
        new_row = {}
        with st.sidebar.form(key='add_form'):
            for column in df.columns[1:]:  # İlk sütunu keçirik
                new_value = st.text_input(f"{column} üçün yeni dəyər:", key=f"add_{column}_input")
                new_row[column] = new_value

            # "Save" düyməsi
            submit_button = st.form_submit_button("Save")
            if submit_button:
                # Yeni sətiri mövcud DataFrame-ə əlavə edirik
                st.session_state.df = pd.concat([st.session_state.df, pd.DataFrame([new_row])], ignore_index=True)

                # Yeni sətiri Google Sheets-ə yazmaq
                sheet.append_row(list(new_row.values()))

                st.write("Yeni sətir əlavə edildi!")

                # DataFrame dərhal yenilənir, əlavə etmə sonrası yeniləməyə ehtiyac yoxdur
                st.experimental_rerun()  # Bu metod tətbiqi avtomatik yeniləyəcək

    # Mövcud sətiri redaktə etmək
    elif action == "Redaktə et":
        # Redaktə etmək istədiyiniz sətiri seçin
        row_idx = st.sidebar.number_input("Redaktə etmək istədiyiniz satırın indeksini daxil edin (0-dan başlayır):", min_value=0, max_value=len(st.session_state.df)-1)
        column_name = st.sidebar.selectbox("Dəyişmək istədiyiniz sütunu seçin:", df.columns[1:])  # İlk sütunu keçirik
        new_value = st.sidebar.text_input(f"{column_name} üçün yeni dəyər:", value=st.session_state.df.iloc[row_idx][column_name])

        # "Save" düyməsi
        submit_button = st.sidebar.button("Dəyişiklikləri tətbiq et")
        
        if submit_button:
            # Redaktə edilən hüceyrəni mövcud DataFrame-də dəyişdiririk
            st.session_state.df.at[row_idx, column_name] = new_value

            # Dəyişiklikləri Google Sheets-ə yazmaq
            sheet.update_cell(row_idx + 2, st.session_state.df.columns.get_loc(column_name) + 1, new_value)

            st.write("Dəyişikliklər saxlanıldı!")

            # DataFrame dərhal yenilənir, redaktə sonrası yeniləməyə ehtiyac yoxdur
            st.experimental_rerun()  # Bu metod tətbiqi avtomatik yeniləyəcək
