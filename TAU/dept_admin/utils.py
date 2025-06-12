import pandas as pd
import io
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from django.db import transaction
from django.contrib.auth.models import User

def create_excel_template():
    """Create an Excel template for bulk student creation."""
    wb = Workbook()
    ws = wb.active
    ws.title = "Student Details"

    # Define headers
    headers = ['First Name', 'Last Name', 'Email']
    
    # Style headers
    header_font = Font(bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="1E40AF", end_color="1E40AF", fill_type="solid")
    
    # Add headers
    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal='center')
        ws.column_dimensions[chr(64 + col)].width = 20

    # Add example row
    example_data = ['John', 'Doe', 'john.doe@example.com']
    for col, value in enumerate(example_data, 1):
        cell = ws.cell(row=2, column=col, value=value)
        cell.font = Font(italic=True, color="808080")

    # Create the file in memory
    excel_file = io.BytesIO()
    wb.save(excel_file)
    excel_file.seek(0)
    
    return excel_file

def process_excel_file(file, department):
    """Process the uploaded Excel file and create student accounts."""
    try:
        df = pd.read_excel(file)
        required_columns = ['First Name', 'Last Name', 'Email']
        
        # Validate columns
        if not all(col in df.columns for col in required_columns):
            raise ValueError("Excel file must contain columns: First Name, Last Name, Email")
        
        # Clean data
        df = df.dropna(subset=required_columns)
        
        # Get the latest roll number
        latest_user = User.objects.filter(username__regex=r'^\d{12}$').order_by('-username').first()
        if latest_user:
            next_number = int(latest_user.username) + 1
        else:
            next_number = int(f"{department.id:02d}{timezone.now().year}00000001")
        
        students_to_create = []
        created_students = []
        errors = []
        
        with transaction.atomic():
            for index, row in df.iterrows():
                try:
                    # Generate roll number
                    roll_number = f"{next_number:012d}"
                    next_number += 1
                    
                    # Create user
                    user = User.objects.create_user(
                        username=roll_number,
                        email=row['Email'].strip(),
                        password="Random@123",
                        first_name=row['First Name'].strip(),
                        last_name=row['Last Name'].strip()
                    )
                    
                    # Update profile
                    user.profile.must_change_password = True
                    user.profile.department = department
                    user.profile.save()
                    
                    created_students.append({
                        'roll_number': roll_number,
                        'first_name': user.first_name,
                        'last_name': user.last_name,
                        'email': user.email
                    })
                    
                except Exception as e:
                    errors.append(f"Row {index + 2}: {str(e)}")
        
        return created_students, errors
        
    except Exception as e:
        raise ValueError(f"Error processing Excel file: {str(e)}") 