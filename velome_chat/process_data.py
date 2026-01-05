import pandas as pd
import os

DATA_DIR = r"c:\Users\ashmi\Videos\Velome\velome_chat\data"
excel_file = os.path.join(DATA_DIR, "Destinations List Countries and Regions with details.xlsx")
ods_file = os.path.join(DATA_DIR, "Selling Price list - Countries & Regions.ods")
output_md = os.path.join(DATA_DIR, "destination_data.md")

def process_data():
    print("Loading data...")
    # Load Pricing
    df_price = pd.read_excel(ods_file, engine="odf")
    df_price = df_price[['Country', 'Selling Price (Per Day) (INR)']].dropna(subset=['Country'])
    df_price.rename(columns={'Selling Price (Per Day) (INR)': 'Price'}, inplace=True)
    
    # Load Details
    df_details = pd.read_excel(excel_file)
    # Clean up column names (strip whitespace)
    df_details.columns = df_details.columns.str.strip()
    
    # Merge on Country
    # Ensure consistent casing
    df_price['Country_Key'] = df_price['Country'].str.strip().str.lower()
    df_details['Country_Key'] = df_details['Country'].str.strip().str.lower()
    
    merged = pd.merge(df_price, df_details, on='Country_Key', how='outer', suffixes=('', '_details'))
    
    # Prioritize the 'Country' name from Price list, fallback to Details list
    merged['Country_Name'] = merged['Country'].fillna(merged['Country_details'])
    
    markdown_content = "# Verified Destination Pricing and Details\n\n"
    
    for _, row in merged.iterrows():
        country = row['Country_Name']
        if pd.isna(country): continue
        
        price = row['Price']
        network = row.get('Network', 'N/A')
        speed = row.get('Speed', 'N/A')
        plan = row.get('Plan Type', 'N/A')
        tethering = row.get('Tethering/Hotspot', 'N/A')
        ekyc = row.get('eKYC', 'N/A')
        
        markdown_content += f"## {country}\n"
        
        # Handle pricing value safely
        try:
             # Try to convert to float first (handles 250.0), then int
             clean_price = int(float(price))
             markdown_content += f"- **Daily Rate**: ₹{clean_price}\n"
        except (ValueError, TypeError):
             # Keep as string if it's text like "Fixed Price"
             markdown_content += f"- **Daily Rate**: {price}\n"
            
        markdown_content += f"- **Network**: {network}\n"
        markdown_content += f"- **Speed**: {speed}\n"
        markdown_content += f"- **Plan Type**: {plan}\n"
        markdown_content += f"- **Hotspot**: {tethering}\n"
        markdown_content += f"- **eKYC Required**: {ekyc}\n"
        markdown_content += "\n"
        
    with open(output_md, "w", encoding="utf-8") as f:
        f.write(markdown_content)
        
    print(f"Successfully wrote {len(merged)} records to {output_md}")

if __name__ == "__main__":
    process_data()
