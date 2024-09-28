import streamlit as st
import pandas as pd
from datetime import datetime, date
from interact_with_contract import create_trial, update_trial, get_trial, get_trial_count, get_accounts, web3
from ipfs import add_csv_to_ipfs, get_csv_from_ipfs

# Page Config
st.set_page_config(page_title="MedChainTrial", page_icon="🔬", layout="wide")
st.title("MedChainTrials: Decentralized Clinical Trial Data Assurance Platform")
# Sidebar for account selection
accounts = get_accounts()
selected_account = st.sidebar.selectbox("Select Account", accounts)

# Debugging information in the sidebar
with st.sidebar.expander("Debug Information", expanded=True):
    st.write("Current Account:", selected_account)
    st.write("Contract Address:", "0x497615B8bbf78A188870251a17565Fc038fAD45F")
    st.write("IPFS Node URL:", "http://127.0.0.1:5001")  # Adjust this to your IPFS node address
    
    if st.button("Check Contract Connection"):
        try:
            trial_count = get_trial_count()
            st.success(f"Successfully connected to the contract. Current trial count: {trial_count}")
        except Exception as e:
            st.error(f"Failed to connect to the contract: {str(e)}")
    
    if st.button("Check IPFS Connection"):
        try:
            # Try to add a simple file to IPFS
            test_hash = add_csv_to_ipfs(pd.DataFrame({'test': [1, 2, 3]}))
            st.success(f"Successfully connected to IPFS. Test hash: {test_hash}")
        except Exception as e:
            st.error(f"Failed to connect to IPFS: {str(e)}")

# Create tabs
tab1, tab2, tab3, tab4 = st.tabs(["🔍 Create Trial", "🔄 Update Trial", "📊 View Trials", "📁 Upload Dataset"])

# Tab 1: Create New Trial (Disease-specific inputs)
with tab1:
    st.header("Create a New Trial")
    st.markdown("Please fill in the details to register a new trial.")

    patient_id = st.text_input("Patient ID", help="Enter the unique Patient ID.")
    patient_name = st.text_input("Patient Name", help="Enter the patient's full name.")

    # Disease selection
    disease = st.selectbox("Select Disease for the Trial", ["Diabetes", "Hypertension", "Cancer", "Cardiovascular"])

    # Gender-specific or age-specific logic
    cancer_type = None
    restricted_gender = None
    restricted_age = None

    # Dynamically change input fields based on disease selection
    if disease == "Diabetes":
        medication = st.text_input("Medication for Diabetes", help="Enter the medication or treatment being tested for Diabetes.")
        dosage = st.text_input("Dosage (mg)", help="Enter the dosage of the medication.")
        blood_sugar_level = st.number_input("Blood Sugar Level (mg/dL)", min_value=50, max_value=500, help="Enter the patient's blood sugar level.")
    
    elif disease == "Hypertension":
        medication = st.text_input("Medication for Hypertension", help="Enter the medication or treatment being tested for Hypertension.")
        dosage = st.text_input("Dosage (mg)", help="Enter the dosage of the medication.")
        blood_pressure = st.text_input("Blood Pressure (mmHg)", help="Enter the patient's blood pressure.")
    
    elif disease == "Cancer":
        cancer_type = st.selectbox("Cancer Type", ["Breast Cancer (Female)", "Ovarian Cancer (Female)", "Prostate Cancer (Male)", "Lung Cancer"])
        
        # Restrict gender based on cancer type
        if "Female" in cancer_type:
            restricted_gender = "Female"
        elif "Male" in cancer_type:
            restricted_gender = "Male"

        medication = st.text_input("Chemotherapy/Medication", help="Enter the medication or treatment being tested for Cancer.")
        dosage = st.text_input("Dosage (mg)", help="Enter the dosage of the medication.")
        cancer_stage = st.selectbox("Cancer Stage", ["Stage I", "Stage II", "Stage III", "Stage IV"])
    
    elif disease == "Cardiovascular":
        medication = st.text_input("Medication for Cardiovascular Disease", help="Enter the medication or treatment being tested.")
        dosage = st.text_input("Dosage (mg)", help="Enter the dosage of the medication.")
        cholesterol_level = st.number_input("Cholesterol Level (mg/dL)", min_value=100, max_value=400, help="Enter the patient's cholesterol level.")

    # Common input fields
    
    patient_dob = st.date_input("Patient Date of Birth", min_value=date(1900, 1, 1), max_value=date.today())
    patient_gender = st.selectbox("Patient Gender", ["Male", "Female", "Other"], disabled=True if restricted_gender else False, index=["Male", "Female", "Other"].index(restricted_gender) if restricted_gender else 0)

    # Age validation for age-specific conditions
    age = (date.today() - patient_dob).days // 365
    if cancer_type and cancer_type == "Ovarian Cancer (Female)" and age < 18:
        st.warning("Ovarian Cancer trials are typically for patients above 18 years old.")
    
    patient_condition = st.text_area("Patient Condition", help="Describe the patient's medical condition.")
    treatment_group = st.selectbox("Treatment Group", ["Control", "Experimental"])
    start_date = st.date_input("Trial Start Date")
    end_date = st.date_input("Expected End Date")

    if st.button("Submit New Trial"):
        try:
            if not all([patient_id, patient_name, patient_condition, medication, dosage]):
                st.warning("All fields marked with * are required.")
            else:
                trial_count = get_trial_count() + 1
                trial_name = f"Trial ID {trial_count} - {patient_name} - {disease}"

                patient_data = {
                    "Trial Name": [trial_name],
                    "Disease": [disease],
                    "Patient ID": [patient_id],
                    "Patient Name": [patient_name],
                    "Date of Birth": [patient_dob],
                    "Age": [age],
                    "Gender": [patient_gender],
                    "Condition": [patient_condition],
                    "Treatment Group": [treatment_group],
                    "Medication": [medication],
                    "Dosage": [dosage],
                    "Start Date": [start_date],
                    "Expected End Date": [end_date]
                }

                if disease == "Diabetes":
                    patient_data["Blood Sugar Level"] = [blood_sugar_level]
                elif disease == "Hypertension":
                    patient_data["Blood Pressure"] = [blood_pressure]
                elif disease == "Cancer":
                    patient_data["Cancer Stage"] = [cancer_stage]
                elif disease == "Cardiovascular":
                    patient_data["Cholesterol Level"] = [cholesterol_level]

                df = pd.DataFrame(patient_data)
                ipfs_hash = add_csv_to_ipfs(df)
                with st.spinner("Submitting trial..."):
                    tx_receipt = create_trial(patient_id, ipfs_hash, selected_account)
                st.success(f"Trial created successfully! IPFS Hash: {ipfs_hash}")
        except Exception as e:
            st.error(f"Error creating trial: {str(e)}")

# Tab 2: Update Existing Trial
with tab2:
    st.header("Update Existing Trial")
    st.markdown("Update the trial status and additional information.")
    
    trial_id = st.number_input("Trial ID", min_value=1, step=1, help="Enter the Trial ID.")
    
    if st.button("Fetch Trial Data"):
        try:
            trial = get_trial(trial_id)
            if trial:
                df = get_csv_from_ipfs(trial[2])
                st.session_state.current_trial_data = df
                st.session_state.trial = trial
                st.success("Trial data fetched successfully!")
            else:
                st.warning(f"No trial found with ID {trial_id}.")
        except Exception as e:
            st.error(f"Error fetching trial data: {str(e)}")
    
    if 'current_trial_data' in st.session_state:
        df = st.session_state.current_trial_data
        trial = st.session_state.trial
        
        new_status = st.selectbox("Trial Status", ["Active", "Completed", "Suspended"], index=trial[3])
        
        st.subheader("Update Trial Information")
        updated_data = {}
        for column in df.columns:
            if column in ['Trial Name', 'Patient ID', 'Patient Name', 'Date of Birth', 'Gender']:
                updated_data[column] = st.text_input(f"{column}", df[column].iloc[0], disabled=True)
            elif column in ['Age']:
                updated_data[column] = st.number_input(f"{column}", value=int(df[column].iloc[0]), disabled=True)
            elif column in ['Start Date', 'Expected End Date']:
                updated_data[column] = st.date_input(f"{column}", pd.to_datetime(df[column].iloc[0]).date())
            else:
                updated_data[column] = st.text_input(f"{column}", df[column].iloc[0])
        
        additional_notes = st.text_area("Additional Notes", help="Enter any additional information or updates.")
        
        if st.button("Update Trial"):
            try:
                updated_df = pd.DataFrame(updated_data, index=[0])
                if additional_notes:
                    updated_df['Additional Notes'] = additional_notes
                new_ipfs_hash = add_csv_to_ipfs(updated_df)
                status_map = {"Active": 0, "Completed": 1, "Suspended": 2}
                with st.spinner("Updating trial..."):
                    tx_receipt = update_trial(trial_id, new_ipfs_hash, status_map[new_status], selected_account)
                st.success(f"Trial updated successfully. New IPFS Hash: {new_ipfs_hash}")
            except Exception as e:
                st.error(f"Error updating trial: {str(e)}")

# Tab 3: View and Download Trials
with tab3:
    st.header("View Trials")
    
    try:
        trial_count = get_trial_count()
        st.info(f"Total Number of Trials: {trial_count}")
    except Exception as e:
        st.error(f"Error fetching trial count: {str(e)}")
    
    trial_id_view = st.number_input("Enter Trial ID to view", min_value=1, step=1, help="Enter the Trial ID to fetch details.")
    
    if st.button("View Trial"):
        try:
            trial = get_trial(trial_id_view)
            st.write(f"**Trial ID**: {trial[0]}")
            st.write(f"**Patient ID**: {trial[1]}")
            st.write(f"**IPFS Hash**: {trial[2]}")
            st.write(f"**Status**: {['Active', 'Completed', 'Suspended'][trial[3]]}")
            st.write(f"**Researcher**: {trial[4]}")
            st.write(f"**Start Date**: {datetime.fromtimestamp(trial[5])}")
            st.write(f"**Last Updated**: {datetime.fromtimestamp(trial[6])}")
            
            if not trial[2]:
                st.warning("No data available for this trial. The IPFS hash is empty.")
            else:
                try:
                    df = get_csv_from_ipfs(trial[2])
                    st.dataframe(df)
                except Exception as ipfs_error:
                    st.error(f"Error retrieving data from IPFS: {str(ipfs_error)}")
        except Exception as e:
            st.error(f"Error viewing trial: {str(e)}")

    if st.button("Download All Trials"):
        try:
            all_trials = []
            for i in range(1, trial_count + 1):
                trial = get_trial(i)
                if trial[2]:
                    try:
                        df = get_csv_from_ipfs(trial[2])
                        df["Trial ID"] = trial[0]
                        df["Status"] = ['Active', 'Completed', 'Suspended'][trial[3]]
                        df["Researcher"] = trial[4]
                        df["Start Date"] = datetime.fromtimestamp(trial[5])
                        df["Last Updated"] = datetime.fromtimestamp(trial[6])
                        all_trials.append(df)
                    except Exception as ipfs_error:
                        st.warning(f"Could not retrieve data for Trial ID {trial[0]}: {str(ipfs_error)}")
                else:
                    st.warning(f"No data available for Trial ID {trial[0]}")
            
            if all_trials:
                all_trials_df = pd.concat(all_trials, ignore_index=True)
                csv = all_trials_df.to_csv(index=False)
                
                st.download_button(
                    label="Download all trials as CSV",
                    data=csv,
                    file_name='all_trials.csv',
                    mime='text/csv'
                )
            else:
                st.warning("No trial data available to download.")
        except Exception as e:
            st.error(f"Error downloading all trials: {str(e)}")

# Tab 4: Upload Dataset
with tab4:
    st.header("Upload a Dataset")
    uploaded_file = st.file_uploader("Choose a CSV file", type="csv")
    
    if uploaded_file is not None:
        try:
            # Read CSV and display it
            dataset = pd.read_csv(uploaded_file)
            st.dataframe(dataset)
            
            # Add dataset to IPFS
            if st.button("Upload Dataset to IPFS"):
                with st.spinner("Uploading dataset to IPFS..."):
                    ipfs_hash = add_csv_to_ipfs(dataset)
                    st.success(f"Dataset uploaded to IPFS successfully! IPFS Hash: {ipfs_hash}")
        except Exception as e:
            st.error(f"Error uploading dataset: {str(e)}")
