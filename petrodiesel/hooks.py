app_name = "petrodiesel"
app_title = "Petrodiesel"
app_publisher = "Aman Boora"
app_description = "Fuel retail outlet (petrol pump) management for Indian dealers on ERPNext"
app_email = "aman.chaudharyboora@gmail.com"
app_license = "mit"

required_apps = ["frappe/erpnext"]

add_to_apps_screen = [
	{
		"name": "petrodiesel",
		"logo": "/assets/petrodiesel/images/logo.svg",
		"title": "Petrol Pump",
		"route": "/petrodesk",
	}
]

after_install = "petrodiesel.setup.install.after_install"
after_migrate = ["petrodiesel.setup.install.after_migrate"]

scheduler_events = {
	"daily": ["petrodiesel.tasks.daily"],
}


website_route_rules = [
	{"from_route": "/petrodesk/<path:app_path>", "to_route": "petrodesk"},
]
