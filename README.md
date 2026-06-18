# 🎯 Smart Attendance System

Complete **Face Recognition Based Attendance Management System** with **GeoFence** validation.

## ✨ Features

### 👨‍💼 Admin Features
- 📊 Dashboard with real-time statistics
- 👥 Employee Management (Add/Edit/Delete)
- 📸 Automatic Face Encoding
- 📅 Attendance Management
- 📝 Leave Approval System
- 💰 Automated Salary Calculation
- 📍 GeoFence Configuration
- 📥 CSV Export

### 👨‍💻 Employee Features
- 📸 Face Recognition Attendance
- 📍 Location Validation
- 📝 Leave Requests
- 📊 Dashboard & Salary View
- 📜 Attendance History

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Setup Database & Admin
```bash
python create_admin.py
```

### 3. Run Server
```bash
python manage.py runserver
```

### 4. Access Application
- **Home:** http://127.0.0.1:8000/
- **Admin Login:** http://127.0.0.1:8000/admin/login/
  - Username: `admin`
  - Password: `admin123`
- **Employee Login:** http://127.0.0.1:8000/employee/login/

## 📋 Project Structure

```
face_recognition_2026/
├── attendance_app/        # Main application
│   ├── models.py         # Database models
│   ├── views.py          # View functions
│   ├── forms.py          # Django forms
│   ├── urls.py           # URL routing
│   └── admin.py          # Admin config
├── templates/            # HTML templates
│   ├── base.html
│   ├── home.html
│   ├── admin/           # Admin templates
│   └── employee/        # Employee templates
├── myproject/           # Django project
│   ├── settings.py
│   └── urls.py
├── media/               # Uploaded files
├── manage.py
└── requirements.txt
```

## 💡 How It Works

### Face Recognition
1. Admin uploads employee photo
2. System generates face encoding (128-dimensional)
3. Employee opens camera for attendance
4. System captures and compares face
5. If matched (threshold: 0.45), marks attendance

### GeoFence Validation
1. Browser gets user location
2. Calculates distance from office
3. Validates if within radius
4. Attendance allowed only if within range

### Salary Calculation
```
Per Day Salary = Base Salary ÷ 30
Total Working Days = Present Days + Approved Leaves
Final Salary = Total Working Days × Per Day Salary
Deduction = Base Salary - Final Salary
```

## 🛠️ Technology Stack

- **Backend:** Django 4.2.7
- **Database:** SQLite
- **Frontend:** HTML, CSS, Bootstrap 5
- **Face Recognition:** OpenCV + face_recognition
- **GeoFence:** Browser Geolocation API

## 📖 Usage Guide

### Admin Workflow
1. Login as admin
2. Configure office location (Settings)
3. Add employees with clear face photos
4. Monitor attendance dashboard
5. Approve/reject leave requests
6. Generate salary reports

### Employee Workflow
1. Login with Employee ID
2. Go to "Punch In/Out"
3. Allow camera and location access
4. Position face clearly
5. Click "Punch In" or "Punch Out"
6. System validates face and location
7. Attendance marked automatically

## 🔐 Security Features

- ✅ Password hashing
- ✅ CSRF protection
- ✅ Role-based access
- ✅ Secure face encoding
- ✅ Duplicate prevention
- ✅ GeoFence validation

## 🐛 Troubleshooting

**Camera not working?**
- Allow camera permission in browser
- Check if camera is available
- Try different browser

**Face not recognized?**
- Ensure good lighting
- Face should be clearly visible
- Re-register with better photo

**Location issues?**
- Allow location permission
- Enable GPS
- Check browser compatibility

## 📝 Default Credentials

**Admin:**
- Username: `admin`
- Password: `admin123`

**Office Location:**
- Latitude: 28.7041
- Longitude: 77.1025
- Radius: 200m

## 🎯 Key Features

- ✅ Real-time face recognition
- ✅ GeoFence validation
- ✅ Automated salary calculation
- ✅ Late detection (after 10:00 AM)
- ✅ Leave management
- ✅ CSV export
- ✅ Responsive design
- ✅ Bootstrap 5 UI

## 📞 Support

For issues or questions, check the troubleshooting section above.

## ⭐ Show Your Support

Give a ⭐️ if this project helped you!

---

Built with ❤️ using Django, OpenCV, and Bootstrap 5
