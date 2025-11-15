import streamlit as st
import pandas as pd
import datetime
from streamlit_calendar import calendar

st.title("Tidal: Your very own Wellness App")

# Create tabs
tab1, tab2, tab3, tab4 = st.tabs(["Period Tracker", "Sleep Schedule", "AI Chatbox","Tests"])

with tab1:
    st.header("Period Tracker")
    # --- Set up session state ---
if "period_events" not in st.session_state:
    # store list of dicts: {"title": "...", "start": "YYYY-MM-DD", "allDay": True}
    st.session_state.period_events = []

st.header("Period Tracker Calendar")

# Input: let user pick a new period-start date
new_date = st.date_input("Log your period start", value=datetime.date.today())

if st.button("Add period start"):
    st.session_state.period_events.append({
        "title": "Period start",
        "start": new_date.isoformat(),
        "allDay": True
    })

# Show calendar
calendar_options = {
    "initialView": "dayGridMonth",
    "selectable": True,
    "headerToolbar": {
        "left": "prev,next today",
        "center": "title",
        "right": "dayGridMonth"
    }
}

cal_data = calendar(
    events=st.session_state.period_events,
    options=calendar_options,
    key="period_calendar"
)

st.write("Calendar data:", cal_data)

# Show the list of period starts
if st.session_state.period_events:
    df = pd.DataFrame(st.session_state.period_events)
    st.subheader("Logged Period Starts")
    st.dataframe(df)

with tab2:
        # Initialize session state for storing sleep logs
    if "sleep_data" not in st.session_state:
        st.session_state.sleep_data = pd.DataFrame(columns=["Date", "Sleep Start", "Wake Up", "Hours Slept", "Quality"])

    # Input for a new sleep entry
    sleep_date = st.date_input("Date", datetime.date.today())
    sleep_start = st.time_input("Sleep Start Time", datetime.time(22, 0))
    wake_up = st.time_input("Wake Up Time", datetime.time(6, 0))
    quality = st.slider("Sleep Quality", min_value=1, max_value=5, value=3)

    # Calculate sleep duration
    sleep_start_dt = datetime.datetime.combine(sleep_date, sleep_start)
    wake_up_dt = datetime.datetime.combine(sleep_date, wake_up)
    if wake_up_dt <= sleep_start_dt:
        wake_up_dt += datetime.timedelta(days=1)
    hours_slept = round((wake_up_dt - sleep_start_dt).total_seconds() / 3600, 2)

    if st.button("Add Sleep Entry"):
        # Add entry to session state dataframe
        st.session_state.sleep_data = pd.concat([
            st.session_state.sleep_data,
            pd.DataFrame([{
                "Date": sleep_date,
                "Sleep Start": sleep_start.strftime("%H:%M"),
                "Wake Up": wake_up.strftime("%H:%M"),
                "Hours Slept": hours_slept,
                "Quality": quality
            }])
        ], ignore_index=True)

    # Show sleep log table (sort by date descending)
    if not st.session_state.sleep_data.empty:
        st.subheader("Sleep Log")
        st.dataframe(st.session_state.sleep_data.sort_values(by="Date", ascending=False))

with tab3: 
    st.header("Your AI Help")

with tab4:
    st.header("Your wellbeing")
    # period tracker code here
