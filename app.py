from flask import Flask, render_template, request, redirect, jsonify
from pymongo import MongoClient
from bson import ObjectId

app = Flask(__name__)

# =========================
# MongoDB Connection
# =========================

client = MongoClient(
    "mongodb+srv://SundaySchool:tpm@cluster0.ku6kpke.mongodb.net/SundaySchool_db?retryWrites=true&w=majority&appName=Cluster0"
)
db = client["SundaySchool_db"]
students = db["students"]
passwords = db["passwords"]
marks = db["marks"]
settings_col = db["settings"]
branches = db["branches"]
@app.route("/")
def login():
    return render_template("login.html")

@app.route("/index")
def home():
    return render_template("index.html")
# =========================
# HOME PAGE
# =========================

# =========================
# OPTIONS PAGE
# =========================

@app.route("/options")
def options():
    return render_template("options.html")

# =========================
# ADD STUDENT PAGE
# =========================

@app.route("/add_student", methods=["GET", "POST"])
def add_student():

    branch_list = list(
        branches.find().sort(
            "branch_name", 1
        )
    )

    if request.method == "POST":

        existing_student = students.find_one({

            "name": request.form["name"].upper(),
            "last_name": request.form["last_name"].upper(),
            "dob": request.form["dob"],
            "place": request.form["place"].upper(),
            "parent_name": request.form["parent_name"].upper(),

        })

        if existing_student:

            return render_template(
                "add_student.html",
                message="STUDENT RECORD ALREADY EXISTS",
                msg_type="error",
                branches=branch_list
            )

        student_data = {

            "name": request.form["name"].upper(),
            "last_name": request.form["last_name"].upper(),
            "dob": request.form["dob"],
            "age": request.form["age"],
            "gender": request.form["gender"],
            "std": request.form["std"],
            "place": request.form["place"].upper(),
            "parent_name": request.form["parent_name"].upper(),
            "admission_date": request.form["admission_date"],
            "admission_class": request.form["admission_class"].upper()
        }

        students.insert_one(student_data)

        return render_template(
            "add_student.html",
            message="STUDENT SAVED SUCCESSFULLY",
            msg_type="success",
            branches=branch_list
        )

    return render_template(
        "add_student.html",
        message="",
        msg_type="",
        branches=branch_list
    )
# =========================
# SEARCH STUDENT PAGE
# =========================

@app.route("/search_student")
def search_student():
    return render_template("search_student.html")

# =========================
# LIVE SEARCH API
# =========================

@app.route("/search_api")
def search_api():

    search = request.args.get("search", "")

    results = []

    if search:

        matched_students = students.find({

            "name": {
                "$regex": "^" + search,
                "$options": "i"
            }

        })

        for student in matched_students:

           results.append({

    "id": str(student["_id"]),

    "name": student.get("name", ""),
    "last_name": student.get("last_name", ""),
    "age": student.get("age", ""),
    "gender": student.get("gender", ""),
    "std": student.get("std", ""),
    "place": student.get("place", ""),
    "parent_name": student.get("parent_name", ""),
    "admission_date": student.get("admission_date", ""),
    "admission_class": student.get("admission_class", "")
})

    return jsonify(results)

# =========================
# STUDENT DETAILS PAGE
# =========================

@app.route("/student/<student_id>")
def student_details(student_id):

    try:

        student = students.find_one({
            "_id": ObjectId(student_id)
        })

        if student is None:
            return "STUDENT NOT FOUND"

        mark = marks.find_one({
            "student_id": student_id
        })

        print("MARK DATA =", mark)

        if not mark:
            mark = {
                "first": "",
                "second": "",
                "third": "",
                "smv": "",
                "attendance_days": "",
                "attendance_percentage": "",
                "grade": ""
            }

        return render_template(
            "student_details.html",
            student=student,
            mark=mark
        )

    except Exception as e:

        return f"ERROR : {str(e)}"
@app.route("/edit_student/<student_id>", methods=["GET", "POST"])
def edit_student(student_id):

    student = students.find_one({
        "_id": ObjectId(student_id)
    })

    branch_list = list(
        branches.find().sort(
            "branch_name", 1
        )
    )

    if student is None:
        return "STUDENT NOT FOUND"

    if request.method == "POST":

        students.update_one(

            {"_id": ObjectId(student_id)},

            {
                "$set": {

                    "name": request.form["name"].upper(),
                    "last_name": request.form["last_name"].upper(),
                    "dob": request.form["dob"],
                    "age": request.form["age"],
                    "gender": request.form["gender"],
                    "std": request.form["std"],
                    "place": request.form["place"].upper(),
                    "parent_name": request.form["parent_name"].upper(),
                    "admission_date": request.form["admission_date"],
                    "admission_class": request.form["admission_class"].upper()

                }
            }
        )

        return redirect(
            f"/student/{student_id}"
        )

    return render_template(
        "edit_student.html",
        student=student,
        branches=branch_list
    )
# =========================
# DELETE STUDENT
# =========================

@app.route("/delete_student/<student_id>")
def delete_student(student_id):

    students.delete_one({
        "_id": ObjectId(student_id)
    })

    marks.delete_one({
        "student_id": student_id
    })

    return redirect("/search_student")
# =========================
# SETTINGS PAGE
# =========================

@app.route("/settings")
def settings():

    record_count = students.count_documents({})

    settings_data = settings_col.find_one() or {}

    class_counts = []

    for i in range(1, 12):

        count = students.count_documents({
            "std": str(i)
        })

        class_counts.append({
            "class": i,
            "count": count
        })

    branch_list = list(
        branches.find().sort(
            "branch_name", 1
        )
    )

    for branch in branch_list:

        branch["student_count"] = students.count_documents({
            "place": branch["branch_name"]
        })

    return render_template(
        "settings.html",
        record_count=record_count,
        settings=settings_data,
        class_counts=class_counts,
        branches=branch_list
    )
# =========================
# SAVE SETTINGS
# =========================

@app.route("/save_settings", methods=["POST"])
def save_settings():

    data = request.get_json()

    settings_col.update_one(
        {},
        {
            "$set": {
                "academic_year": data["academic_year"].upper(),
                "attendance_days": data["attendance_days"],
                "center_name": data["center_name"].upper(),
                "assembly_name": data["assembly_name"].upper()
            }
        },
        upsert=True
    )

    return jsonify({
        "success": True
    })
# =========================
# ADD BRANCH
# =========================

@app.route("/add_branch", methods=["POST"])
def add_branch():

    data = request.get_json()

    branch_name = data["branch_name"].strip().upper()

    existing = branches.find_one({
        "branch_name": branch_name
    })

    if existing:
        return jsonify({
            "success": False
        })

    result = branches.insert_one({
        "branch_name": branch_name
    })

    return jsonify({
        "success": True,
        "id": str(result.inserted_id)
    })
# =========================
# DELETE BRANCH
# =========================
@app.route("/delete_branch/<branch_id>", methods=["DELETE"])
def delete_branch(branch_id):

    branches.delete_one({
        "_id": ObjectId(branch_id)
    })

    return jsonify({
        "success": True
    })
# =========================
# CHANGE PASSWORD
# =========================

@app.route("/change_password", methods=["GET", "POST"])
def change_password():

    if request.method == "POST":

        current_password = request.form["current_password"]
        new_password = request.form["new_password"]
        confirm_password = request.form["confirm_password"]

        password_doc = passwords.find_one()

        if current_password != password_doc["access_code"]:

            return render_template(
                "change_password.html",
                message="CURRENT ACCESS CODE INCORRECT",
                color="red"
            )

        if new_password != confirm_password:

            return render_template(  "change_password.html",
                message="NEW ACCESS CODES DO NOT MATCH",
                color="red"
            )

        passwords.update_one(
            {"_id": password_doc["_id"]},
            {
                "$set": {
                    "access_code": new_password
                }
            }
        )

        return render_template(
            "change_password.html",
            message="ACCESS CODE UPDATED SUCCESSFULLY",
            color="#00ff88"
        )

    return render_template(
        "change_password.html",
        message="",
        color="#00ff88"
    )



@app.route("/verify_access_code", methods=["POST"])
def verify_access_code():

    data = request.get_json()

    entered_code = data.get("access_code", "")

    password_doc = passwords.find_one()

    print("Entered:", entered_code)
    print("DB Data:", password_doc)

    if (
        password_doc and
        entered_code == password_doc["access_code"]
    ):

        return jsonify({
            "success": True
        })

    return jsonify({
        "success": False
    })
@app.route("/view_students")
def view_students():

    all_students = students.find().sort("name", 1)

    return render_template(
        "view_students.html",
        students=all_students
    )
marks = db["marks"]

@app.route("/attendance_marks")
def attendance_marks():

    all_students = list(
        students.find().sort("std", 1)
    )

    for student in all_students:

        mark = marks.find_one({
            "student_id": str(student["_id"])
        })

        if mark:

            student["first"] = mark.get("first", "")
            student["second"] = mark.get("second", "")
            student["third"] = mark.get("third", "")
            student["smv"] = mark.get("smv", "")
            student["attendance_days"] = mark.get("attendance_days", "")
            student["attendance_percentage"] = mark.get("attendance_percentage", "")
            student["grade"] = mark.get("grade", "PASSED")
            student["locked"] = mark.get("locked", False)

        else:

            student["first"] = ""
            student["second"] = ""
            student["third"] = ""
            student["smv"] = ""
            student["attendance_days"] = ""
            student["attendance_percentage"] = ""
            student["grade"] = "PASSED"
            student["locked"] = False

    settings_data = settings_col.find_one() or {}

    return render_template(
        "attendance_marks.html",
        students=all_students,
        attendance_days=settings_data.get(
            "attendance_days",
            72
        )
    )
@app.route("/save_marks", methods=["POST"])
def save_marks():

    data = request.get_json()

    # Get student details
    student = students.find_one({
        "_id": ObjectId(data["student_id"])
    })

    current_class = int(student["std"])
    grade = data["grade"]

    # Decide next class
    new_class = current_class

    if grade == "ABSENT":
        new_class = current_class

    elif grade != "":
        if current_class < 11:
            new_class = current_class + 1

    # Save marks
    marks.update_one(

        {
            "student_id": data["student_id"]
        },

        {
            "$set": {

                "first": data["first"],
                "second": data["second"],
                "third": data["third"],
                "smv": data["smv"],

                "attendance_days":
                data["attendance_days"],

                "attendance_percentage":
                data["attendance_percentage"],

                "grade":
                grade,

                "locked": True
            }
        },

        upsert=True
    )

    # Update student's class
    students.update_one(
        {
            "_id": ObjectId(data["student_id"])
        },
        {
            "$set": {
                "std": str(new_class)
            }
        }
    )

    return jsonify({
        "success": True
    })

@app.route("/save_all_marks", methods=["POST"])
def save_all_marks():

    data = request.get_json()

    for row in data:

        marks.update_one(

            {
                "student_id":
                row["student_id"]
            },

            {
                "$set": {

                    "first": row["first"],
                    "second": row["second"],
                    "third": row["third"],
                    "smv": row["smv"],

                    "attendance_days":
                    row["attendance_days"],

                    "attendance_percentage":
                    row["attendance_percentage"],

                    "grade":
                    row["grade"],

                    "locked": True
                }
            },

            upsert=True
        )

    return jsonify({
        "success": True
    })



@app.route("/unlock_marks", methods=["POST"])
def unlock_marks():

    data = request.get_json()

    marks.update_one(
        {"student_id": data["student_id"]},
        {"$set": {"locked": False}}
    )

    return jsonify({"success": True})


# =========================
# RUN APP
# =========================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )