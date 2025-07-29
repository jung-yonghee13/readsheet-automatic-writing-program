import streamlit as st
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="유형자산 총괄표 자동화", layout="wide")
st.title("유형자산 총괄표 자동화 프로그램")

# 1. 기준일자 입력
st.subheader("1️⃣ 기준일자 입력")
col_date1, col_date2 = st.columns(2)
with col_date1:
    기준일자_기초 = st.text_input("기초 기준일자 (예: 2023-12-31)", value="2023-12-31")
with col_date2:
    기준일자_기말 = st.text_input("기말 기준일자 (예: 2024-12-31)", value="2024-12-31")

# 2. 정산표 금액 입력
st.subheader("2️⃣ 정산표 금액 입력")

st.markdown("** 기초 금액 입력**")
col1, col2 = st.columns(2)
with col1:
    input_beg_acq = st.number_input("기초 취득가액", min_value=0, step=1)
with col2:
    input_beg_dep = st.number_input("기초 감가상각누계액", min_value=0, step=1)

st.markdown("** 기말 금액 입력**")
col3, col4 = st.columns(2)
with col3:
    input_end_acq = st.number_input("기말 취득가액", min_value=0, step=1)
with col4:
    input_end_dep = st.number_input("기말 감가상각누계액", min_value=0, step=1)

# 3. XBRL 재무제표 업로드
st.subheader("3️⃣ XBRL 재무제표(엑셀) 업로드")
xbrl_file = st.file_uploader("XBRL 재무제표 파일 업로드", type=["xlsx"])

# 4. 총괄표 템플릿 업로드
st.subheader("4️⃣ 총괄표 템플릿 엑셀 업로드")
template_file = st.file_uploader("총괄표 양식 파일 업로드", type=["xlsx"])

# 5. 총괄표 작성 버튼
if st.button("총괄표 작성"):

    if not xbrl_file or not template_file:
        st.error("❌ XBRL 재무제표 파일과 총괄표 템플릿을 모두 업로드해주세요.")
    else:
        try:
            # XBRL 파일 처리
            df = pd.read_excel(xbrl_file, sheet_name="D210005", header=None) #시트를 지정해버렸음 좀 더 나은 방법 강구
            df.columns = df.iloc[4]
            df = df.drop(index=list(range(0, 5))).reset_index(drop=True)
            df.rename(columns={df.columns[0]: "계정과목"}, inplace=True)

            # 🔍 기준일자별 유형자산 찾기 함수
            def get_value(date_str):
                row = df[df["계정과목"].astype(str).str.strip() == "유형자산"]
                if row.empty or date_str not in row.columns:
                    return None
                val = pd.to_numeric(str(row[date_str].values[0]).replace(",", ""), errors="coerce")
                return val if pd.notnull(val) else None

            xbrl_beg_acq = get_value(기준일자_기초)
            xbrl_end_acq = get_value(기준일자_기말)

            if xbrl_beg_acq is None or xbrl_end_acq is None:
                st.error("❌ XBRL 재무제표에서 '유형자산' 행 또는 기준일자 열을 찾을 수 없습니다.")
            else:
                st.write(f"📘 XBRL 기준 기초 취득가액: {xbrl_beg_acq:,.0f}")
                st.write(f"📘 XBRL 기준 기말 취득가액: {xbrl_end_acq:,.0f}")

                if abs(input_beg_acq - xbrl_beg_acq) > 1 or abs(input_end_acq - xbrl_end_acq) > 1:
                    st.error("❌ 정산표와 XBRL 재무제표의 취득가액이 일치하지 않습니다.")
                else:
                    # 총괄표 템플릿 불러오기
                    template_df = pd.read_excel(template_file)
                    result_df = template_df.copy()

                    # 자동 열 이름 및 자산명 열 설정
                    asset_col = result_df.columns[0]  # 첫 번째 열이 자산명
                    col_beg = f"전기말({기준일자_기초})"
                    col_end = f"당기말({기준일자_기말})"

                    # 데이터 입력
                    result_df.loc[result_df[asset_col] == "유형자산", col_beg] = input_beg_acq - input_beg_dep
                    result_df.loc[result_df[asset_col] == "유형자산", col_end] = input_end_acq - input_end_dep

                    st.success("✅ 총괄표 작성 완료")
                    st.dataframe(result_df)

                    # 엑셀 다운로드
                    towrite = BytesIO()
                    result_df.to_excel(towrite, index=False, engine="openpyxl")
                    towrite.seek(0)

                    st.download_button(
                        label="💾 총괄표 엑셀 다운로드",
                        data=towrite,
                        file_name="총괄표_작성본.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
        except Exception as e:
            st.error(f"❌ 처리 중 오류 발생: {e}")










