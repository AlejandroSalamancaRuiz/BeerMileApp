import streamlit as st
import pandas as pd
import json
import os

DATA_FILE = "data.json"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                data = {"users": {}, "events": []}
        return data
    else:
        return {"users": {}, "events": []}

def save_data():
    data = {"users": st.session_state.users, "events": st.session_state.events}
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

# -------------------------------
# CONSTANTS
# -------------------------------
F1_TEAMS = [
    "Mercedes",
    "Red Bull Racing",
    "Ferrari",
    "McLaren",
    "Alpine",
    "Aston Martin",
    "AlphaTauri",
    "Sauber",         # Changed from Alfa Romeo
    "Haas F1 Team",
    "Williams"
]

BEER_TYPES = [
    "Lager",
    "Pilsner",
    "IPA",
    "Stout",
    "Porter",
    "Pale Ale",
    "Wheat Beer",
    "Amber Ale",
    "Belgian Ale",
    "Sour Ale",
    "Fruit Beer"      # Added Fruit Beer
]

# -------------------------------
# INITIALIZE SESSION STATE WITH PERSISTENCE
# -------------------------------
if "users" not in st.session_state or "events" not in st.session_state:
    data = load_data()
    st.session_state.users = data.get("users", {})
    st.session_state.events = data.get("events", [])

# -------------------------------
# SIDEBAR NAVIGATION
# -------------------------------
st.sidebar.title("🏎️ F1 Beer Mile")
page = st.sidebar.radio("Navigate", ["Welcome", "Register", "Log Beer", "Log Penalty", "Standings"])

# -------------------------------
# WELCOME PAGE
# -------------------------------
if page == "Welcome":
    st.title("🏁 Welcome to the F1 Beer Mile! 🍺")
    st.markdown("""
    **How to Play:**
    
    - **Register:** Enter your name and select your F1 team.
    - **Log Beer:** Each time you hit a pub, log your beer!
        - **Points:** Earn **10 points** for every **½ pint** (i.e. 1 pint = 20 points).
    - **Beer Variety Bonus:** Gain **+5 points** for each **unique beer type** you try.
    - **Pub Visit Bonus:** Gain **+10 points** for every unique **pub** you visit.
    - **Penalties:** If you skip a pub or enter incorrect information, you lose **10 points**.
    
    **Championships:**
    
    - **Driver’s Championship:** Individual leaderboard.
    - **Constructor’s Championship:** Team leaderboard (team score is the average per driver).
    
    **Remember:**  
    Race smart, drink responsibly, and may the best team win!
    """)

# -------------------------------
# REGISTRATION PAGE
# -------------------------------
elif page == "Register":
    st.title("🏎️ Register for the F1 Beer Mile")
    name = st.text_input("Enter your name:")
    team = st.selectbox("Select your F1 Team:", F1_TEAMS)
    if st.button("Register"):
        if name:
            st.session_state.users[name] = team
            save_data()  # Save after registration
            st.success(f"Welcome, **{name}**! You are now driving for **{team}**.")
        else:
            st.error("Please enter your name.")

# -------------------------------
# LOG BEER PAGE
# -------------------------------
elif page == "Log Beer":
    st.title("🍺 Log Your Beer")
    if not st.session_state.users:
        st.warning("No registered users yet. Please register first!")
    else:
        user = st.selectbox("Select your name:", list(st.session_state.users.keys()))
        pub = st.selectbox("Select Pub Number:", list(range(1, 201)))
        beer_type = st.selectbox("Select Beer Type:", BEER_TYPES)
        # Default value is set to 0.5 pint
        pints = st.number_input("Amount consumed (in pints)", min_value=0.0, step=0.1, value=0.5, format="%.2f")
        if st.button("Submit Beer"):
            if pints > 0:
                event = {
                    "type": "beer",
                    "user": user,
                    "pub": pub,
                    "beer_type": beer_type,
                    "pints": pints,
                }
                st.session_state.events.append(event)
                save_data()  # Save after logging beer
                st.success(f"Beer event logged at Pub #{pub}!")
            else:
                st.error("Please enter a valid number of pints.")

# -------------------------------
# LOG PENALTY PAGE
# -------------------------------
elif page == "Log Penalty":
    st.title("⚠️ Log a Penalty")
    if not st.session_state.users:
        st.warning("No registered users yet. Please register first!")
    else:
        user = st.selectbox("Select your name:", list(st.session_state.users.keys()), key="penalty_user")
        penalty_reason = st.selectbox("Select penalty reason:", ["Skipped Pub", "Incorrect Info"])
        if st.button("Submit Penalty"):
            event = {
                "type": "penalty",
                "user": user,
                "penalty_reason": penalty_reason,
                "points": -10,
            }
            st.session_state.events.append(event)
            save_data()  # Save after logging penalty
            st.success("Penalty logged successfully!")

# -------------------------------
# STANDINGS PAGE
# -------------------------------
elif page == "Standings":
    st.title("🏁 Championship Standings")
    
    # Calculate driver scores
    driver_scores = {user: 0 for user in st.session_state.users.keys()}
    beer_types = {user: set() for user in st.session_state.users.keys()}
    pubs_visited = {user: set() for user in st.session_state.users.keys()}
    
    for event in st.session_state.events:
        user = event["user"]
        if event["type"] == "beer":
            # 10 points per ½ pint (thus pints * 20 points)
            consumption_points = event["pints"] * 20
            driver_scores[user] += consumption_points
            beer_types[user].add(event["beer_type"])
            pubs_visited[user].add(event["pub"])
        elif event["type"] == "penalty":
            driver_scores[user] += event["points"]
    
    # Add bonus points for unique beer types and pub visits
    for user in driver_scores:
        driver_scores[user] += len(beer_types[user]) * 5   # +5 per unique beer type
        driver_scores[user] += len(pubs_visited[user]) * 10   # +10 per pub visited

    # Build Driver's Championship DataFrame
    drivers = []
    for user, points in driver_scores.items():
        drivers.append({
            "Driver": user,
            "Team": st.session_state.users[user],
            "Points": round(points, 2)
        })
    drivers_df = pd.DataFrame(drivers).sort_values("Points", ascending=False)
    
    st.markdown("### 🏎️ **Driver's Championship**")
    st.table(drivers_df.style.set_properties(**{'text-align': 'center', 'font-weight': 'bold'}))
    
    # Calculate Constructor's Championship (average team points per member)
    team_scores = {}
    team_counts = {}
    for user, team in st.session_state.users.items():
        team_scores.setdefault(team, 0)
        team_counts.setdefault(team, 0)
        team_scores[team] += driver_scores[user]
        team_counts[team] += 1

    teams = []
    for team in team_scores:
        avg_score = team_scores[team] / team_counts[team]
        teams.append({"Team": team, "Avg Points": round(avg_score, 2)})
    teams_df = pd.DataFrame(teams).sort_values("Avg Points", ascending=False)
    
    st.markdown("### 🏆 **Constructor's Championship**")
    st.table(teams_df.style.set_properties(**{'text-align': 'center', 'font-weight': 'bold'}))
    
    # --- Fun Race Track Graphic ---
    st.markdown("## 🏁 Race Track Standings")
    
    def create_track(avg, max_avg, length=30):
        """Return a string representing the track progress."""
        if max_avg == 0:
            pos = 0
        else:
            pos = int((avg / max_avg) * (length - 1))
        track = "-" * pos + "🏎️" + "-" * (length - pos - 1)
        return track

    if teams:
        max_avg = max(team["Avg Points"] for team in teams)
        st.markdown("<style> .track { font-family: monospace; font-size: 16px; } </style>", unsafe_allow_html=True)
        for idx, row in teams_df.iterrows():
            team_name = row["Team"]
            avg_points = row["Avg Points"]
            track = create_track(avg_points, max_avg)
            st.markdown(f"<div class='track'><b>{team_name}</b> ({avg_points} pts): {track}</div>", unsafe_allow_html=True)
    
    st.markdown("#### May your pints be swift and your teams legendary! 🍻🏁")
