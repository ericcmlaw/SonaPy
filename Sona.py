import requests

class Sona:
	def __init__(self, username, password, domain):
		self.studies = []
		self.domain = domain
		self.api = domain + '/services/SonaMobileAPI.svc/'
		# only p_username and p_password essential
		self.data = { 
			'p_username': username, 
			'p_password': password, 
			#'p_language_pref': 'EN', 
			#'p_mobile_version': '1.0.0'
		}
		self.__login()
		
	def __login(self):
		response = requests.post(self.api + 'Authenticate', json=self.data).json()
		self.session = {'p_sessionToken': response['Result']}
		return response['ErrorCode'] # 0=ok, -1=invalid
	
	def __post(self, action, data):
		response = requests.post(self.api + action, json=data).json()
		# -1001 is wrong session, -1002 is expired session
		while response['ErrorCode'] in (-1001, -1002) and self.session['p_sessionToken'] != '': # session renew and retry
			self.__login()
			data.update(self.session)
			response = requests.post(self.api + action, json=data).json()
		if response['ErrorCode'] == 0:
			return response['Result']
		
	def logout(self):
		return self.__post('ProcessLogoff', self.session) # true
	
	def get_study(self, id):
		session = dict(self.session)
		session["p_experiment_id"] = id
		return self.__post('GetStudyInfo', session)

	def get_study_eligibility(self, id):
		return self.get_study(id)['display_timeslots_button']	

	def get_timeslot(self, id):
		session = dict(self.session)
		session["p_experiment_id"] = id
		return self.__post('GetAllTimeslotInfo', session)

	def get_free_timeslot(self, id):
		timeslot = self.get_timeslot(id)
		return [item for item in timeslot if item['display_signup_button'] == True]
			
	def get_studies(self):
		return self.__post('GetStudiesPageInfo', self.session)['studies']
	
	def get_available_studies(self):
		studies = self.get_studies()
		return [item for item in studies if item['timeslots_available'] and not item['first_line'].startswith('HK')]
		
	def get_new_studies(self):
		available = self.get_available_studies()
		temp = [item for item in available if item not in self.studies]
		if temp:
			self.studies = temp
		return temp
	
	# messes with pickle load
	#def __del__(self):
		#self.logout()
