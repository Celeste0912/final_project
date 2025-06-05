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

if not df.empty:
    st.subheader("📊 날짜별 민원 수 통계")
    date_counts = df["Date"].value_counts().sort_index()
    st.bar_chart(date_counts)

class CommunityPost:
    def __init__(self, author, content, date):
        self.author = author
        self.content = content
        self.date = date

    def __str__(self):
        return f"{self.date} - {self.author}: {self.content}"

    def to_dict(self):
        return {
            "Author": self.author,
            "Content": self.content,
            "Date": self.date.strftime("%Y-%m-%d")
        }

class QnAPost:
    def __init__(self, author, question, answer, date):
        self.author = author
        self.question = question
        self.answer = answer
        self.date = date

    def __str__(self):
        return f"{self.date} - {self.author}: Q) {self.question} / A) {self.answer}"

    def to_dict(self):
        return {
            "Author": self.author,
            "Question": self.question,
            "Answer": self.answer,
            "Date": self.date.strftime("%Y-%m-%d")
        }

try:
    commu_sheet = client.open("Final").worksheet("Community")
except:
    commu_sheet = client.open("Final").add_worksheet(title="Community", rows="100", cols="3")
    commu_sheet.append_row(["Author", "Content", "Date"])

try:
    qna_sheet = client.open("Final").worksheet("QnA")
except:
    qna_sheet = client.open("Final").add_worksheet(title="QnA", rows="100", cols="4")
    qna_sheet.append_row(["Author", "Question", "Answer", "Date"])

st.header("커뮤니티 정보공유")
commu_author = st.text_input("작성자(커뮤니티)", key="commu_author")
commu_content = st.text_area("내용(커뮤니티)", key="commu_content")
commu_date = st.date_input("날짜(커뮤니티)", value=datetime.date.today(), key="commu_date")
if st.button("커뮤니티 글 등록"):
    if commu_author and commu_content:
        post = CommunityPost(commu_author, commu_content, commu_date)
        commu_sheet.append_row(list(post.to_dict().values()))

st.header("Q&A (질문/답변)")
qna_author = st.text_input("작성자(Q&A)", key="qna_author")
qna_question = st.text_area("질문", key="qna_question")
qna_answer = st.text_area("답변", key="qna_answer")
qna_date = st.date_input("날짜(Q&A)", value=datetime.date.today(), key="qna_date")
if st.button("Q&A 등록"):
    if qna_author and qna_question and qna_answer:
        post = QnAPost(qna_author, qna_question, qna_answer, qna_date)
        qna_sheet.append_row(list(post.to_dict().values()))

st.subheader("커뮤니티 글 목록")
commu_records = commu_sheet.get_all_records()
commu_df = pd.DataFrame(commu_records)
st.write(commu_df)

st.subheader("Q&A 목록")
qna_records = qna_sheet.get_all_records()
qna_df = pd.DataFrame(qna_records)
st.write(qna_df)
