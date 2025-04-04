# 시안_app.py
import streamlit as st
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication

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

def show_popup():
    # 팝업 HTML과 스크립트 주입
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

st.title("🌳 그늘막 고장 신고 시스템")

#value = st.query_params.get("value", "기본값")  # 기본값은 옵션

with st.form(key='report_form'):
    value = st.query_params.get("value", "기본값")  # 기본값은 옵션
    #value = st.text_input("번호*", placeholder="ex) 100", help="숫자만 입력해주세요")
    title = st.text_input("제목", value=f"{value}번 그늘막 고장 신고")
    manage_num = st.text_input("관리번호", value=value)
    location = st.text_input("위치", value="인천광역시 미추흘구 독정이로 95")
    content = st.text_area("고장내용", value="그늘막 파손")
    location_image = st.file_uploader("위치도 이미지 업로드", type=['png', 'jpg', 'jpeg'])    
    submitted = st.form_submit_button("📤 제출")
    
    if submitted:
        # 유효성 검사
        if not value or not location or not content:
            st.warning("⚠️ 필수 항목(*)을 모두 입력해주세요!")
        else:
            show_popup()
            
            email_content = f"""
            🚨 신고 접수 내용 🚨
            ► 제목: {title}
            ► 관리번호: {manage_num}
            ► 위치: {location}
            ► 고장 내용: {content}
            """
            
            if send_email(f"[고장신고] {title}", email_content, location_image):
                st.success(f"✅ {value}번 신고가 접수되었습니다!")
                st.balloons()
            else:
                st.error("❌ 메일 전송에 실패했습니다. 다시 시도해주세요.")