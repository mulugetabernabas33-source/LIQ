# Central Constants Extracted from pro.py

REGIONS = [
    "Select Region",
    "Addis Ababa",
    "Oromia",
    "Amhara",
    "Tigray",
    "Sidama",
    "Afar",
    "Somali",
    "Benshangul-Gumuuz",
    "Harari",
    "SNNPR",
    "Gambela",
]

KIFLE_KETEMAS = [
    "Select Kifle Ketema",
    "Bole",
    "Arada",
    "Yeka",
    "Kirkos",
    "Lideta",
    "Addis Ketema",
    "Akaki Kality",
    "Kolfe Keranio",
    "Nifas Silk-Lafto",
    "Gulele",
    "Lemi Kura",
]

WEREDAS = [
    "Select Wereda",
    "Wereda 01",
    "Wereda 02",
    "Wereda 03",
    "Wereda 04",
    "Wereda 05",
    "Wereda 06",
    "Wereda 07",
    "Wereda 08",
    "Wereda 09",
    "Wereda 10",
]

SCHOOLS = [
    "Select School",
    "NEPS",
    "OMEGA",
    "CRUISE",
    "EWIKET LE FIRE",
    "YANTETA",
    "FUTURE",
    "STANDFORD",
    "SOUTH WEST",
    "EVEREST YOUTH ACADEMY",
    "BISRATE GEBIREL",
]

TEACHER_CREDENTIALS = {"tafesse": {"id": "neps-t-4567", "pass": "1234"}}
PARENT_CREDENTIALS = {"jallel million": {"id": "neps-s-8903", "pass": "1234"}}

SCHOOL_IMAGE_MAP = {
    "NEPS":               "/download.png",
    "BGIS":               "/bgis.png",
    "CRUISE":             "/cruise.jfif",
    "OMEGA":              "/omega.jfif",
    "SCHOOL OF TOMORROW": "/schoolof.jfif",
    "FUTURE":             "/future.jfif",
    "SOUTH WEST":         "/south_west.jfif",
    "STANDFORD":          "/standford.png",
}

CLASSROOMS = [
    "9A",
    "9B",
    "9C",
    "9D",
    "10A",
    "10B",
    "10C",
    "10D",
    "11A",
    "11B",
    "11C",
    "11D",
    "12A",
    "12B",
    "12C",
    "12D",
]

COMPONENTS = {
    "Worksheet (0-10)": 10,
    "Test (0-10)": 10,
    "Mid Exam (0-30)": 30,
    "Final Exam (0-40)": 40,
    "Assignment (0-10)": 10,
}

ATTENDANCE_ROW = "Attendance"
ALL_ROWS = list(COMPONENTS.keys()) + [ATTENDANCE_ROW]

COMPONENT_AXIS = {
    "Worksheet (0-10)": {"range": [0, 10], "dtick": 2},
    "Test (0-10)": {"range": [0, 10], "dtick": 2},
    "Assignment (0-10)": {"range": [0, 10], "dtick": 2},
    "Mid Exam (0-30)": {"range": [0, 30], "dtick": 5},
    "Final Exam (0-40)": {"range": [0, 40], "dtick": 10},
}

COMPONENT_DISPLAY = {
    "Worksheet (0-10)": "Worksheet",
    "Test (0-10)": "Test",
    "Assignment (0-10)": "Assignment",
    "Mid Exam (0-30)": "Mid Exam",
    "Final Exam (0-40)": "Final Exam",
}

QUARTERS = ["Q1", "Q2", "Q3", "Q4"]

DASH_MENU = {
    "Dashboard": "Dashboard",
    "1st Quarter": "1st Quarter",
    "2nd Quarter": "2nd Quarter",
    "3rd Quarter": "3rd Quarter",
    "4th Quarter": "4th Quarter",
    "Teacher Notes": "Teacher's Notes & Concerns",
    "System Initialization": "System Initialization",
}
