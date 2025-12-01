import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime

# --- 1. 데이터 저장/로드 관련 함수 (파일로 관리) ---
LOG_FILE = 'bitbuzz_log.csv'
CONFIG_FILE = 'bitbuzz_config.json'

# 기본 설정 (파일이 없을 때 초기값)
DEFAULT_CONFIG = {
    "employees": ["김철수", "이영희", "박지민"],
    "channels": ["숏멘토", "댓골", "겉약속근", "스트리트TMI"]
}

def load_config():
    """설정(직원, 채널 목록) 불러오기"""
    if not os.path.exists(CONFIG_FILE):
        return DEFAULT_CONFIG
    with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_config(config_data):
    """설정 저장하기"""
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config_data, f, ensure_ascii=False, indent=4)

def load_log():
    """작업 일지 불러오기"""
    if not os.path.exists(LOG_FILE):
        return pd.DataFrame(columns=["날짜", "직원명", "채널명", "제목", "링크_URL", "입력시간"])
    return pd.read_csv(LOG_FILE)

def save_log(date, name, channel, title, url):
    """작업 일지 저장하기"""
    df = load_log()
    new_data = {
        "날짜": date,
        "직원명": name,
        "채널명": channel,
        "제목": title,
        "링크_URL": url,
        "입력시간": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    new_df = pd.concat([df, pd.DataFrame([new_data])], ignore_index=True)
    new_df.to_csv(LOG_FILE, index=False)

# --- 2. 화면 구성 시작 ---
st.set_page_config(page_title="BITBUZZ 전산망 v3.0", layout="wide")
st.title("🎬 BITBUZZ 영상 제작 관리 시스템")

# 설정 데이터 로드
config = load_config()

# 탭 메뉴 만들기 (작업등록 / 현황판 / 관리자설정)
tab1, tab2, tab3 = st.tabs(["📝 작업 등록", "📊 현황판(대장)", "⚙️ 관리자 설정"])

# --- [탭 1] 작업 등록 ---
with tab1:
    st.subheader("오늘 만든 영상 기록하기")
    
    with st.form("entry_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            input_date = st.date_input("작업 날짜")
            # 설정 파일에서 불러온 직원 목록 표시
            input_name = st.selectbox("담당자 (누가 만들었나요?)", config['employees'])
        with col2:
            # 설정 파일에서 불러온 채널 목록 표시
            input_channel = st.selectbox("업로드 채널", config['channels'])
        
        input_title = st.text_input("영상 제목 (리스트에 표시될 이름)")
        input_url = st.text_input("유튜브 링크 (URL)")
        
        submit = st.form_submit_button("등록 완료")
        
        if submit:
            if input_title and input_url:
                save_log(input_date, input_name, input_channel, input_title, input_url)
                st.success(f"{input_name}님의 작업이 등록되었습니다!")
            else:
                st.error("제목과 링크를 빠짐없이 입력해주세요.")

# --- [탭 2] 현황판 ---
with tab2:
    st.subheader("실시간 제작 현황")
    df = load_log()
    
    if not df.empty:
        # 최신순 정렬
        df = df.sort_values(by="입력시간", ascending=False)
        
        # 필터링 기능 (선택사항)
        col_filter1, col_filter2 = st.columns(2)
        with col_filter1:
            filter_name = st.multiselect("직원별 모아보기", df['직원명'].unique())
        with col_filter2:
            filter_channel = st.multiselect("채널별 모아보기", df['채널명'].unique())
            
        if filter_name:
            df = df[df['직원명'].isin(filter_name)]
        if filter_channel:
            df = df[df['채널명'].isin(filter_channel)]

        # 데이터프레임 표시 (제목 클릭 기능 포함)
        st.dataframe(
            df,
            column_config={
                "제목": st.column_config.LinkColumn(
                    "영상 제목 (클릭 시 재생)",
                    display_text=r"https://(www\.)?youtube\.com/.*",
                    help="클릭하면 유튜브로 이동합니다."
                ),
                "링크_URL": None  # URL 열 숨김
            },
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("아직 데이터가 없습니다. '작업 등록' 탭에서 첫 영상을 기록해보세요.")

# --- [탭 3] 관리자 설정 (직원/채널 추가 및 삭제) ---
with tab3:
    st.warning("⚠️ 이곳은 직원 및 채널 목록을 관리하는 곳입니다.")
    
    col_set1, col_set2 = st.columns(2)
    
    # 1. 직원 관리
    with col_set1:
        st.markdown("### 👤 직원 관리")
        current_employees = config['employees']
        st.write(f"현재 등록된 직원: {', '.join(current_employees)}")
        
        # 직원 추가
        with st.form("add_emp"):
            new_emp = st.text_input("새 직원 이름 추가")
            if st.form_submit_button("직원 추가"):
                if new_emp and new_emp not in config['employees']:
                    config['employees'].append(new_emp)
                    save_config(config)
                    st.success(f"'{new_emp}'님이 추가되었습니다.")
                    st.rerun() # 화면 새로고침
        
        # 직원 삭제
        with st.form("del_emp"):
            del_emp = st.selectbox("삭제할 직원 선택", config['employees'])
            if st.form_submit_button("직원 삭제"):
                config['employees'].remove(del_emp)
                save_config(config)
                st.error(f"'{del_emp}'님이 삭제되었습니다.")
                st.rerun()

    # 2. 채널 관리
    with col_set2:
        st.markdown("### 📺 채널 관리")
        current_channels = config['channels']
        st.write(f"현재 등록된 채널: {', '.join(current_channels)}")
        
        # 채널 추가
        with st.form("add_ch"):
            new_ch = st.text_input("새 채널명 추가")
            if st.form_submit_button("채널 추가"):
                if new_ch and new_ch not in config['channels']:
                    config['channels'].append(new_ch)
                    save_config(config)
                    st.success(f"'{new_ch}' 채널이 추가되었습니다.")
                    st.rerun()
        
        # 채널 삭제
        with st.form("del_ch"):
            del_ch = st.selectbox("삭제할 채널 선택", config['channels'])
            if st.form_submit_button("채널 삭제"):
                config['channels'].remove(del_ch)
                save_config(config)
                st.error(f"'{del_ch}' 채널이 삭제되었습니다.")
                st.rerun()
