import streamlit as st
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from streamlit_folium import st_folium
import pandas as pd
import folium
from folium.plugins import MarkerCluster

# CSS & JS 코드
POPUP_SCRIPT = """
<style>
.popup {
    position: fixed;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    background: #4CAF50;
    color: white;
    padding: 30px 50px;
    border-radius: 10px;
    box-shadow: 0 0 20px rgba(0,0,0,0.2);
    z-index: 9999;
    font-size: 18px;
    animation: fadeOut 5s forwards;
}

@keyframes fadeOut {
    0% { opacity: 1; }
    90% { opacity: 1; }
    100% { opacity: 0; }
}
</style>

<script>
// 5초 후 팝업 제거
window.onload = function() {
    setTimeout(function(){
        var popup = document.querySelector('.popup');
        if(popup) popup.remove();
    }, 5000);
};
</script>
"""

@st.cache_data
def load_data():
    df = pd.read_excel('sunshade_location.xlsx')
    df = df.dropna(subset=['위도'])
    return df

def wrap_text(words, max_line_length=20):
    words = words.split()
    wrapped_text = ''
    line_length = 0
    for word in words:
        if line_length + len(word) > max_line_length:
            wrapped_text += '<br>'
            line_length = 0
        wrapped_text += word + ' '
        line_length += len(word) + 1
    return wrapped_text

def create_map(df):
    # 선택된 마커의 좌표 추출
    marker_lat = selected_df.iloc[0]['위도']
    marker_lon = selected_df.iloc[0]['경도']
    
    # 지도 생성 시 중심 좌표를 마커 위치로 설정
    map = folium.Map(
        location=[marker_lat, marker_lon], 
        zoom_start=17,  # 더 가까운 확대 수준
        min_zoom=10, 
        max_zoom=18
    )

    basemaps_vworld = {
        'VWorldBase': folium.TileLayer(
            tiles='http://api.vworld.kr/req/wmts/1.0.0./CCA5DC05-6EDE-3BE5-A2DE-582966148562/Base/{z}/{y}/{x}.png',
            attr='VWorldBase', name='VWorldBase', overlay=True, control=False, min_zoom=10)
    }
    
    basemaps_vworld['VWorldBase'].add_to(map)

    style_function = lambda x: {"fillOpacity": 0, "opacity": 0.5}
    tooltip_style = 'font-size: 13px; max-width: 500px;'
    
    for index, row in df.iterrows():
        address = wrap_text(row['설치장소명'])
        popup_html = f"""
        <table style="width:100%; border-collapse: collapse; border: 2px solid #ddd; border-radius: 5px; background-color: #f9f9f9;">
            <tr>
                <td style="border-right: 1px solid #ddd; border-bottom: 1px solid #ddd; padding: 5px;"><b>관리번호</b></td>
                <td style="border-bottom: 1px solid #ddd; padding: 5px;">{row['관리번호']}</td>
            </tr>
            <tr>
                <td style="border-right: 1px solid #ddd; border-bottom: 1px solid #ddd; padding: 5px;"><b>주&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;소</b></td>
                <td style="border-bottom: 1px solid #ddd; padding: 5px;">{address}</td>
            </tr>
        </table>
        """

        tooltip_html = f"<b>관리번호:</b> {row['관리번호']}<br>"
        
        folium.Marker(
            [row['위도'], row['경도']], 
            icon=folium.Icon(color='blue', prefix= 'fa', icon='umbrella'),
            popup=folium.Popup(popup_html, style=tooltip_style, max_width=300),
            tooltip=folium.Tooltip(tooltip_html, style=tooltip_style),
            tags=[row['읍면동']]
        ).add_to(map)

    return map

# 스타일 설정
st.markdown("""
    <style>
    .centered {
        display: flex;
        justify-content: center;
        align-items: center;
        height: 0.5vh;
    }
    .stSpinner > div > div {
        border-color: #1A9F68 !important;
    }
    </style>
    """, unsafe_allow_html=True)

def show_popup():
    st.markdown(POPUP_SCRIPT, unsafe_allow_html=True)
    st.markdown('<div class="popup">✅ 정상처리 되었습니다!</div>', unsafe_allow_html=True)

def send_email(subject, content, attached_file=None):
    sender_email = st.secrets["email"]["sender"]
    sender_password = st.secrets["email"]["password"]
    receiver_email = st.secrets["email"]["receiver"]
    
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = receiver_email
    msg['Subject'] = subject

    msg.attach(MIMEText(content, 'plain'))
    
    if attached_file is not None:
        part = MIMEApplication(attached_file.read(), Name=attached_file.name)
        part['Content-Disposition'] = f'attachment; filename="{attached_file.name}"'
        msg.attach(part)
    
    try:
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, receiver_email, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        st.error(f"메일 전송 실패: {e}")
        return False

# 메인 앱 구조
st.title("🌳 그늘막 고장 신고 시스템 🌳")
df = load_data()
param_value = st.query_params.get("value", "")
#    value = param_value
# 관리번호 입력 섹션
manage_number =  param_value
# 관리번호 입력 섹션
#manage_number = st.text_input("관리번호를 입력해주세요*", placeholder="ex) 100", help="숫자만 입력해주세요")

# 지도 표시
if manage_number:
    try:
        selected_df = df[df['관리번호'] == int(manage_number)]
        if not selected_df.empty:
            st.subheader("📌 고장난 그늘막 위치")
            st_folium(create_map(selected_df), width=1000, height=500)
        else:
            st.warning("해당 관리번호의 그늘막 정보가 없습니다.")
    except:
        st.error("지도 표시 중 오류가 발생했습니다.")

# 신고 폼 섹션
with st.form(key='report_form'):
    st.subheader("📝 고장 신고 양식")
    
    # 선택된 그늘막 정보가 있는 경우 기본값 설정
    default_location = "인천광역시 미추흘구 독정이로 95"
    if manage_number and not selected_df.empty:
        default_location = selected_df.iloc[0]['설치장소명']

    title = st.text_input("제목", value=f"{manage_number}번 그늘막 고장 신고" if manage_number else "")
    location = st.text_input("위치", value= default_location)
    content = st.text_area("고장내용", value="그늘막 파손")
    location_image = st.file_uploader("그늘막 파손 사진 업로드", type=['png', 'jpg', 'jpeg'])
    
    submitted = st.form_submit_button("📤 제출")

    if submitted:
        if not manage_number or not location or not content:
            st.warning("⚠️ 필수 항목(*)을 모두 입력해주세요!")
        else:
            email_content = f"""
            🚨 신고 접수 내용 🚨
            ► 제목: {title}
            ► 관리번호: {manage_number}
            ► 위치: {location}
            ► 고장 내용: {content}
            """
            
            if send_email(f"[고장신고] {title}", email_content, location_image):
                st.session_state.show_popup = True
                st.success(f"✅ {manage_number}번 신고가 접수되었습니다!")
                st.balloons()
            else:
                st.error("❌ 메일 전송에 실패했습니다. 다시 시도해주세요.")

# 팝업 표시
if st.session_state.get('show_popup'):
    show_popup()
    st.session_state.show_popup = False