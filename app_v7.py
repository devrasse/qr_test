import streamlit as st
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from streamlit_folium import st_folium
import pandas as pd
import folium
from PIL import Image

# 상수 정의
POPUP_DURATION = 5000  # 5초
MAP_ZOOM_LEVEL = 17
MAX_LINE_LENGTH = 20
EMAIL_TEMPLATE = """
<html>
    <body>
        <h2 style="color: #d9534f; border-bottom: 2px solid #ddd; padding-bottom: 10px;">🚨 신고 접수 내용</h2>
        <table border="1" cellpadding="10" cellspacing="0" style="border-collapse: collapse; width: 100%; max-width: 600px; font-family: Arial, sans-serif; border: 1px solid #ddd;">
            {rows}
        </table>
        <p style="margin-top: 20px; font-size: 12px; color: #777; border-top: 1px solid #eee; padding-top: 10px;">
            ※ 이 메일은 그늘막 고장 신고 시스템에서 자동으로 발송되었습니다.
        </p>
    </body>
</html>
"""

# CSS & JS 코드
POPUP_SCRIPT = f"""
<style>
.popup {{
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
    animation: fadeOut {POPUP_DURATION/1000}s forwards;
}}

@keyframes fadeOut {{
    0% {{ opacity: 1; }}
    90% {{ opacity: 1; }}
    100% {{ opacity: 0; }}
}}
</style>

<script>
setTimeout(function(){{
    var popup = document.querySelector('.popup');
    if(popup) popup.remove();
}}, {POPUP_DURATION});
</script>
"""

@st.cache_data
def load_data():
    """데이터 로드 함수"""
    df = pd.read_excel('sunshade_location.xlsx')
    return df.dropna(subset=['위도'])

def wrap_text(text, max_line_length=MAX_LINE_LENGTH):
    """텍스트를 지정된 길이에 맞게 줄바꿈 처리"""
    words = text.split()
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
    """지도 생성 함수"""
    marker_lat = df.iloc[0]['위도']
    marker_lon = df.iloc[0]['경도']
    
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

    # 마커 추가
    for _, row in df.iterrows():
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
        
        folium.Marker(
            [row['위도'], row['경도']], 
            icon=folium.Icon(color='blue', prefix='fa', icon='umbrella'),
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=f"<b>관리번호:</b> {row['관리번호']}<br>"
        ).add_to(map)

    return map

def send_email(subject, email_content, attached_file=None):
    """이메일 전송 함수"""
    sender_email = st.secrets["email"]["sender"]
    sender_password = st.secrets["email"]["password"]
    receiver_email = st.secrets["email"]["receiver"]
    
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = receiver_email
    msg['Subject'] = subject
    msg.attach(MIMEText(email_content, 'html'))
    
    if attached_file:
        part = MIMEApplication(attached_file.read(), Name=attached_file.name)
        part['Content-Disposition'] = f'attachment; filename="{attached_file.name}"'
        msg.attach(part)
    
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, receiver_email, msg.as_string())
        return True
    except Exception as e:
        st.error(f"메일 전송 실패: {e}")
        return False

def show_popup():
    """팝업 표시 함수"""
    st.markdown(POPUP_SCRIPT, unsafe_allow_html=True)
    st.markdown('<div class="popup">✅ 정상처리 되었습니다!</div>', unsafe_allow_html=True)

def main():
    """메인 애플리케이션"""
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

    st.title("🌳 그늘막 고장 신고 시스템 🌳")
    df = load_data()
    manage_number = st.query_params.get("value", "")
    # 지도 표시
    if manage_number:
        try:
            selected_df = df[df['관리번호'] == int(manage_number)]
            if not selected_df.empty:
                st.subheader("📌 고장 신고 그늘막 위치")
                st_folium(create_map(selected_df), width=1000, height=500)
            else:
                st.warning("해당 관리번호의 그늘막 정보가 없습니다.")
        except Exception as e:
            st.error(f"지도 표시 중 오류 발생: {e}")

    st.subheader("🖼️ 그늘막 고장 사진 업로드")
    location_image = st.file_uploader("그늘막 파손 사진 업로드", type=['png', 'jpg', 'jpeg'])

    if location_image:
        try:
            image = Image.open(location_image)
            st.image(image, caption="첨부된 고장 사진", use_column_width=True)
        except:
            st.error("이미지를 미리보기할 수 없습니다.")
    # 📸 파일 업로더 (폼 밖)


    # 신고 폼
    with st.form(key='report_form'):
        st.subheader("📝 고장 신고 양식")
        
        default_location = "인천광역시 미추흘구 독정이로 95"
        if manage_number and not selected_df.empty:
            default_location = selected_df.iloc[0]['설치장소명']

        title = st.text_input("제목", value=f"{manage_number}번 그늘막 고장 신고" if manage_number else "")
        location = st.text_input("위치", value=default_location)
        content = st.text_area("고장내용", value="그늘막 파손")
        #location_image = st.file_uploader("그늘막 파손 사진 업로드", type=['png', 'jpg', 'jpeg'])

        address = selected_df.iloc[0]['주소']

        if st.form_submit_button("📤 제출"):
            if not manage_number or not location or not content:
                st.warning("⚠️ 필수 항목(*)을 모두 입력해주세요!")
            else:
                rows = [
                    ("제목", title),
                    ("관리번호", manage_number),
                    ("위치", location),
                    ("주소", address),
                    ("고장 내용", content),
                    ("접수 시간", pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S'))
                ]
                
                email_content = EMAIL_TEMPLATE.format(
                    rows="\n".join(
                        f'<tr><td style="border: 1px solid #ddd; padding: 10px;"><strong>{key}</strong></td>'
                        f'<td style="border: 1px solid #ddd; padding: 10px;">{value}</td></tr>'
                        for key, value in rows
                    )
                )
                
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

if __name__ == "__main__":
    main()