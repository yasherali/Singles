from rest_framework import generics , status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated,AllowAny
# from loggings.utils import save_system_logs,get_username
from .serializers import *
from .utils import *
from django_notification.utils import *
from datetime import datetime
from user_management.permissions import IsAdmin, IsUser

# Create your views here.
BILLING_CYCLE_VALUE = {"monthly" : 1,"annually" : 12,"yearly" : 12}
class GetPlan(APIView):
    def get(self, request):
        response = {"status": True, "data": None}
        data = []
        plan_qs = Plan.objects.filter(i_plan_type = 1)
        try:
            active_plan = get_plan_of_customer(self.request.user.profile)
        except:
            active_plan = None
        for plan in plan_qs:
            is_subscribed = False
            price = None
            first_month_price = None
            expires_at = None
            if plan is not None:
                if active_plan is not None:
                    if plan.pk == active_plan:
                        is_subscribed = True
                        membership_obj = Membership.objects.get(i_plan__pk = active_plan, i_profile = self.request.user.profile, is_active = True)
                        expires_at = membership_obj.ends_at
            plan_charges = PlanCharges.objects.filter(i_plan =  plan.pk)
            for charges in plan_charges:
                if charges.charges_type == "monthly":
                    price = charges.price
                elif charges.charges_type == "first_month":
                    first_month_price = charges.price
            description = str(plan.description).replace(r'\\', '')
            description = description.replace('"', "'")
            data.append({
                "pk": plan.pk,
                "name" : plan.name,
                "price" : price,
                "first_month_price" : first_month_price,
                'description' : description,
                "created_at" : plan.created_at,
                "is_subscribed" : is_subscribed,
                "expires_at" : expires_at

            })
        response['data'] = data
        return Response(response)

class CreatePlan(generics.CreateAPIView):
    permission_classes = [IsAdmin]
    serializer_class = PlanSerializer

class UpdatePlan(APIView):
    permission_classes = [IsAdmin]
    serializer_class = PlanSerializer
    def post(self,request,*args,**kwargs):
        pk = kwargs.get('pk')
        response = {"status" :  False}
        try:
            instance = Plan.objects.get(pk=pk)  
            serializer = self.serializer_class(instance, data=request.data, context={'request': request})
            if serializer.is_valid():
                resp = serializer.update(instance, serializer.validated_data)  # Execute the update method
                response = resp
            else:
                response["error"] = serializer.errors
        except Exception as e:
            print (e)
            response["error"] = "Plan does not exist"
        return Response(response)

class DeletePlan(APIView):
    permission_classes = [IsAdmin]
    def post(self,request,*args,**kwargs):
        pk = kwargs.get('pk')
        response = {"status" :  False}
        try:
            instance = Plan.objects.get(pk=pk)  
            instance.delete()
            response['status'] = True
            response['message'] = "Plan deleted successfully"
        except Exception as e:
            response["error"] = "Error deleting instance does not exist"
        return Response(response)









class CreateOrUpgradeSubscription(APIView):
    permission_classes = [IsUser]
    def post(self, request):
        response ={"status": False,"message": "Default response message",
                   "status_code": status.HTTP_400_BAD_REQUEST, "data" : None}
        
        plan_id  = self.request.data.get('plan_id', None)
        billing_cycle  = self.request.data.get('billing_cycle', None)
        reference_id = self.request.data.get('reference_id', None)
        product_id = self.request.data.get('product_id', None)
        provider = self.request.data.get('provider', None)
        amount = self.request.data.get('amount', None)
        user_obj = self.request.user
        
        plan_qs = Plan.objects.filter(pk = plan_id)
        if plan_qs:
            plan_obj = plan_qs.first()
            try:
                data  = {
                    "user_obj":user_obj,"plan_obj" : plan_obj,
                    "billing_cycle" : billing_cycle, 'product_id' : product_id,
                    "reference_id" : reference_id, "provider" : provider, "amount" : amount
                }
                response = create_subscription_only(**data)
            except Exception as e:
                response["message"]=repr(e)
        else:
           response["message"]="Plan does not exist"
        
        return Response(response,status=response['status_code'])
    
class GetPackages(APIView):
    def get(self, request):
        data_lst = []
        plan_qs = Plan.objects.all()
        for plan in plan_qs:
            plan_charges = PlanCharges.objects.all()
            for charges in plan_charges:
                data_lst.append({
                    "plan_id" : plan.pk,
                    "name" : plan.name,
                    "description" : plan.description,
                    "plan_type" : charges.charges_type,
                    "price" : charges.price 
                })
        resp = {
            "status" : True,
            "status_code" : status.HTTP_200_OK,
            "message" : "Plans",
            "data" : {"plans": data_lst}
        }
        return Response(resp,status=status.HTTP_200_OK)
    
class CheckSubscription(APIView):
    def get(self, request):
        resp = {}
        try:
            subscription_obj = Membership.objects.filter(i_profile = request.user.profile, is_active = True)

            resp['status'] = True
            resp['status_code'] = status.HTTP_200_OK
            resp['message'] = "Already Subscribed"
            resp['data'] = {}
        except Membership.DoesNotExist:
            resp['status'] = False
            resp['status_code'] = status.HTTP_400_BAD_REQUEST
            resp['message'] = "No Subscription Found"
            resp['data'] = {}
        return Response(resp, status=resp['status_code'])