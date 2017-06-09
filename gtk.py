import MAX
import gi
gi.require_version('Gtk','3.0')
from gi.repository import Gtk, GLib, GdkPixbuf, Gio
import threading
import urllib.request
from PIL import Image, ImageOps, ImageDraw
from io import BytesIO

def noop(*args, **kwargs):
	pass


""" Things executing in background thread """

def load_data():
	MAX.connect()
	student = MAX.get_student_detail(199)
	GLib.idle_add(hide_spinner)
	GLib.idle_add(show_info,student)


def url_to_icon(url,size=100):
	response = urllib.request.urlopen(url)
	img = Image.open(BytesIO(response.read()))

	round_mask = Image.new('L',(size*3,size*3),0)
	draw = ImageDraw.Draw(round_mask)
	draw.ellipse((0,0,size*3,size*3),fill=255)
	round_mask = round_mask.resize(img.size, Image.ANTIALIAS)
	img.putalpha(round_mask)

	rounded = BytesIO()
	img.save(rounded, format='PNG')
	stream = Gio.MemoryInputStream.new_from_data(rounded.getvalue(),None)
	return GdkPixbuf.Pixbuf.new_from_stream_at_scale(stream, size,size,True, None)

def newLabel(text):
	label = Gtk.Label()
	label.set_justify(Gtk.Justification.LEFT)
	label.set_markup(text)
	return label



""" To be queued for GTK thread running """
def hide_spinner():
	window.get_child().remove(builder.get_object("spinner"))


def show_info(student):
	layout = window.get_child()
	info = builder.get_object("infoWin")


	# Picture and Name
	idBox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=20)
	student_icon = Gtk.Image.new_from_pixbuf(url_to_icon(student.photo_url))

	nameBox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
	nameBox.pack_start(newLabel(f"<span font='Lato Medium 22'>{student.first_name} {student.last_name}</span>"), False, True, 5)
	nameBox.pack_start(newLabel("<span font='Lato Light 11'>checked in</span>" if student.checked_in else "<span font='Lato Light 11'>checked out</span>"), False, True, 0)

	idBox.pack_start(student_icon, False, True, 10)
	idBox.pack_start(nameBox, False, True, 0)

	info.pack_start(idBox, False, True, 0)


	# Current Room
	if student.current_room:
		roomBox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
		roomNameBox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)

		roomNameBox.pack_start(newLabel("<span font='Lato 16'>Room:</span>"),False,False,30)
		roomNameBox.pack_start(newLabel(f"<span font='Lato 13' underline='single'>{student.current_room.name}</span>"),False,False,0)
		roomBox.pack_start(roomNameBox,False,False,0)

		teachBox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=0)
		for t in student.current_room.teachers:
			trow = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL,spacing=2)
			timg = Gtk.Image.new_from_pixbuf(url_to_icon(t.photo_url,50))
			trow.pack_start(timg, False, True, 10)
			trow.pack_start(newLabel(f"<span font='Lato Light 11'>{t}</span>"),False,True,0)
			teachBox.pack_start(trow, False, True, 0)

		roomBox.pack_start(teachBox, False, True, 0)
		info.pack_start(roomBox, False, True, 0)

	# Daily Sheet

	info.pack_start(newLabel("<span font='Lato Medium 16'>Meals</span>"),False,False,0)
	mealsBox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
	for meal in student.info.meals:
		mealRow = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
		mealRow.pack_start(newLabel(f"<span font='Lato 14'>{meal.time}</span>"),False,True,15)

		foodBox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
		for food in meal.foods:
			foodBox.pack_start(newLabel(f"<span font='Lato Light 14'>{food}</span>"), False, True, 0)
		mealRow.pack_start(foodBox, False, True, 0)

		mealsBox.pack_start(mealRow, False, True, 0)
	info.pack_start(mealsBox, False, True, 0)

	info.pack_start(newLabel("<span font='Lato Medium 16'>Naps</span>"),False,False,0)
	napBox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
	for nap in student.info.naps:
		napRow = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
		napRow.pack_start(newLabel(f"<span font='Lato Medium 15'>{nap.start_time} - {nap.end_time}</span>"), False, True, 15)
		napRow.pack_start(newLabel("<span font='Lato Light 16'>Duration: %dh %dm</span>" % divmod(nap.duration,60)), False, True, 0)

		napBox.pack_start(napRow,False,True,0)
	if not student.info.naps:
		napBox.pack_start(newLabel("<span font='Lato Light 13'>None</span>"),True,True,0)
	info.pack_start(napBox,False,True,0)

	info.pack_start(newLabel("<span font='Lato Medium 16'>Bathroom</span>"),False,False,0)
	pottyBox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
	for potty in student.info.bathroom_visits:
		pottyRow = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
		pottyRow.pack_start(newLabel(f"<span font='Lato 14'>{potty.time}</span>"), False, True, 15)
		pottyRow.pack_start(newLabel(f"<span font='Lato Light 12'>{potty.type}</span>"), False, False, 0)
		pottyRow.pack_start(newLabel( "<span font='Lato Light 13'>" + ", ".join(potty.diaper_type) + "</span>" ), False, True, 0)

		pottyBox.pack_start(pottyRow,False,True,0)
	info.pack_start(pottyBox,False,True,0)


	layout.pack_start(info, True, True, 0)
	window.show_all()


builder = Gtk.Builder()
builder.add_from_file("layout.glade")
builder.connect_signals({
	'on_primary_quit': Gtk.main_quit,
	'primary_visible': noop,
	'password_ok': noop,
	'password_cancel': noop,
})

window = builder.get_object("primary")
window.show_all()


thread = threading.Thread(target=load_data)
thread.daemon=True
thread.start()
Gtk.main()