import streamlit as st
import pandas as pd
import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from streamlit_folium import st_folium
import folium

scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
client = gspread.authorize(creds)
sheet = client.open("Final").sheet1

class Complaint:
    def __init__(self, author, content, coordinates, date):
        self.author = author
        self.content = content
        self.coordinates = coordinates
        self.date = date

    def __str__(self):
        return f"{self.date} - {self.author} @ {self.coordinates}: {self.content}"

    def to_dict(self):
        return {
            "Author": self.author,
            "Content": self.content,
            "Lat": self.coordinates[0],
            "Lon": self.coordinates[1],
            "Date": self.date.strftime("%Y-%m-%d")
        }

st.title("📌 동네 민원 신고 플랫폼")
st.sidebar.header("민원 작성")
author = st.sidebar.text_input("작성자")
content = st.sidebar.text_area("내용")
date = st.sidebar.date_input("날짜", value=datetime.date.today())

if 'coords' not in st.session_state:
    st.session_state.coords = None

st.subheader("🗺️ 민원 위치 선택")
m = folium.Map(location=[37.5665, 126.9780], zoom_start=12)
m.add_child(folium.LatLngPopup())
result = st_folium(m, width=700, height=500)

if result["last_clicked"]:
    lat = result["last_clicked"]["lat"]
    lon = result["last_clicked"]["lng"]
    st.session_state.coords = (lat, lon)
    st.success(f"선택된 위치: {st.session_state.coords}")

if st.sidebar.button("민원 제출"):
    if st.session_state.coords is None:
        st.warning("🗺️ 지도를 클릭하여 위치를 먼저 선택하세요.")
    elif not author or not content:
        st.warning("✏️ 작성자와 내용을 모두 입력해주세요.")
    else:
        comp = Complaint(author, content, st.session_state.coords, date)
        st.success("✅ 민원이 접수되었습니다.")
        st.write(str(comp))
        try:
            sheet.append_row(list(comp.to_dict().values()))
            st.success("✅ Google Sheet에 업로드 완료되었습니다.")
        except Exception as e:
            st.error(f"❌ 업로드 실패: {e}")

records = sheet.get_all_records()
df = pd.DataFrame(records)

if not df.empty:
    st.subheader("📍 등록된 민원 보기")
    fmap = folium.Map(location=[37.5665, 126.9780], zoom_start=12)
    for _, row in df.iterrows():
        folium.Marker(
            location=[row["Lat"], row["Lon"]],
            popup=f"{row['Date']}<br>{row['Author']}<br>{row['Content']}",
            tooltip=row['Author']
        ).add_to(fmap)
    st_folium(fmap, width=700, height=500)

st.sidebar.header("작성자 조회")
query_author = st.sidebar.text_input("작성자 이름 입력")
if st.sidebar.button("조회"):
    result = df[df["Author"] == query_author]
    st.subheader(f"🔍 {query_author}님의 민원 조회 결과")
    st.write(result)

# -------------------- 날짜별 민원 통계 --------------------
if not df.empty:
    st.subheader("📊 날짜별 민원 수 통계")
    date_counts = df["Date"].value_counts().sort_index()
    st.bar_chart(date_counts)