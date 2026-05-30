import pandas as pd
import os
import glob

def merge_wind_files():
    input_dir = 'wind_outputs'
    output_file = 'merged_wind_data.xlsx'
    
    # 1. Check if the directory exists
    if not os.path.exists(input_dir):
        print(f"Error: The folder '{input_dir}' does not exist.")
        return

    # 2. Get a list of all .xlsx files in that folder
    # This uses glob to find everything ending in .xlsx
    file_list = glob.glob(os.path.join(input_dir, "*.xlsx"))
    
    if not file_list:
        print("No Excel files found to merge.")
        return

    print(f"Found {len(file_list)} files. Starting merge...")

    # 3. Read each file and add it to a list
    all_data = []
    for file in file_list:
        df = pd.read_excel(file)
        all_data.append(df)
        print(f"Imported: {os.path.basename(file)}")

    # 4. Concatenate (stack) all dataframes together
    merged_df = pd.concat(all_data, ignore_index=True)

    # 5. Save the final result
    merged_df.to_excel(output_file, index=False)
    print(f"\nSuccess! All data merged into: {output_file}")

if __name__ == "__main__":
    merge_wind_files()