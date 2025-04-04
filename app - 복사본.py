import streamlit as st

# # URL에서 쿼리 파라미터 추출 (예: ?value=113)
# #params = st.query_params()
# params = st.experimental_get_query_params()
# input_value = params.get("value", [None])[0]  # "value" 키가 없으면 None 반환

# URL에서 파라미터 추출 (예: ?value=100)
value = st.query_params.get("value", "기본값")  # 기본값은 옵션

# st.title("QR 파라미터 테스트")
# st.write(f"전달된 값: {value}")

# 화면에 표시
st.title("QR 코드 값 읽기 예제")

if value:
    st.success(f"QR 코드에서 전달된 값: **{value}**")
else:
    st.warning("전달된 값이 없습니다. QR 코드에 '?value=숫자'를 추가하세요.")