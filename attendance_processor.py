"""
Attendance Processor for Excel File Integration
Processes attendance data from Excel files for payroll calculations
"""

import pandas as pd
from datetime import datetime, timedelta
from collections import defaultdict
import re

class AttendanceProcessor:
    """Process attendance data from Excel files for payroll integration"""
    
    def __init__(self, excel_file_path):
        self.excel_file_path = excel_file_path
        self.attendance_data = None
        self.processed_data = {}
        
    def read_excel_file(self):
        """Read and validate Excel file format"""
        try:
            # Try reading with xlrd engine first
            self.attendance_data = pd.read_excel(
                self.excel_file_path, 
                engine='xlrd'
            )
            return True
        except Exception as e:
            try:
                # Fallback to openpyxl
                self.attendance_data = pd.read_excel(
                    self.excel_file_path, 
                    engine='openpyxl'
                )
                return True
            except Exception as e2:
                print(f"Error reading Excel file: {e2}")
                return False
    
    def process_attendance_data(self, month_year=None):
        """
        Process attendance data and calculate working hours for each employee
        
        Args:
            month_year: Format 'MM/YYYY' to filter specific month
        
        Returns:
            dict: Employee attendance summary
        """
        if self.attendance_data is None:
            if not self.read_excel_file():
                return {}
        
        # Clean and prepare data
        df = self.attendance_data.copy()
        
        # Convert Time column to datetime
        df['Time'] = pd.to_datetime(df['Time'], errors='coerce')
        
        # Filter by month if specified
        if month_year:
            try:
                month, year = month_year.split('/')
                df = df[
                    (df['Time'].dt.month == int(month)) & 
                    (df['Time'].dt.year == int(year))
                ]
            except:
                pass
        
        # Group by employee (using name and card number)
        employee_summary = defaultdict(lambda: {
            'name': '',
            'card_number': '',
            'days_worked': 0,
            'total_hours': 0,
            'overtime_hours': 0,
            'attendance_records': []
        })
        
        # Process each record
        for _, row in df.iterrows():
            if pd.isna(row['Time']):
                continue
                
            # Combine name fields
            first_name = str(row.get('Prénom', '')).strip()
            last_name = str(row.get('Last Name', '')).strip()
            personnel_name = str(row.get('Nombre du personnel', '')).strip()
            
            # Use the most complete name
            full_name = f"{first_name} {last_name}".strip()
            if not full_name or full_name == ' ':
                full_name = personnel_name
            
            card_number = str(row.get('Numéro de carte', '')).strip()
            
            # Create unique key for employee
            employee_key = f"{full_name}_{card_number}"
            
            # Store basic info
            employee_summary[employee_key]['name'] = full_name
            employee_summary[employee_key]['card_number'] = card_number
            
            # Add attendance record
            employee_summary[employee_key]['attendance_records'].append({
                'time': row['Time'],
                'in_out_status': str(row.get('In / Out Status', '')).strip(),
                'device': str(row.get('Device', '')).strip()
            })
        
        # Calculate working hours for each employee
        for employee_key, data in employee_summary.items():
            self._calculate_working_hours(data)
        
        self.processed_data = dict(employee_summary)
        return self.processed_data
    
    def _calculate_working_hours(self, employee_data):
        """Calculate total working hours and overtime for an employee"""
        records = sorted(employee_data['attendance_records'], key=lambda x: x['time'])
        
        daily_hours = defaultdict(list)
        
        # Group records by date
        for record in records:
            date_key = record['time'].date()
            daily_hours[date_key].append(record)
        
        total_hours = 0
        days_worked = 0
        
        # Calculate hours for each day
        for date, day_records in daily_hours.items():
            # Find check-in and check-out times
            in_times = []
            out_times = []
            
            for record in day_records:
                if 'in' in record['in_out_status'].lower():
                    in_times.append(record['time'])
                elif 'out' in record['in_out_status'].lower():
                    out_times.append(record['time'])
            
            # Calculate daily hours
            if in_times and out_times:
                # Use first check-in and last check-out
                first_in = min(in_times)
                last_out = max(out_times)
                
                # Calculate hours worked
                time_diff = last_out - first_in
                hours_worked = time_diff.total_seconds() / 3600
                
                # Subtract lunch break (1 hour) if working > 6 hours
                if hours_worked > 6:
                    hours_worked -= 1
                
                if hours_worked > 0:
                    total_hours += hours_worked
                    days_worked += 1
        
        # Update employee data
        employee_data['total_hours'] = round(total_hours, 2)
        employee_data['days_worked'] = days_worked
        
        # Calculate overtime (assuming 8 hours standard per day)
        standard_hours = days_worked * 8
        if total_hours > standard_hours:
            employee_data['overtime_hours'] = round(total_hours - standard_hours, 2)
        else:
            employee_data['overtime_hours'] = 0
    
    def match_with_database_employees(self):
        """Match processed attendance data with database employees"""
        if not self.processed_data:
            return {}
        
        # Import here to avoid circular imports
        from models import Employee
        
        matched_data = {}
        
        for employee_key, attendance_data in self.processed_data.items():
            name = attendance_data['name']
            card_number = attendance_data['card_number']
            
            # Try to find employee in database by name or card number
            employee = None
            
            # First try exact name match
            if name:
                employee = Employee.query.filter(
                    Employee.name.ilike(f"%{name}%")
                ).filter_by(is_active=1).first()
            
            # If not found, try card number in employee_id field
            if not employee and card_number:
                employee = Employee.query.filter(
                    Employee.employee_id == card_number
                ).filter_by(is_active=1).first()
            
            if employee:
                matched_data[employee.id] = {
                    'employee_id': employee.id,
                    'employee_name': employee.name,
                    'database_name': employee.name,
                    'attendance_name': name,
                    'card_number': card_number,
                    'days_worked': attendance_data['days_worked'],
                    'total_hours': attendance_data['total_hours'],
                    'overtime_hours': attendance_data['overtime_hours']
                }
        
        return matched_data
    
    def get_attendance_summary(self, month_year=None):
        """Get complete attendance summary with database matching"""
        self.process_attendance_data(month_year)
        matched_data = self.match_with_database_employees()
        
        return {
            'total_records': len(self.processed_data),
            'matched_employees': len(matched_data),
            'unmatched_count': len(self.processed_data) - len(matched_data),
            'attendance_data': matched_data,
            'raw_data': self.processed_data
        }