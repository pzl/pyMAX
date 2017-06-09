import MAX
import gi
gi.require_version('Gtk','3.0')
from gi.repository import Gtk, GLib, GdkPixbuf, Gio
import threading
import urllib.request


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
	stream = Gio.MemoryInputStream.new_from_data(response.read(),None)
	return GdkPixbuf.Pixbuf.new_from_stream_at_scale(stream, size,size,True, None)
def newLabel(text):
	label = Gtk.Label()
	label.set_justify(Gtk.Justification.LEFT)
	label.set_text(text)
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
	nameBox.pack_start(newLabel(f"{student.first_name} {student.last_name}"), True, True, 0)
	nameBox.pack_start(newLabel("checked in" if student.checked_in else "checked out"), True, True, 0)

	idBox.pack_start(student_icon, True, True, 0)
	idBox.pack_start(nameBox, True, True, 0)

	info.pack_start(idBox, True, True, 0)


	# Current Room
	if student.current_room:
		roomBox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=20)
		roomBox.pack_start(newLabel(f"Room: {student.current_room.name}"),True,True,0)

		teachBox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=0)
		for t in student.current_room.teachers:
			tbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL,spacing=2)
			timg = Gtk.Image.new_from_pixbuf(url_to_icon(t.photo_url,50))
			tbox.pack_start(timg, True, True, 0)
			tbox.pack_start(newLabel(str(t)),True,True,0)
			teachBox.pack_start(tbox, True, True, 0)

		roomBox.pack_start(teachBox, True, True, 0)
		info.pack_start(roomBox, True, True, 0)

	# Daily Sheet

	mealsBox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=15)
	for meal in student.info.meals:
		mealRow = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
		mealRow.pack_start(newLabel(meal.time),True,True,0)

		foodBox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
		for food in meal.foods:
			foodBox.pack_start(newLabel(str(food)), True, True, 0)
		mealRow.pack_start(foodBox, True, True, 0)

		mealsBox.pack_start(mealRow, True, True, 0)
	info.pack_start(mealsBox, True, True, 0)

	napBox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
	for nap in student.info.naps:
		napRow = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
		napRow.pack_start(newLabel(f"Start: {nap.start_time}"), True, True, 0)
		napRow.pack_start(newLabel(f"End: {nap.end_time}"), True, True, 0)
		napRow.pack_start(newLabel("Duration: %dm %d sec" % divmod(nap.duration,60)), True, True, 0)

		napBox.pack_start(napRow,True,True,0)
	info.pack_start(napBox,True,True,0)

	pottyBox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
	for potty in student.info.bathroom_visits:
		pottyRow = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
		pottyRow.pack_start(newLabel(f"Bathroom visit: {potty.type}"), True, True, 0)
		pottyRow.pack_start(newLabel(f"At: {potty.time}"), True, True, 0)

		types = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
		for t in potty.diaper_type:
			types.pack_start(newLabel(t),True,True,0)
		pottyRow.pack_start(types, True, True, 0)

		pottyBox.pack_start(pottyRow,True,True,0)
	info.pack_start(pottyBox,True,True,0)


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