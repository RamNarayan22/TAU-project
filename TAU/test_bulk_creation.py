from dept_admin.utils import process_excel_file, check_user_profile_status
from core.models import Department
import pandas as pd
import io

# Create a test Excel file with the problematic data
def create_test_excel():
    data = {
        'First Name': ['John', 'Jane'],
        'Last Name': ['Doe', 'Smith'],
        'Email': ['240202400001@apollouniversity.edu.in', '240202400002@apollouniversity.edu.in']
    }
    df = pd.DataFrame(data)
    
    # Create Excel file in memory
    excel_file = io.BytesIO()
    with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)
    excel_file.seek(0)
    return excel_file

print("=== TESTING BULK CREATION ===")

# Check if the problematic user exists
print("\n1. Checking user 240202400001:")
check_user_profile_status('240202400001')

# Create test Excel file
print("\n2. Creating test Excel file...")
test_file = create_test_excel()

# Get a department
department = Department.objects.get(name='Mess')

# Process the file
print("\n3. Processing Excel file...")
try:
    created_students, errors = process_excel_file(test_file, department)
    print(f"\nResults:")
    print(f"Created students: {len(created_students)}")
    print(f"Errors: {len(errors)}")
    
    if created_students:
        print("\nCreated students:")
        for student in created_students:
            print(f"  {student['roll_number']}: {student['first_name']} {student['last_name']}")
    
    if errors:
        print("\nErrors:")
        for error in errors:
            print(f"  {error}")
            
except Exception as e:
    print(f"Exception occurred: {str(e)}")

# Check the user again after processing
print("\n4. Checking user 240202400001 after processing:")
check_user_profile_status('240202400001') 