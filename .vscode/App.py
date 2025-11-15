import streamlit as st 
import pandas as pd
import datetime
from streamlit_calendar import calendar
import uuid
import os
from PIL import Image
import io
import openai
import matplotlib.pyplot as plt
import time 

st.set_page_config(page_title="Tidal")
# ====================================================
# BACKGROUND
# ====================================================

st.markdown(
    """
    <style>
    .stApp {
        /* Dark overlay on the background image */
        background-image: 
            linear-gradient(rgba(0, 0, 0, 0.4), rgba(0, 0, 0, 0.4)),  /* adjust 0.4 for darkness */
            url("https://images.unsplash.com/photo-1506744038136-46273834b3fb");
        background-size: cover;
        background-repeat: no-repeat;
        background-attachment: fixed;
    }

    /* Optional: make text more visible */
    .stApp * {
        color: white;
    }
    </style>
    """,
    unsafe_allow_html=True
)



def get_new_calendar_key():
    return str(uuid.uuid4())

# ====================================================
# START OF APP
# ====================================================

st.title("Tidal")
st.header("Your very own personalised wellbeing app")

if "period_events" not in st.session_state:
    st.session_state.period_events = []

if "cal_key" not in st.session_state:
    st.session_state.cal_key = get_new_calendar_key()

if "sleep_data" not in st.session_state:
    st.session_state.sleep_data = pd.DataFrame(
        columns=["Date", "Sleep Start", "Wake Up", "Hours Slept", "Quality"]
    )

# ----------------------------------------------------
# Tabs
# ----------------------------------------------------
tab1, tab2, tab3, tab4 = st.tabs(["Period Tracker", "Sleep Schedule", "AI Chatbox", "My Health Data"])

# ====================================================
# PERIOD TRACKER
# ====================================================

with tab1:
    st.header("Period Tracker")

    # ----------------------------------------------------
    # Load saved history (ONCE)
    # ----------------------------------------------------
    if "period_loaded" not in st.session_state:
        if os.path.exists("period_history.csv"):
            saved = pd.read_csv("period_history.csv")
            st.session_state.period_events = [
                {
                    "title": "Period",
                    "start": row["Date"],
                    "allDay": True,
                    "id": str(uuid.uuid4())
                }
                for _, row in saved.iterrows()
            ]
        st.session_state.period_loaded = True

    # ----------------------------------------------------
    # Calendar UI
    # ----------------------------------------------------
    calendar_options = {
        "initialView": "dayGridMonth",
        "selectable": True,
        "headerToolbar": {
            "left": "prev,next today",
            "center": "title",
            "right": "dayGridMonth"
        },
        "eventColor": "#0d9590",
        "eventTextColor": "white",
    }

    cal_data = calendar(
        key="period_tracker_stable",
        events=st.session_state.period_events,
        options=calendar_options
    )

    # ----------------------------------------------------
    # HANDLE DATE CLICKS — SIMPLE & STABLE
    # ----------------------------------------------------
    if cal_data and cal_data.get("dateClick"):
        date_str = cal_data["dateClick"]["date"]

        exists = any(e["start"] == date_str for e in st.session_state.period_events)

        if exists:
            # remove
            st.session_state.period_events = [
                e for e in st.session_state.period_events if e["start"] != date_str
            ]
            st.success(f"Removed: {date_str}")
        else:
            # add
            st.session_state.period_events.append({
                "title": "Period",
                "start": date_str,
                "allDay": True,
                "id": str(uuid.uuid4())
            })
            st.success(f"Added: {date_str}")

        # SAVE HISTORY
        pd.DataFrame(
            sorted([e["start"] for e in st.session_state.period_events]),
            columns=["Date"]
        ).to_csv("period_history.csv", index=False)

        # RERUN SAFELY (NO GLITCH)
        st.rerun()

    # ----------------------------------------------------
    # HISTORY DISPLAY
    # ----------------------------------------------------
    st.markdown("---")
    st.subheader("Period History")

    if st.session_state.period_events:
        dates = sorted([e["start"] for e in st.session_state.period_events])
        st.write(", ".join(dates))

        csv_data = pd.DataFrame(dates, columns=["Date"]).to_csv(index=False)

        st.download_button(
            "📥 Download History",
            data=csv_data,
            file_name="period_history.csv",
            mime="text/csv"
        )
    else:
        st.info("Click a date to log your period.")


# ====================================================
# SLEEP SCHEDULE
# ====================================================
with tab2:
    st.header("Sleep Schedule")

    with st.form("sleep_form"):
        st.subheader("Add New Sleep Entry")
        col1, col2, col3 = st.columns(3)

        with col1:
            sleep_date = st.date_input("Date", datetime.date.today())
        with col2:
            sleep_start = st.time_input("Sleep Start Time", datetime.time(22, 0))
        with col3:
            wake_up = st.time_input("Wake Up Time", datetime.time(6, 0))

        quality = st.slider("Sleep Quality (1-5)", 1, 5, 3)

        submitted_sleep = st.form_submit_button("Add Sleep Entry")

        if submitted_sleep:
            sleep_start_dt = datetime.datetime.combine(sleep_date, sleep_start)
            wake_up_dt = datetime.datetime.combine(sleep_date, wake_up)

            if wake_up_dt <= sleep_start_dt:
                wake_up_dt += datetime.timedelta(days=1)

            hours_slept = round((wake_up_dt - sleep_start_dt).total_seconds() / 3600, 2)

            new_entry = pd.DataFrame([{
                "Date": sleep_date,
                "Sleep Start": sleep_start.strftime("%H:%M"),
                "Wake Up": wake_up.strftime("%H:%M"),
                "Hours Slept": hours_slept,
                "Quality": quality
            }])

            # Prevent duplicate rows
            st.session_state.sleep_data = (
                pd.concat([st.session_state.sleep_data, new_entry], ignore_index=True)
                .drop_duplicates()
            )

            st.success(f"Sleep entry added: {hours_slept} hours slept.")
            st.rerun()  # <<< FIX

    st.markdown("---")

    if not st.session_state.sleep_data.empty:
        st.subheader("Sleep Log History")

        display_df = st.session_state.sleep_data.sort_values(
            by="Date", ascending=False
        ).reset_index(drop=True)

        st.dataframe(display_df, use_container_width=True)
    else:
        st.info("No sleep entries logged yet. Use the form above to add your first entry.")


# ====================================================
# AI CHATBOX
# ====================================================
with tab3:
    st.header("Your AI Help")
    user_input = st.text_input("Your question:")

# -----------------------------
# 4. User input
# -----------------------------
if user_input and st.button("Ask"):
    # Add user message to session memory
    st.session_state.chat_history.append({"role": "user", "content": user_input})

    # Limit memory to last 10 messages to prevent token overflow
    MAX_MEMORY = 10
    st.session_state.chat_history = st.session_state.chat_history[-MAX_MEMORY:]

    # -----------------------------
    # 5. Delay to prevent rate limits
    # -----------------------------
    time.sleep(1)  # wait 1 second between API calls

    # -----------------------------
    # 6. Call OpenAI API safely
    # -----------------------------
    try:
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",  # Use GPT-3.5 to ensure access
            messages=st.session_state.chat_history
        )
        answer = response.choices[0].message.content
        # Add assistant message to session memory
        st.session_state.chat_history.append({"role": "assistant", "content": answer})

    except openai.OpenAIError as e:
        st.error(f"OpenAI API error: {e}")


# Set your API key safely
openai.api_key = "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"

# -----------------------------
# 2. Streamlit page setup
# -----------------------------

# -----------------------------
# 3. Initialize session memory safely
# -----------------------------
if "chat_history" not in st.session_state:
    st.session_state.chat_history = [
        {
            "role": "system",
            "content": (
                "You are an expert in women's health. "
                "Answer questions clearly, accurately, and kindly."
            )
        }
    ]

# -----------------------------
# 7. Display chat safely
# -----------------------------
for msg in st.session_state.chat_history:
    if msg["role"] == "user":
        st.markdown(f"**You:** {msg['content']}")
    elif msg["role"] == "assistant":
        st.markdown(f"**Bot:** {msg['content']}")

# ====================================================
# TESTS
# ====================================================
with tab4:
    st.header("Your Wellbeing")
    
    # Unique keys prevent duplicate ID errors
    lab_file = st.file_uploader(
        "Upload lab results (key:value per line)", 
        type=["txt"], 
        key="lab_file_tab4"
    )
    cycle_csv = st.file_uploader(
        "Upload menstrual cycle CSV (StartDate column)", 
        type=["csv"], 
        key="cycle_csv_tab4"
    )

    # Button to "send data to doctor"
    if st.button("Sync Data with Doctor", key="send_button_tab4"):
        if lab_file is not None or cycle_csv is not None:
            st.success("Data uploaded and sent to your doctor!")
        else:
            st.warning("Nothing uploaded")

    # Reference ranges
    ESTROGEN_RANGES = {0: (19, 140), 1: (110, 410), 2: (19, 160), 3: (30, 450)}
    PROGESTERONE_RANGES = {0: (0.1, 0.3), 1: (0.2, 1.5), 2: (5.0, 20.0), 3: (1.7, 27.0)}
    HEMOGLOBIN_RANGE = (12, 17.5)
    FERRITIN_RANGE = (20, 200)
    CORTISOL_RANGES = {
        "Cortisol_Morning": (10, 20),
        "Cortisol_Afternoon": (3, 10),
        "Cortisol_Night": (2, 4),
        "Cortisol_24h": (10, 55)
    }
    CYCLE_STAGES = ["Menstrual", "Follicular", "Ovulatory", "Luteal"]

    def get_range(test_name, cycle_stage):
        test_name_lower = test_name.lower()
        if test_name_lower == "estrogen":
            return ESTROGEN_RANGES.get(cycle_stage, (0, 9999))
        elif test_name_lower == "progesterone":
            return PROGESTERONE_RANGES.get(cycle_stage, (0, 9999))
        elif test_name_lower == "hemoglobin":
            return HEMOGLOBIN_RANGE
        elif test_name_lower == "ferritin":
            return FERRITIN_RANGE
        elif test_name in CORTISOL_RANGES:
            return CORTISOL_RANGES[test_name]
        else:
            return None

    def plot_lab_values(values_dict, cycle_stage=0):
        keys = list(values_dict.keys())
        values = list(values_dict.values())
        colors = []
        for test in keys:
            ref_range = get_range(test, cycle_stage)
            if ref_range is None:
                colors.append("gray")
            else:
                low, high = ref_range
                colors.append("green" if low <= values_dict[test] <= high else "red")

        fig, ax = plt.subplots(figsize=(10, 5))
        ax.bar(keys, values, color=colors)
        ax.set_ylabel("Value")
        ax.set_title(f"Lab Results (Cycle Stage: {CYCLE_STAGES[cycle_stage]})")
        ax.set_xticks(range(len(keys)))
        ax.set_xticklabels(keys, rotation=45, ha="right")
        ax.grid(axis='y', linestyle='--', alpha=0.5)
        st.pyplot(fig)

    # Example hard-coded patient
    lab_values_1 = {
        "Estrogen": 120,
        "Progesterone": 0.5,
        "Hemoglobin": 15.0,
        "Ferritin": 70,
        "Cortisol_Morning": 12,
        "Cortisol_Afternoon": 7,
        "Cortisol_Night": 3
    }
    st.subheader("Example Patient 1 - Follicular Stage")
    plot_lab_values(lab_values_1, cycle_stage=1)



