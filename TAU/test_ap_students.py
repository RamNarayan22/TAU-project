import pandas as pd

# Create sample student data with Andhra Pradesh names
students = [
    {'Roll Number': '240202400001', 'First Name': 'Venkata', 'Last Name': 'Naidu'},
    {'Roll Number': '240202400002', 'First Name': 'Sai Krishna', 'Last Name': 'Reddy'},
    {'Roll Number': '240202400003', 'First Name': 'Lakshmi', 'Last Name': 'Devi'},
    {'Roll Number': '240202400004', 'First Name': 'Surya Prakash', 'Last Name': 'Rao'},
    {'Roll Number': '240202400005', 'First Name': 'Rama', 'Last Name': 'Chandra'},
    {'Roll Number': '240202400006', 'First Name': 'Naga', 'Last Name': 'Babu'},
    {'Roll Number': '240202400007', 'First Name': 'Sri', 'Last Name': 'Venkateswara'},
    {'Roll Number': '240202400008', 'First Name': 'Padma', 'Last Name': 'Priya'},
    {'Roll Number': '240202400009', 'First Name': 'Chandra', 'Last Name': 'Sekhar'},
    {'Roll Number': '240202400010', 'First Name': 'Satya', 'Last Name': 'Prasad'}
]

# Create DataFrame
df = pd.DataFrame(students)

# Save to Excel
df.to_excel('ap_students.xlsx', index=False)
print("Test Excel file created: ap_students.xlsx with Andhra Pradesh student names") 