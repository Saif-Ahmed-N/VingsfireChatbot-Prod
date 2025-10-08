import pandas as pd
import os
from collections import defaultdict

# --- Configuration: Define all your service files here ---
SERVICE_FILES = {
    "App Development": "App_Development_Consolidated.xlsx", 
    "Web Development": "Web_Development_Pricing_Models.xlsx",
    "Digital Marketing Services": "Digital_Marketing_Pricing_Models.xlsx",
    "SEO Services": "SEO_Services_Pricing_Models.xlsx",
    "AI Development Services": "AI_Development_Pricing_Models.xlsx",
    "Software Development Services": "Software_Development_Pricing_Models.xlsx"
}

def load_service_data():
    """
    Loads data from all service files. Assumes all files now contain the 'sub_category'
    column for consistent grouping.
    """
    app_sub_category_definitions = defaultdict(list)
    all_dataframes = []
    
    print("Searching for service pricing files...")
    for main_service, file_path in SERVICE_FILES.items():
        if os.path.exists(file_path):
            try:
                print(f"Found and loading '{file_path}' for '{main_service}'...")
                df = pd.read_excel(file_path)
                df['main_service'] = main_service
                all_dataframes.append(df)
            except Exception as e:
                print(f"WARNING: Could not read the file '{file_path}'. Error: {e}")
        else:
            print(f"INFO: File '{file_path}' not found, skipping.")

    if not all_dataframes:
        print("ERROR: No valid service data files were found.")
        return None, None, None, None

    master_df = pd.concat(all_dataframes, ignore_index=True)
    
    # --- Step 1: Robust Data Cleaning and Normalization ---
    # Fill pandas NaN values with an empty string
    master_df = master_df.fillna('')
    
    # Normalize keys: convert all object columns to string type and strip whitespace
    for col in master_df.select_dtypes(include=['object']).columns:
        master_df[col] = master_df[col].astype(str).str.strip()
        
    # Crucial Fix: Ensure the sub_category key is usable.
    # Replace empty strings (''), the literal 'nan' string, and any remnants of missing data with '_default'
    master_df['sub_category'] = master_df['sub_category'].replace({
        '': '_default', 
        'nan': '_default'
    })
    
    # Ensure 'category' is not empty (a critical key)
    master_df['category'] = master_df['category'].replace({'': 'Untitled Category'})
    

    # --- Step 2: Process and structure the data ---
    try:
        grouped_data = defaultdict(lambda: defaultdict(dict))
        sub_categories_for_other_services = defaultdict(list)

        for row in master_df.to_dict('records'):
            main_service = row['main_service']
            category = row['category']
            # sub_cat is guaranteed to be a valid name or '_default'
            sub_cat = row['sub_category'] 

            if main_service and category:
                grouped_data[main_service][sub_cat][category] = row
                
                # Build the App Development definition structure for UI buttons
                if main_service == "App Development" and sub_cat != '_default':
                    app_sub_category_definitions[sub_cat].append(category)

                # Collect unique sub-categories for non-App services
                if main_service != "App Development" and sub_cat != '_default' and sub_cat not in sub_categories_for_other_services[main_service]:
                    sub_categories_for_other_services[main_service].append(sub_cat)

        main_services_list = sorted(list(grouped_data.keys()))
        print(f"Successfully loaded and grouped data for services: {main_services_list}")
        
        # Clean up the App Development definitions (remove duplicates, sort)
        cleaned_app_defs = {k: sorted(list(set(v))) for k, v in app_sub_category_definitions.items()}

        # Return 4 items: raw data, main service list, sub-cats for other services, and the detailed app dev map
        return grouped_data, main_services_list, dict(sub_categories_for_other_services), cleaned_app_defs

    except KeyError as e:
        print(f"ERROR: A required column is missing from one of your Excel files. Ensure 'category' and 'sub_category' are present: {e}.")
        return None, None, None, None
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None, None, None, None