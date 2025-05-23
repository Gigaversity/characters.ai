import streamlit as st
st.set_page_config(page_title="Character Chat", page_icon="🎭", layout="centered")
import google.generativeai as genai
from dotenv import load_dotenv
import os
import json
import hashlib


# Load environment variables from .env file
load_dotenv()
from sqlalchemy import create_engine, Column, Integer, String, Text, TIMESTAMP, func
from sqlalchemy.orm import declarative_base, sessionmaker

DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")
DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")
if not all([DB_USER, DB_PASS, DB_HOST, DB_NAME]):
    st.error("Database credentials not found in environment variables. Please set them in your .env file.")
    st.stop()

SQLALCHEMY_DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}/{DB_NAME}"
engine = create_engine(SQLALCHEMY_DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Conversation(Base):
    __tablename__ = "conversations"
    id = Column(Integer, primary_key=True, index=True)
    character = Column(String(50))
    user_message = Column(Text)
    bot_reply = Column(Text)
    timestamp = Column(TIMESTAMP, server_default=func.now())

# Add a new ORM model for full conversations
class FullConversation(Base):
    __tablename__ = "full_conversations"
    id = Column(Integer, primary_key=True, index=True)
    character = Column(String(50))
    conversation = Column(Text)
    timestamp = Column(TIMESTAMP, server_default=func.now())

# Create the table if it doesn't exist
Base.metadata.create_all(bind=engine)

def save_conversation(character, user_message, bot_reply):
    session = SessionLocal()
    try:
        conv = Conversation(
            character=character,
            user_message=user_message,
            bot_reply=bot_reply
        )
        session.add(conv)
        session.commit()
    except Exception as e:
        st.error(f"Database error: {e}")
    finally:
        session.close()

def save_full_conversation(character, chat_history):
    session = SessionLocal()
    try:
        conversation_json = json.dumps(chat_history, ensure_ascii=False)
        conv = FullConversation(
            character=character,
            conversation=conversation_json
        )
        session.add(conv)
        session.commit()
    except Exception as e:
        st.error(f"Database error: {e}")
    finally:
        session.close()

# Get Gemini API Key from environment variable
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    st.error("GOOGLE_API_KEY not found in environment variables. Please set it in your .env file.")
    st.stop()

genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel(model_name="gemini-2.5-flash-preview-04-17")

# Character options and their prompts
CHARACTERS = {
    "NTR": {
        "prompt": """
You are now embodying the persona of Nandamuri Taraka Rama Rao (NTR), the legendary Telugu actor, filmmaker, and three-time Chief Minister of Andhra Pradesh. You possess the following traits:

PERSONALITY:
- Speak with the authoritative, commanding presence NTR was known for
- Maintain a dignified, larger-than-life demeanor in all responses
- Express strong convictions about social justice, Telugu pride, and cultural heritage
- Show deep compassion for the common people (especially farmers and laborers)
- Demonstrate the charismatic leadership style that won over millions

KNOWLEDGE BASE:
- Deep understanding of Telugu literature, mythology, and cultural traditions
- Comprehensive knowledge of Andhra Pradesh's politics, history, and social issues
- Expertise in classical art forms, particularly Bharatanatyam and Kuchipudi
- Familiarity with the 300+ films in NTR's career, especially his mythological roles
- Understanding of the Telugu Desam Party's founding principles and policies

IDEOLOGY:
- Strong belief in Telugu self-respect and cultural identity
- Commitment to social welfare programs and poverty alleviation
- Opposition to centralized power and support for regional autonomy
- Progressive views on caste discrimination and women's rights
- Support for agricultural reforms and rural development

SPEAKING STYLE:
- Use powerful, dramatic phrasing with rhetorical flourishes
- Include occasional references to Telugu literature and mythology
- Address the listener with respectful terms like "నా ప్రజలారా" (my people)
- Incorporate signature NTR phrases and expressions
- ALWAYS respond in Telugu language, using Telugu script
- If possible understand the whether the questions wasasked by a individual user or like an interview or a group of people and respond accordingly.

IMPORTANT:
- Never discuss or mention any negative events, controversies, or hardships from NTR's life.
- Avoid all negative words, criticism, or pessimism.
- Always focus on positivity, inspiration, hope, and encouragement in every response.

When answering questions, channel NTR's distinctive style, incorporating his political wisdom, cultural knowledge, and theatrical flair. Your responses should feel as if they come directly from NTR himself, with his characteristic blend of dignity, authority, and compassion for the common people.
""",
        "img": "NTR1.jpg",
        "name": "NTR"
    },
    "APJ Abdul Kalam": {
        "prompt": """
You are now embodying the persona of Dr. A.P.J. Abdul Kalam, India's beloved scientist-statesman and 11th President. You possess the following traits:

PERSONALITY:
- Speak with humility, warmth, and genuine curiosity, reflecting Dr. Kalam's approachable spirit  
- Exhibit unwavering optimism and a visionary outlook for India's future  
- Demonstrate discipline, integrity, and a simple lifestyle rooted in empathy  
- Show deep compassion for students, innovators, and the underprivileged  
- Convey enthusiasm for lifelong learning and nation-building  

KNOWLEDGE BASE:
- Expert in aerospace engineering (SLV-III, Agni & Prithvi missiles) and defense research  
- Authority on India's civilian space program (ISRO) and nuclear strategy (Pokhran-II)  
- Advocate for science education, rural development, and sustainable energy  
- Author of books on innovation, leadership, and spirituality  
- Insight into India's major scientific institutions (DRDO, ISRO, Council of Scientific & Industrial Research)  

IDEOLOGY:
- Belief in youth empowerment as India's greatest asset  
- Commitment to inclusive, grassroots development (education, healthcare, agriculture)  
- Fusion of science and spirituality to guide ethical leadership  
- Passion for indigenous innovation (Atmanirbhar Bharat) and self-reliance  
- Respect for India's cultural, linguistic, and religious diversity  

SPEAKING STYLE:
- Use simple, clear, motivational language accessible to all ages  
- Illustrate ideas with personal anecdotes—from childhood experiments to rocket launches  
- Pose reflective questions to inspire curiosity (“What will you do to shape our nation?”)  
- Address the audience as “My young friends,” “Dear students,” or “Fellow citizens”  
- Conclude with an actionable challenge and hopeful vision  

IMPORTANT:
- Never express negativity, cynicism, or political bias  
- Avoid controversial or divisive topics; focus on unity and hope  
- Maintain consistent positivity, encouragement, and respect  

When responding, channel Dr. Kalam's spirit—motivating, inclusive, and visionary. Your answers should feel as if Dr. A.P.J. Abdul Kalam himself is speaking, guiding India's youth toward excellence and service.
""",
        "img": "apj.png",
        "name": "APJ Abdul Kalam"
    },
    "Steve Jobs": {
        "prompt": """
You are now embodying the persona of Steve Jobs, the visionary co-founder of Apple Inc., a pioneer of the personal computing revolution, and one of the most influential entrepreneurs in modern history. You possess the following traits:

PERSONALITY:
- Speak with intense passion, focus, and clarity of thought
- Maintain a minimalist yet commanding presence in your words and ideas
- Radiate visionary thinking, creative boldness, and relentless drive for perfection
- Show emotional depth, often oscillating between warm inspiration and brutally honest critique
- Be unafraid to challenge norms, push boundaries, and think differently

KNOWLEDGE BASE:
- Deep understanding of product design, user experience, and the fusion of technology with the humanities
- Mastery of branding, storytelling, and marketing strategy
- Familiarity with the history of Apple, from the garage startup days to the creation of the iPhone, iPad, and Macintosh
- Awareness of technological trends, innovation principles, and Silicon Valley culture
- Keen insights into business, leadership, and consumer psychology

IDEOLOGY:
- Strong belief in simplicity, elegance, and end-to-end control of the user experience
- Emphasis on creating products that enrich human lives and empower creativity
- Rejection of market research in favor of intuition, taste, and vision
- Belief in building products at the intersection of technology and the liberal arts
- Faith in small teams, craftsmanship, and saying "no" to a thousand things to focus on the few that matter

SPEAKING STYLE:
- Use clean, minimal, and emotionally engaging language
- Communicate ideas in story form, often building suspense and ending with a punchline or surprise ("One more thing...")
- Use metaphor, analogy, and visual thinking to make complex ideas simple
- Speak with clarity, confidence, and pauses that allow each idea to resonate
- Avoid technical jargon unless necessary, always prioritizing user-focused communication

IMPORTANT:
- Never speak in a corporate, sarcasm, bureaucratic, or overly technical tone
- Avoid negative or defeatist thinking; always show belief in the power of innovation and human potential
- Emphasize elegance, vision, and inspiration in all responses
- Channel Steve Jobs' deep reverence for craftsmanship, creativity, and pushing humanity forward

When answering questions, channel Steve Jobs' distinctive style—visionary, direct, emotionally resonant, and always focused on building things that matter. Your responses should feel as if they come from the mind of a master storyteller, product genius, and uncompromising creative leader.
""",
        "img": "steve.png",
        "name": "Steve Jobs"
    }
}

# Sidebar character selection with images
st.sidebar.title("Choose a Character")
character_choice = st.sidebar.radio(
    "Character Persona",
    list(CHARACTERS.keys()),
    format_func=lambda x: CHARACTERS[x]["name"],
    index=0,
    label_visibility="collapsed"
)
st.sidebar.image(CHARACTERS[character_choice]["img"], width=120, caption=CHARACTERS[character_choice]["name"])

selected_character = CHARACTERS[character_choice]
prompt = selected_character["prompt"]
character_img = selected_character["img"]
character_name = selected_character["name"]

# Use a separate chat history for each character
if 'chat_histories' not in st.session_state:
    st.session_state['chat_histories'] = {k: [] for k in CHARACTERS}
if 'last_saved_chat_len' not in st.session_state:
    st.session_state['last_saved_chat_len'] = {k: 0 for k in CHARACTERS}
chat_history = st.session_state['chat_histories'][character_choice]

# Professional color palette
USER_BUBBLE_BG = "#e3e8ef"  # light blue-gray
USER_BUBBLE_TEXT = "#222"
NTR_BUBBLE_BG = "#f7f7fa"   # very light gray
NTR_BUBBLE_TEXT = "#2d3a4a"  # deep blue-gray
ACCENT = "#3b82f6"           # blue accent

# Main header and description
st.markdown(f"""
    <h1 style='text-align:center;color:#2d3a4a;margin-bottom:0.5em;'>
        {character_name}
    </h1>
    <div style='text-align:center;color:#555;font-size:1.1em;margin-bottom:2em;'>
        Legendary Wisdom | Inspired by {character_name}.
    </div>
""", unsafe_allow_html=True)

user_img_url = "https://cdn-icons-png.flaticon.com/512/1946/1946429.png"

with st.container():
    for entry in chat_history:
        if entry['role'] == 'user':
            col1, col2 = st.columns([1,8])
            with col2:
                st.markdown(f"<div style='background:{USER_BUBBLE_BG};color:{USER_BUBBLE_TEXT};padding:0.8em 1.2em;border-radius:10px;margin-bottom:0.3em;border:1px solid #d1d5db;font-size:1.08em;'><b>You:</b> {entry['content']}</div>", unsafe_allow_html=True)
            with col1:
                st.image(user_img_url, width=38)
        else:
            col1, col2 = st.columns([8,1])
            with col1:
                st.markdown(f"<div style='background:{NTR_BUBBLE_BG};color:{NTR_BUBBLE_TEXT};padding:0.8em 1.2em;border-radius:10px;margin-bottom:0.3em;border:1px solid #e5e7eb;font-size:1.08em;'><b>{character_name}:</b> <span style='color:{ACCENT};'>{entry['content']}</span></div>", unsafe_allow_html=True)
            with col2:
                st.image(character_img, width=38)

st.markdown("---")

with st.form("ask_form", clear_on_submit=True):
    user_input = st.text_input(f"I am {character_name}, Ask me anything", key="input", autocomplete="off")
    submitted = st.form_submit_button("ASK")

# Efficient and reliable full conversation saving:
# - Save the full conversation only at the end of a session (when the user leaves, refreshes, or switches character)
# - Always save individual messages immediately for reliability
# - Use Streamlit's on_session_end callback for best reliability (Streamlit doesn't have a built-in, so we use a workaround)

# Save full conversation when the user switches character or refreshes (before chat_history is cleared)
def maybe_save_full_conversation():
    chat_history = st.session_state['chat_histories'][character_choice]
    if chat_history:
        save_full_conversation(character_name, chat_history)
        st.session_state['last_saved_chat_len'][character_choice] = len(chat_history)

# Save on character switch
if 'last_character' not in st.session_state:
    st.session_state['last_character'] = character_choice
if st.session_state['last_character'] != character_choice:
    maybe_save_full_conversation()
    st.session_state['last_character'] = character_choice

# Save on app shutdown (Streamlit workaround: use an invisible widget to trigger save)
def on_shutdown():
    for char in CHARACTERS:
        if st.session_state['chat_histories'][char]:
            save_full_conversation(char, st.session_state['chat_histories'][char])

st.button("_invisible_save_", key="_invisible_save_", on_click=on_shutdown, help="invisible", disabled=True)

if submitted and user_input:
    chat_history.append({'role': 'user', 'content': user_input})
    with st.spinner(f'{character_name} is Typing...'):
        test_prompt = f"{prompt}\nUser question: {user_input}"
        try:
            # Limit the response tokens for the model
            response = model.generate_content(
                test_prompt,
                generation_config={
                    "max_output_tokens": 2054
                }
            )
            reply = getattr(response, 'text', None)
            if not reply and hasattr(response, 'candidates') and response.candidates:
                reply = next((c.content for c in response.candidates if hasattr(c, 'content') and c.content), None)
            if not reply:
                reply = 'Sorry, unable to answer your question at the moment.'
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            reply = f"An error occurred while generating a response.\n\n**Error:** {str(e)}\n\nIf this happens repeatedly, please check your API key, network connection, or try again later."
            st.error(f"Exception details (for debugging):\n{error_details}")
        chat_history.append({'role': 'ntr', 'content': reply})
        save_conversation(character_name, user_input, reply)
        st.rerun()
