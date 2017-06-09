import os, sys
from pathlib import Path

from MAX import api
from MAX.api import connect
from MAX.types import (
	Student,
	InfoSheet,
)

def get_students():
	return list(map(Student,api.request("/students")))

def get_student_detail(id):
	return Student(api.request(f"/students/{id}"))

def get_info(student_id,date=None):
	params = {"date":date} if date else None
	return InfoSheet(api.request(f"/students/{student_id}/dcs",params=params))