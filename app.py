import MAX

MAX.connect()


students = MAX.get_students()


for student in students:
	info = MAX.get_student_details(student)

	print(info)
