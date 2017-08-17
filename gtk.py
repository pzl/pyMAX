import MAX
import datetime
import gi
gi.require_version('Gtk','3.0')
from gi.repository import Gtk, GLib, GdkPixbuf, Gio
import threading, queue
import urllib.request
from pathlib import Path
import hashlib
from PIL import Image, ImageOps, ImageDraw
from io import BytesIO
import os

class L(Gtk.Label):
	def __init__(self,markup,*args,**kwargs):
		super(L,self).__init__(*args,**kwargs)
		self.set_markup(str(markup))

def passwin(q):
	dog = Gtk.Dialog(title="Log In")
	dog.set_modal(True)
	dog.add_buttons(Gtk.STOCK_CANCEL,Gtk.ResponseType.CANCEL,Gtk.STOCK_OK,Gtk.ResponseType.OK)


	container = dog.get_content_area()
	grid = Gtk.Grid()


	grid.attach(L("Username:"),0,0,1,1)
	user_entry = Gtk.Entry(placeholder_text="Username")
	grid.attach(user_entry,1,0,1,1)

	grid.attach(L("Password:"),0,1,1,1)
	pass_entry = Gtk.Entry(placeholder_text="Password",visibility=False)
	grid.attach(pass_entry,1,1,1,1)

	container.pack_start(grid,True,True,0)
	container.show_all()

	response = dog.run()
	if response == Gtk.ResponseType.CANCEL:
		dog.destroy()
		# quit app?
	else:
		username = user_entry.get_text()
		password = pass_entry.get_text()
		user_entry.set_editable(False)
		pass_entry.set_editable(False)
		pass_entry.set_progress_fraction(0.5)
		user_entry.progress_pulse()

		q.put(username)
		q.put(password)
		q.put(dog)
		dog.destroy()

# must be called from Non-GTK thread.
def auth(username=None,password=None):
	try:
		MAX.connect()
	except MAX.api.PasswordRequired:
		q = queue.Queue()
		GLib.idle_add(passwin,q)
		username = q.get()
		password = q.get()
		result = MAX.connect(username,password)

		if 'error' in result:
			return auth()


def local_img(filename,size=20):
	pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale("icons/"+filename,size,size,True)
	return Gtk.Image.new_from_pixbuf(pixbuf)

def fetch_img(url):
	IMG_CACHE=Path("/tmp/MAX/")
	IMG_CACHE.mkdir(parents=True,exist_ok=True)
	url_hash = hashlib.md5(url.encode('utf-8')).hexdigest()
	if (IMG_CACHE/url_hash).exists():
		return IMG_CACHE/url_hash

	response = urllib.request.urlopen(url)
	content = response.read()
	with open(IMG_CACHE/url_hash,"wb") as f:
		f.write(content)
	return BytesIO(content)


def url_to_icon(url,size=100):
	pillow_img = Image.open(fetch_img(url))

	round_mask = Image.new('L',(size*3,size*3),0)
	draw = ImageDraw.Draw(round_mask)
	draw.ellipse((0,0,size*3,size*3),fill=255)
	round_mask = round_mask.resize(pillow_img.size, Image.ANTIALIAS)
	pillow_img.putalpha(round_mask)

	rounded = BytesIO()
	pillow_img.save(rounded, format='PNG')
	stream = Gio.MemoryInputStream.new_from_data(rounded.getvalue(),None)
	return GdkPixbuf.Pixbuf.new_from_stream_at_scale(stream, size,size,True, None)


class Page(Gtk.Box):
	"""the area of content """
	title="page"
	icon="view-paged"

	def __init__(self):
		super(Page, self).__init__(orientation=Gtk.Orientation.VERTICAL)

	def set_urgent(self,urgent=True):
		self.get_parent().child_set_property(self,"needs-attention",urgent)

	def set_loading(self):
		for child in self.get_children():
			child.destroy()
		spinner = Gtk.Spinner(active=True,halign=Gtk.Align.CENTER,valign=Gtk.Align.CENTER)
		self.pack_start(spinner,True,True,0)
		spinner.show()

	def load(self,*args):
		self.set_loading()
		thread = threading.Thread(target=self.fetch_data,args=args)
		thread.daemon=True
		thread.start()

	def load_complete(self):
		for child in self.get_children():
			child.destroy()

	def fetch_data(self):
		GLib.idle_add(self.load_complete)

class InfoPage(Page):
	"""The DCS-displaying page"""
	title="Info"
	icon="dialog-information-symbolic"

	def load_complete(self,student):
		super(InfoPage,self).load_complete()
		
		WALL_MARGIN=10
		ICON_TO_NAME_SPACE=7

		basic_info = Gtk.Box(orientation=Gtk.Orientation.VERTICAL,margin_left=WALL_MARGIN,margin_right=WALL_MARGIN,spacing=15)
		namedate = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL,spacing=ICON_TO_NAME_SPACE)
		img = student.rounded_image if hasattr(student,'rounded_image') else url_to_icon(student.photo_url,size=50)
		student_icon = Gtk.Image.new_from_pixbuf(img)
		student_icon.set_halign(Gtk.Align.START)
		student_icon.set_valign(Gtk.Align.CENTER)
		namedate.pack_start(student_icon,False,False,0)
		namedate.pack_start(L(f"{student.first_name} {student.last_name}",halign=Gtk.Align.START,valign=Gtk.Align.CENTER),False,False,0)
		namedate.pack_end(L(student.info.day.strftime("%a, %b %-d"),halign=Gtk.Align.END,valign=Gtk.Align.CENTER),False,True,0)
		basic_info.pack_start(namedate,False,False,0)


		if student.current_room:
			roombox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL,spacing=ICON_TO_NAME_SPACE)
			roombox.pack_start(Gtk.Image.new_from_icon_name("avatar-default",Gtk.IconSize.SMALL_TOOLBAR),False,False,0)
			roombox.pack_start(L(student.current_room.name),False,False,0)
			basic_info.pack_start(roombox,False,False,0)
			teachers = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
			for t in student.current_room.teachers:
				teachbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL,spacing=ICON_TO_NAME_SPACE)
				img = t.rounded_image if hasattr(t,'rounded_image') else url_to_icon(t.photo_url,size=50)
				teachbox.pack_start(Gtk.Image.new_from_pixbuf(t.rounded_image),False,False,0)
				teachbox.pack_start(L(f"{t.first_name} {t.last_name}"),False,False,0)
				teachers.pack_start(teachbox,True,False,0)
			basic_info.pack_start(teachers,False,False,0)

		self.pack_start(basic_info,False,False,0)
		self.pack_start(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL),False,False,10) # separator padding

		togglebox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL,halign=Gtk.Align.CENTER,valign=Gtk.Align.START,margin_bottom=25)
		togglebox.pack_start(L("Grouped",halign=Gtk.Align.START),False,False,0)
		self.toggle = Gtk.Switch()
		self.toggle.connect("notify::active",self.show_dcs)
		togglebox.pack_start(self.toggle,False,False,0)
		togglebox.pack_start(L("Ordered"),False,False,0)
		self.pack_start(togglebox,False,False,0)


		### DCS
		self.events=[]
		self.events.extend(student.info.meals)
		self.events.extend(student.info.naps)
		self.events.extend(student.info.bathroom_visits)

		self.events = sorted(self.events,key=lambda x: x.time.time if hasattr(x,'time') else x.start_time.time)
		self.student = student

		if hasattr(self,'dcs_box') and self.dcs_box:
			self.dcs_box.destroy()
		self.dcs_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL,margin_left=WALL_MARGIN,margin_right=WALL_MARGIN)
		self.pack_start(self.dcs_box,True,True,0)
		self.show_dcs()

		self.show_all()

	def fetch_data(self,date=None):
		auth()
		student = MAX.get_student_detail(199)

		if date and date != datetime.date.today():
			student.info = MAX.get_info(199,date.strftime("%Y-%m-%d"))
			student.current_room = None
		else:
			if student.current_room:
				for t in student.current_room.teachers:
					t.rounded_image = url_to_icon(t.photo_url,50)
		GLib.idle_add(self.load_complete,student)

	def show_dcs(self,*_):
		for child in self.dcs_box.get_children():
			child.destroy()


		COLSPACE=4
		ROWSPACE=8

		if not self.toggle.get_active():
			# Grouped
			self.dcs_box.pack_start(L("<big><b>Food</b></big>",halign=Gtk.Align.START,margin_bottom=ROWSPACE),False,False,0)
			mealgrid = Gtk.Grid(orientation=Gtk.Orientation.VERTICAL,column_spacing=COLSPACE,row_spacing=ROWSPACE)
			mealgrid.row =0
			self.dcs_box.pack_start(mealgrid,False,False,0)
			meals = [x for x in self.events if type(x) == MAX.types.Meal]
			for meal in meals:
				self.make_meal(mealgrid,meal)
			self.dcs_box.pack_start(L("<big><b>Naps</b></big>",halign=Gtk.Align.START,margin_top=ROWSPACE*3,margin_bottom=ROWSPACE),False,False,0)
			napgrid = Gtk.Grid(orientation=Gtk.Orientation.VERTICAL,column_spacing=COLSPACE,row_spacing=ROWSPACE)
			napgrid.row=0
			self.dcs_box.pack_start(napgrid,False,False,0)
			naps = [x for x in self.events if type(x) == MAX.types.Nap]
			for nap in naps:
				self.make_nap(napgrid,nap)
			self.dcs_box.pack_start(L("<big><b>Bathroom</b></big>",halign=Gtk.Align.START,margin_top=ROWSPACE*3,margin_bottom=ROWSPACE),False,False,0)
			visits = [x for x in self.events if type(x) == MAX.types.BathroomVisit]
			pottygrid = Gtk.Grid(orientation=Gtk.Orientation.VERTICAL,column_spacing=COLSPACE,row_spacing=ROWSPACE)
			pottygrid.row=0
			self.dcs_box.pack_start(pottygrid,False,False,0)
			for visit in visits:
				self.make_potty(pottygrid,visit)

		else:
			grid = Gtk.Grid(orientation=Gtk.Orientation.VERTICAL,column_spacing=COLSPACE,row_spacing=ROWSPACE)
			grid.row=0
			self.dcs_box.pack_start(grid,False,False,0)
			for event in self.events:
				if type(event) == MAX.types.Meal:
					add_event = self.make_meal
				elif type(event) == MAX.types.Nap:
					add_event = self.make_nap
				else:
					add_event = self.make_potty
				add_event(grid,event)


		if self.student.info.messages:
			self.dcs_box.pack_start(L("<big><b>Messages</b></big>",halign=Gtk.Align.START,margin_top=ROWSPACE*3,margin_bottom=ROWSPACE),False,False,0)
			msg_grid = Gtk.Grid(orientation=Gtk.Orientation.VERTICAL,column_spacing=COLSPACE,row_spacing=ROWSPACE)
			msg_grid.row=0
			self.dcs_box.pack_start(msg_grid,False,False,0)
			for msg in self.student.info.messages:
				self.make_dcs_message(msg_grid,msg)

		if self.student.info.request_items:
			self.dcs_box.pack_start(L("<big><b>Request Items</b></big>",halign=Gtk.Align.START,margin_top=ROWSPACE*3,margin_bottom=ROWSPACE),False,False,0)
			reqs_grid = Gtk.Grid(orientation=Gtk.Orientation.VERTICAL,column_spacing=COLSPACE,row_spacing=ROWSPACE)
			reqs_grid.row=0
			self.dcs_box.pack_start(reqs_grid,False,False,0)
			for item in self.student.info.request_items:
				self.make_req(reqs_grid,item)

		if self.student.info.teacher_notes:
			self.dcs_box.pack_start(L("<big><b>Teacher Notes</b></big>",halign=Gtk.Align.START,margin_top=ROWSPACE*3,margin_bottom=ROWSPACE),False,False,0)
			notes = Gtk.Grid(orientation=Gtk.Orientation.VERTICAL,column_spacing=COLSPACE,row_spacing=ROWSPACE)
			notes.row=0
			self.dcs_box.pack_start(notes,False,False,0)
			for note in self.student.info.teacher_notes:
				self.make_note(notes,note)

		self.dcs_box.show_all()

	def make_meal(self,container,meal):
		container.attach(L(meal.time,valign=Gtk.Align.START,halign=Gtk.Align.END),0,container.row,1,len(meal.foods))
		for i,food in enumerate(meal.foods):
			if food.category.lower() == "drink":
				icon = local_img("bottle.svg")
			else:
				filename = food.name.lower().replace(" ","_")
				if os.path.exists("icons/"+filename+".svg"):
					icon = local_img(filename+".svg")
				elif os.path.exists("icons/"+filename+".png"):
					icon = local_img(filename+".png")
				else:
					icon = Gtk.Image.new_from_icon_name("avatar-default",Gtk.IconSize.SMALL_TOOLBAR)
			container.attach(icon,1,container.row,1,1)
			container.attach(L(food,halign=Gtk.Align.START),2,container.row,1,1)
			container.row += 1
		if meal.comment:
			container.attach(Gtk.Image.new_from_icon_name("user-available",Gtk.IconSize.SMALL_TOOLBAR),0,container.row,1,1)
			container.attach(meal.comment,1,container.row,2,1)
			container.row +=1


	def make_nap(self,container,nap):
		container.attach(L(nap.start_time,halign=Gtk.Align.END),0,container.row,1,1)
		container.attach(Gtk.Image.new_from_icon_name("face-tired",Gtk.IconSize.SMALL_TOOLBAR),1,container.row,1,1)
		container.attach(L(str(nap.end_time)+" Duration: %dh %dm" % divmod(nap.duration,60),halign=Gtk.Align.START),2,container.row,1,1)
		container.row +=1

	def make_potty(self,container,visit):
		container.attach(L(visit.time,halign=Gtk.Align.END),0,container.row,1,1)
		icons = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
		for action in visit.diaper_type:
			icons.pack_start(local_img("pee.svg" if action=='wet' else 'poo.svg'),True,True,0)
		container.attach(icons,1,container.row,1,1)
		if visit.notes:
			container.attach(L(visit.notes,halign=Gtk.Align.START),2,container.row,1,1)
		container.row +=1

	def make_dcs_message(self,container,msg):
		container.attach(L(msg.updated_at,halign=Gtk.Align.END),0,container.row,1,1)
		container.attach(Gtk.Image.new_from_icon_name("user-offline" if msg.read else "user-available",Gtk.IconSize.SMALL_TOOLBAR),1,container.row,1,1)
		text = L(msg.content,halign=Gtk.Align.START)
		text.set_line_wrap(True)
		container.attach(text,2,container.row,1,1)
		container.row += 1

	def make_req(self,container,item):
		container.attach(L(item.updated_at,halign=Gtk.Align.END),0,container.row,1,1)
		for thing in item.items:
			container.attach(L(thing.name,halign=Gtk.Align.START),1,container.row,2,1)
			container.row +=1
		# @todo: due_on / due_at

	def make_note(self,container,note):
		container.attach(L(note.updated_at),0,container.row,1,1)
		container.attach(Gtk.Image.new_from_icon_name("user-available",Gtk.IconSize.SMALL_TOOLBAR),1,container.row,1,1)
		text = L(note)
		text.set_line_wrap(True)
		container.attach(text,2,container.row,1,1)
		container.row += 1

class MessagePage(Page):
	title="Messages"
	icon="mail-message-new"

class Window(Gtk.Window):
	"""It just organizes stuff"""
	def __init__(self):
		super(Window, self).__init__()
		self.set_position(Gtk.WindowPosition.MOUSE)
		self.set_default_size(450,500)
		self.connect("delete-event",Gtk.main_quit)
		self._create_header()
		self.scroll = Gtk.ScrolledWindow()
		self.scroll.set_propagate_natural_height(True)
		super(Window,self).add(self.scroll)
		self._create_stack()


	def add(self,widget):
		self.scroll.add(widget)

	def add_page(self,page):
		self.stack.add_titled(page,page.title,page.title)
		self.stack.child_set_property(page,"icon-name",page.icon)
		page.load()
		return page

	def _create_stack(self):
		self.stack = Gtk.Stack(
			transition_type=Gtk.StackTransitionType.SLIDE_LEFT_RIGHT,
			transition_duration=300,
			vhomogeneous=False)
		self.stack.connect("notify::visible-child",self.event_stack_switched)
		self.add(self.stack)
		self.switcher.set_stack(self.stack)

	def _create_header(self):
		self.date = datetime.date.today()

		self.header = Gtk.HeaderBar()
		self.header.set_show_close_button(True)
		self.header.set_title("Bernie")
		self.header.set_has_subtitle(True)
		self.header.set_decoration_layout(":minimize,close")
		self.set_titlebar(self.header)

		self.switcher = Gtk.StackSwitcher(valign=Gtk.Align.CENTER,halign=Gtk.Align.CENTER)
		self.header.pack_start(self.switcher)

		self.time_nav = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
		self.back = Gtk.Button()
		self.back.get_style_context().add_class("linked")
		self.back.connect("clicked",self.event_arrow_clicked)
		self.back.add(Gtk.Image.new_from_icon_name("pan-start-symbolic",Gtk.IconSize.SMALL_TOOLBAR))
		self.time_nav.pack_start(self.back,False,False,0)

		pickdate = Gtk.MenuButton()
		pickdate.get_style_context().add_class("linked")
		pickdate.add(Gtk.Image.new_from_icon_name("x-office-calendar",Gtk.IconSize.SMALL_TOOLBAR))
		self.time_nav.pack_start(pickdate,False,False,0)

		self.forward = Gtk.Button()
		self.forward.get_style_context().add_class("linked")
		self.forward.connect("clicked",self.event_arrow_clicked)
		self.forward.add(Gtk.Image.new_from_icon_name("pan-end-symbolic",Gtk.IconSize.SMALL_TOOLBAR))
		self.time_nav.pack_start(self.forward,False,False,0)


		self.date_pop = Gtk.Popover()
		self.cal = Gtk.Calendar()
		self.cal.connect("day-selected-double-click",self.event_cal_changed)
		self.date_pop.connect("closed",self.event_cal_hidden)
		self.date_pop.add(self.cal)
		self.cal.show_all()
		pickdate.set_popover(self.date_pop)

		self.header.pack_end(self.time_nav)

		refresh = Gtk.Button()
		refresh.add(Gtk.Image.new_from_icon_name("view-refresh-symbolic",Gtk.IconSize.SMALL_TOOLBAR))
		refresh.connect("clicked",lambda w: self.stack.get_visible_child().load())
		self.header.pack_start(refresh)

	def change_date(self,date):
		self.date=date
		self.header.set_subtitle(self.date.strftime("%Y-%m-%d"))
		self.cal.disconnect_by_func(self.event_cal_changed)
		self.cal.select_month(date.month-1,date.year)
		self.cal.select_day(date.day)
		self.cal.connect("day-selected-double-click",self.event_cal_changed)
		self.stack.get_visible_child().load(self.date)

	def event_cal_changed(self,cal):
		"""A date was double-clicked. Hide the popover, and update"""
		self.date_pop.disconnect_by_func(self.event_cal_hidden)
		self.date_pop.popdown()
		self.date_pop.connect("closed",self.event_cal_hidden)
		y,m,d = cal.get_date()
		self.change_date(datetime.date(y,m+1,d))

	def event_cal_hidden(self,popover):
		"""The popover closed, update if needed"""
		y,m,d = self.cal.get_date()
		date = datetime.date(y,m+1,d)
		if self.date != date:
			self.change_date(date)

	def event_arrow_clicked(self,button):
		direction=1
		if button == self.back:
			direction=-1

		d = self.date + datetime.timedelta(days=direction)
		while d.isoweekday() in (6,7): #Saturday, Sunday
			d += datetime.timedelta(days=direction)

		self.change_date(d)

	def event_stack_switched(self,stack,event):
		tabname = stack.get_visible_child_name()
		if tabname == "Info":
			self.time_nav.show()
			self.header.set_subtitle(self.date.strftime("%Y-%m-%d"))
		else:
			self.time_nav.hide()
			self.header.set_subtitle()


def main():
	window = Window()

	styles = Gtk.CssProvider()
	styles.load_from_data(b"")
	Gtk.StyleContext.add_provider_for_screen(window.get_screen(),styles,Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

	dcs_page = window.add_page(InfoPage())
	inbox_page = window.add_page(MessagePage())
	inbox_page.set_urgent()

	window.show_all()
	GLib.MainLoop().run()

if __name__ == "__main__":
	main()

### @todo: Notes/Messages in the DCS -- re: diarrhea 
