import sqlite3
import time

# Helper function for database connection
def get_db_connection():
    conn = sqlite3.connect('database.db')
    return conn

# Function for input validation
def validate_input(data):
    if not isinstance(data, str) or len(data) == 0:
        raise ValueError("Input must be a non-empty string.")

# Rate limiting decorator
def rate_limiter(max_calls, period):
    def decorator(func):
        calls = []
        def wrapper(*args, **kwargs):
            current_time = time.time()
            nonlocal calls
            # Remove calls outside the period
            calls = [call for call in calls if call > current_time - period]
            if len(calls) < max_calls:
                calls.append(current_time)
                return func(*args, **kwargs)
            else:
                print("Rate limit exceeded. Please try again later.")
                return None
        return wrapper
    return decorator

@rate_limiter(max_calls=5, period=60)  # Allow 5 calls per minute
# Main function to run the app
def main():
    try:
        # Sample input
        user_input = input("Enter some data: ")
        validate_input(user_input)
        conn = get_db_connection()
        # Perform database operations
        with conn:
            conn.execute('INSERT INTO records (data) VALUES (?)', (user_input,))
        print("Data saved successfully!")
    except ValueError as ve:
        print(f'Input error: {ve}')
    except sqlite3.DatabaseError as db_err:
        print(f'Database error: {db_err}')
    except Exception as e:
        print(f'An unexpected error occurred: {e}')
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    main()