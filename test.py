from mediplanner import MedicoverForm

mf = MedicoverForm()
data = mf.medicover_session.get_form_data({'bookingTypeId': 2, 'regionId': 204, 'specializationId': 4800})
print data
