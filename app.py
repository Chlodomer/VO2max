import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import json
import os
import streamlit_authenticator as stauth

# Page configuration
st.set_page_config(
    page_title="Fitness Tracker",
    page_icon="🏃‍♂️",
    layout="wide"
)

# Initialize authentication
if 'username' not in st.session_state:
    st.session_state.username = None

def check_password():
    """Returns `True` if the user had the correct password."""
    
    # Initialize session state variables if they don't exist
    if 'authentication_status' not in st.session_state:
        st.session_state.authentication_status = False
        st.session_state.username = None
        st.session_state.logout_clicked = False
        st.session_state.current_tab = "Login"  # Add this line
    
    # Initialize users from file or create default
    if 'users' not in st.session_state:
        if os.path.exists('data/users.json'):
            with open('data/users.json', 'r') as f:
                st.session_state.users = json.load(f)
        else:
            st.session_state.users = {'admin': 'abc123'}  # Default admin account
        
    if st.session_state.authentication_status and not st.session_state.logout_clicked and st.session_state.username:
        # Show user icon and name in top right with logout button
        col1, col2, col3 = st.columns([5, 0.7, 0.3])
        with col2:
            user_initial = st.session_state.username[0].upper() if st.session_state.username else "?"
            st.markdown(
                f"""
                <div style="
                    background-color: #f0f2f6;
                    padding: 8px 15px;
                    border-radius: 20px;
                    display: flex;
                    align-items: center;
                    gap: 10px;
                ">
                    <div style="
                        background-color: #FF4B4B;
                        color: white;
                        width: 25px;
                        height: 25px;
                        border-radius: 50%;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        font-weight: bold;
                    ">
                        {user_initial}
                    </div>
                    <span>{st.session_state.username}</span>
                </div>
                """,
                unsafe_allow_html=True
            )
        with col3:
            if st.button("🚪", help="Logout"):
                st.session_state.authentication_status = False
                st.session_state.username = None
                st.session_state.logout_clicked = True
                st.rerun()
        return True

    # Create tabs for login and signup
    login_tab, signup_tab = st.tabs(["Login", "Sign Up"])
    
    with login_tab:
        # Login form
        with st.form("login_form"):
            username = st.text_input("Username", key="username_input")
            password = st.text_input("Password", type="password", key="password")
            submitted = st.form_submit_button("Log In")
            
            if submitted:
                if username in st.session_state.users and st.session_state.users[username] == password:
                    st.session_state.authentication_status = True
                    st.session_state.username = username
                    st.session_state.logout_clicked = False
                    st.rerun()
                    return True
                else:
                    st.error("Invalid username or password")
                    return False
    
    with signup_tab:
        st.write("Create a new account")
        # Sign up form
        with st.form("signup_form"):
            new_username = st.text_input("Choose Username")
            new_password = st.text_input("Choose Password", type="password")
            confirm_password = st.text_input("Confirm Password", type="password")
            signup_submitted = st.form_submit_button("Sign Up")
            
            if signup_submitted:
                if not new_username:
                    st.error("Please enter a username!")
                elif new_username in st.session_state.users:
                    st.error("Username already exists!")
                elif new_password != confirm_password:
                    st.error("Passwords don't match!")
                elif len(new_password) < 6:
                    st.error("Password must be at least 6 characters long!")
                else:
                    st.session_state.users[new_username] = new_password
                    # Save users to file
                    os.makedirs('data', exist_ok=True)
                    with open('data/users.json', 'w') as f:
                        json.dump(st.session_state.users, f)
                    st.success(f"✅ Account created successfully! Welcome, {new_username}!")
                    st.balloons()
    
    return False

if not check_password():
    st.stop()

# Initialize session state for data storage
if 'workouts' not in st.session_state:
    st.session_state.workouts = []

if 'user_profile' not in st.session_state:
    st.session_state.user_profile = None

def load_data():
    """Load data from JSON files"""
    username = st.session_state.username
    
    # Load user-specific profile
    profile_file = f'data/profile_{username}.json'
    workouts_file = f'data/workouts_{username}.json'
    
    if os.path.exists(profile_file):
        with open(profile_file, 'r') as f:
            st.session_state.user_profile = json.load(f)
    else:
        # Default empty profile
        st.session_state.user_profile = {
            'name': '',
            'age': 30,
            'weight': 70.0,
            'height': 170
        }
    
    if os.path.exists(workouts_file):
        with open(workouts_file, 'r') as f:
            st.session_state.workouts = json.load(f)
    else:
        st.session_state.workouts = []

def save_data():
    """Save data to JSON files"""
    username = st.session_state.username
    os.makedirs('data', exist_ok=True)
    
    # Save user-specific profile
    with open(f'data/profile_{username}.json', 'w') as f:
        json.dump(st.session_state.user_profile, f)
    
    with open(f'data/workouts_{username}.json', 'w') as f:
        json.dump(st.session_state.workouts, f)

def calculate_vo2max(pace_min_km, heart_rate, workout_type='steady', incline=0, stroke_rate=0):
    """
    Calculate VO2max based on workout type and metrics
    """
    if workout_type in ['steady', 'interval']:  # Removed 'tempo' and 'long'
        # Running calculation (modified Daniels formula)
        speed_mpm = 1000 / pace_min_km  # meters per minute
        vo2 = -4.60 + 0.182258 * speed_mpm + 0.000104 * speed_mpm ** 2
        
        # Adjust for workout type
        type_multipliers = {
            'steady': 1.0,
            'interval': 1.05,  # Higher intensity
        }
        vo2 *= type_multipliers[workout_type]
        
    elif workout_type == 'incline_walk':
        # Walking calculation (ACSM formula)
        speed_mph = (60 / pace_min_km) / 1.609  # Convert to mph
        vo2 = (0.1 * speed_mph) + (1.8 * speed_mph * incline) + 3.5
        
    elif workout_type == 'rowing':
        # Rowing calculation (modified from general fitness equations)
        speed_mpm = 1000 / pace_min_km
        vo2 = (4.0 * speed_mpm * 0.17) + (0.35 * stroke_rate) + 7.0
    
    # Adjust for heart rate
    max_hr = 220 - st.session_state.user_profile['age']
    hr_ratio = heart_rate / max_hr
    vo2max = vo2 / hr_ratio
    
    return round(vo2max, 1)

def profile_page():
    st.header('👤 Profile')
    
    # Profile container with rounded corners
    st.markdown("""
        <div style="
            background-color: #f0f2f6;
            padding: 25px;
            border-radius: 15px;
            margin-bottom: 30px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        ">
    """, unsafe_allow_html=True)
    
    if st.session_state.user_profile is None:
        st.session_state.user_profile = {}
    
    col1, col2 = st.columns(2)
    
    with col1:
        name = st.text_input('Name', st.session_state.user_profile.get('name', ''))
        age = st.number_input('Age', 0, 120, st.session_state.user_profile.get('age', 30), step=1)
        
    with col2:
        # Convert all weight values to float
        stored_weight = float(st.session_state.user_profile.get('weight', 70))
        weight = st.number_input('Weight (kg)', 30.0, 200.0, stored_weight, step=0.1)
        
        # Convert all height values to int
        stored_height = int(st.session_state.user_profile.get('height', 170))
        height = st.number_input('Height (cm)', 100, 250, stored_height, step=1)
    
    if st.button('Save Profile'):
        st.session_state.user_profile = {
            'name': name,
            'age': age,
            'weight': float(weight),  # Ensure weight is stored as float
            'height': int(height)     # Ensure height is stored as int
        }
        save_data()
        st.success('Profile saved!')
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Add the treadmill image below the profile with adjusted width
    col1, col2, col3 = st.columns([1, 2, 1])  # Creates three columns
    with col2:  # Use middle column for image
        st.image('assets/treadmill.png', 
                caption='Track your fitness journey', 
                use_container_width=True)  # Fixed deprecation warning

def workout_page():
    st.header('💪 Add New Workout')
    
    # Create a unique key for the form
    if 'form_key' not in st.session_state:
        st.session_state.form_key = 0
    
    with st.form(f'workout_form_{st.session_state.form_key}'):
        col1, col2 = st.columns(2)
        
        with col1:
            date = st.date_input('Workout Date')
            workout_type = st.selectbox('Workout Type', [
                'steady',
                'interval',
                'incline_walk',
                'rowing'
            ])  # Removed 'tempo' and 'long'
            
        with col2:
            duration_mins = st.number_input('Duration (minutes)', 1, 300)
            heart_rate = st.number_input('Average Heart Rate (bpm)', 60, 220)
            
        # Conditional inputs based on workout type
        if workout_type in ['steady', 'interval', 'tempo', 'long', 'incline_walk']:
            pace = st.number_input('Average Pace (min/km)', 1.0, 15.0, step=0.1)
            distance = st.number_input('Distance (km)', 0.1, 100.0, step=0.1)
            
            if workout_type == 'incline_walk':
                incline = st.number_input('Incline (%)', 0.0, 15.0, step=0.5)
            else:
                incline = 0
                
        elif workout_type == 'rowing':
            pace = st.number_input('Average Pace (min/500m)', 1.0, 5.0, step=0.1)
            distance = st.number_input('Distance (meters)', 100, 10000, step=100) / 1000
            stroke_rate = st.number_input('Stroke Rate (spm)', 15, 40)
        
        submitted = st.form_submit_button('Add Workout')
        
        if submitted:
            workout = {
                'date': date.strftime('%Y-%m-%d'),
                'type': workout_type,
                'duration': duration_mins,
                'distance': distance,
                'heart_rate': heart_rate,
                'pace': pace,
                'vo2max': calculate_vo2max(
                    pace, 
                    heart_rate, 
                    workout_type,
                    incline if workout_type == 'incline_walk' else 0,
                    stroke_rate if workout_type == 'rowing' else 0
                )
            }
            st.session_state.workouts.append(workout)
            save_data()
            st.success('Workout added!')
            
            # Increment the form key to reset the form
            st.session_state.form_key += 1
            
            # Show recent workouts
            if st.session_state.workouts:
                st.subheader('Recent Workouts')
                df = pd.DataFrame(st.session_state.workouts[-3:])
                st.dataframe(
                    df.sort_values('date', ascending=False),
                    column_config={
                        "date": "Date",
                        "type": "Type",
                        "duration": "Duration (mins)",
                        "distance": st.column_config.NumberColumn("Distance (km)", format="%.2f"),
                        "heart_rate": "Heart Rate (bpm)",
                        "pace": st.column_config.NumberColumn("Pace (min/km)", format="%.1f"),
                        "vo2max": st.column_config.NumberColumn("VO₂ Max", format="%.1f")
                    },
                    hide_index=True
                )
            st.experimental_rerun()

def stats_page():
    st.header('📊 Workout Statistics')
    
    if st.session_state.workouts:
        df = pd.DataFrame(st.session_state.workouts)
        df['date'] = pd.to_datetime(df['date'])
        
        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Workouts", len(df))
        with col2:
            st.metric("Total Distance", f"{df['distance'].sum():.1f} km")
        with col3:
            st.metric("Avg VO₂ Max", f"{df['vo2max'].mean():.1f}")
        with col4:
            st.metric("Avg Pace", f"{df['pace'].mean():.1f} min/km")
        
        # VO2max trend
        st.subheader('VO₂ Max Trend')
        fig_vo2max = px.line(df, x='date', y='vo2max',
                           title='VO₂ Max Progress',
                           labels={'vo2max': 'VO₂ Max (ml/kg/min)', 'date': 'Date'})
        fig_vo2max.update_layout(
            height=400,
            showlegend=False,
            xaxis_title="Date",
            yaxis_title="VO₂ Max (ml/kg/min)"
        )
        st.plotly_chart(fig_vo2max, use_container_width=True)
        
        # Workout management section
        st.subheader('Manage Workouts')
        
        # Sort workouts by date (newest first)
        workouts = sorted(st.session_state.workouts, 
                         key=lambda x: x['date'], 
                         reverse=True)
        
        # Store the index to delete
        if 'workout_to_delete' not in st.session_state:
            st.session_state.workout_to_delete = None
        
        for idx, workout in enumerate(workouts):
            with st.expander(f"Workout on {workout['date']} - {workout['type']}"):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    new_duration = st.number_input('Duration (mins)', 
                                                 value=float(workout['duration']), 
                                                 key=f'dur_{idx}')
                    new_distance = st.number_input('Distance (km)', 
                                                 value=float(workout['distance']), 
                                                 key=f'dist_{idx}')
                
                with col2:
                    new_heart_rate = st.number_input('Heart Rate (bpm)', 
                                                    value=int(workout['heart_rate']), 
                                                    key=f'hr_{idx}')
                    new_pace = st.number_input('Pace (min/km)', 
                                             value=float(workout['pace']), 
                                             key=f'pace_{idx}')
                
                with col3:
                    if st.button('Update', key=f'update_{idx}'):
                        # Find the workout in the original list
                        original_idx = st.session_state.workouts.index(workout)
                        # Update the workout
                        st.session_state.workouts[original_idx].update({
                            'duration': new_duration,
                            'distance': new_distance,
                            'heart_rate': new_heart_rate,
                            'pace': new_pace,
                            'vo2max': calculate_vo2max(
                                new_pace,
                                new_heart_rate,
                                workout['type']
                            )
                        })
                        save_data()
                        st.success('Workout updated!')
                        st.experimental_rerun()
                    
                    if st.button('Delete', key=f'delete_{idx}', type='secondary'):
                        # Find the workout in the original list
                        original_idx = st.session_state.workouts.index(workout)
                        # Remove the workout
                        st.session_state.workouts.remove(workout)
                        save_data()
                        st.success('Workout deleted!')
                        st.experimental_rerun()
        
        # Download data
        st.download_button(
            label="📥 Download Workout Data",
            data=df.to_csv(index=False).encode('utf-8'),
            file_name='workouts.csv',
            mime='text/csv'
        )
    else:
        st.info('No workouts recorded yet. Add your first workout to see statistics!')

def main():
    load_data()  # Load saved data at startup
    st.title('🏃‍♂️ Fitness Tracker')
    
    # Sidebar for navigation
    with st.sidebar:
        st.image('assets/logo.png', width=100)
        st.header('Navigation')
        page = st.radio('', ['Profile', 'Add Workout', 'View Stats'])
    
    if page == 'Profile':
        profile_page()
    elif page == 'Add Workout':
        workout_page()
    elif page == 'View Stats':
        stats_page()

if __name__ == '__main__':
    main()