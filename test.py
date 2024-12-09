import csv
from datetime import datetime

def save_to_csv_auto(csv_data):
    """
    Saves a list of strings with CSV format (e.g., "a,b,c") to a CSV file with an auto-generated name.
    
    :param csv_data: List of strings, where each string represents a row in "a,b,c" format.
    """
    # Generate a unique file name based on the current date and time
    file_name = datetime.now().strftime("data_%Y%m%d_%H%M%S.csv")
    
    try:
        # Open the file in write mode
        with open(file_name, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)

            # Process each string in csv_data
            for row in csv_data:
                # Split the string by ',' to create a list of values
                writer.writerow(row.split(','))
        
        print(f"Data saved to {file_name} successfully.")
    except Exception as e:
        print(f"Error saving to CSV: {e}")

# Example usage
csv_data = ["1,2,3", "3,4,5", "6,7,8"]
save_to_csv_auto(csv_data)
