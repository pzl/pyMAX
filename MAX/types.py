import datetime


class MAXObj(object):
	"""generic shared parent"""
	def __init__(self):
		super(MAXObj, self).__init__()
	def __repr__(self):
		return f"{self.__class__.__name__}({self.__dict__})"	


class Time(MAXObj):
	"""Convert wonky dates/times to reasonable objects"""
	def __init__(self,t):
		super(Time,self).__init__()
		if not t:
			self.time = None
			return
		proper_tz = ''.join(t.rsplit(':',1)) #there is an extra colon in the timezone to remove
		self.time = datetime.datetime.strptime(proper_tz,"%Y-%m-%dT%H:%M:%S.%f%z")
		if self.time.year == 2000: #it was meant to be a time-only string
			self.time = self.time.time()

		# Time was probably entered wrong. Let's correct this.
		if self.time.hour > 17:
			self.time -= datetime.timedelta(hours=12)

	def __str__(self):
		if not self.time:
			return ""
		return self.time.strftime("%-I:%M%p").lower()

	def __bool__(self):
		return not not self.time

	def __eq__(self,other): return self.time == other.time
	def __lt__(self,other): return self.time < other.time

class Person(MAXObj):
	"""Generic person class based on MAX fields"""
	def __init__(self, info):
		super(Person, self).__init__()
		for field in ["id","first_name","last_name","photo_url","photo_processing","type"]:
			setattr(self,field,info[field])
	
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
		y,m,d = list(map(int,info['day'].split('-')))
		self.day = datetime.date(y,m,d)
		for field in ["report_id","student_id","locked","sent",
					"achievements","request_items", "teacher_notes","parent_request"]:
			if field in info:
				setattr(self,field,info[field])

		for field in ["created_at","updated_at","checked_in_at","checked_out_at",
						"schedule_check_in","schedule_check_out"]:
				setattr(self,field,Time(info[field]))


		self.meals = sorted(list(map(Meal,info['meals'])),key=lambda m: m.time)
		self.messages = list(map(Message,info['messages']))
		self.naps = sorted(list(map(Nap,info['naps'])),key=lambda n: n.start_time)
		self.bathroom_visits = sorted(list(map(BathroomVisit, info['bathroom_visits'])),key=lambda b: b.time)

class Meal(MAXObj):
	def __init__(self, info):
		super(Meal, self).__init__()
		for field in ['id','time_type','comment']:
			if field in info:
				setattr(self,field,info[field])
		for field in ['time','created_at','updated_at']:
			setattr(self,field,Time(info[field]))

		self.foods = list(map(Food,info['entries_attributes']))	

class Food(MAXObj):
	def __init__(self, info):
		super(Food, self).__init__()
		for field in ['id','food_id','category','name','eaten','unit_type']:
			if field in info:
				setattr(self,field,info[field])
		self.created_at = Time(info['created_at'])
		self.updated_at = Time(info['updated_at'])

	def __str__(self):
		if self.unit_type == "fractions":
			amount = "all" if self.eaten ==1 else "{0:.0f}%".format(self.eaten * 100)
		else:
			amount = f"{self.eaten} {self.unit_type}"
		return f"{self.name}, {amount}"

class Nap(MAXObj):
	def __init__(self, info):
		super(Nap, self).__init__()
		self.id = info['id']
		self.duration = info['duration']
		for field in ['start_time','end_time','created_at','updated_at']:
			setattr(self,field,Time(info[field]))


class BathroomVisit(MAXObj):
	def __init__(self, info):
		super(BathroomVisit, self).__init__()
		for field in ['id','type','diaper_type','bathroom_type','notes']:
			if field in info:
				setattr(self,field,info[field])
		for field in ['time','created_at','updated_at']:
			setattr(self,field,Time(info[field]))


class Message(MAXObj):
	"""MAX generic Message"""
	def __init__(self, info):
		super(Message, self).__init__()
		for field in ['id','content','read','attachment_url',
						'attachment_file_name','attachment_content_type',
						'attachment_file_size','system_generated']:
			if field in info:
				setattr(self,field,info[field])

		for field in ['read_at','created_at','updated_at','attachment_updated_at']:
			setattr(self,field,Time(info[field]))

		if 'author' in info:
			self.author = Person(info['author'])

		if 'student' in info:
			self.student = Person(info['student'])
		
class TeacherRequest(MAXObj):
	"""Teacher request for items from Parent"""
	def __init__(self, info):
		super(TeacherRequest, self).__init__()
		for field in ['id','due_type','due_on']:
			if field in info:
				setattr(self,field,info[field])
		for field in ['created_at','updated_at','due_at']:
			setattr(self,field,Time(info[field]))

		self.items = list(map(RequestItem,info['item_ids']))
		
class RequestItem(MAXObj):
	"""A thing the Teacher can request"""
	def __init__(self, info):
		super(RequestItem, self).__init__()
		self.id = info['id']
		self.name = info['name']
		self.created_at = Time(info['created_at'])
		self.updated_at = Time(info['updated_at'])
	def __str__(self):
		return self.name
