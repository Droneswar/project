from flask import Flask, render_template, request,flash
from pymysql import connections
import os
import boto3
from config import *

app = Flask(__name__)

bucket = custombucket
region = customregion

db_conn = connections.Connection(
    host=customhost,
    port=3306,
    user=customuser,
    password=custompass,
    db=customdb

)
output = {}
table = 'student'


@app.route("/", methods=['GET', 'POST'])
def home():
    return render_template('AddStudent.html')


@app.route("/addstudent", methods=['POST'])
def AddStudent():
    roll_no = request.form['roll_no']
    first_name = request.form['first_name']
    last_name = request.form['last_name']
    branch = request.form['branch']
    college = request.form['college']
    student_image_file = request.files['student_image_file']

    insert_sql = "INSERT INTO student VALUES (%s, %s, %s, %s, %s)"
    cursor = db_conn.cursor()
    
    if roll_no=="" or first_name=="" or last_name=="" or branch=="" or college=="":
        flash('Please enter full details.',category='error')
    elif student_image_file.filename == "":
        flash('Please upload image file.',category='error')

    try:

        cursor.execute(insert_sql, (roll_no, first_name, last_name, branch, college))
        db_conn.commit()
        student_name = "" + first_name + " " + last_name
        # Uplaod image file in S3 #
        student_image_file_name_in_s3 = "roll-no-" + str(roll_no) + "_image_file"
        s3 = boto3.resource('s3')

        try:
            print("Data inserted in MySQL RDS... uploading image to S3...")
            s3.Bucket(custombucket).put_object(Key=student_image_file_name_in_s3, Body=student_image_file)
            bucket_location = boto3.client('s3').get_bucket_location(Bucket=custombucket)
            s3_location = (bucket_location['LocationConstraint'])

            if s3_location is None:
                s3_location = ''
            else:
                s3_location = '-' + s3_location

            object_url = "https://s3{0}.amazonaws.com/{1}/{2}".format(
                s3_location,
                custombucket,
                student_image_file_name_in_s3)

        except Exception as e:
            return str(e)

    finally:
        cursor.close()

    print("all modification done...")
    return render_template('AddStudentOutput.html', name=student_name)

@app.route("/getstudent",methods=['GET','POST'])
def GetStudent():
    return render_template('GetStudent.html')

@app.route("/fetchdata",methods=['GET','POST'])
def GetStudent():
    roll_no=request.form['roll_no']
    try:
        cur = mysql.connection.cursor() 
        cur.execute("""SELECT * FROM student_data WHERE roll_no = %s""", (roll_no,))
        Student = cur.fetchall()
        for row in student:
            roll = row[0]
            fname = row[1]
            lname = row[2]
            branch = row[3]
            college = row[4]
    else:
        flash('Details not found.', category='error')
    bucket_location = boto3.client('s3').get_bucket_location(Bucket=custombucket)
    s3_location = (bucket_location['LocationConstraint'])
    student_image_file_name_in_s3 = "roll-no-" + str(roll_no) + "_image_file"
    object_url = "https://s3{0}.amazonaws.com/{1}/{2}".format(
                s3_location,
                custombucket,
                student_image_file_name_in_s3)
    return render_template('GetStudentOutput.html', roll_no =roll, fname=fname, lname=lname, branch=branch, college=college, image_url=object_url )


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)
