import streamlit as st
import random
import time
import json
from anthropic import Anthropic, APIError

# --- 기본 설정 ---
st.set_page_config(
    page_title="Tarot AI - Mystical Night",
    page_icon="🌙",
    layout="centered",
    initial_sidebar_state="expanded"
)

# --- 커스텀 CSS (신비로운 테마) ---
st.markdown("""
<style>
    /* 전체 배경은 Streamlit 다크모드를 권장하며, 카드는 별도 스타일링 */
    .stApp {
        font-family: 'Noto Serif KR', serif;
    }
    .tarot-card {
        background-color: #12152A;
        border: 2px solid #C9A84C;
        border-radius: 10px;
        padding: 20px 10px;
        text-align: center;
        min-height: 250px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.5);
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        margin-bottom: 20px;
    }
    .card-symbol { font-size: 3rem; margin-bottom: 10px; text-shadow: 0 0 10px rgba(201,168,76,0.5); }
    .card-name-ko { color: #C9A84C; font-weight: bold; font-size: 1.2rem; }
    .card-name-en { color: #8a6e30; font-size: 0.8rem; margin-bottom: 10px; font-family: 'Cinzel', serif; }
    .card-badge { 
        font-size: 0.75rem; border: 1px solid #7B5EA7; color: #a07dd4; 
        padding: 2px 8px; border-radius: 10px; background: rgba(123, 94, 167, 0.1); 
    }
    .reversed .card-symbol { transform: rotate(180deg); }
    
    .result-box {
        background: rgba(18, 21, 42, 0.75);
        border: 1px solid #8a6e30;
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 20px;
    }
    .result-title { color: #C9A84C; font-weight: bold; margin-bottom: 10px; border-bottom: 1px solid rgba(138, 110, 48, 0.3); padding-bottom: 5px;}
</style>
""", unsafe_allow_html=True)

# --- 데이터 정의 ---
CATEGORIES = [
    {"id": "love", "label": "연애", "icon": "❤️"},
    {"id": "career", "label": "직장", "icon": "💼"},
    {"id": "health", "label": "건강", "icon": "🌿"},
    {"id": "wealth", "label": "금전", "icon": "💰"},
    {"id": "daily", "label": "하루운세", "icon": "☀️"},
    {"id": "yearly", "label": "1년운세", "icon": "📅"}
]

TAROT_DECK = [
    {"id": 0, "name_ko": "바보", "name_en": "The Fool", "symbol": "🎒", "keywords": ["시작", "순수", "자유", "무계획"]},
    {"id": 1, "name_ko": "마법사", "name_en": "The Magician", "symbol": "🪄", "keywords": ["창조", "자신감", "의지", "능력"]},
    {"id": 2, "name_ko": "고위 여사제", "name_en": "The High Priestess", "symbol": "📖", "keywords": ["직관", "비밀", "지혜", "무의식"]},
    {"id": 3, "name_ko": "여황제", "name_en": "The Empress", "symbol": "👑", "keywords": ["풍요", "모성", "아름다움", "성장"]},
    {"id": 4, "name_ko": "황제", "name_en": "The Emperor", "symbol": "🛡️", "keywords": ["권위", "구조", "안정", "통제"]},
    {"id": 5, "name_ko": "교황", "name_en": "The Hierophant", "symbol": "⛪", "keywords": ["전통", "믿음", "가르침", "집단"]},
    {"id": 6, "name_ko": "연인", "name_en": "The Lovers", "symbol": "💞", "keywords": ["사랑", "조화", "선택", "결합"]},
    {"id": 7, "name_ko": "전차", "name_en": "The Chariot", "symbol": " रथ", "keywords": ["전진", "의지력", "승리", "결단"]},
    {"id": 8, "name_ko": "힘", "name_en": "Strength", "symbol": "🦁", "keywords": ["용기", "인내", "내면의 힘", "포용"]},
    {"id": 9, "name_ko": "은둔자", "name_en": "The Hermit", "symbol": "🏮", "keywords": ["탐구", "고독", "내성", "지혜"]},
    {"id": 10, "name_ko": "운명의 수레바퀴", "name_en": "Wheel of Fortune", "symbol": "🎡", "keywords": ["운명", "전환점", "순환", "기회"]},
    {"id": 11, "name_ko": "정의", "name_en": "Justice", "symbol": "⚖️", "keywords": ["공정", "균형", "진실", "인과응보"]},
    {"id": 12, "name_ko": "매달린 사람", "name_en": "The Hanged Man", "symbol": "🪢", "keywords": ["희생", "관점의 변화", "기다림", "수용"]},
    {"id": 13, "name_ko": "죽음", "name_en": "Death", "symbol": "💀", "keywords": ["종결", "새로운 시작", "변화", "전환"]},
    {"id": 14, "name_ko": "절제", "name_en": "Temperance", "symbol": "🏺", "keywords": ["균형", "중용", "치유", "조화"]},
    {"id": 15, "name_ko": "악마", "name_en": "The Devil", "symbol": "😈", "keywords": ["집착", "유혹", "속박", "물질주의"]},
    {"id": 16, "name_ko": "탑", "name_en": "The Tower", "symbol": "⚡", "keywords": ["붕괴", "갑작스러운 변화", "해방", "재난"]},
    {"id": 17, "name_ko": "별", "name_en": "The Star", "symbol": "⭐", "keywords": ["희망", "영감", "평온", "치유"]},
    {"id": 18, "name_ko": "달", "name_en": "The Moon", "symbol": "🌙", "keywords": ["불안", "환상", "무의식", "혼란"]},
    {"id": 19, "name_ko": "태양", "name_en": "The Sun", "symbol": "☀️", "keywords": ["성공", "활력", "기쁨", "긍정"]},
    {"id": 20, "name_ko": "심판", "name_en": "Judgement", "symbol": "📯", "keywords": ["부활", "평가", "구원", "각성"]},
    {"id": 21, "name_ko": "세계", "name_en": "The World", "symbol": "🌍", "keywords": ["완성", "통합", "성취", "끝과 시작"]}
]

# --- 세션 상태 초기화 ---
if 'category' not in st.session_state: st.session_state.category = None
if 'shuffled' not in st.session_state: st.session_state.shuffled = False
if 'drawn_cards' not in st.session_state: st.session_state.drawn_cards = []
if 'interpretation' not in st.session_state: st.session_state.interpretation = None
if 'status_msg' not in st.session_state: st.session_state.status_msg = "카테고리를 선택해주세요."

# --- 기능 함수 ---
def set_category(cat_label):
    st.session_state.category = cat_label
    st.session_state.shuffled = False
    st.session_state.drawn_cards = []
    st.session_state.interpretation = None
    st.session_state.status_msg = f"[{cat_label}] 운세를 봅니다. 방향 설정 후 덱을 섞어주세요."

def shuffle_deck():
    if not st.session_state.category:
        st.warning("먼저 카테고리를 선택해주세요.")
        return
    st.session_state.shuffled = True
    st.session_state.drawn_cards = []
    st.session_state.interpretation = None
    st.session_state.status_msg = "덱을 섞었습니다. 카드를 뽑아주세요."

def get_fallback_interpretation(cards):
    def get_meaning(c):
        direction_text = '역방향이므로 이 키워드들이 지연되거나 내면적으로 작용할 수 있습니다.' if c['reversed'] else '정방향이므로 이 긍정적인 에너지가 강하게 발현됩니다.'
        return f"{c['name_ko']} 카드의 키워드는 {', '.join(c['keywords'])} 입니다. {direction_text}"
    
    return {
        "past": get_meaning(cards[0]),
        "present": get_meaning(cards[1]),
        "future": get_meaning(cards[2]),
        "summary": "우주의 흐름에 몸을 맡기고, 현재의 직관을 믿고 앞으로 나아가시길 바랍니다."
    }

def draw_cards(direction_mode, api_key):
    st.session_state.status_msg = "카드를 뽑고 해석을 요청하는 중..."
    
    # 카드 3장 무작위 뽑기
    deck_copy = list(TAROT_DECK)
    random.shuffle(deck_copy)
    selected = deck_copy[:3]
    
    for card in selected:
        card['reversed'] = (random.choice([True, False]) if direction_mode == "역방향 포함" else False)
        
    st.session_state.drawn_cards = selected
    
    # AI 해석 요청
    prompt = f"""
    당신은 전문 타로 리더입니다.
    카테고리: {st.session_state.category}
    뽑힌 카드:
    - 과거: {selected[0]['name_ko']} ({'역방향' if selected[0]['reversed'] else '정방향'})
    - 현재: {selected[1]['name_ko']} ({'역방향' if selected[1]['reversed'] else '정방향'})
    - 미래: {selected[2]['name_ko']} ({'역방향' if selected[2]['reversed'] else '정방향'})
    
    위 정보를 바탕으로 타로 해석을 작성해주세요. 
    반드시 아래 JSON 형식으로만 응답하세요. 마크다운(` ```json `)을 포함하지 말고 순수 JSON 문자열만 출력하세요.
    {{
        "past": "과거에 대한 해석",
        "present": "현재에 대한 해석",
        "future": "미래에 대한 해석",
        "summary": "종합 조언"
    }}
    """
    
    if api_key:
        try:
            client = Anthropic(api_key=api_key)
            # 최신 Claude 3.5 Sonnet 모델 사용
            response = client.messages.create(
                model="claude-3-5-sonnet-20240620",
                max_tokens=1000,
                temperature=0.7,
                messages=[{"role": "user", "content": prompt}]
            )
            json_str = response.content[0].text.strip()
            # 마크다운 코드 블럭 제거 방어 코드
            if json_str.startswith('```'):
                json_str = json_str.split('\n', 1)[1]
                if json_str.endswith('```'):
                    json_str = json_str.rsplit('\n', 1)[0]
            
            st.session_state.interpretation = json.loads(json_str)
            st.session_state.status_msg = "별빛이 당신의 운명을 비춥니다."
        except Exception as e:
            st.error(f"AI 해석 중 오류 발생: {e}")
            st.session_state.interpretation = get_fallback_interpretation(selected)
            st.session_state.status_msg = "로컬 모드로 해석을 완료했습니다."
    else:
        # API 키가 없을 경우 로컬 폴백 사용
        time.sleep(1.5) # 애니메이션 효과를 위한 지연
        st.session_state.interpretation = get_fallback_interpretation(selected)
        st.session_state.status_msg = "API 키가 없어 기본 해석을 제공합니다."

def reset_app():
    st.session_state.category = None
    st.session_state.shuffled = False
    st.session_state.drawn_cards = []
    st.session_state.interpretation = None
    st.session_state.status_msg = "초기화되었습니다. 카테고리를 선택해주세요."


# --- UI 렌더링 ---

# 사이드바
with st.sidebar:
    st.title("⚙️ 설정")
    anthropic_api_key = st.text_input("Anthropic API Key", type="password", help="Claude AI 해석을 위해 필요합니다. 비워두면 기본 해석이 제공됩니다.")
    direction_mode = st.radio("방향 설정", ["정방향만", "역방향 포함"], index=1)
    
    st.markdown("---")
    st.write("✨ **Tarot AI Guide**")
    st.write("1. 메인 화면에서 카테고리를 선택하세요.")
    st.write("2. '덱 섞기'를 누르세요.")
    st.write("3. '카드 뽑기'를 눌러 결과를 확인하세요.")

# 메인 화면 헤더
st.markdown("<h1 style='text-align: center; color: #C9A84C; font-family: Cinzel, serif;'>Tarot AI</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #a9a0be;'>✦ 당신의 과거, 현재, 그리고 미래를 읽어보세요 ✦</p>", unsafe_allow_html=True)

st.info(st.session_state.status_msg)

# 카테고리 선택 영역
st.write("### 1. 카테고리 선택")
cols = st.columns(6)
for i, cat in enumerate(CATEGORIES):
    with cols[i]:
        # 현재 선택된 카테고리 표시 (Streamlit 기본 버튼으로 구현)
        btn_type = "primary" if st.session_state.category == cat['label'] else "secondary"
        if st.button(f"{cat['icon']}\n{cat['label']}", key=f"cat_{cat['id']}", type=btn_type, use_container_width=True):
            set_category(cat['label'])
            st.rerun()

# 컨트롤 영역
st.write("### 2. 행동")
c1, c2, c3 = st.columns(3)
with c1:
    if st.button("덱 섞기 🪄", disabled=(st.session_state.category is None), use_container_width=True):
        shuffle_deck()
        st.rerun()
with c2:
    if st.button("카드 뽑기 🎴", disabled=(not st.session_state.shuffled or len(st.session_state.drawn_cards) > 0), type="primary", use_container_width=True):
        with st.spinner("우주의 기운을 모으는 중..."):
            draw_cards(direction_mode, anthropic_api_key)
        st.rerun()
with c3:
    if st.button("초기화 🔄", use_container_width=True):
        reset_app()
        st.rerun()

# 카드 및 결과 표시 영역
st.markdown("---")
if len(st.session_state.drawn_cards) == 3:
    st.write("### 3. 운명의 카드")
    
    card_cols = st.columns(3)
    labels = ["과거", "현재", "미래"]
    
    for i in range(3):
        card = st.session_state.drawn_cards[i]
        rev_class = "reversed" if card['reversed'] else ""
        dir_text = "역방향" if card['reversed'] else "정방향"
        
        with card_cols[i]:
            st.markdown(f"<div style='text-align: center; color:#a07dd4; font-weight:bold; margin-bottom:10px;'>{labels[i]}</div>", unsafe_allow_html=True)
            st.markdown(f"""
            <div class="tarot-card {rev_class}">
                <div class="card-symbol">{card['symbol']}</div>
                <div class="card-name-ko">{card['name_ko']}</div>
                <div class="card-name-en">{card['name_en']}</div>
                <div class="card-badge">{dir_text}</div>
            </div>
            """, unsafe_allow_html=True)

    # AI 해석 결과 출력
    if st.session_state.interpretation:
        st.write("### 🔮 AI 리딩 결과")
        interp = st.session_state.interpretation
        keys = ["past", "present", "future"]
        
        for i in range(3):
            st.markdown(f"""
            <div class="result-box">
                <div class="result-title">[{labels[i]}] {st.session_state.drawn_cards[i]['name_ko']} ({'역방향' if st.session_state.drawn_cards[i]['reversed'] else '정방향'})</div>
                <div style="color: #EDE8F5; line-height: 1.6;">{interp.get(keys[i], '')}</div>
            </div>
            """, unsafe_allow_html=True)
            
        st.markdown(f"""
        <div class="result-box" style="background: rgba(123, 94, 167, 0.15); border-color: #7B5EA7;">
            <div class="result-title" style="color: #a07dd4;">🌙 종합 조언</div>
            <div style="color: #EDE8F5; line-height: 1.6; font-size: 1.05rem;">{interp.get('summary', '')}</div>
        </div>
        """, unsafe_allow_html=True)