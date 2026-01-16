import streamlit as st
import pandas as pd
import os
from ai_processor import process_ai_analysis

# 1. PERSISTENCE LAYER (Keeps results visible)
if "data" not in st.session_state:
    st.session_state.data = None

st.set_page_config(page_title="Edu-Portal 2026", layout="wide")

# Sidebar Navigation
st.sidebar.title("🏫 School AI Portal")
role = st.sidebar.radio("Switch View:", [" Teacher Dashboard", " Student Dashboard"])

# --- TEACHER DASHBOARD ---
if role == " Teacher Dashboard":
    st.title("Teacher Administration Panel")
    t_tab1, t_tab2, t_tab3 = st.tabs([" Mode 1: Analytics", " Mode 2: Deep Dive", " Note Sharing"])

    with t_tab1:
        st.subheader("General Performance (Mode 1)")
        m1_file = st.file_uploader("Upload Marksheet PDF", type="pdf", key="m1_up")
        if st.button("Process Mode 1") and m1_file:
            with st.spinner("AI analyzing marks..."):
                st.session_state.data = process_ai_analysis(m1_file)
                st.rerun()

    with t_tab2:
        st.subheader("Question & Paper Analysis (Mode 2)")
        col_m, col_q = st.columns(2)
        m2_m = col_m.file_uploader("Question-wise Marks PDF", type="pdf", key="m2m")
        m2_q = col_q.file_uploader("Question Paper PDF", type="pdf", key="m2q")
        if st.button("Process Mode 2") and m2_m and m2_q:
            with st.spinner("Deep Analyzing Questions..."):
                st.session_state.data = process_ai_analysis(m2_m, m2_q)
                st.rerun()

    # Shared Teacher Results
    if st.session_state.data:
        res = st.session_state.data
        if "error" in res:
            st.error(f"API Error: {res['error']}")
        elif "students" in res:
            df = pd.DataFrame(res["students"])
            st.divider()
            st.header("Overall Class Analytics")
            k1, k2 = st.columns(2)
            k1.metric("Class Average", f"{df['percentage'].mean():.1f}%")
            k2.write("### Quick Overview")
            st.dataframe(df[["name", "percentage", "strong_subjects", "weak_subjects"]])
            
            # Mode 2 Global Metrics
            if "mistake_type" in df.columns:
                st.warning(f" Most Common Class Error: {df['mistake_type'].mode()[0]}")

    with t_tab3:
        st.subheader("Upload Notes for Students")
        n_up = st.file_uploader("Upload PDF/Doc")
        if n_up and st.button("Publish to Dashboard"):
            if not os.path.exists("class_notes"): os.makedirs("class_notes")
            with open(os.path.join("class_notes", n_up.name), "wb") as f:
                f.write(n_up.getbuffer())
            st.success("File shared successfully!")

# --- STUDENT DASHBOARD ---
elif role == "👨‍🎓 Student Dashboard":
    st.title("Student Personal Portal")
    st.info("👋 Welcome! Results are not yet available. Please wait for the teacher.")
    
    if not st.session_state.data or "students" not in st.session_state.data:
        st.info("👋 Welcome! Results are not yet available. Please wait for the teacher.")
    else:
        # PRIVACY FILTER: Student picks only their name
        students = st.session_state.data["students"]
        choice = st.selectbox("Select your name to view your Private Report:", ["-- Choose Name --"] + [s["name"] for s in students])

        if choice != "-- Choose Name --":
            # Filter the list to only the selected student
            s_data = next(s for s in students if s["name"] == choice)
            
            s_tab1, s_tab2, s_tab3 = st.tabs([" My Report (M1)", " AI Feedback (M2)", " Notes"])

            with s_tab1:
                st.header(f"Performance: {choice}")
                st.metric("Overall Percentage", f"{s_data['percentage']}%")
                
                c_left, c_right = st.columns(2)
                with c_left:
                    st.write("### Subject-wise Marks")
                    st.bar_chart(pd.Series(s_data["marks"]))
                with c_right:
                    st.success(f"🌟 **Strong Subjects:** {', '.join(s_data.get('strong_subjects', []))}")
                    st.error(f"⚠️ **Weak Subjects:** {', '.join(s_data.get('weak_subjects', []))}")

            with s_tab2:
                if "q_marks" in s_data:
                    st.header("Question-wise Diagnosis")
                    st.table(pd.Series(s_data["q_marks"], name="Marks Scored"))
                    
                    err = s_data.get("mistake_type", "None")
                    st.subheader("Why did I lose marks?")
                    if err == "Calculation mistake":
                        st.warning(f"❌ **{err}**: You know the concept, but made a math error. Practice speed-tests.")
                    elif err == "Concept error":
                        st.error(f"❌ **{err}**: You need to re-read the core logic of this chapter.")
                    elif err == "Formula error":
                        st.info(f"❌ **{err}**: You used the wrong formula. Try making a formula sheet.")
                    
                    st.info(f"**AI Tip:** {s_data.get('suggestions', 'Keep it up!')}")
                else:
                    st.warning("Deep Analysis (Mode 2) data is not available for this test.")

            with s_tab3:
                st.header("Class Downloads")
                if os.path.exists("class_notes") and os.listdir("class_notes"):
                    for file in os.listdir("class_notes"):
                        st.download_button(f" Download {file}", open(f"class_notes/{file}", "rb"), file_name=file)
                else:
                    st.write("No files shared yet.")