import streamlit as st
import os
from google import genai
from google.genai import errors

# ==============================================================================
# 0. 진로 상담사 역할을 위한 시스템 지침 설정 (가장 중요한 부분!)
# ==============================================================================
SYSTEM_INSTRUCTION = (
    "당신은 친절하고 전문적인 10대 진로 상담사입니다. 사용자는 청소년이므로, "
    "쉽고 긍정적이며 구체적인 조언을 제공해야 합니다. "
    "꿈과 진로, 공부 방법, 적성 찾기 등에 대해 격려하며 도움을 주세요. "
    "어려운 전문 용어는 피하고, 항상 희망적인 어조로 답변하세요."
)

# 1. API 키 설정 및 클라이언트 초기화
# Streamlit Cloud에 배포할 때는 'GEMINI_API_KEY'라는 이름의 환경 변수(Secrets)를 사용합니다.
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    # 로컬 환경에서 키가 없거나 Streamlit Cloud Secrets에 키가 없는 경우 오류 메시지 표시
    st.error("❌ 오류: 'GEMINI_API_KEY' 환경 변수 또는 Streamlit Secret이 설정되지 않았습니다.")
    st.error("👉 사이드바의 '실행 방법' 섹션을 참고하여 API 키를 설정해주세요.")
    st.stop()

# Gemini 클라이언트 초기화
try:
    client = genai.Client(api_key=api_key)
except Exception as e:
    st.error(f"⚠️ Gemini 클라이언트 초기화 실패: {e}")
    st.stop()

# 사용할 모델 설정
MODEL_NAME = "gemini-2.5-flash"

# Streamlit UI 설정 (제목 변경)
st.set_page_config(page_title="진로 상담 제미나이 챗봇", layout="centered")
st.title("✨ 10대 진로 상담 챗봇: 진로 제미나이")
st.caption("여러분의 꿈과 적성을 찾아주는 인공지능 진로 상담사입니다.")
st.divider()

# 2. 채팅 기록 초기화
if "messages" not in st.session_state:
    # 환영 메시지 변경
    st.session_state.messages = [
        {"role": "assistant", "content": "안녕하세요! 저는 여러분의 꿈과 적성을 찾아주는 친절한 진로 상담사 제미나이입니다. 어떤 고민이 있나요? 무엇이든 이야기해주세요!"}
    ]

# 3. 채팅 기록 표시
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 4. 사용자 입력 처리
if prompt := st.chat_input("진로, 적성, 공부 방법에 대해 질문하세요..."):
    # 4-1. 사용자 메시지 기록 및 화면 표시
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 4-2. Gemini API 호출을 위한 대화 기록 준비
    history = []
    for message in st.session_state.messages:
        role_map = {"user": "user", "assistant": "model"}
        if message["role"] in role_map:
            history.append(
                {"role": role_map[message["role"]], "parts": [{"text": message["content"]}]}
            )

    # 4-3. 챗봇 응답 스트리밍
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        
        try:
            # generate_content_stream 호출 시 config에 시스템 지침을 추가!
            response_stream = client.models.generate_content_stream(
                model=MODEL_NAME,
                contents=history,
                config={"system_instruction": SYSTEM_INSTRUCTION}  # <--- 이 부분이 추가되었습니다!
            )

            for chunk in response_stream:
                if chunk.text:
                    full_response += chunk.text
                    message_placeholder.markdown(full_response + "▌") 
            
            message_placeholder.markdown(full_response)
            
        except errors.APIError as e:
            error_message = f"API 호출 중 오류가 발생했습니다: {e}"
            st.error(error_message)
            full_response = error_message
        except Exception as e:
            error_message = f"예상치 못한 오류가 발생했습니다: {e}"
            st.error(error_message)
            full_response = error_message

    # 4-4. 최종 응답을 채팅 기록에 저장
    st.session_state.messages.append({"role": "assistant", "content": full_response})

# 5. 실행 및 배포 방법 안내 (사이드바)
st.sidebar.header("실행 및 배포 방법")
st.sidebar.markdown(
    """
### 1. 라이브러리 설치
```bash
pip install streamlit google-genai
```

### 2. API 키 설정 (중요!)
Streamlit Cloud의 'Secrets' 설정에 **`GEMINI_API_KEY`**와 여러분의 API 키를 입력해주세요.

### 3. 앱 실행
```bash
streamlit run app.py
```
"""
)
