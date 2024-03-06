from django.shortcuts import render, redirect
from django.views import View
from django.http import HttpResponseRedirect, response, JsonResponse, HttpResponse
import requests, json
from cv_api.models import PersonalInfo, TokensForUser
from cv_api.forms import (
    PersonalInfoForm,
    OverviewForm,
    EducationfoForm,
    JobfoForm,
    JobAccomplishmentfoForm,
    ProjectsForm,
    ProgrammingAreaForm,
    SkillAndSkillLevelForm,
    PublicationForm
)
from django.views.decorators.csrf import csrf_exempt
from datetime import datetime
from datetime import date
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView
from Homepage.models import CustomUser
from cv_api.create_read_update_delete_user import TokenUtils
from django.contrib import messages
# from django.db import transaction


# from django.contrib.auth.decorators import login_required







class DateTimeEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, (datetime, date)):
            return o.isoformat()
        return json.JSONEncoder.default(self, o)




class CVApiPostRequest(TemplateView):
    template_name = "cv.html"


    def get_or_create_api_user(self, user_id):
        user = CustomUser.objects.filter(id= user_id)
        print(f"user_get_or_create_api_user_______{user}")
        
        json_response = TokenUtils.get_user(user)
        if json_response is None or []:
            json_response = TokenUtils.register_user(user)
        return json_response

    
    def get_tokens_for_user(self, user_id):
        tokens = TokenUtils.get_tokens_for_user(user_id)
        return tokens

        
    def verify_token_for_user(self, token_instance):

        access_token = token_instance.access_token
        if TokenUtils.verify_access_token_for_user(access_token):
            return True
        else:
            return False

    def get_new_access_token_for_user(self, token_instance):

        access_token = TokenUtils.get_new_access_token_for_user(token_instance.refresh_token)
        if access_token is not None:
            return access_token
        else:
            return None
 
    def create_token_instance_for_user(self, user_id):
        user = CustomUser.objects.filter(id = user_id)
        if user:
            user = user[0]
            token_instance_created_for_user = TokensForUser.objects.create(user = user)
            print("____________token_instance_created_for_user")
        return token_instance_created_for_user or None

        
    def get(self, request, **kwargs):
        access_token = None
        if "user_id" in self.request.session and self.request.user.is_authenticated:
            user_id = self.request.session["user_id"]

            user_data = self.get_or_create_api_user(user_id)
            print(f"user_data_____________{user_data['id']}")   

            token_instance = TokensForUser.objects.filter(user__id=user_id)
            print(f"token_instance_______________{token_instance}")
            if token_instance:
                token_instance = token_instance[0]
                print(f"token_instance_access_token_______________{token_instance.access_token}")
                if token_instance.access_token is not None:
                    token_is_valid = self.verify_token_for_user(token_instance)
                    if token_is_valid:
                        pass
                    else:
                        access_token = self.get_new_access_token_for_user(token_instance)
                        if access_token:
                            token_instance.access_token = access_token
                        else:
                            return JsonResponse({"access_token_in_[get_new_access_token_for_user_]" : "None"}, safe=False)
            else:
                token_instance = self.create_token_instance_for_user(user_id)

            tokens = self.get_tokens_for_user(user_id)
            access_token = tokens["access"]
            token_instance.access_token = tokens["access"]
            token_instance.refresh_token = tokens["refresh"]
            token_instance.save()
   
        else:
            return redirect("Homepage:login")
        return super().get(request, **kwargs)
    

    def get_context_data(self, **kwargs):
        context = super().get_context_data( **kwargs)
        return context

    



class CVApiSubmitForm(View):

    def get_api_user_id(self, user_id):
        try:
            personal_info_instance = PersonalInfo.objects.filter(user_id_for_personal_info__id = 
                                                    user_id).first()
            if personal_info_instance:
                api_user_id = personal_info_instance.api_user_id_for_cv
                print(f"api_user_id________________{api_user_id}")
                return api_user_id
            else:
                try:
                    user_data = {}
                    user = CustomUser.objects.filter(id = user_id)
                    token_instance = TokensForUser.objects.filter(user__id = user_id)

                    if token_instance:
                        token_instance = token_instance[0]
                    else:
                        return JsonResponse({"error" : f"token instance for user_id {user_id} not found"})

                    user_data = TokenUtils.get_user(user)
                    print(f"user_data__**************____id________________{user_data}")
                    return user_data["id"]
                except Exception as e:
                    return JsonResponse(str(e), safe=False)
        except Exception as e:
                return JsonResponse(str(e), safe=False)


    def get(self, request, **kwargs):
        api_user_id = self.get_api_user_id(self.request.user.id)
        print(f"api_user_id___________{api_user_id}")
        try:
            PersonalInfo.objects.create(user_id_for_personal_info = self.request.user,
                                        api_user_id_for_cv = api_user_id,
                                          api_id_of_cv='9999999')
        except Exception as e:
            return JsonResponse({"error________________" :str(e)})
        return HttpResponseRedirect(f"https://osamaaslam.pythonanywhere.com/api/?user_id={api_user_id}")




class ListOfCVForUser(TemplateView):
    template_name = "list_of_cv_for_user.html"
    cv_data = None

    def get_token_from_database(self, user_id):
        token_instance_for_user_id = TokensForUser.objects.filter(user__id=user_id)
        if token_instance_for_user_id:
            access_token = token_instance_for_user_id[0].access_token
            return access_token
        else:
            return None
        
    def get(self, request, **kwargs):
        user_id = self.request.user.id
        access_token = self.get_token_from_database(user_id)
        if access_token:
            personal_info_instance = PersonalInfo.objects.filter(user_id_for_personal_info__id = 
                                                    user_id).first()
            if personal_info_instance:
                api_user_id = personal_info_instance.api_user_id_for_cv
            else:
                return super().get(request, **kwargs)
            
            url = f"https://osamaaslam.pythonanywhere.com/api/get-personal-info-data-for-user/?user_id={api_user_id}"

            headers = {"Content-Type": "application/json",
                    "Authorization": f"Bearer {access_token}"}

            try:
                response = requests.get(url, headers=headers)
                print(response.json())
                response.raise_for_status()

                self.cv_data = response.json()
            except requests.RequestException as e:
                messages.error(self.request, f"Error fetching CV data: {e}")
        else:
            messages.error(self.request, "access token does not exist")
        return super().get(request, **kwargs)



    def get_context_data(self, **kwargs):
        context= super().get_context_data(**kwargs)

        if self.cv_data:
            print(self.cv_data)
            context["cv_data"] = self.cv_data
        else:
            context["cv_data"] = None
        return context 




      



class RetrieveCVDataToUpdate(View):


    def get_token_from_database(self, user_id):
        token_instance_for_user_id = TokensForUser.objects.filter(user__id=user_id)
        if token_instance_for_user_id:
            access_token = token_instance_for_user_id[0].access_token
            return access_token
        else:
            return None


    def get(self, request, **kwargs):
        user_id = self.request.user.id
        access_token = self.get_token_from_database(user_id)
        if access_token:
            # api_user_id = PersonalInfo.objects.get(user_id_for_personal_info__id = user_id).api_user_id_for_cv
            # url = f"https://diverse-intense-whippet.ngrok-free.app/api/get-personal-info-data-for-user/?user_id={api_user_id}"

            personal_info_id = kwargs["personal_info_id"]
            url = f"https://osamaaslam.pythonanywhere.com/api/api/get-personal-info-data/{personal_info_id}/"

            headers = {"Content-Type": "application/json",
                    "Authorization": f"Bearer {access_token}"}
        else:
            return JsonResponse({"error" : f"token is null / not valid / expires {access_token}"})


        # verify = Flase, is used to bypass SSL or ask the API endpoint not to validate the request
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            # convert the json to '{}' or dictionary
            json_to_dic = response.json()
            # return JsonResponse(json_to_dic, safe=False)
            try:
                overview_text = json_to_dic["overview"]
            except Exception as e:
                return JsonResponse({"error in handling keys in json_to_dic_overview": str(e)})
            try:    
                education_data = json_to_dic["education"]
            except Exception as e:
                return JsonResponse({"error in handling keys in json_to_dic_education": str(e)})
                # I have used loop, because "job" is a "list" of {}
            job_data = []
            accomplishment_data = []

            try:
                accomplishment_data = json_to_dic["job"]["accomplishment"]
            except Exception as e:
                return JsonResponse({"error in handling keys in json_to_dic": str(e)})
                
            print(f"accomplishment_data____________{accomplishment_data}")
            del json_to_dic["job"]["accomplishment"]
            
            print(f"job_____________________{json_to_dic['job']}")
                
            try:    
                job_data = json_to_dic["job"]
            except Exception as e:
                return JsonResponse({"error in handling keys in json_to_dic_job": str(e)})
            try:
                skill_data = json_to_dic["skill"]
            except Exception as e:
                return JsonResponse({"error in handling keys in json_to_dic_skill": str(e)})
            try:    
                programming_area_data = json_to_dic["programming_area"]
            except Exception as e:
                return JsonResponse({"error in handling keys in json_to_dic_programming_area": str(e)})
            try:    
                projects_data = json_to_dic["projects"]
            except Exception as e:
                return JsonResponse({"error in handling keys in json_to_dic_projects": str(e)})
            try:    
                publication_data = json_to_dic["publications"]
            except Exception as e:
                return JsonResponse({"error in handling keys in json_to_dic_publication": str(e)})





            del json_to_dic["overview"]
            del json_to_dic["projects"]
            del json_to_dic["programming_area"]
            del json_to_dic["education"]
            del json_to_dic["job"]
            del json_to_dic["skill"]
            del json_to_dic["publications"]

            personal_info = json_to_dic

            # Convert dates to mm/dd/yyyy format
            for education in education_data:
                if (
                    "education_start_date" in education
                    and "education_end_date" in education
                ):
                    if (
                        education["education_start_date"]
                        and education["education_end_date"]
                    ):
                        education["education_start_date"] = datetime.strptime(
                            education["education_start_date"], "%Y-%m-%d"
                        ).strftime("%Y-%m-%d")
                        education["education_end_date"] = datetime.strptime(
                            education["education_end_date"], "%Y-%m-%d"
                        ).strftime("%Y-%m-%d")

            if "job_start_date" in job_data and "job_end_date" in job_data:
                if job_data["job_start_date"] and job_data["job_end_date"]:
                    job_data["job_start_date"] = datetime.strptime(
                        job_data["job_start_date"], "%Y-%m-%d"
                    ).strftime("%Y/%m/%d")
                    job_data["job_end_date"] = datetime.strptime(
                        job_data["job_end_date"], "%Y-%m-%d"
                    ).strftime("%Y/%m/%d")

            form = PersonalInfoForm(initial=personal_info)
            overview_form = OverviewForm(initial=overview_text)

            education_form_list = []
            for items in education_data:
                education_form = EducationfoForm(initial=items)
                education_form_list.append(education_form)

            job_form = JobfoForm(initial=job_data)
            accomplishment_form = JobAccomplishmentfoForm(initial=accomplishment_data)

            skill_form_list = []
            for skill in skill_data:
                skill_form = SkillAndSkillLevelForm(initial=skill)
                skill_form_list.append(skill_form)

            programming_area_form_list = []
            for programming_area in programming_area_data:
                programming_area_form = ProgrammingAreaForm(initial=programming_area)
                programming_area_form_list.append(programming_area_form)

            projects_form_list = []
            for projects in projects_data:
                projects_form = ProjectsForm(initial=projects)
                projects_form_list.append(projects_form)

            publication_form_list = []
            for publication in publication_data:
                publication_form = PublicationForm(initial=publication)
                publication_form_list.append(publication_form)



            response = render(
                self.request,
                "cv_api.html",
                {
                    "form": form,
                    "overview_form": overview_form,
                    "education_form": education_form_list,
                    "job_form": job_form,
                    "accomplishment_form": accomplishment_form,
                    "skill_form": skill_form_list,
                    "programming_area_form": programming_area_form_list,
                    "projects_form": projects_form_list,
                    "publication_form": publication_form_list,
                },
            )

            # cookie set by backend, it is not encrypted
            response.set_cookie(
                "cv_data",
                json.dumps(
                    {
                        "education_data": education_data,
                        "job_data": job_data,
                        "accomplishment_data": accomplishment_data,
                        "skill_data": skill_data,
                        "projects_data": projects_data,
                        "overview_text": overview_text,
                        "programming_area_data": programming_area_data,
                        "personal_info": personal_info,
                        "publications" : publication_data
                    }
                ),
            )

            return response
        else:
            return JsonResponse({"page": "not found"})

    def post(self, request, **kwargs):
        personal_info_id = kwargs["personal_info_id"]

        if request.method == "POST":
            # return {} if cookie named "cv_data" not in browser
            cookie_data = json.loads(request.COOKIES.get("cv_data", "{}"))

            overview_text_data = cookie_data["overview_text"]
            education_data = cookie_data["education_data"]
            job_data = cookie_data["job_data"]
            accomplishment_data = cookie_data["accomplishment_data"]
            skill_data = cookie_data["skill_data"]
            programming_area_data = cookie_data["programming_area_data"]
            projects_data = cookie_data["projects_data"]
            personal_info = cookie_data["personal_info"]
            publication_data = cookie_data["publications"]
       


            # since i have not stored the data in database, we parse the instances
            # from cookie provided as initial values
            # Remember! initial must be a dictionary
            # Do Not Get Confuse! initial contains actuall values of fiels of instance
            # parse from the API endpoint
            form = PersonalInfoForm(self.request.POST, initial=personal_info)
            overview_form = OverviewForm(self.request.POST, initial=overview_text_data)

            education_form_list = []
            for form_data in education_data:
                education_form = EducationfoForm(self.request.POST, initial=form_data)
                education_form_list.append(education_form)

            job_form = JobfoForm(self.request.POST, initial=job_data)

            accomplishment_form = JobAccomplishmentfoForm(
                self.request.POST, initial=accomplishment_data
            )

            skill_form_list = []
            for skill in skill_data:
                skill_form = SkillAndSkillLevelForm(self.request.POST, initial=skill)
                skill_form_list.append(skill_form)

            programming_area_form_list = []
            for programming_area in programming_area_data:
                programming_area_form = ProgrammingAreaForm(
                    self.request.POST, initial=programming_area
                )
                programming_area_form_list.append(programming_area_form)

            projects_form_list = []
            for project in projects_data:
                projects_form = ProjectsForm(self.request.POST, initial=project)
                projects_form_list.append(projects_form)

            publication_form_list = []
            for publication in publication_data:
                publication_form = PublicationForm(self.request.POST, initial=publication)
                publication_form_list.append(publication_form)

            if (
                form.is_valid() and overview_form.is_valid() and [education_form.is_valid() for education_form in education_form_list] and job_form.is_valid() and accomplishment_form.is_valid() and [skill_form.is_valid() for skill_form in skill_form_list] and [programming_area_form.is_valid()for programming_area_form in programming_area_form_list] and [projects_form.is_valid() for projects_form in projects_form_list] or [publication_form.is_valid() for publication_form in publication_form_list]
            ):

                # convert the HTML <form> to dictionary
                personalinfo_dic = form.cleaned_data
                overview_dic = overview_form.cleaned_data

                education_dic_list = []
                for education_form in education_form_list:
                    education_dic = education_form.cleaned_data
                    # The API expects the date to be in '%Y-%m-%d'
                    education_dic["education_start_date"] = education_dic[
                        "education_start_date"
                    ].strftime("%Y-%m-%d")
                    education_dic["education_end_date"] = education_dic[
                        "education_end_date"
                    ].strftime("%Y-%m-%d")
                    education_dic_list.append(education_dic)

                job_dic = job_form.cleaned_data
                if "job_start_date" in job_dic and "job_end_date" in job_dic:
                    if job_dic["job_start_date"] and job_dic["job_end_date"]:
                        job_dic["job_start_date"] = job_dic["job_start_date"].strftime(
                            "%Y-%m-%d"
                        )
                        print(job_dic["job_start_date"])
                        job_dic["job_end_date"] = job_dic["job_end_date"].strftime("%Y-%m-%d")
                        print(job_dic["job_end_date"])
                    else:
                        pass
                    

                accomplishment_dic = accomplishment_form.cleaned_data

                skill_dic_list = []
                for skill_form in skill_form_list:
                    skill_dic = skill_form.cleaned_data
                    skill_dic_list.append(skill_dic)

                programming_area_dic_list = []
                for programming_area_form in programming_area_form_list:
                    programming_area_dic = programming_area_form.cleaned_data
                    programming_area_dic_list.append(programming_area_dic)

                projects_dic_list = []
                for projects_form in projects_form_list:
                    project_dic = projects_form.cleaned_data
                    projects_dic_list.append(project_dic)

                
                publication_dic_list = []
                for publication_form in publication_form_list:
                    publication_dic = publication_form.cleaned_data
                    publication_dic_list.append(publication_dic)

                # making the dictionary manually
                personal_info = personalinfo_dic
                personal_info["overview"] = overview_dic

                # The API expects education to be list of dictionaries
                personal_info["education"] = education_dic_list
                # The API expects accomplishment nested within Job
                job_dic["accomplishment"] = accomplishment_dic
                personal_info["job"] = job_dic
                # The API expects skill to be list of dictionaries
                personal_info["skill"] = skill_dic_list
                personal_info["programming_area"] = programming_area_dic_list
                personal_info["projects"] = projects_dic_list
                personal_info["publications"] = publication_dic_list


                user_id = self.request.user.id
                access_token = self.get_token_from_database(user_id)
                if access_token:
                    # api_user_id = 1
                    api_user_id = PersonalInfo.objects.get(user_id_for_personal_info__id = user_id, 
                                                           api_id_of_cv = personal_info_id).api_user_id_for_cv
                    url = f"https://osamaaslam.pythonanywhere.com/api/patch-put-personal-info-data-for-user/?id={personal_info_id}&user_id={api_user_id}"

                    headers = {"Content-Type": "application/json",
                            "Authorization": f"Bearer {access_token}"}

                # personal_info_id = kwargs["personal_info_id"]
                # url = f"https://diverse-intense-whippet.ngrok-free.app/api/api/get-personal-info-data/{personal_info_id}/"
                # headers = {"Content-Type": "application/json"}

                try:
                    json_data = json.dumps(personal_info, cls=DateTimeEncoder)
                except Exception as e:
                    return JsonResponse({"personal_info_dic_dump__error": str(e)})

                response = requests.patch(
                    url, headers=headers, data=json_data)
                if response.status_code == 200:
                    return JsonResponse({"message": json_data})
                else:
                    return JsonResponse({"personal_info_json_status": json_data})
            else:

                return redirect("cv_api:get_cv_to_update" , personal_info_id=personal_info_id)
        else:
            return HttpResponse("Invalid request method")




class DeleteCVForUser(View):
    template_name = "list_of_cv_for_user.html"

    def get_token_from_database(self, user_id):
        instance_for_access_token = TokensForUser.objects.filter(user__id=user_id)
        if instance_for_access_token:
            access_token = instance_for_access_token[0].access_token
            return access_token
        else:
            return None
        
    def get(self, request, **kwargs):
        user_id = self.request.user.id
        access_token = self.get_token_from_database(user_id)
        if access_token:
           
            headers = {"Content-Type": "application/json",
                    "Authorization": f"Bearer {access_token}"}

            personal_info_id = kwargs["personal_info_id"] 
            url = f"https://osamaaslam.pythonanywhere.com/api/api/get-personal-info-data/{personal_info_id}/"

            try:
                response = requests.delete(url, headers=headers)
                # Raise exception for any error status code
                if response.status_code == 200:
                    return HttpResponseRedirect("/")
                else:
                    return JsonResponse({"response" : str(response.status_code)})
            except requests.RequestException as e:
                return JsonResponse({"error" : f"Error fetching CV data: {e}"})
        else:    
            return JsonResponse({"error" : f"token not valid / expires "})




@method_decorator(csrf_exempt, name="dispatch")
class WebHookEvent(View):
    def post(self, request, **kwargs):
        try:
            data = json.loads(request.body)
            print(f"request.body________________{request.body}")
            try:

                personal_info = PersonalInfo.objects.filter(api_id_of_cv = data["id"], 
                                                            api_user_id_for_cv = data['user_id'])
                if personal_info:
                    personal_info = personal_info[0]
                else:
                    personal_info = PersonalInfo.objects.filter(api_id_of_cv = '9999999', 
                                                            api_user_id_for_cv = data['user_id'])
                    personal_info = personal_info[0]                                         

            except Exception as e:
                print(f"________exception as e: {str(e)}")
                return JsonResponse({"error" : str(e)})

            if data["event"] == "cv_created":
                try:
            
                    personal_info.status = data["status"]
                    personal_info.api_id_of_cv = data["id"]
                    personal_info.save()

                    return JsonResponse(
                        {
                            "status": data["status"],
                            "instance_id": f"instance with id= {data['id']}",
                        }
                    )
                except Exception as e:
                    return JsonResponse({"error": str(e)})



            if data["event"] == "cv_updated":
                try:
            
                    personal_info.status = data["status"]
                    print(f"status________________{personal_info.status}")
                    personal_info.save()

                    return JsonResponse(
                        {
                            "status": data["status"],
                            "instance_id": f"instance with id= {data['id']}",
                        }
                    )
                except Exception as e:
                    return JsonResponse({"error": str(e)})
            
            elif data["event"] == "cv_deleted":
                try:
                    personal_info.delete()

                    return JsonResponse(
                        {
                            "status": data["status"],
                            "instance_id": f"instance with id= {data['id']}",
                        }
                    )
                except Exception as e:
                    return JsonResponse({"error": str(e)})
                    
            elif data["event"] == "cv_deletIion_failed":
                try:
                    personal_info.status = data["status"]
                    personal_info.save()

                    return JsonResponse(
                        {
                            "status": data["status"],
                            "instance_id": f"instance with id= {data['id']}",
                        }
                    )
                except Exception as e:
                    return JsonResponse({"error": str(e)})


            elif data["event"] == "cv_update_failed":
                try:
                    personal_info.status = data["status"]
                    personal_info.save()

                    return JsonResponse(
                        {
                            "status": data["status"],
                            "instance_id": f"instance with id= {data['id']}",
                        }
                    )
                except Exception as e:
                    return JsonResponse({"error": str(e)})
            

            else:
                return JsonResponse({"event_type": "event type is not cv_updated/cv_deleted"})
        except Exception as e:
            return JsonResponse({"data error": str(e)})
