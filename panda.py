import pandas as pd
import matplotlib.pyplot as plt
from flask import Flask, render_template, request
from werkzeug.utils import secure_filename
import os
# Deployment (Flask Example)
app = Flask(__name__)

# Define upload folder
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Function to generate drivers
def generate_drivers(num_drivers):
    drivers = []
    for i in range(num_drivers):
        drivers.append(f"Driver {i+1}")
    return drivers

# Function to assign drivers
def assign_drivers(data, target_date):
    # Filter data for the target date
    data = data[data['Pick-up Date'] == target_date]

    # Sort filtered data by pickup time
    data.sort_values(by=['PU Time'], inplace=True)

    # Create a list of 40 drivers dynamically
    drivers = generate_drivers(35)
    last_assigned_times = {driver: pd.Timestamp.now() for driver in drivers} 
    driver_assignments = []

    for index, row in data.iterrows():
        # Combine date and time into a single datetime object
        pu_datetime = pd.Timestamp.combine(row['Pick-up Date'], row['PU Time'])

        # Filter drivers that are available
        available_drivers = []
        for driver in drivers:
            if last_assigned_times[driver] + pd.Timedelta(hours=3) <= pu_datetime:
                available_drivers.append(driver)

        # Assign the first available driver to the current row
        if available_drivers:
            driver = available_drivers[0]
            driver_assignments.append((row['Pick-up Date'], row['PU Airport'], row['PU Time'], driver))
            last_assigned_times[driver] = pu_datetime  # Update last assigned time for the driver
        else:
            # If no available driver found, assign 'No Driver'
            driver_assignments.append((row['Pick-up Date'], row['PU Airport'], row['PU Time'], 'No Driver'))

    return driver_assignments

# Function to count assignments
def count_assignments(driver_assignments):
    counts = {}
    for assignment in driver_assignments:
        driver = assignment[3]  # Driver name is in the 4th position of the tuple
        if driver != 'No Driver':
            counts[driver] = counts.get(driver, 0) + 1
    return counts

# Route for uploading file
@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        file = request.files['file']
        if file:
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            return render_template('upload_success.html', filename=filename)
    return render_template('upload.html')

# Route for processing data
@app.route('/process', methods=['POST'])
def process_data():
    # Get uploaded file path
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], request.form['filename'])
    
    # Read data from uploaded Excel file
    data = pd.read_excel(file_path)

    # Get target date from form
    target_date = request.form['target_date']

    # Call assign_drivers function for the target date
    assigned_data = assign_drivers(data, target_date)
    
    # Create DataFrame from assigned_data
    df = pd.DataFrame(assigned_data, columns=['Pick-up Date', 'PU Airport', 'PU Time', 'Driver'])
    
    # Render DataFrame as HTML table
    table_html = df.to_html(index=False, classes='table table-striped')
    counts = count_assignments(assigned_data)
    return render_template('index.html', table=table_html, counts=counts)

# Route for visualization
@app.route('/visualize', methods=['POST'])
def visualize():
    # Get table HTML and counts from form data
    table_html = request.form['table_html']
    counts = eval(request.form['counts'])  # Convert string representation of dictionary to dictionary
    
    # Visualize counts
    plt.figure(figsize=(8, 6))
    plt.bar(counts.keys(), counts.values(), color='skyblue')
    plt.xlabel('Driver')
    plt.ylabel('Count')
    plt.title('Driver Counts')
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.tight_layout()
    
    # Save the visualization as an image
    os.makedirs('static', exist_ok=True)
    file_path = os.path.join('static', 'driver_counts.png')
    plt.savefig(file_path) 
    plt.close()
    
    return render_template('visualize.html', table=table_html, file_path=file_path)

@app.route('/')
def index():
    return render_template('main.html')

if __name__ == '__main__':
    app.run(debug=True)
