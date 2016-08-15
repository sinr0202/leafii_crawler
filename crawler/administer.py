from connector import database
from parser import get_pdf, get_html
import time
import re

class bcolors:
	HEAD = '\033[95m'
	OKGREEN = '\033[92m'
	FAIL = '\033[91m'
	ENDC = '\033[0m'
	OKBLUE = '\033[94m'

def get_all_urls():
	"""
	() --> list

	Returns a list of all the urls users have submitted.
	"""
	db = database()
	url_list = []
	data = []

	for i in db.users.find():
		if i.get("profile").get("url"):
			url_list.append(i.get("profile").get("url"))
	
	return url_list

def find_user_by_id(user_id):
	#returns a user's info with their id
	try:
		db = database()
		if type(user_id) != str:
			raise TypeError 

		data = db.users.find_one({"_id" : user_id})
		if data:
			return data
		else:
			raise ValueError

	except TypeError:
		raise TypeError(bcolors.FAIL + "Invalid Input. Enter a valid user id as a string to use this function" + bcolors.ENDC)
		return False
	except ValueError:
		raise ValueError(bcolors.FAIL + "Invalid User ID" + bcolors.ENDC)
		return False

def find_user_by_email(email):
	#returns a user's info with their email
	try:
		db = database()
		data = []

		if type(email) != str:
			raise TypeError 

		data = db.users.find_one({"emails.address" : email})
		if data:
			return data
		else:
			raise ValueError

	except TypeError:
		raise TypeError(bcolors.FAIL +"Invalid Input. Enter a valid email as a string to use this function" + bcolors.ENDC)
		return False
	except ValueError:
		raise ValueError(bcolors.FAIL + "No user found with that email" + bcolors.ENDC)
		return False

def find_user_by_name(name):
	#returns a list of all user's who have the input name as their first or last name
	try:
		start_time = time.time()
		
		db = database()
		data = []
		if type(name) != str:
			raise TypeError 
		name = name.lower()

		for i in db.users.find():
			data.append(i)

		#seperates string into array of words	
		temp_name = re.findall(r'\w+', name)

		user_list = []
		#changes search parameters based on number of words in search
		if len(temp_name) == 1:
			#searches for name in the first and last names of people in the profile
			for i in range(len(data)):
				temp_profile = data[i].get("profile")
				if name in temp_profile.get("firstName").lower() or name in temp_profile.get("lastName").lower() :
					user_list = user_list + [data[i]]

		elif len(temp_name) == 2:
			#searches for the full name with exact match
			temp_firstName = temp_name[0]
			temp_lastName = temp_name[1]
			for i in range(len(data)):
				temp_profile = data[i].get("profile")
				if temp_firstName in temp_profile.get("firstName").lower() and temp_lastName in temp_profile.get("lastName").lower():  
					user_list = user_list + [data[i]]

		elif len(temp_name) > 2:
			#if more than three words are in name search, checks each word against first and last name 
			for i in range(len(data)):
				for c in range(len(temp_name)):
					temp_profile = data[i].get("profile")
					if temp_name[c] in temp_profile.get("firstName").lower() or temp_name[c] in temp_profile.get("lastName").lower():
						user_list = user_list + [data[i]]

		if len(user_list) == 0:
			raise ValueError

		for i in range(len(user_list)):
			print user_list[i]
			print ""
		return user_list

	except TypeError:
		raise TypeError(bcolors.FAIL + "Invalid Input. Enter a valid name as a string to use this function" + bcolors.ENDC)
		return False
	except ValueError:
		raise ValueError(bcolors.FAIL + "Name not found in database" + bcolors.ENDC)

def parse_user_site(user_id):
	#parses through a user's site 
	try:
		start_time = time.time()
		db = database()
		if type(user_id) != str and type(user_id) != unicode:
			raise TypeError
		user_id = str(user_id)
		# data is user data from user collection.
		# we will be uploading our keywords to
		# keywords collection.
		user = db.users.find_one({"_id" : user_id})
		if user:
 			url_temp = user.get("profile").get("url")
		else:
			raise ValueError

		print bcolors.OKGREEN + ("parsing through: " + url_temp) + bcolors.ENDC
		user_id = user.get("_id")
		

		# there will be 2 types of tags,
		# from website, and from pdf
		tags_temp = get_html(url_temp) # this is keywords from the html
		tagsPDF_temp = get_pdf(url_temp) # this is keywords from the pdf

		seen = set()
		tags = []
		tagsPDF = []

		for item in tags_temp:
			if item not in seen:
				seen.add(item)
				tags.append(item)

		for item in tagsPDF_temp:
			if item not in seen:
				seen.add(item)
				tagsPDF.append(item)

		key_count = 0
		# update the mongoDB with html keywords, with another id generated
		seen2 = set()
		for k in range(len(tags)):
			seperateTags = tags[k].split(" ")
			for l in range(len(seperateTags)):
				if seperateTags[l] not in seen2:
					try:
						keyword_weightage = db.word_count.find({"word" : seperateTags[l].lower()})[0].get("weightage")
						seen2.add(seperateTags[l])
						key_db = {"keyword": seperateTags[l].lower(), "type" : "web", "keyword_weightage": str(keyword_weightage), "url": url_temp, "user_id": user_id}
						key_count += 1
						print key_db

						key_dict_id = db.keywords_coll.insert_one(key_db).inserted_id
					except Exception, e:
						print e
						print bcolors.FAIL + "Unable to add keyword:" + seperateTags[l] + bcolors.ENDC
		# update the mongoDB with pdf keywords, with another id generated

		for j in range(len(tagsPDF)):
			seperateTagspdf = tagsPDF[j].split(" ")
			for h in range(len(seperateTagspdf)):
				if seperateTagspdf[h] not in seen2:
					keyword_weightage = db.word_count.find({"word" : seperateTags[l].lower()})[0].get("weightage")
					seen2.add(seperateTagspdf[h])
					key_db = {"keyword": seperateTagspdf[h].lower(), "type": "pdf", "keyword_weightage" : str(keyword_weightage), "url": url_temp, "user_id": user_id}
					key_count += 1
					print key_db

					key_dict_id = db.keywords_coll.insert_one(key_db).inserted_id

		

		print ""
		print bcolors.OKGREEN + ("Took %s seconds total" % (time.time() - start_time)) + bcolors.ENDC
		print bcolors.OKGREEN + ("Went through %s" % user.get("profile.url")) + bcolors.ENDC
		print bcolors.OKGREEN + "Generated " + str(key_count) + " keywords" + bcolors.ENDC
		print bcolors.OKBLUE + "--------------------------------------------" + bcolors.ENDC + '\n'


	except TypeError:
		raise TypeError(bcolors.FAIL + "Invalid user_id" + bcolors.ENDC)
	except ValueError:
		if user_exists == True:
			raise ValueError(bcolors.FAIL + "User has no url assosciated with account" + bcolors.ENDC)
		else:
			raise ValueError(bcolors.FAIL + "Invalid User ID" + bcolors.ENDC)

	except Exception as e:
		print e
		raise

def parse_all_users():
	#parses through all the users' sites
	try:
		db = database()
		data = []
		
		#gets a list of all user ids
		for i in db.users.find():
			try:
				parse_user_site(i.get("_id"))
			except Exception as e:
				print e
				pass
		return True

	except Exception as e:
		print e
		return False

def delete_user_keywords(user_id):
	#deletes all of a single user's keywords
	try:
		db = database()
		if type(user_id) != str and type(user_id) != unicode:
			raise TypeError 
		data = db.users.find_one({"_id" : user_id})
		if data:
			db.keywords_coll.delete_many({"user_id": user_id})
		else:
			raise ValueError	

		print "User Entries Deleted"
		return True

	except TypeError, e:
		print e
		raise TypeError(bcolors.FAIL + "Invalid ID type" + bcolors.ENDC)
		return False
	except ValueError:
		raise ValueError(bcolors.FAIL + "User with given ID not found" + bcolors.ENDC)
		return False

def delete_all_keywords():
	#deletes all keywords of all users
	try:
		db = database()
		
		#deletes existing data
		db.keywords_coll.drop()
		db.word_count.drop()
		print "All Entries Deleted"
		return True

	except Exception as e:
		print e
		return False

def re_parse_all():
	#deletes existing keywords and reparses through them all
	try:
		
		#wipes existing keywords
		delete_all_keywords()
		#parse all users
		parse_all_users()

	except Exception as e:
		print e
		return False