import datetime

class MAXObj(object):
	"""generic shared parent"""
	def __init__(self):
		super(MAXObj, self).__init__()

	def __repr__(self):
		return f"{self.__class__.__name__}({self.__dict__})"	

	def _parsetime(self,t):
		proper_tz = ''.join(t.rsplit(':',1))
		return datetime.datetime.strptime(proper_tz,"%Y-%m-%dT%H:%M:%S.%f%z").time().strftime("%I:%M %p")

class Person(MAXObj):
	"""Generic person class based on MAX fields"""
	def __init__(self, info):
		super(Person, self).__init__()
		for field in ["id","first_name","last_name","photo_url","photo_processing","type"]:
			self.__dict__[field] = info[field]
	
	def __str__(self):
		return f"{self.first_name} {self.last_name}, {self.type}"


class Student(Person):
	"""MAX concept of a Child/Student"""
	def __init__(self, info):
		super(Student, self).__init__(info)
		self.checked_in = info['checked_in']
		self.medical_alerts_count = info['medical_alerts_count']

		if 'current_room' in info:
			if info['current_room']:
				self.current_room = Room(info['current_room'])
			else:
				self.current_room = None

		if 'dcs' in info:
			self.info = InfoSheet(info['dcs'])


class Teacher(Person):
	"""MAX concept of a Child/Teacher"""
	def __init__(self, info):
		super(Teacher, self).__init__(info)
		self.title = info['title']


class Room(MAXObj):
	"""MAX child room"""
	def __init__(self, info):
		super(Room, self).__init__()
		self.id = info['id']
		self.name = info['name']
		self.teachers = list(map(Teacher,info['current_teachers']))
	def __str__(self):
		return self.name

class InfoSheet(MAXObj):
	"""Daily Contact Sheet"""
	def __init__(self, info):
		super(InfoSheet, self).__init__()
		for field in ["report_id","student_id","day","created_at","updated_at",
					  "locked","sent","achievements","request_items",
					  "teacher_notes","checked_in_at","checked_out_at","schedule_check_in",
					  "schedule_check_out","parent_request"]:
			if field in info:
				self.__dict__[field] = info[field]
			else:
				print("DCS report did not contain field: %s" % (field,))


		self.meals = sorted(list(map(Meal,info['meals'])),key=lambda m: m._time)
		self.messages = list(map(Message,info['messages']))
		self.naps = sorted(list(map(Nap,info['naps'])),key=lambda n: n._start_time)
		self.bathroom_visits = sorted(list(map(BathroomVisit, info['bathroom_visits'])),key=lambda b: b._time)

class Meal(MAXObj):
	def __init__(self, info):
		super(Meal, self).__init__()
		for field in ['id','time_type','comment','created_at','updated_at']:
			if field in info:
				self.__dict__[field] = info[field]
		self._time = info['time']
		self.time = self._parsetime(self._time)
		self.foods = list(map(Food,info['entries_attributes']))	

class Food(MAXObj):
	def __init__(self, info):
		super(Food, self).__init__()
		for field in ['id','food_id','category','name','eaten','created_at','updated_at','unit_type']:
			if field in info:
				self.__dict__[field] = info[field]
	def __str__(self):
		if self.unit_type == "fractions":
			if self.eaten == 1:
				amount = "all"
			else:
				amount = "{0:.0f}%".format(self.eaten * 100)
		else:
			amount = f"{self.eaten} {self.unit_type}"
		return f"{self.name}, {amount}"

class Nap(MAXObj):
	def __init__(self, info):
		super(Nap, self).__init__()
		for field in ['id','duration','created_at','updated_at']:
			if field in info:
				self.__dict__[field] = info[field]

		self._start_time = info['start_time']
		self._end_time = info['end_time']
		self.start_time = self._parsetime(info['start_time'])
		self.end_time = self._parsetime(info['end_time'])

class BathroomVisit(MAXObj):
	def __init__(self, info):
		super(BathroomVisit, self).__init__()
		for field in ['id','type','diaper_type','bathroom_type','notes','created_at','updated_at']:
			if field in info:
				self.__dict__[field] = info[field]
		self._time = info['time']
		self.time = self._parsetime(info['time'])

class Message(MAXObj):
	"""MAX generic Message"""
	def __init__(self, info):
		super(Message, self).__init__()
		for field in ['id','content','read','read_at','created_at','updated_at',
					'attachment_url','attachment_file_name','attachment_content_type',
					'attachment_file_size','attachment_updated_at','system_generated']:
			if field in info:
				self.__dict__[field] = info[field]

		if 'author' in info:
			self.author = Person(info['author'])

		if 'student' in info:
			self.student = Person(info['student'])
		
class TeacherRequest(MAXObj):
	"""Teacher request for items from Parent"""
	def __init__(self, info):
		super(TeacherRequest, self).__init__()
		for field in ['id','due_type','created_at','updated_at','due_on','due_at']:
			if field in info:
				self.__dict__[field] = info[field]

		self.items = list(map(RequestItem,info['item_ids']))
		
class RequestItem(MAXObj):
	"""A thing the Teacher can request"""
	def __init__(self, info):
		super(RequestItem, self).__init__()
		for field in ['id','name','created_at','updated_at']:
			if field in info:
				self.__dict__[field] = info[field]
	def __str__(self):
		return self.name
