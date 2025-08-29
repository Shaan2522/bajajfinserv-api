from flask import Flask, request, jsonify
from flask_cors import CORS
from collections import OrderedDict
import json
import logging
import traceback

app = Flask(__name__)
CORS(app)

# Configure Flask to preserve JSON key order
app.config['JSON_SORT_KEYS'] = False

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def validate_input(data):
    """Validate input data"""
    if data is None:
        return False, "Data cannot be null"
    
    if not isinstance(data, list):
        return False, "Data must be an array"
    
    if len(data) == 0:
        return False, "Data array cannot be empty"
    
    if len(data) > 1000:  # Reasonable limit
        return False, "Data array too large (max 1000 elements)"
    
    return True, None

def safe_string_convert(item):
    """Safely convert item to string"""
    try:
        if item is None:
            return ""
        return str(item).strip()
    except Exception as e:
        logger.warning(f"Error converting item to string: {e}")
        return ""

def process_data(data):
    """Process the input data array and return categorized results"""
    
    try:
        # Initialize arrays
        numbers = []
        alphabets = []
        special_characters = []
        
        # Process each item in the data array
        for item in data:
            try:
                # Convert item to string safely
                str_item = safe_string_convert(item)
                
                if not str_item:  # Skip empty strings
                    continue
                
                # Check if it's a number (including multi-digit)
                if str_item.isdigit():
                    numbers.append(str_item)
                # Check if it's alphabetic
                elif str_item.isalpha():
                    alphabets.append(str_item.upper())
                # Otherwise it's a special character or mixed
                else:
                    # Check if it contains any alphabetic characters
                    has_alpha = any(c.isalpha() for c in str_item)
                    has_digit = any(c.isdigit() for c in str_item)
                    
                    if has_alpha or has_digit:
                        # Extract alphabetic characters and convert to uppercase
                        alpha_chars = ''.join([c.upper() for c in str_item if c.isalpha()])
                        if alpha_chars:
                            alphabets.append(alpha_chars)
                        
                        # Extract numeric characters
                        digit_chars = ''.join([c for c in str_item if c.isdigit()])
                        if digit_chars:
                            numbers.append(digit_chars)
                        
                        # Extract special characters
                        special_chars = ''.join([c for c in str_item if not c.isalnum()])
                        if special_chars:
                            special_characters.append(special_chars)
                    else:
                        # Pure special character
                        special_characters.append(str_item)
                        
            except Exception as e:
                logger.warning(f"Error processing item '{item}': {e}")
                # Add to special characters if processing fails
                special_characters.append(safe_string_convert(item))
        
        # Separate odd and even numbers
        odd_numbers = []
        even_numbers = []
        total_sum = 0
        
        for num_str in numbers:
            try:
                num = int(num_str)
                total_sum += num
                if num % 2 == 0:
                    even_numbers.append(num_str)
                else:
                    odd_numbers.append(num_str)
            except ValueError as e:
                logger.warning(f"Error converting '{num_str}' to integer: {e}")
                # If conversion fails, treat as special character
                special_characters.append(num_str)
        
        # Create concatenation string (reverse order, alternating caps)
        concat_string = ""
        try:
            if alphabets:
                # Get all alphabetic characters from the original data
                all_alpha_chars = []
                for item in data:
                    str_item = safe_string_convert(item)
                    for char in str_item:
                        if char.isalpha():
                            all_alpha_chars.append(char)
                
                # Reverse the order
                all_alpha_chars.reverse()
                
                # Apply alternating caps
                for i, char in enumerate(all_alpha_chars):
                    if i % 2 == 0:
                        concat_string += char.upper()
                    else:
                        concat_string += char.lower()
        except Exception as e:
            logger.warning(f"Error creating concatenation string: {e}")
            concat_string = ""
        
        return {
            "odd_numbers": odd_numbers,
            "even_numbers": even_numbers,
            "alphabets": alphabets,
            "special_characters": special_characters,
            "sum": str(total_sum),
            "concat_string": concat_string
        }
        
    except Exception as e:
        logger.error(f"Error in process_data: {e}")
        logger.error(traceback.format_exc())
        raise

def create_error_response(message, status_code=400):
    """Create standardized error response"""
    error_response = OrderedDict([
        ("is_success", False),
        ("error", message),
        ("status_code", status_code)
    ])
    return app.response_class(
        response=json.dumps(error_response),
        status=status_code,
        mimetype='application/json'
    )

def create_success_response(data, status_code=200):
    """Create standardized success response"""
    return app.response_class(
        response=json.dumps(data),
        status=status_code,
        mimetype='application/json'
    )

@app.route('/bfhl', methods=['POST'])
def handle_bfhl():
    try:
        # Validate content type
        if not request.is_json:
            return create_error_response("Content-Type must be application/json", 415)
        
        # Get JSON data from request
        try:
            request_data = request.get_json()
        except Exception as e:
            logger.error(f"Invalid JSON in request: {e}")
            return create_error_response("Invalid JSON format", 400)
        
        if not request_data:
            return create_error_response("Request body is empty", 400)
        
        if 'data' not in request_data:
            return create_error_response("Missing 'data' field in request body", 400)
        
        data = request_data['data']
        
        # Validate input
        is_valid, error_message = validate_input(data)
        if not is_valid:
            return create_error_response(error_message, 400)
        
        # Process the data
        try:
            result = process_data(data)
        except Exception as e:
            logger.error(f"Error processing data: {e}")
            logger.error(traceback.format_exc())
            return create_error_response("Internal server error during data processing", 500)
        
        # Build response in EXACT order using OrderedDict
        response = OrderedDict([
            ("is_success", True),
            ("user_id", "shantanu_wani_27102004"),
            ("email", "shantanudinesh.wani2022@vitstudent.ac.in"),
            ("roll_number", "22BAI1403"),
            ("even_numbers", result["even_numbers"]),
            ("odd_numbers", result["odd_numbers"]),
            ("alphabets", result["alphabets"]),
            ("special_characters", result["special_characters"]),
            ("sum", result["sum"]),
            ("concat_string", result["concat_string"])
        ])
        
        return create_success_response(response)
        
    except Exception as e:
        logger.error(f"Unexpected error in handle_bfhl: {e}")
        logger.error(traceback.format_exc())
        return create_error_response("Internal server error", 500)

@app.route('/bfhl', methods=['GET'])
def handle_get():
    """Handle GET requests to return operation code"""
    try:
        response = OrderedDict([
            ("operation_code", 1)
        ])
        return create_success_response(response)
    except Exception as e:
        logger.error(f"Error in handle_get: {e}")
        return create_error_response("Internal server error", 500)

@app.route('/', methods=['GET'])
def home():
    """Home endpoint with API information"""
    try:
        response = OrderedDict([
            ("message", "BFHL API is running"),
            ("version", "1.0.0"),
            ("endpoints", OrderedDict([
                ("POST /bfhl", "Main endpoint for data processing"),
                ("GET /bfhl", "Returns operation code")
            ])),
            ("status", "healthy")
        ])
        return create_success_response(response)
    except Exception as e:
        logger.error(f"Error in home: {e}")
        return create_error_response("Internal server error", 500)

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return create_success_response(OrderedDict([
        ("status", "healthy"),
        ("timestamp", "2025-08-29T10:58:00Z")
    ]))

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return create_error_response("Endpoint not found", 404)

@app.errorhandler(405)
def method_not_allowed(error):
    return create_error_response("Method not allowed", 405)

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {error}")
    return create_error_response("Internal server error", 500)

if __name__ == '__main__':
    try:
        logger.info("Starting BFHL API server...")
        app.run(debug=True, host='0.0.0.0', port=5000)
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
