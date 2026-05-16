from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import numpy as np
import pickle
import pandas as pd
from datetime import datetime, timedelta

# Load the CSV data once when the app starts
historical_data = pd.read_csv('./final_testing_data.csv')
historical_data["datetime"] = pd.to_datetime(historical_data["datetime"])

# Print available date range for debugging
print(f"Available data range: {historical_data['datetime'].min()} to {historical_data['datetime'].max()}")
print(f"Total data points: {len(historical_data)}")

# Exclude specified columns
excluded_columns = ['DELHI', 'BRPL', 'BYPL', 'NDPL', 'NDMC', 'MES', 'datetime']
feature_columns = [col for col in historical_data.columns if col not in excluded_columns]

# Set datetime as index after selecting required columns
historical_data = historical_data[['datetime'] + feature_columns]
historical_data.set_index("datetime", inplace=True)

def create_input_sequences(start_datetime, end_datetime, feature_scaler, sequence_length=12):
    """
    Create input sequences for the model from a given date range with 5-minute intervals.
    
    Parameters:
        start_datetime (str): The start datetime in 'YYYY-MM-DD HH:MM:SS' format.
        end_datetime (str): The end datetime in 'YYYY-MM-DD HH:MM:SS' format.
        feature_scaler (scaler object): Scaler to normalize the feature data.
        sequence_length (int): Number of 5-minute intervals to form a sequence (default: 12 for 1 hour).
    
    Returns:
        np.array: Input sequences for the model.
        pd.DatetimeIndex: Corresponding timestamps for sequences.
    """
    # Convert timestamps to datetime
    start_time = pd.to_datetime(start_datetime)
    end_time = pd.to_datetime(end_datetime)
    
    # Get the data for the specified time window
    mask = (historical_data.index >= start_time) & (historical_data.index <= end_time)
    sequence_data = historical_data.loc[mask]
    
    # Check if we have enough data
    if len(sequence_data) < sequence_length:
        raise ValueError(f"Insufficient data: At least {sequence_length} rows are required, but found {len(sequence_data)}.")

    # Handle missing timestamps by forward-filling or interpolating
    sequence_data = sequence_data.resample('5T').mean().interpolate()
    
    # Get features for the model
    sequence_data = sequence_data[feature_columns]  # Ensure 'feature_columns' are predefined
    
    # Scale the data
    scaled_data = feature_scaler.transform(sequence_data)
    
    # Create sequences
    X_sequences = []
    timestamps = []
    for i in range(len(scaled_data) - sequence_length + 1):
        X_sequences.append(scaled_data[i:i + sequence_length])
        timestamps.append(sequence_data.index[i + sequence_length - 1])  # Timestamp for the last step in the sequence

    X_sequences = np.array(X_sequences)
    
    # Debug information
    print(f"Processed sequence data shape: {sequence_data.shape}")
    print(f"Number of sequences created: {len(X_sequences)}")
    print(f"Sequence input shape for model: {X_sequences.shape}")
    
    return X_sequences, pd.DatetimeIndex(timestamps)

app = Flask(__name__)
CORS(app)  # Enable CORS for all domains

# Load the model and scalers
try:
    # Load model and scalers from pkl files
    with open('40model.pkl', 'rb') as file:
        model = pickle.load(file)
    
    with open('40fs.pkl', 'rb') as f_file:
        feature_scalar = pickle.load(f_file)
    
    with open('40ts.pkl', 'rb') as t_file:
        target_scalar = pickle.load(t_file)
        
except Exception as e:
    model = None
    print(f"Error loading model or scaler: {str(e)}")

@app.route('/predict', methods=['POST'])
def predict():
    try:
        print("Received a request to the /predict endpoint.")

        # Check if model is loaded
        if model is None:
            print("Error: Model not loaded properly.")
            return jsonify({'error': 'Model not loaded properly'}), 500

        
        # Get input data from request
        data = request.get_json()
        print(f"Input data received: {data}")
        print("////////////////////////////////////")
        # Validate input data
        if not data or 'startDateTime' not in data or 'endDateTime' not in data:
            print("Error: Start or end datetime not provided in input data.")
            return jsonify({'error': 'Please provide both startDateTime and endDateTime in the request'}), 400

        try:
            # Create input sequences using the provided datetime range
            input_sequences, timestamps = create_input_sequences(
                data['startDateTime'], 
                data['endDateTime'], 
                feature_scalar
            )
            
            # Make predictions
            print("Making predictions...")
            predictions = model.predict(input_sequences)
            
            # Inverse transform predictions
            predictions = target_scalar.inverse_transform(predictions.reshape(-1, 1))
            
            # Create response with predictions for each timestamp
            response_data = {
                'success': True,
                'predictions': [
                    {
                        'timestamp': ts.isoformat(),
                        'value': float(pred[0])  # Extract single value from prediction
                    }
                    for ts, pred in zip(timestamps, predictions)
                ],
                'metadata': {
                    'number_of_predictions': len(predictions),
                    'features_used': feature_columns,
                    'time_range': {
                        'start': timestamps[0].isoformat(),
                        'end': timestamps[-1].isoformat()
                    }
                }
            }
            
            return jsonify(response_data)
            
        except ValueError as ve:
            print(f"Value Error: {str(ve)}")
            return jsonify({'error': str(ve)}), 400
        except Exception as e:
            print(f"Error processing input: {str(e)}")
            return jsonify({'error': f'Error processing input: {str(e)}'}), 400

    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
