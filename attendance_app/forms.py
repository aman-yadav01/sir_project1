"""

Smart Attendance System - Forms

All forms for Admin and Employee operations

"""

import json



from django import forms

from django.contrib.auth.forms import AuthenticationForm

import face_recognition



from .models import User, Employee, Leave, OfficeLocation, Attendance, Shift, WeekOff, Holiday, SalaryCycleSettings, SalaryPayment, Incentive, Task, WorkLog





class AdminLoginForm(AuthenticationForm):

    """Admin Login Form"""

    username = forms.CharField(

        widget=forms.TextInput(attrs={

            'class': 'form-control',

            'placeholder': 'Username',

            'autofocus': True

        })

    )

    password = forms.CharField(

        widget=forms.PasswordInput(attrs={

            'class': 'form-control',

            'placeholder': 'Password'

        })

    )





class EmployeeLoginForm(forms.Form):

    """Employee Login Form using Employee ID"""

    employee_id = forms.CharField(

        max_length=20,

        widget=forms.TextInput(attrs={

            'class': 'form-control',

            'placeholder': 'Employee ID',

            'autofocus': True

        })

    )

    password = forms.CharField(

        widget=forms.PasswordInput(attrs={

            'class': 'form-control',

            'placeholder': 'Password'

        })

    )





class EmployeeRegistrationForm(forms.ModelForm):

    """

    Employee Registration Form for Admin

    Creates both User and Employee records

    """

    password = forms.CharField(

        widget=forms.PasswordInput(attrs={

            'class': 'form-control',

            'placeholder': 'Password'

        }),

        help_text='Password for employee login'

    )

    confirm_password = forms.CharField(

        widget=forms.PasswordInput(attrs={

            'class': 'form-control',

            'placeholder': 'Confirm Password'

        })

    )



    class Meta:

        model = Employee

        fields = [

            'employee_id', 'full_name', 'designation',

            'email', 'mobile_number', 'photo', 'base_salary', 'date_of_birth', 'is_active'

        ]

        widgets = {

            'employee_id': forms.TextInput(attrs={

                'class': 'form-control',

                'placeholder': 'e.g., EMP001'

            }),

            'full_name': forms.TextInput(attrs={

                'class': 'form-control',

                'placeholder': 'Full Name'

            }),

            'designation': forms.TextInput(attrs={

                'class': 'form-control',

                'placeholder': 'e.g., Software Engineer'

            }),

            'email': forms.EmailInput(attrs={

                'class': 'form-control',

                'placeholder': 'email@example.com'

            }),

            'mobile_number': forms.TextInput(attrs={

                'class': 'form-control',

                'placeholder': '1234567890'

            }),

            'photo': forms.FileInput(attrs={

                'class': 'form-control',

                'accept': 'image/*'

            }),

            'base_salary': forms.NumberInput(attrs={

                'class': 'form-control',

                'placeholder': 'Monthly Salary',

                'step': '0.01'

            }),

            'is_active': forms.CheckboxInput(attrs={

                'class': 'form-check-input'

            }),

            'date_of_birth': forms.DateInput(attrs={

                'class': 'form-control',

                'type': 'date'

            }),

        }



    def clean(self):

        """Validate passwords match"""

        cleaned_data = super().clean()

        password = cleaned_data.get('password')

        confirm_password = cleaned_data.get('confirm_password')



        if password and confirm_password:

            if password != confirm_password:

                raise forms.ValidationError("Passwords do not match")



        return cleaned_data



    def clean_employee_id(self):

        """Check if employee ID already exists"""

        employee_id = self.cleaned_data.get('employee_id')

        if User.objects.filter(employee_id=employee_id).exists():

            raise forms.ValidationError("Employee ID already exists")

        return employee_id



    def clean_email(self):

        """Check if email already exists"""

        email = self.cleaned_data.get('email')

        if User.objects.filter(email=email).exists():

            raise forms.ValidationError("Email already exists")

        return email



    def clean_photo(self):

        """Validate photo and check for face detection"""

        photo = self.cleaned_data.get('photo')



        if photo:

            # Check file size (max 5MB)

            if photo.size > 5 * 1024 * 1024:

                raise forms.ValidationError(

                    "Photo size should not exceed 5MB"

                )



            # Check file type

            if not photo.content_type.startswith('image'):

                raise forms.ValidationError("File must be an image")



            try:

                # Load image and detect face

                image = face_recognition.load_image_file(photo)

                face_locations = face_recognition.face_locations(image)



                if not face_locations:

                    raise forms.ValidationError(

                        "No face detected in photo. "

                        "Please upload a clear face photo."

                    )



                if len(face_locations) > 1:

                    raise forms.ValidationError(

                        "Multiple faces detected. "

                        "Please upload photo with single face."

                    )



            except Exception as e:

                error_msg = f"Error processing photo: {str(e)}"

                raise forms.ValidationError(error_msg)



        return photo



    def save(self, commit=True):

        """

        Save employee and create user account

        Generate face encoding automatically

        """

        employee = super().save(commit=False)



        # Create User account

        user = User.objects.create(

            username=self.cleaned_data['employee_id'],

            email=self.cleaned_data['email'],

            employee_id=self.cleaned_data['employee_id'],

            mobile_number=self.cleaned_data['mobile_number'],

            role='employee',

            is_active=self.cleaned_data.get('is_active', True)

        )

        user.set_password(self.cleaned_data['password'])

        user.save()



        employee.user = user



        if commit:

            employee.save()



            # Generate face encoding

            try:

                image = face_recognition.load_image_file(

                    employee.photo.path

                )

                face_locations = face_recognition.face_locations(image)



                if face_locations:

                    face_encodings = face_recognition.face_encodings(

                        image,

                        face_locations

                    )



                    if face_encodings:

                        # Convert encoding to JSON string

                        encoding_list = face_encodings[0].tolist()

                        employee.face_encoding = json.dumps(

                            encoding_list

                        )

                        employee.save()



            except Exception as e:

                print(f"Error generating face encoding: {e}")



        return employee





class EmployeeUpdateForm(forms.ModelForm):

    """

    Employee Update Form

    Admin can update employee details including photo and password

    """

    password = forms.CharField(

        required=False,

        widget=forms.PasswordInput(attrs={

            'class': 'form-control',

            'placeholder': 'Leave blank to keep current password'

        }),

        help_text='Leave blank if you don\'t want to change password'

    )

    confirm_password = forms.CharField(

        required=False,

        widget=forms.PasswordInput(attrs={

            'class': 'form-control',

            'placeholder': 'Confirm new password'

        })

    )

    

    class Meta:

        model = Employee

        fields = [

            'employee_id', 'full_name', 'designation', 'email',

            'mobile_number', 'base_salary', 'photo', 'date_of_birth', 'is_active'

        ]

        widgets = {

            'employee_id': forms.TextInput(

                attrs={'class': 'form-control', 'readonly': 'readonly'}

            ),

            'full_name': forms.TextInput(

                attrs={'class': 'form-control'}

            ),

            'designation': forms.TextInput(

                attrs={'class': 'form-control'}

            ),

            'email': forms.EmailInput(

                attrs={'class': 'form-control'}

            ),

            'mobile_number': forms.TextInput(

                attrs={'class': 'form-control'}

            ),

            'base_salary': forms.NumberInput(attrs={

                'class': 'form-control',

                'step': '0.01'

            }),

            'photo': forms.FileInput(attrs={

                'class': 'form-control',

                'accept': 'image/*'

            }),

            'is_active': forms.CheckboxInput(

                attrs={'class': 'form-check-input'}

            ),

            'date_of_birth': forms.DateInput(

                attrs={'class': 'form-control', 'type': 'date'}

            ),

        }

    

    def clean_photo(self):

        """Validate photo if provided"""

        photo = self.cleaned_data.get('photo')

        

        if photo and hasattr(photo, 'size'):

            if photo.size > 5 * 1024 * 1024:

                raise forms.ValidationError("Photo size should not exceed 5MB")

            

            try:

                image = face_recognition.load_image_file(photo)

                face_locations = face_recognition.face_locations(image)

                

                if not face_locations:

                    raise forms.ValidationError("No face detected in photo")

                

                if len(face_locations) > 1:

                    raise forms.ValidationError("Multiple faces detected")

            

            except Exception as e:

                raise forms.ValidationError(f"Error processing photo: {str(e)}")

        

        return photo

    

    def clean(self):

        """Validate password confirmation"""

        cleaned_data = super().clean()

        password = cleaned_data.get('password')

        confirm_password = cleaned_data.get('confirm_password')

        

        if password and password != confirm_password:

            raise forms.ValidationError("Passwords do not match")

        

        return cleaned_data

    

    def save(self, commit=True):

        """Save employee and update password/face encoding if changed"""

        employee = super().save(commit=False)

        

        # Update password if provided

        password = self.cleaned_data.get('password')

        if password:

            employee.user.set_password(password)

            if commit:

                employee.user.save()

        

        if commit:

            employee.save()

            

            # Regenerate face encoding if photo changed

            if self.cleaned_data.get('photo') and hasattr(self.cleaned_data.get('photo'), 'size'):

                try:

                    image = face_recognition.load_image_file(employee.photo.path)

                    face_locations = face_recognition.face_locations(image)

                    

                    if face_locations:

                        face_encodings = face_recognition.face_encodings(image, face_locations)

                        

                        if face_encodings:

                            encoding_list = face_encodings[0].tolist()

                            employee.face_encoding = json.dumps(encoding_list)

                            employee.save()

                

                except Exception as e:

                    print(f"Error regenerating face encoding: {e}")

        

        return employee





class EmployeePhotoUpdateForm(forms.ModelForm):

    """

    Separate form for updating employee photo

    Regenerates face encoding

    """

    class Meta:

        model = Employee

        fields = ['photo']

        widgets = {

            'photo': forms.FileInput(attrs={

                'class': 'form-control',

                'accept': 'image/*'

            })

        }



    def clean_photo(self):

        """Validate photo and check for face detection"""

        photo = self.cleaned_data.get('photo')



        if photo:

            if photo.size > 5 * 1024 * 1024:

                raise forms.ValidationError(

                    "Photo size should not exceed 5MB"

                )



            try:

                image = face_recognition.load_image_file(photo)

                face_locations = face_recognition.face_locations(image)



                if not face_locations:

                    raise forms.ValidationError(

                        "No face detected in photo"

                    )



                if len(face_locations) > 1:

                    raise forms.ValidationError(

                        "Multiple faces detected"

                    )



            except Exception as e:

                error_msg = f"Error processing photo: {str(e)}"

                raise forms.ValidationError(error_msg)



        return photo



    def save(self, commit=True):

        """Save and regenerate face encoding"""

        employee = super().save(commit=commit)



        if commit and employee.photo:

            try:

                image = face_recognition.load_image_file(

                    employee.photo.path

                )

                face_locations = face_recognition.face_locations(image)



                if face_locations:

                    face_encodings = face_recognition.face_encodings(

                        image,

                        face_locations

                    )



                    if face_encodings:

                        encoding_list = face_encodings[0].tolist()

                        employee.face_encoding = json.dumps(

                            encoding_list

                        )

                        employee.save()



            except Exception as e:

                print(f"Error regenerating face encoding: {e}")



        return employee





class LeaveRequestForm(forms.ModelForm):

    """

    Leave Request Form for Employees

    """

    class Meta:

        model = Leave

        fields = ['start_date', 'end_date', 'reason']

        widgets = {

            'start_date': forms.DateInput(attrs={

                'class': 'form-control',

                'type': 'date'

            }),

            'end_date': forms.DateInput(attrs={

                'class': 'form-control',

                'type': 'date'

            }),

            'reason': forms.Textarea(attrs={

                'class': 'form-control',

                'rows': 4,

                'placeholder': 'Enter reason for leave'

            }),

        }



    def clean(self):

        """Validate date range"""

        cleaned_data = super().clean()

        start_date = cleaned_data.get('start_date')

        end_date = cleaned_data.get('end_date')



        if start_date and end_date:

            if end_date < start_date:

                raise forms.ValidationError(

                    "End date cannot be before start date"

                )



        return cleaned_data





class LeaveReviewForm(forms.ModelForm):

    """

    Leave Review Form for Admin

    Approve or Reject leave requests

    """

    class Meta:

        model = Leave

        fields = ['status', 'admin_remarks']

        widgets = {

            'status': forms.Select(attrs={

                'class': 'form-select'

            }),

            'admin_remarks': forms.Textarea(attrs={

                'class': 'form-control',

                'rows': 3,

                'placeholder': 'Optional remarks'

            }),

        }





class OfficeLocationForm(forms.ModelForm):

    """

    Office Location Form for GeoFence Settings

    """

    class Meta:

        """Meta configuration for OfficeLocationForm"""

        model = OfficeLocation

        fields = [

            'name', 'latitude', 'longitude', 'radius', 'is_active'

        ]

        widgets = {

            'name': forms.TextInput(attrs={

                'class': 'form-control',

                'placeholder': 'Office Name'

            }),

            'latitude': forms.NumberInput(attrs={

                'class': 'form-control',

                'placeholder': 'e.g., 28.7041',

                'step': '0.000001'

            }),

            'longitude': forms.NumberInput(attrs={

                'class': 'form-control',

                'placeholder': 'e.g., 77.1025',

                'step': '0.000001'

            }),

            'radius': forms.NumberInput(attrs={

                'class': 'form-control',

                'placeholder': 'Radius in meters (e.g., 200)'

            }),

            'is_active': forms.CheckboxInput(attrs={

                'class': 'form-check-input'

            }),

        }





class AttendanceFilterForm(forms.Form):

    """

    Attendance Filter Form for Admin

    Filter by date and employee

    """

    date = forms.DateField(

        required=False,

        widget=forms.DateInput(attrs={

            'class': 'form-control',

            'type': 'date'

        })

    )

    employee = forms.ModelChoiceField(

        queryset=Employee.objects.filter(is_active=True),

        required=False,

        widget=forms.Select(attrs={

            'class': 'form-select'

        }),

        empty_label='All Employees'

    )

    status = forms.ChoiceField(

        required=False,

        choices=(

            [('', 'All Status')] +

            list(Attendance._meta.get_field('status').choices)

        ),

        widget=forms.Select(attrs={

            'class': 'form-select'

        })

    )





class DateRangeForm(forms.Form):

    """

    Date Range Form for Reports

    """

    start_date = forms.DateField(

        widget=forms.DateInput(attrs={

            'class': 'form-control',

            'type': 'date'

        })

    )

    end_date = forms.DateField(

        widget=forms.DateInput(attrs={

            'class': 'form-control',

            'type': 'date'

        })

    )



    def clean(self):

        """Validate date range"""

        cleaned_data = super().clean()

        start_date = cleaned_data.get('start_date')

        end_date = cleaned_data.get('end_date')



        if start_date and end_date:

            if end_date < start_date:

                raise forms.ValidationError(

                    "End date cannot be before start date"

                )



        return cleaned_data







class ShiftForm(forms.ModelForm):

    """Form for creating and editing shifts"""

    

    class Meta:

        model = Shift

        fields = ['name', 'punch_in_start', 'punch_in_end', 'punch_out_time', 'is_active']

        widgets = {

            'name': forms.Select(attrs={'class': 'form-select'}),

            'punch_in_start': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),

            'punch_in_end': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),

            'punch_out_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),

            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),

        }

        labels = {

            'name': 'Shift Type',

            'punch_in_start': 'Punch In Start Time',

            'punch_in_end': 'Punch In End Time (Late After This)',

            'punch_out_time': 'Expected Punch Out Time',

            'is_active': 'Active',

        }





class EmployeeShiftAssignForm(forms.ModelForm):

    """Form for assigning shift to employee"""

    

    class Meta:

        model = Employee

        fields = ['shift']

        widgets = {

            'shift': forms.Select(attrs={'class': 'form-select'}),

        }

        labels = {

            'shift': 'Assign Shift',

        }





class WeekOffForm(forms.ModelForm):

    """Week Off Configuration Form"""

    class Meta:

        model = WeekOff

        fields = ['weekday', 'is_active']

        widgets = {

            'weekday': forms.Select(attrs={

                'class': 'form-select form-select-lg'

            }),

            'is_active': forms.CheckboxInput(attrs={

                'class': 'form-check-input'

            })

        }

        labels = {

            'weekday': 'Day of Week',

            'is_active': 'Active (Week Off)'

        }







class HolidayForm(forms.ModelForm):

    """Holiday Management Form"""

    class Meta:

        model = Holiday

        fields = ['name', 'start_date', 'end_date', 'description', 'is_active']

        widgets = {

            'name': forms.TextInput(attrs={

                'class': 'form-control form-control-lg',

                'placeholder': 'e.g., Republic Day, Diwali'

            }),

            'start_date': forms.DateInput(attrs={

                'class': 'form-control form-control-lg',

                'type': 'date'

            }),

            'end_date': forms.DateInput(attrs={

                'class': 'form-control form-control-lg',

                'type': 'date'

            }),

            'description': forms.Textarea(attrs={

                'class': 'form-control',

                'rows': 3,

                'placeholder': 'Optional description'

            }),

            'is_active': forms.CheckboxInput(attrs={

                'class': 'form-check-input'

            })

        }

        labels = {

            'name': 'Holiday Name',

            'start_date': 'Start Date',

            'end_date': 'End Date',

            'description': 'Description',

            'is_active': 'Active'

        }







class SalaryCycleSettingsForm(forms.ModelForm):

    """Salary Cycle Configuration Form"""

    class Meta:

        model = SalaryCycleSettings

        fields = ['cycle_name', 'cycle_start_day', 'is_active']

        widgets = {

            'cycle_name': forms.TextInput(attrs={

                'class': 'form-control form-control-lg',

                'placeholder': 'e.g., Monthly Salary Cycle'

            }),

            'cycle_start_day': forms.NumberInput(attrs={

                'class': 'form-control form-control-lg',

                'min': '1',

                'max': '31',

                'placeholder': 'Day of month (1-31)'

            }),

            'is_active': forms.CheckboxInput(attrs={

                'class': 'form-check-input'

            })

        }

        labels = {

            'cycle_name': 'Cycle Name',

            'cycle_start_day': 'Cycle Start Day',

            'is_active': 'Active'

        }

        help_texts = {

            'cycle_start_day': 'Enter the day of month when salary cycle starts (e.g., 10 for 10th to 9th cycle)'

        }





class SalaryPaymentForm(forms.ModelForm):

    """Salary Payment Form"""

    class Meta:

        model = SalaryPayment

        fields = ['amount', 'payment_date', 'payment_method', 'reference_number', 'notes']

        widgets = {

            'amount': forms.NumberInput(attrs={

                'class': 'form-control form-control-lg',

                'placeholder': 'Enter amount',

                'step': '0.01',

                'min': '0'

            }),

            'payment_date': forms.DateInput(attrs={

                'class': 'form-control form-control-lg',

                'type': 'date'

            }),

            'payment_method': forms.Select(attrs={

                'class': 'form-select form-select-lg'

            }),

            'reference_number': forms.TextInput(attrs={

                'class': 'form-control',

                'placeholder': 'Transaction ID / Cheque Number (optional)'

            }),

            'notes': forms.Textarea(attrs={

                'class': 'form-control',

                'rows': 3,

                'placeholder': 'Additional notes (optional)'

            })

        }

        labels = {

            'amount': 'Payment Amount',

            'payment_date': 'Payment Date',

            'payment_method': 'Payment Method',

            'reference_number': 'Reference Number',

            'notes': 'Notes'

        }

    

    def __init__(self, *args, **kwargs):

        self.salary = kwargs.pop('salary', None)

        super().__init__(*args, **kwargs)

        

        # Set default payment date to today

        if not self.instance.pk:

            from datetime import date

            self.fields['payment_date'].initial = date.today()

        

        # Set max amount to pending amount

        if self.salary:

            self.fields['amount'].widget.attrs['max'] = float(self.salary.pending_amount)

            self.fields['amount'].help_text = f'Maximum: ₹{self.salary.pending_amount} (Pending amount)'

    

    def clean_amount(self):

        """Validate payment amount"""

        amount = self.cleaned_data.get('amount')

        

        if amount <= 0:

            raise forms.ValidationError('Amount must be greater than 0')

        

        if self.salary and amount > self.salary.pending_amount:

            raise forms.ValidationError(

                f'Amount cannot exceed pending amount of ₹{self.salary.pending_amount}'

            )

        

        return amount





class IncentiveForm(forms.ModelForm):

    """Form for adding incentive to an employee"""

    class Meta:

        model = Incentive

        fields = ['employee', 'incentive_type', 'title', 'amount', 'incentive_date', 'reason']

        widgets = {

            'employee': forms.Select(attrs={'class': 'form-select form-select-lg'}),

            'incentive_type': forms.Select(attrs={'class': 'form-select form-select-lg'}),

            'title': forms.TextInput(attrs={

                'class': 'form-control form-control-lg',

                'placeholder': 'e.g., Diwali Bonus, Q1 Performance'

            }),

            'amount': forms.NumberInput(attrs={

                'class': 'form-control form-control-lg',

                'placeholder': 'Enter amount',

                'step': '0.01',

                'min': '1'

            }),

            'incentive_date': forms.DateInput(attrs={

                'class': 'form-control form-control-lg',

                'type': 'date'

            }),

            'reason': forms.Textarea(attrs={

                'class': 'form-control',

                'rows': 3,

                'placeholder': 'Reason / description (optional)'

            }),

        }

        labels = {

            'employee': 'Select Employee',

            'incentive_type': 'Incentive Type',

            'title': 'Title',

            'amount': 'Amount (₹)',

            'incentive_date': 'Date',

            'reason': 'Reason',

        }



    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        self.fields['employee'].queryset = Employee.objects.filter(is_active=True).order_by('employee_id')

        if not self.instance.pk:

            from datetime import date

            self.fields['incentive_date'].initial = date.today()



    def clean_amount(self):

        amount = self.cleaned_data.get('amount')

        if amount and amount <= 0:

            raise forms.ValidationError('Amount must be greater than 0')

        return amount



class TaskForm(forms.ModelForm):
    """Admin task create/edit form"""
    class Meta:
        model = Task
        fields = ['title', 'description', 'assigned_to', 'priority', 'deadline']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control form-control-lg',
                'placeholder': 'Task title'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Task ki detail description...'
            }),
            'assigned_to': forms.Select(attrs={
                'class': 'form-select form-select-lg'
            }),
            'priority': forms.Select(attrs={
                'class': 'form-select form-select-lg'
            }),
            'deadline': forms.DateInput(attrs={
                'class': 'form-control form-control-lg',
                'type': 'date'
            }),
        }
        labels = {
            'title': 'Task Title',
            'description': 'Description',
            'assigned_to': 'Assign To Employee',
            'priority': 'Priority',
            'deadline': 'Deadline',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['assigned_to'].queryset = Employee.objects.filter(is_active=True).order_by('employee_id')


class WorkLogForm(forms.ModelForm):
    """Employee work log submit form"""
    class Meta:
        model = WorkLog
        fields = ['log_date', 'description', 'hours_worked', 'photo']
        widgets = {
            'log_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Aaj kya kiya? Detail mein likho...'
            }),
            'hours_worked': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., 3.5',
                'step': '0.5',
                'min': '0',
                'max': '24'
            }),
            'photo': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*',
                'id': 'photoFileInput',
                'name': 'photo',
            }),
        }
        labels = {
            'log_date': 'Date',
            'description': 'Aaj Kya Kiya (Work Update)',
            'hours_worked': 'Ghante Kaam Kiya (Optional)',
            'photo': 'Task Photo Proof (Optional)',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from datetime import date
        if not self.instance.pk:
            self.fields['log_date'].initial = date.today()

    def clean_photo(self):
        photo = self.cleaned_data.get('photo')
        if photo and hasattr(photo, 'size'):
            # Max 10MB
            if photo.size > 10 * 1024 * 1024:
                raise forms.ValidationError('Photo size 10MB se zyada nahi honi chahiye.')
        return photo
